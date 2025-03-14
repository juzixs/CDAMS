from datetime import datetime
import os
from flask import render_template, flash, redirect, url_for, request, jsonify, send_file, current_app, session
from flask_login import login_required, current_user
from sqlalchemy import or_
from werkzeug.utils import secure_filename
from app import db
from app.vehicle.license_plate import bp
from app.models import Vehicle
from app.vehicle.license_plate.forms import VehicleForm
from app.vehicle.license_plate.utils import export_vehicles_to_excel, import_vehicles_from_excel, create_import_template
from app.utils.pdf_generator import generate_vehicle_pass_pdf
from flask_wtf import FlaskForm
import pandas as pd
from io import BytesIO

class EmptyForm(FlaskForm):
    pass

@bp.route('/')
@login_required
def index():
    """车辆通行证首页"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    vehicle_type = request.args.get('vehicle_type', '')
    department = request.args.get('department', '')
    per_page = request.args.get('per_page', 10, type=int)
    
    query = Vehicle.query
    
    if search:
        query = query.filter(
            or_(
                Vehicle.plate_number.contains(search),
                Vehicle.owner_name.contains(search),
                Vehicle.department.contains(search)
            )
        )
    
    if status:
        query = query.filter_by(status=status)
        
    if vehicle_type:
        query = query.filter_by(vehicle_type=vehicle_type)
        
    if department:
        query = query.filter_by(department=department)
    
    vehicles = query.order_by(Vehicle.created_at.desc()).paginate(page=page, per_page=per_page)
    
    # 在会话中记录当前页面为车辆通行证页面
    session['vehicle_list_source'] = 'index'
    
    # 创建空表单用于CSRF保护
    form = EmptyForm()
    
    return render_template('vehicle/license_plate/index.html', 
                         vehicles=vehicles, 
                         search=search, 
                         status=status,
                         vehicle_type=vehicle_type,
                         department=department,
                         form=form)

@bp.route('/pending')
@login_required
def pending():
    """待审核车辆列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    vehicles = Vehicle.query.filter_by(status='pending').order_by(Vehicle.created_at.desc()).paginate(page=page, per_page=per_page)
    
    # 在会话中记录当前页面为待审核页面
    session['vehicle_list_source'] = 'pending'
    
    return render_template('vehicle/license_plate/pending.html', vehicles=vehicles)

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
        return redirect(url_for('license_plate.index'))
    return render_template('vehicle/license_plate/add.html', form=form)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    vehicle = Vehicle.query.get_or_404(id)
    if not current_user.is_admin and vehicle.user_id != current_user.id:
        flash('您没有权限编辑此车辆信息')
        return redirect(url_for('license_plate.index'))
    
    form = VehicleForm(obj=vehicle)
    if form.validate_on_submit():
        # 检查新车牌号是否与其他记录重复
        existing_vehicle = Vehicle.query.filter(
            Vehicle.plate_number == form.plate_number.data,
            Vehicle.id != id
        ).first()
        
        if existing_vehicle:
            flash(f'车牌号 {form.plate_number.data} 已存在，请使用其他车牌号')
            return render_template('vehicle/license_plate/edit.html', form=form, vehicle=vehicle)
            
        try:
            vehicle.plate_number = form.plate_number.data
            vehicle.vehicle_type = form.vehicle_type.data
            vehicle.owner_name = form.owner_name.data
            vehicle.department = form.department.data
            vehicle.remarks = form.remarks.data
            db.session.commit()
            flash('车辆信息已更新')
            
            # 根据会话中记录的来源页面决定跳转目标
            source = session.get('vehicle_list_source', 'index')
            if source == 'pending':
                return redirect(url_for('license_plate.pending'))
            else:
                return redirect(url_for('license_plate.index'))
            
        except Exception as e:
            db.session.rollback()
            flash('更新失败，请稍后重试')
            return render_template('vehicle/license_plate/edit.html', form=form, vehicle=vehicle)
        
    return render_template('vehicle/license_plate/edit.html', form=form, vehicle=vehicle)

