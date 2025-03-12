from datetime import datetime
import os
from flask import render_template, flash, redirect, url_for, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_
from werkzeug.utils import secure_filename
from app import db
from app.vehicle.vehicle_exit import bp
from app.models import VehicleExit
from app.vehicle.vehicle_exit.forms import VehicleExitForm
from app.utils.permissions import admin_required
from flask_wtf import FlaskForm

class EmptyForm(FlaskForm):
    pass

@bp.route('/')
@login_required
def index():
    """车辆出门记录首页"""
    # 当前活动的标签页（外协或产成品）
    active_tab = request.args.get('tab', 'outsourcing')  # 默认是"外协"标签
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    per_page = request.args.get('per_page', 10, type=int)
    
    query = VehicleExit.query.filter_by(exit_type=active_tab)
    
    if search:
        query = query.filter(
            or_(
                VehicleExit.plate_number.contains(search),
                VehicleExit.driver_name.contains(search),
                VehicleExit.destination.contains(search),
                VehicleExit.items.contains(search)
            )
        )
    
    if status:
        query = query.filter_by(status=status)
    
    records = query.order_by(VehicleExit.created_at.desc()).paginate(page=page, per_page=per_page)
    
    form = EmptyForm()
    
    return render_template('vehicle/vehicle_exit/index.html',
                          records=records,
                          form=form,
                          active_tab=active_tab)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """添加车辆出门记录"""
    exit_type = request.args.get('exit_type', 'outsourcing')
    form = VehicleExitForm()
    
    if request.method == 'GET':
        form.exit_type.data = exit_type
    
    if form.validate_on_submit():
        exit_record = VehicleExit(
            # 基本信息
            exit_type=form.exit_type.data,
            
            # 申请信息
            department=form.department.data,
            initiator=form.initiator.data,
            certificate_number=form.certificate_number.data,
            
            # 车辆和司机信息
            plate_number=form.plate_number.data,
            driver_name=form.driver_name.data,
            id_number=form.id_number.data,
            phone=form.phone.data,
            
            # 物流信息
            vehicle_type=form.vehicle_type.data,
            logistics_type=form.logistics_type.data,
            logistics_company=form.logistics_company.data,
            logistics_number=form.logistics_number.data,
            
            # 物品和目的地信息
            company=form.company.data,
            item_category=form.item_category.data,
            destination=form.destination.data,
            items=form.items.data,
            purpose=form.purpose.data,
            
            # 时间信息
            exit_time=form.exit_time.data,
            expected_return_time=form.expected_return_time.data,
            confirmed_exit_time=form.confirmed_exit_time.data,
            
            # 审批信息
            reviewer=form.reviewer.data,
            issuer=form.issuer.data,
            guard=form.guard.data,
            
            # 其他信息
            remarks=form.remarks.data,
            created_by=current_user.id,
            status='pending'
        )
        
        db.session.add(exit_record)
        
        # 单独设置 approver_name 字段
        if hasattr(exit_record, 'approver_name'):
            exit_record.approver_name = form.approver_name.data
        
        db.session.commit()
        
        flash(f'{"外协" if exit_type == "outsourcing" else "产成品"}车辆出门记录已添加', 'success')
        return redirect(url_for('vehicle_exit.index', tab=exit_type))
    
    return render_template('vehicle/vehicle_exit/add.html',
                          form=form,
                          exit_type=exit_type)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    """编辑车辆出门记录"""
    exit_record = VehicleExit.query.get_or_404(id)
    form = VehicleExitForm()
    
    if request.method == 'GET':
        # 基本信息
        form.exit_type.data = exit_record.exit_type
        
        # 申请信息
        form.department.data = exit_record.department
        form.initiator.data = exit_record.initiator
        form.certificate_number.data = exit_record.certificate_number
        
        # 车辆和司机信息
        form.plate_number.data = exit_record.plate_number
        form.driver_name.data = exit_record.driver_name
        form.id_number.data = exit_record.id_number
        form.phone.data = exit_record.phone
        
        # 物流信息
        form.vehicle_type.data = exit_record.vehicle_type
        form.logistics_type.data = exit_record.logistics_type
        form.logistics_company.data = exit_record.logistics_company
        form.logistics_number.data = exit_record.logistics_number
        
        # 物品和目的地信息
        form.company.data = exit_record.company
        form.item_category.data = exit_record.item_category
        form.destination.data = exit_record.destination
        form.items.data = exit_record.items
        form.purpose.data = exit_record.purpose
        
        # 时间信息
        form.exit_time.data = exit_record.exit_time
        form.expected_return_time.data = exit_record.expected_return_time
        form.confirmed_exit_time.data = exit_record.confirmed_exit_time
        
        # 审批信息
        form.reviewer.data = exit_record.reviewer
        form.issuer.data = exit_record.issuer
        # 处理approver_name可能不存在的情况
        if hasattr(exit_record, 'approver_name'):
            form.approver_name.data = exit_record.approver_name
        elif hasattr(exit_record, 'approver'):
            form.approver_name.data = exit_record.approver
        else:
            form.approver_name.data = None
        form.guard.data = exit_record.guard
        
        # 其他信息
        form.remarks.data = exit_record.remarks
    
    if form.validate_on_submit():
        # 基本信息保持不变
        # exit_record.exit_type = form.exit_type.data
        
        # 申请信息
        exit_record.department = form.department.data
        exit_record.initiator = form.initiator.data
        exit_record.certificate_number = form.certificate_number.data
        
        # 车辆和司机信息
        exit_record.plate_number = form.plate_number.data
        exit_record.driver_name = form.driver_name.data
        exit_record.id_number = form.id_number.data
        exit_record.phone = form.phone.data
        
        # 物流信息
        exit_record.vehicle_type = form.vehicle_type.data
        exit_record.logistics_type = form.logistics_type.data
        exit_record.logistics_company = form.logistics_company.data
        exit_record.logistics_number = form.logistics_number.data
        
        # 物品和目的地信息
        exit_record.company = form.company.data
        exit_record.item_category = form.item_category.data
        exit_record.destination = form.destination.data
        exit_record.items = form.items.data
        exit_record.purpose = form.purpose.data
        
        # 时间信息
        exit_record.exit_time = form.exit_time.data
        exit_record.expected_return_time = form.expected_return_time.data
        exit_record.confirmed_exit_time = form.confirmed_exit_time.data
        
        # 审批信息
        exit_record.reviewer = form.reviewer.data
        exit_record.issuer = form.issuer.data
        # 单独设置 approver_name 字段
        if hasattr(exit_record, 'approver_name'):
            exit_record.approver_name = form.approver_name.data
        exit_record.guard = form.guard.data
        
        # 其他信息
        exit_record.remarks = form.remarks.data
        exit_record.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'{"外协" if exit_record.exit_type == "outsourcing" else "产成品"}车辆出门记录已更新', 'success')
        return redirect(url_for('vehicle_exit.index', tab=exit_record.exit_type))
    
    return render_template('vehicle/vehicle_exit/edit.html',
                          form=form,
                          exit_type=exit_record.exit_type)

