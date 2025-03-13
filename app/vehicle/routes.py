from datetime import datetime
import os
from flask import render_template, flash, redirect, url_for, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_
from werkzeug.utils import secure_filename
from app import db
from app.vehicle import bp
from app.models import Vehicle
from app.vehicle.forms import VehicleForm
from app.vehicle.utils import export_vehicles_to_excel, import_vehicles_from_excel
import pandas as pd
from io import BytesIO

@bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    vehicle_type = request.args.get('vehicle_type', '')
    department = request.args.get('department', '')
    
    query = Vehicle.query
    
    if not current_user.is_admin:
        query = query.filter_by(user_id=current_user.id)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Vehicle.plate_number.ilike(search_term),
                Vehicle.owner_name.ilike(search_term),
                Vehicle.department.ilike(search_term)
            )
        )
    
    if status:
        if status == 'issued':
            query = query.filter(Vehicle.issued_at != None)
        elif status == 'not_issued':
            query = query.filter(Vehicle.issued_at == None)
        else:
            query = query.filter_by(status=status)
            
    if vehicle_type:
        query = query.filter_by(vehicle_type=vehicle_type)
    if department:
        query = query.filter_by(department=department)
        
    vehicles = query.order_by(Vehicle.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('vehicle/index.html', vehicles=vehicles)

@bp.route('/pending')
@login_required
def pending():
    if not current_user.is_admin:
        flash('只有管理员可以访问此页面')
        return redirect(url_for('vehicle.index'))
    
    page = request.args.get('page', 1, type=int)
    vehicles = Vehicle.query.filter_by(status='pending').order_by(Vehicle.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('vehicle/pending.html', vehicles=vehicles)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = VehicleForm()
    if form.validate_on_submit():
        vehicle = Vehicle(
            plate_number=form.plate_number.data,
            vehicle_type=form.vehicle_type.data,
            owner_name=form.owner_name.data,
            department=form.department.data,
            remarks=form.remarks.data,
            status='approved' if current_user.is_admin else 'pending',
            user_id=current_user.id
        )
        db.session.add(vehicle)
        db.session.commit()
        flash('车辆信息已添加')
        return redirect(url_for('vehicle.index'))
    return render_template('vehicle/add.html', form=form)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    vehicle = Vehicle.query.get_or_404(id)
    if not current_user.is_admin and vehicle.user_id != current_user.id:
        flash('您没有权限编辑此车辆信息')
        return redirect(url_for('vehicle.index'))
        
    form = VehicleForm(obj=vehicle)
    if form.validate_on_submit():
        vehicle.plate_number = form.plate_number.data
        vehicle.vehicle_type = form.vehicle_type.data
        vehicle.owner_name = form.owner_name.data
        vehicle.department = form.department.data
        vehicle.remarks = form.remarks.data
        db.session.commit()
        flash('车辆信息已更新')
        return redirect(url_for('vehicle.index'))
    return render_template('vehicle/edit.html', form=form, vehicle=vehicle)

@bp.route('/batch_delete', methods=['POST'])
@login_required
def batch_delete():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '没有权限执行此操作'}), 403

    vehicle_ids = request.form.getlist('vehicle_ids[]')
    if not vehicle_ids:
        return jsonify({'success': False, 'message': '请选择要删除的车辆'}), 400

    try:
        # 获取当前页码和查询参数
        current_page = request.args.get('page', 1, type=int)
        
        # 删除选中的车辆
        vehicles = Vehicle.query.filter(Vehicle.id.in_(vehicle_ids)).all()
        for vehicle in vehicles:
            db.session.delete(vehicle)
        db.session.commit()
        
        # 检查当前页是否还有数据
        query = Vehicle.query
        if not current_user.is_admin:
            query = query.filter_by(user_id=current_user.id)
        total_pages = (query.count() + 9) // 10  # 10是每页的记录数
        
        # 如果当前页大于总页数，返回前一页
        if current_page > total_pages and current_page > 1:
            return jsonify({
                'success': True, 
                'message': '删除成功',
                'redirect': url_for('vehicle.index', page=current_page-1)
            })
            
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/delete/<int:id>')
@login_required
def delete(id):
    vehicle = Vehicle.query.get_or_404(id)
    if not current_user.is_admin and vehicle.user_id != current_user.id:
        flash('您没有权限删除此车辆信息')
        return redirect(url_for('vehicle.index'))
    
    try:
        # 获取当前页码
        current_page = request.args.get('page', 1, type=int)
        
        # 删除车辆
        db.session.delete(vehicle)
        db.session.commit()
        
        # 检查当前页是否还有数据
        query = Vehicle.query
        if not current_user.is_admin:
            query = query.filter_by(user_id=current_user.id)
        total_pages = (query.count() + 9) // 10  # 10是每页的记录数
        
        flash('车辆信息已删除')
        
        # 如果当前页大于总页数，返回前一页
        if current_page > total_pages and current_page > 1:
            return redirect(url_for('vehicle.index', page=current_page-1))
            
        return redirect(url_for('vehicle.index', page=current_page))
    except Exception as e:
        db.session.rollback()
        flash('删除失败：' + str(e))
        return redirect(url_for('vehicle.index', page=current_page))

