from datetime import datetime
import os
from flask import render_template, flash, redirect, url_for, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_
from werkzeug.utils import secure_filename
from app import db
from app.vehicle.license_plate import bp
from app.models import Vehicle
from app.vehicle.license_plate.forms import VehicleForm
from app.vehicle.license_plate.utils import export_vehicles_to_excel, import_vehicles_from_excel, create_import_template
from app.utils.pdf_generator import generate_vehicle_pass_pdf

@bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
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
        query = query.filter(Vehicle.department.ilike(f"%{department}%"))
        
    vehicles = query.order_by(Vehicle.created_at.desc()).paginate(page=page, per_page=per_page)
    return render_template('vehicle/license_plate/index.html', vehicles=vehicles)

@bp.route('/pending')
@login_required
def pending():
    if not current_user.is_admin:
        flash('只有管理员可以访问此页面')
        return redirect(url_for('license_plate.index'))
    
    page = request.args.get('page', 1, type=int)
    vehicles = Vehicle.query.filter_by(status='pending').order_by(Vehicle.created_at.desc()).paginate(page=page, per_page=10)
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
            
            # 根据来源页面决定跳转目标
            if request.referrer and 'pending' in request.referrer:
                return redirect(url_for('license_plate.pending'))
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

@bp.route('/import_template')
@login_required
def import_template():
    """下载导入模板"""
    filename = 'vehicle_import_template.xlsx'
    filepath = os.path.join(current_app.instance_path, filename)
    os.makedirs(current_app.instance_path, exist_ok=True)
    create_import_template(filepath)
    
    return send_file(filepath,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

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
        flash('所有待审核车牌已通过')
    elif action == 'reject_all':
        # 全部拒绝
        vehicles = Vehicle.query.filter_by(status='pending').all()
        for vehicle in vehicles:
            vehicle.status = 'rejected'
        db.session.commit()
        flash('所有待审核车牌已拒绝')
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
        flash(f'已{status}选中的车牌')
    
    return redirect(url_for('license_plate.pending'))

@bp.route('/batch_delete', methods=['POST'])
@login_required
def batch_delete():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '没有权限执行此操作'}), 403

    vehicle_ids = request.form.getlist('vehicle_ids[]')
    if not vehicle_ids:
        return jsonify({'success': False, 'message': '请选择要删除的车辆'}), 400

    try:
        vehicles = Vehicle.query.filter(Vehicle.id.in_(vehicle_ids)).all()
        for vehicle in vehicles:
            db.session.delete(vehicle)
        db.session.commit()
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500 