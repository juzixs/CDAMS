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
import pandas as pd
from io import BytesIO

# 添加自定义过滤器，用于反转排序顺序
@bp.app_template_filter('reverse_order')
def reverse_order(order):
    return 'asc' if order == 'desc' else 'desc'

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
    year = request.args.get('year', '')
    month = request.args.get('month', '')
    per_page = request.args.get('per_page', 10, type=int)
    sort_order = request.args.get('sort_order', 'desc')  # 默认是降序（新的在前）
    
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
    
    # 添加年份筛选
    if year:
        query = query.filter(db.extract('year', VehicleExit.exit_time) == int(year))
    
    # 添加月份筛选
    if month:
        query = query.filter(db.extract('month', VehicleExit.exit_time) == int(month))
    
    # 根据排序参数决定排序方式
    if sort_order == 'asc':
        records = query.order_by(VehicleExit.created_at.asc()).paginate(page=page, per_page=per_page)
    else:
        records = query.order_by(VehicleExit.created_at.desc()).paginate(page=page, per_page=per_page)
    
    # 获取所有不同的年份列表（包括所有数据的年份）
    try:
        # 首先尝试直接从数据库获取年份列表
        available_years = []
        
        # 使用更安全的方式查询年份
        years_query = db.session.query(
            db.func.strftime('%Y', VehicleExit.exit_time)
        ).filter(
            VehicleExit.exit_time != None
        ).distinct().all()
        
        # 提取年份并转为整数
        available_years = [int(year[0]) for year in years_query if year[0] is not None and year[0].isdigit()]
        available_years.sort(reverse=True)
    except Exception as e:
        # 如果查询出错，则使用一个基本的年份列表
        current_year = datetime.now().year
        available_years = list(range(current_year, current_year-5, -1))
    
    # 确保当前年份也在列表中
    current_year = datetime.now().year
    if not available_years or current_year not in available_years:
        available_years.append(current_year)
        available_years.sort(reverse=True)
    
    form = EmptyForm()
    
    return render_template('vehicle/vehicle_exit/index.html',
                          records=records,
                          form=form,
                          active_tab=active_tab,
                          now=datetime.now(),
                          available_years=available_years)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """添加车辆出门记录"""
    exit_type = request.args.get('exit_type', 'outsourcing')
    form = VehicleExitForm()
    
    if request.method == 'GET':
        form.exit_type.data = exit_type
        
        # 根据出门类型设置不同的物流方式选项
        if exit_type == 'product':
            form.logistics_type.choices = [
                ('company', '公司自有车辆'),
                ('logistics', '物流公司车辆'),
                ('other', '其他车辆')
            ]
            # 设置出厂物品分类默认为"产成品交付"
            form.item_category.data = 'product'
    
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
            approver_text=form.approver_text.data,
            
            # 其他信息
            remarks=form.remarks.data,
            created_by=current_user.id,
            status='completed',
            actual_return_time=datetime.utcnow()
        )
        
        db.session.add(exit_record)
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
    
    # 根据出门类型设置不同的物流方式选项
    if exit_record.exit_type == 'product':
        form.logistics_type.choices = [
            ('company', '公司自有车辆'),
            ('logistics', '物流公司车辆'),
            ('other', '其他车辆')
        ]
    
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
        form.approver_text.data = exit_record.approver_text
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
        exit_record.approver_text = form.approver_text.data
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
    exit_type = request.args.get('exit_type', 'outsourcing')
    search = request.args.get('search', '')
    year = request.args.get('year', '')
    month = request.args.get('month', '')
    
    # 创建与index页面一致的查询条件
    query = VehicleExit.query.filter_by(exit_type=exit_type)
    
    if search:
        query = query.filter(
            or_(
                VehicleExit.plate_number.contains(search),
                VehicleExit.driver_name.contains(search),
                VehicleExit.destination.contains(search),
                VehicleExit.items.contains(search)
            )
        )
    
    # 添加年份筛选
    if year:
        query = query.filter(db.extract('year', VehicleExit.exit_time) == int(year))
    
    # 添加月份筛选
    if month:
        query = query.filter(db.extract('month', VehicleExit.exit_time) == int(month))
    
    # 注意这里使用created_at升序（与展示页面相反）
    records = query.order_by(VehicleExit.created_at.asc()).all()
    
    if not records:
        flash('没有符合条件的记录可导出', 'warning')
        return redirect(url_for('vehicle_exit.index', tab=exit_type))
    
    # 转换记录为字典列表
    data = []
    for i, record in enumerate(records, 1):
        # 处理数据格式化
        exit_time = record.exit_time.strftime('%Y-%m-%d') if record.exit_time else '-'
        confirmed_exit_time = record.confirmed_exit_time.strftime('%Y-%m-%d') if record.confirmed_exit_time else '-'
        
        # 物品分类格式化
        if record.item_category == 'product':
            item_category = '产成品交付'
        elif record.item_category == 'outsourcing':
            item_category = '外协'
        elif record.item_category == 'material':
            item_category = '园区物料周转'
        elif record.item_category == 'other':
            item_category = '其他'
        else:
            item_category = record.item_category or '-'
            
        # 车型格式化
        if record.vehicle_type == 'truck':
            vehicle_type = '货车'
        elif record.vehicle_type == 'tractor':
            vehicle_type = '拖拉机'
        elif record.vehicle_type == 'express':
            vehicle_type = '快递'
        elif record.vehicle_type == 'other':
            vehicle_type = '其他'
        else:
            vehicle_type = record.vehicle_type or '-'
            
        # 物流方式格式化
        if record.logistics_type == 'company':
            logistics_type = '公司自有车辆'
        elif record.logistics_type == 'logistics':
            logistics_type = '物流公司车辆'
        elif record.logistics_type == 'outsourcing':
            logistics_type = '外协车辆'
        elif record.logistics_type == 'other':
            logistics_type = '其他车辆'
        else:
            logistics_type = record.logistics_type or '-'
        
        data.append({
            '序号': i,
            '申请部门': record.department or '-',
            '发起人': record.initiator or '-',
            '门证编号': record.certificate_number or '-',
            '申请出厂日期': exit_time,
            '接收单位': record.company or '-',
            '出厂物品分类': item_category,
            '车型': vehicle_type,
            '物流方式': logistics_type,
            '物流公司名称': record.logistics_company or '-',
            '司机姓名': record.driver_name or '-',
            '车牌号': record.plate_number or '-',
            '司机联系电话': record.phone or '-',
            '物流单号': record.logistics_number or '-',
            '审核人': record.reviewer or '-',
            '发放人': record.issuer or '-',
            '审批人': record.approver_text or '-',
            '门卫': record.guard or '-',
            '确认出厂日期': confirmed_exit_time,
            '备注': record.remarks or '-'
        })
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 创建Excel文件
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    # 指定sheet名称
    sheet_name = '外协出门记录' if exit_type == 'outsourcing' else '产成品出门记录'
    df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    # 自动调整列宽
    worksheet = writer.sheets[sheet_name]
    for i, col in enumerate(df.columns):
        column_width = max(df[col].astype(str).map(len).max(), len(col) + 2)
        worksheet.set_column(i, i, column_width)
    
    writer.close()
    output.seek(0)
    
    # 生成文件名
    filename = f"{'外协' if exit_type == 'outsourcing' else '产成品'}_出门记录_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    
    return send_file(
        output, 
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@bp.route('/import_template')
@login_required
def import_template():
    """下载导入模板"""
    # 此处应实现模板下载功能
    # 由于需要更多的实现细节，此处只返回一个提示
    flash('模板下载功能尚未实现，请后续开发', 'info')
    return redirect(url_for('vehicle_exit.index', tab=request.args.get('exit_type', 'outsourcing'))) 