@bp.route('/delete/<int:id>')
@login_required
def delete(id):
    vehicle = Vehicle.query.get_or_404(id)
    if not current_user.is_admin and vehicle.user_id != current_user.id:
        flash('您没有权限删除此车辆信息')
        return redirect(url_for('license_plate.index'))
        
    db.session.delete(vehicle)
    db.session.commit()
    flash('车辆信息已删除')
    return redirect(url_for('license_plate.index'))

@bp.route('/approve/<int:id>')
@login_required
def approve(id):
    if not current_user.is_admin:
        flash('只有管理员可以审核车辆信息')
        return redirect(url_for('license_plate.index'))
        
    vehicle = Vehicle.query.get_or_404(id)
    vehicle.status = 'approved'
    db.session.commit()
    flash('车辆信息已审核通过')
    return redirect(url_for('license_plate.pending'))

@bp.route('/reject/<int:id>')
@login_required
def reject(id):
    if not current_user.is_admin:
        flash('只有管理员可以审核车辆信息')
        return redirect(url_for('license_plate.index'))
        
    vehicle = Vehicle.query.get_or_404(id)
    vehicle.status = 'rejected'
    db.session.commit()
    flash('车辆信息已被拒绝')
    return redirect(url_for('license_plate.pending'))

@bp.route('/issue/<int:id>')
@login_required
def issue(id):
    if not current_user.is_admin:
        flash('只有管理员可以发放车牌')
        return redirect(url_for('license_plate.index'))
        
    vehicle = Vehicle.query.get_or_404(id)
    vehicle.issued_at = datetime.utcnow()
    db.session.commit()
    flash('车牌已发放')
    return redirect(url_for('license_plate.index'))

@bp.route('/generate_pdf', methods=['POST'])
@login_required
def generate_pdf():
    if not current_user.is_admin:
        flash('权限不足', 'danger')
        return redirect(url_for('license_plate.index'))
        
    # 获取选中的车辆ID
    vehicle_ids = request.form.getlist('vehicle_ids[]')
    if not vehicle_ids:
        flash('请至少选择一个车牌', 'warning')
        return redirect(url_for('license_plate.index'))
        
    try:
        # 查询选中的车辆
        vehicles = Vehicle.query.filter(Vehicle.id.in_(vehicle_ids)).all()
        plate_numbers = [v.plate_number for v in vehicles]
        
        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'vehicle_pass_{timestamp}.pdf'
        
        # 设置输出路径
        output_dir = os.path.join(current_app.root_path, 'static', 'pdfs')
        output_path = os.path.join(output_dir, filename)
        
        # 生成PDF
        count = generate_vehicle_pass_pdf(plate_numbers, output_path)
        
        # 返回生成的PDF文件
        return send_file(
            output_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'生成PDF失败: {str(e)}', 'danger')
        return redirect(url_for('license_plate.index'))

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
    df.to_excel(writer, sheet_name='车辆通行证', index=False)
    
    # 自动调整列宽
    worksheet = writer.sheets['车辆通行证']
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

