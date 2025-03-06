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

@bp.route('/delete/<int:id>')
@login_required
def delete(id):
    vehicle = Vehicle.query.get_or_404(id)
    if not current_user.is_admin and vehicle.user_id != current_user.id:
        flash('您没有权限删除此车辆信息')
        return redirect(url_for('vehicle.index'))
        
    db.session.delete(vehicle)
    db.session.commit()
    flash('车辆信息已删除')
    return redirect(url_for('vehicle.index'))

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
    filepath = os.path.join(current_app.instance_path, filename)
    os.makedirs(current_app.instance_path, exist_ok=True)
    export_vehicles_to_excel(vehicles, filepath)
    
    return send_file(filepath, 
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

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