@bp.route('/approve/<int:id>')
@login_required
def approve(id):
    if not current_user.is_admin:
        flash('只有管理员可以审核车辆信息')
        return redirect(url_for('vehicle.index'))
        
    vehicle = Vehicle.query.get_or_404(id)
    vehicle.status = 'approved'
    db.session.commit()
    flash('车辆信息已审核通过')
    return redirect(url_for('vehicle.pending'))

@bp.route('/reject/<int:id>')
@login_required
def reject(id):
    if not current_user.is_admin:
        flash('只有管理员可以审核车辆信息')
        return redirect(url_for('vehicle.index'))
        
    vehicle = Vehicle.query.get_or_404(id)
    vehicle.status = 'rejected'
    db.session.commit()
    flash('车辆信息已被拒绝')
    return redirect(url_for('vehicle.pending'))

@bp.route('/issue/<int:id>')
@login_required
def issue(id):
    if not current_user.is_admin:
        flash('只有管理员可以发放车牌')
        return redirect(url_for('vehicle.index'))
        
    vehicle = Vehicle.query.get_or_404(id)
    vehicle.issued_at = datetime.utcnow()
    db.session.commit()
    flash('车牌已发放')
    return redirect(url_for('vehicle.index'))

@bp.route('/generate_pdf', methods=['POST'])
@login_required
def generate_pdf():
    if not current_user.is_admin:
        return jsonify({'error': '只有管理员可以生成PDF'}), 403
        
    vehicle_ids = request.form.getlist('vehicle_ids[]')
    # TODO: 实现PDF生成功能
    return jsonify({'message': 'PDF生成功能待实现'})

@bp.route('/export')
@login_required
def export():
    # 获取筛选条件
    status = request.args.get('status', '')
    vehicle_type = request.args.get('vehicle_type', '')
    department = request.args.get('department', '')
    search = request.args.get('search', '')
    
    query = Vehicle.query
    
    if not current_user.is_admin:
        query = query.filter_by(user_id=current_user.id)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Vehicle.plate_number.ilike(search_term),
                Vehicle.owner_name.ilike(search_term),
                Vehicle.department.ilike(search_term)
            )
        )
    
    if status:
        if status == 'issued':
            query = query.filter(Vehicle.issued_at != None)
        elif status == 'not_issued':
            query = query.filter(Vehicle.issued_at == None)
        else:
            query = query.filter_by(status=status)
    
    if vehicle_type:
        query = query.filter_by(vehicle_type=vehicle_type)
    if department:
        query = query.filter_by(department=department)
    
    vehicles = query.all()
    
    # 生成Excel文件
    filename = f'vehicles_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    # 创建内存中的Excel文件，而不是保存到文件系统
    data = []
    for vehicle in vehicles:
        data.append({
            '车牌号': vehicle.plate_number,
            '车辆类型': vehicle.vehicle_type,
            '车主姓名': vehicle.owner_name,
            '所属部门': vehicle.department,
            '备注': vehicle.remarks,
            '状态': vehicle.status,
            '创建时间': vehicle.created_at.strftime('%Y-%m-%d %H:%M:%S') if vehicle.created_at else '',
            '发放时间': vehicle.issued_at.strftime('%Y-%m-%d %H:%M:%S') if vehicle.issued_at else ''
        })
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 创建内存中的Excel文件
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='车辆信息', index=False)
    
    # 自动调整列宽
    worksheet = writer.sheets['车辆信息']
    for i, col in enumerate(df.columns):
        column_width = max(df[col].astype(str).map(len).max(), len(col) + 2)
        worksheet.set_column(i, i, column_width)
    
    writer.close()
    output.seek(0)
    
    return send_file(
        output, 
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@bp.route('/import', methods=['POST'])
@login_required
def import_vehicles():
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not file.filename.endswith('.xlsx'):
        return jsonify({'error': '只支持.xlsx格式的Excel文件'}), 400
    
    try:
        success_count, error_messages = import_vehicles_from_excel(file, current_user.id)
        
        response = {
            'success_count': success_count,
            'error_messages': error_messages
        }
        
        if success_count > 0:
            response['message'] = f'成功导入{success_count}条记录'
        
        if error_messages:
            response['error'] = '部分数据导入失败，请查看详细信息'
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': f'导入失败：{str(e)}'}), 400 