@bp.route('/delete/<int:id>')
@login_required
def delete(id):
    """删除车辆出门记录"""
    exit_record = VehicleExit.query.get_or_404(id)
    exit_type = exit_record.exit_type
    
    db.session.delete(exit_record)
    db.session.commit()
    
    flash(f'{"外协" if exit_type == "outsourcing" else "产成品"}车辆出门记录已删除', 'success')
    return redirect(url_for('vehicle_exit.index', tab=exit_type))

@bp.route('/approve/<int:id>')
@login_required
@admin_required
def approve(id):
    """审核通过车辆出门记录"""
    exit_record = VehicleExit.query.get_or_404(id)
    
    if exit_record.status == 'pending':
        exit_record.status = 'approved'
        exit_record.approved_by = current_user.id
        db.session.commit()
        flash('车辆出门记录已审核通过', 'success')
    
    return redirect(url_for('vehicle_exit.index', tab=exit_record.exit_type))

@bp.route('/complete/<int:id>')
@login_required
def complete(id):
    """完成车辆出门记录（标记为已返回）"""
    exit_record = VehicleExit.query.get_or_404(id)
    
    if exit_record.status == 'approved':
        exit_record.status = 'completed'
        exit_record.actual_return_time = datetime.utcnow()
        db.session.commit()
        flash('车辆已标记为已返回', 'success')
    
    return redirect(url_for('vehicle_exit.index', tab=exit_record.exit_type))

@bp.route('/batch_action', methods=['POST'])
@login_required
def batch_action():
    """批量操作车辆出门记录"""
    action = request.form.get('action')
    exit_type = request.form.get('exit_type', 'outsourcing')
    record_ids = request.form.getlist('record_ids[]')
    
    if not record_ids:
        flash('请至少选择一条记录', 'warning')
        return redirect(url_for('vehicle_exit.index', tab=exit_type))
    
    if action == 'delete':
        for id in record_ids:
            exit_record = VehicleExit.query.get(id)
            if exit_record:
                db.session.delete(exit_record)
        
        db.session.commit()
        flash('已删除选中的记录', 'success')
    
    return redirect(url_for('vehicle_exit.index', tab=exit_type))

@bp.route('/import_records', methods=['POST'])
@login_required
def import_records():
    """导入车辆出门记录"""
    # 此处应实现导入功能
    # 可以使用pandas读取Excel文件并将数据导入到数据库
    # 由于需要更多的实现细节，此处只返回一个成功消息
    return jsonify({'message': '导入功能尚未实现，请后续开发'})

@bp.route('/export')
@login_required
def export():
    """导出车辆出门记录"""
    # 此处应实现导出功能
    # 可以使用pandas将数据导出为Excel文件
    # 由于需要更多的实现细节，此处只返回一个提示
    flash('导出功能尚未实现，请后续开发', 'info')
    return redirect(url_for('vehicle_exit.index', tab=request.args.get('exit_type', 'outsourcing')))

@bp.route('/import_template')
@login_required
def import_template():
    """下载导入模板"""
    # 此处应实现模板下载功能
    # 由于需要更多的实现细节，此处只返回一个提示
    flash('模板下载功能尚未实现，请后续开发', 'info')
    return redirect(url_for('vehicle_exit.index', tab=request.args.get('exit_type', 'outsourcing'))) 