@bp.route('/import_template')
@login_required
def import_template():
    """下载导入模板"""
    filename = 'vehicle_import_template.xlsx'
    
    # 创建内存中的Excel文件，而不是保存到文件系统
    df = pd.DataFrame(columns=['车牌号', '车辆类型', '车主姓名', '所属部门', '备注'])
    df.loc[0] = ['浙A12345', '燃油', '张三', '技术部', '示例数据，导入时请删除此行']
    
    # 创建内存中的Excel文件
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='车辆通行证', index=False)
    
    # 自动调整列宽
    worksheet = writer.sheets['车辆通行证']
    for i, col in enumerate(df.columns):
        column_width = max(len(col) + 2, 15)  # 最小宽度为15
        worksheet.set_column(i, i, column_width)
    
    # 添加说明sheet
    instructions_data = {
        '字段': ['车牌号', '车辆类型', '车主姓名', '所属部门', '备注'],
        '说明': [
            '车辆牌照号码（必填）',
            '车辆类型，如：燃油、新能源（必填）',
            '车主姓名（必填）',
            '所属部门（必填）',
            '备注信息（可选）'
        ],
        '是否必填': ['是', '是', '是', '是', '否']
    }
    
    # 创建说明DataFrame
    instructions_df = pd.DataFrame(instructions_data)
    instructions_df.to_excel(writer, sheet_name='填写说明', index=False)
    
    # 设置说明sheet的列宽
    instructions_worksheet = writer.sheets['填写说明']
    instructions_worksheet.set_column(0, 0, 15)
    instructions_worksheet.set_column(1, 1, 30)
    instructions_worksheet.set_column(2, 2, 10)
    
    writer.close()
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@bp.route('/batch_action', methods=['POST'])
@login_required
def batch_action():
    if not current_user.is_admin:
        flash('只有管理员可以审核车辆信息')
        return redirect(url_for('license_plate.index'))
    
    action = request.args.get('action')
    if action == 'approve_all':
        # 全部通过
        vehicles = Vehicle.query.filter_by(status='pending').all()
        for vehicle in vehicles:
            vehicle.status = 'approved'
        db.session.commit()
        flash('已通过所有待审核车辆')
    elif action == 'reject_all':
        # 全部拒绝
        vehicles = Vehicle.query.filter_by(status='pending').all()
        for vehicle in vehicles:
            vehicle.status = 'rejected'
        db.session.commit()
        flash('已拒绝所有待审核车辆')
    elif action in ['batch_approve', 'batch_reject']:
        # 批量操作选中项
        vehicle_ids = request.form.getlist('vehicle_ids[]')
        if not vehicle_ids:
            flash('请选择要操作的车牌')
            return redirect(url_for('license_plate.pending'))
        
        status = 'approved' if action == 'batch_approve' else 'rejected'
        vehicles = Vehicle.query.filter(Vehicle.id.in_(vehicle_ids)).all()
        for vehicle in vehicles:
            vehicle.status = status
        db.session.commit()
        message = '已通过选择的车辆' if status == 'approved' else '已拒绝选择的车辆'
        flash(message)
    
    return redirect(url_for('license_plate.pending'))

@bp.route('/batch_delete', methods=['POST'])
@login_required
def batch_delete():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '没有权限执行此操作'}), 403

    vehicle_ids = request.form.getlist('vehicle_ids[]')
    if not vehicle_ids:
        return jsonify({'success': False, 'message': '请选择要删除的车辆'}), 400
        
    # 获取当前页码和每页显示条数
    current_page = request.form.get('page', 1, type=int)
    per_page = request.form.get('per_page', 10, type=int)
    search = request.form.get('search', '')
    status = request.form.get('status', '')
    vehicle_type = request.form.get('vehicle_type', '')
    department = request.form.get('department', '')
    
    try:
        # 先获取要删除的车辆
        vehicles = Vehicle.query.filter(Vehicle.id.in_(vehicle_ids)).all()
        
        # 执行删除操作
        for vehicle in vehicles:
            db.session.delete(vehicle)
        db.session.commit()
        
        # 查询总数，计算新的总页数
        query = Vehicle.query
        if search:
            query = query.filter(
                or_(
                    Vehicle.plate_number.contains(search),
                    Vehicle.owner_name.contains(search),
                    Vehicle.department.contains(search)
                )
            )
        
        if status:
            query = query.filter_by(status=status)
            
        if vehicle_type:
            query = query.filter_by(vehicle_type=vehicle_type)
            
        if department:
            query = query.filter_by(department=department)
        
        # 计算总记录数和总页数
        total_items = query.count()
        total_pages = (total_items + per_page - 1) // per_page if total_items > 0 else 1
        
        # 决定重定向策略
        if total_items == 0:
            # 如果没有任何数据，则重定向到第一页
            return jsonify({
                'success': True, 
                'message': '删除成功',
                'redirect': True,
                'url': url_for('license_plate.index', page=1, 
                              search=search, status=status, 
                              vehicle_type=vehicle_type, department=department,
                              per_page=per_page)
            })
        elif current_page > total_pages:
            # 如果当前页超过了总页数，则重定向到最后一页
            return jsonify({
                'success': True, 
                'message': '删除成功',
                'redirect': True,
                'url': url_for('license_plate.index', page=total_pages, 
                              search=search, status=status, 
                              vehicle_type=vehicle_type, department=department,
                              per_page=per_page)
            })
        
        # 当前页有效，无需重定向
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        # 回滚事务并记录错误
        db.session.rollback()
        print(f"批量删除错误: {str(e)}")
        return jsonify({'success': False, 'message': '删除操作失败，请稍后重试'}), 500 