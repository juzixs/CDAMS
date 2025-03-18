from flask import render_template, flash, redirect, url_for, request, jsonify, send_file
from flask_login import login_required, current_user
from app import db
from app.vehicle.official_car import bp
from app.models.official_car import OfficialCar, CarStatus, CarUsageRecord, CarMaintenanceRecord, CarFuelRecord, CarInsurance
from app.vehicle.official_car.forms import OfficialCarForm, CarUsageRecordForm, CarReturnForm, CarUsageRecordFullForm, CarMaintenanceRecordForm, CarFuelRecordForm, CarInsuranceForm, CarMaintenanceCompleteForm
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta, time
import pandas as pd
import uuid
from sqlalchemy import desc, extract
from io import BytesIO

@bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 获取查询参数
    usage_nature = request.args.get('usage_nature', '')
    search = request.args.get('search', '')
    
    # 构建查询
    query = OfficialCar.query.filter(OfficialCar.status != CarStatus.scrapped)
    
    if usage_nature:
        query = query.filter(OfficialCar.usage_nature == usage_nature)
    
    if search:
        query = query.filter(
            (OfficialCar.asset_number.ilike(f'%{search}%')) |
            (OfficialCar.plate_number.ilike(f'%{search}%')) |
            (OfficialCar.brand.ilike(f'%{search}%')) |
            (OfficialCar.asset_description.ilike(f'%{search}%')) |
            (OfficialCar.model.ilike(f'%{search}%')) |
            (OfficialCar.car_model.ilike(f'%{search}%')) |
            (OfficialCar.car_type.ilike(f'%{search}%')) |
            (OfficialCar.responsible_person.ilike(f'%{search}%')) |
            (OfficialCar.usage_nature.ilike(f'%{search}%'))
        )
    
    # 按添加时间升序排序（新添加的在下）
    query = query.order_by(OfficialCar.created_at)
    
    # 获取所有唯一的使用性质
    all_usage_natures = db.session.query(OfficialCar.usage_nature).filter(
        OfficialCar.usage_nature.isnot(None),
        OfficialCar.usage_nature != ''
    ).distinct().order_by(OfficialCar.usage_nature).all()
    usage_natures = [nature[0] for nature in all_usage_natures if nature[0]]
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page)
    cars = pagination.items
    
    # 获取每辆车的最新保险信息
    car_insurance_info = {}
    for car in cars:
        latest_insurance = CarInsurance.query.filter_by(car_id=car.id).order_by(CarInsurance.insurance_end_date.desc()).first()
        if latest_insurance:
            car_insurance_info[car.id] = f"{latest_insurance.insurance_start_date.strftime('%Y-%m-%d')}至{latest_insurance.insurance_end_date.strftime('%Y-%m-%d')}"
        else:
            car_insurance_info[car.id] = '-'
    
    return render_template('vehicle/official_car/index.html', 
                          title='公务车辆',
                          cars=cars,
                          pagination=pagination,
                          page=page,
                          per_page=per_page,
                          usage_natures=usage_natures,
                          car_insurance_info=car_insurance_info)

@bp.route('/car_info')
@login_required
def car_info():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 获取查询参数
    usage_nature = request.args.get('usage_nature', '')
    search = request.args.get('search', '')
    
    # 构建查询
    query = OfficialCar.query.filter(OfficialCar.status != CarStatus.scrapped)
    
    if usage_nature:
        query = query.filter(OfficialCar.usage_nature == usage_nature)
    
    if search:
        query = query.filter(
            (OfficialCar.asset_number.ilike(f'%{search}%')) |
            (OfficialCar.plate_number.ilike(f'%{search}%')) |
            (OfficialCar.brand.ilike(f'%{search}%')) |
            (OfficialCar.asset_description.ilike(f'%{search}%')) |
            (OfficialCar.model.ilike(f'%{search}%')) |
            (OfficialCar.car_model.ilike(f'%{search}%')) |
            (OfficialCar.car_type.ilike(f'%{search}%')) |
            (OfficialCar.responsible_person.ilike(f'%{search}%')) |
            (OfficialCar.usage_nature.ilike(f'%{search}%'))
        )
    
    # 按添加时间升序排序（新添加的在下）
    query = query.order_by(OfficialCar.created_at)
    
    # 获取所有唯一的使用性质
    all_usage_natures = db.session.query(OfficialCar.usage_nature).filter(
        OfficialCar.usage_nature.isnot(None),
        OfficialCar.usage_nature != ''
    ).distinct().order_by(OfficialCar.usage_nature).all()
    usage_natures = [nature[0] for nature in all_usage_natures if nature[0]]
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page)
    cars = pagination.items
    
    # 获取每辆车的最新保险信息
    car_insurance_info = {}
    for car in cars:
        latest_insurance = CarInsurance.query.filter_by(car_id=car.id).order_by(CarInsurance.insurance_end_date.desc()).first()
        if latest_insurance:
            car_insurance_info[car.id] = f"{latest_insurance.insurance_start_date.strftime('%Y-%m-%d')}至{latest_insurance.insurance_end_date.strftime('%Y-%m-%d')}"
        else:
            car_insurance_info[car.id] = '-'
    
    return render_template('vehicle/official_car/car_info.html', 
                          title='车辆信息',
                          cars=cars,
                          pagination=pagination,
                          page=page,
                          per_page=per_page,
                          usage_natures=usage_natures,
                          car_insurance_info=car_insurance_info)

@bp.route('/add_car', methods=['GET', 'POST'])
@login_required
def add_car():
    form = OfficialCarForm()
    if form.validate_on_submit():
        # 检查资产编号是否已存在
        if OfficialCar.query.filter_by(asset_number=form.asset_number.data).first():
            flash('资产编号已存在，请使用其他资产编号', 'danger')
            return render_template('vehicle/official_car/add_car.html', title='新增车辆', form=form)
        
        # 创建新车辆
        car = OfficialCar(
            asset_number=form.asset_number.data,
            card_number=form.card_number.data,
            brand=form.brand.data,
            asset_description=form.asset_description.data,
            model=form.model.data,
            original_value=form.original_value.data,
            is_business_car=form.is_business_car.data,
            plate_number=form.plate_number.data,
            car_model=form.car_model.data,
            car_type=form.car_type.data,
            registration_time=form.registration_time.data,
            seat_count=form.seat_count.data,
            displacement=form.displacement.data,
            responsible_person=form.responsible_person.data,
            usage_nature=form.usage_nature.data,
            status=CarStatus.idle,
            created_by=current_user.id
        )
        
        # 处理车辆照片上传
        if form.vehicle_license.data and hasattr(form.vehicle_license.data, 'filename'):
            filename = secure_filename(form.vehicle_license.data.filename)
            # 生成唯一文件名
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            # 确保上传目录存在
            upload_dir = os.path.join(os.getcwd(), 'app', 'static', 'uploads', 'vehicle_licenses')
            os.makedirs(upload_dir, exist_ok=True)
            # 保存文件
            file_path = os.path.join(upload_dir, unique_filename)
            form.vehicle_license.data.save(file_path)
            # 保存文件路径到数据库
            car.vehicle_license = f'/static/uploads/vehicle_licenses/{unique_filename}'
        
        db.session.add(car)
        db.session.commit()
        flash('车辆信息添加成功', 'success')
        return redirect(url_for('official_car.car_info'))
    
    return render_template('vehicle/official_car/add_car.html', title='新增车辆', form=form)

@bp.route('/edit_car/<int:car_id>', methods=['GET', 'POST'])
@login_required
def edit_car(car_id):
    car = OfficialCar.query.get_or_404(car_id)
    form = OfficialCarForm(obj=car)
    
    if form.validate_on_submit():
        # 检查资产编号是否已被其他车辆使用
        existing_car = OfficialCar.query.filter_by(asset_number=form.asset_number.data).first()
        if existing_car and existing_car.id != car_id:
            flash('资产编号已存在，请使用其他资产编号', 'danger')
            return render_template('vehicle/official_car/edit_car.html', title='编辑车辆', form=form, car=car)
        
        # 更新车辆信息
        car.asset_number = form.asset_number.data
        car.card_number = form.card_number.data
        car.brand = form.brand.data
        car.asset_description = form.asset_description.data
        car.model = form.model.data
        car.original_value = form.original_value.data
        car.is_business_car = form.is_business_car.data
        car.plate_number = form.plate_number.data
        car.car_model = form.car_model.data
        car.car_type = form.car_type.data
        car.registration_time = form.registration_time.data
        car.seat_count = form.seat_count.data
        car.displacement = form.displacement.data
        car.responsible_person = form.responsible_person.data
        car.usage_nature = form.usage_nature.data
        car.updated_by = current_user.id
        car.updated_at = datetime.now()
        
        # 处理车辆照片上传
        if form.vehicle_license.data and hasattr(form.vehicle_license.data, 'filename'):
            # 如果已有照片，尝试删除旧文件
            if car.vehicle_license:
                old_file_path = os.path.join(os.getcwd(), 'app', car.vehicle_license.lstrip('/'))
                try:
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                except Exception as e:
                    print(f"无法删除旧文件: {e}")
            
            filename = secure_filename(form.vehicle_license.data.filename)
            # 生成唯一文件名
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            # 确保上传目录存在
            upload_dir = os.path.join(os.getcwd(), 'app', 'static', 'uploads', 'vehicle_licenses')
            os.makedirs(upload_dir, exist_ok=True)
            # 保存文件
            file_path = os.path.join(upload_dir, unique_filename)
            form.vehicle_license.data.save(file_path)
            # 保存文件路径到数据库
            car.vehicle_license = f'/static/uploads/vehicle_licenses/{unique_filename}'
        
        db.session.commit()
        flash('车辆信息更新成功', 'success')
        return redirect(url_for('official_car.car_info'))
    
    return render_template('vehicle/official_car/edit_car.html', title='编辑车辆', form=form, car=car)

@bp.route('/scrap_car/<int:car_id>', methods=['POST'])
@login_required
def scrap_car(car_id):
    car = OfficialCar.query.get_or_404(car_id)
    car.status = CarStatus.scrapped
    car.is_scrapped = True
    car.scrap_time = datetime.now()
    car.scrapped_by = current_user.id
    db.session.commit()
    flash('车辆已报废', 'success')
    return redirect(url_for('official_car.index'))

@bp.route('/scrapped_cars')
@login_required
def scrapped_cars():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search = request.args.get('search', '')
    usage_nature = request.args.get('usage_nature', '')
    
    # 构建查询
    query = OfficialCar.query.filter_by(is_scrapped=True)
    
    if usage_nature:
        query = query.filter(OfficialCar.usage_nature == usage_nature)
    
    if search:
        query = query.filter(
            (OfficialCar.asset_number.ilike(f'%{search}%')) |
            (OfficialCar.plate_number.ilike(f'%{search}%')) |
            (OfficialCar.brand.ilike(f'%{search}%')) |
            (OfficialCar.asset_description.ilike(f'%{search}%')) |
            (OfficialCar.model.ilike(f'%{search}%')) |
            (OfficialCar.car_model.ilike(f'%{search}%')) |
            (OfficialCar.car_type.ilike(f'%{search}%')) |
            (OfficialCar.responsible_person.ilike(f'%{search}%')) |
            (OfficialCar.usage_nature.ilike(f'%{search}%'))
        )
    
    # 获取所有唯一的使用性质
    all_usage_natures = db.session.query(OfficialCar.usage_nature).filter(
        OfficialCar.usage_nature.isnot(None),
        OfficialCar.usage_nature != ''
    ).distinct().order_by(OfficialCar.usage_nature).all()
    usage_natures = [nature[0] for nature in all_usage_natures if nature[0]]
    
    # 按报废时间升序排序（新报废的在下）
    query = query.order_by(OfficialCar.scrap_time)
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page)
    cars = pagination.items
    
    return render_template('vehicle/official_car/scrapped_cars.html', 
                          title='报废车辆信息',
                          cars=cars,
                          pagination=pagination,
                          page=page,
                          per_page=per_page,
                          usage_natures=usage_natures)

def calculate_usage_duration(departure_date, departure_time, return_time):
    """
    根据出车时间和收车时间计算使用时长
    
    计算规则：
    1. 同一天出车和收车：按小时计算，显示为"XH"
    2. 跨天出车和收车：按天数计算，精确到小数点后两位，显示为"X.XX天"
    """
    # 确保departure_date是date类型
    if isinstance(departure_date, datetime):
        departure_date = departure_date.date()
    
    # 创建出车的完整日期时间
    departure_datetime = datetime.combine(departure_date, departure_time)
    
    # 获取收车日期（从return_time中提取）
    return_date = return_time.date()
    
    # 计算时间差（总秒数）
    time_diff_seconds = (return_time - departure_datetime).total_seconds()
    
    # 计算天数差（包括小数部分）
    days_diff = time_diff_seconds / (24 * 3600)
    
    # 计算小时差
    hours_diff = time_diff_seconds / 3600
    
    # 根据规则计算使用时长
    if return_date == departure_date:
        # 同一天出车和收车，按小时计算
        return f"{int(hours_diff)}H"
    else:
        # 跨天出车和收车，按天数计算（精确到小数点后两位）
        return f"{days_diff:.2f}天"

@bp.route('/return_car/<int:record_id>', methods=['GET', 'POST'])
@login_required
def return_car(record_id):
    record = CarUsageRecord.query.get_or_404(record_id)
    car = OfficialCar.query.get_or_404(record.car_id)
    form = CarReturnForm()
    
    if form.validate_on_submit():
        record.return_time = form.return_time.data
        record.return_mileage = form.return_mileage.data
        record.refueling = form.refueling.data
        record.maintenance = form.maintenance.data
        # 修改：只有当toll_fee字段为None时才设置默认值，如果是空字符串则保留用户的输入
        if form.toll_fee.data is None:
            record.toll_fee = 'etc'
        else:
            record.toll_fee = form.toll_fee.data
        record.parking_fee = form.parking_fee.data
        record.accident_violation = form.accident_violation.data
        
        # 计算使用时长
        record.usage_duration = calculate_usage_duration(
            record.departure_date, 
            record.departure_time, 
            form.return_time.data
        )
        
        # 更新车辆状态为空闲
        car.status = CarStatus.idle
        
        db.session.commit()
        flash('车辆归还成功！', 'success')
        return redirect(url_for('vehicle.official_car.car_usage'))
    
    # 在GET请求时预填充toll_fee字段为'etc'
    if request.method == 'GET':
        form.toll_fee.data = 'etc'
    
    return render_template('vehicle/official_car/return_car.html', form=form, record=record, car=car)

@bp.route('/car_usage')
@login_required
def car_usage():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 获取查询参数
    year = request.args.get('year', '')
    plate_number = request.args.get('plate_number', '')
    search = request.args.get('search', '')
    
    # 构建查询
    query = CarUsageRecord.query
    
    if year:
        query = query.filter(db.extract('year', CarUsageRecord.departure_date) == year)
    
    if plate_number:
        query = query.filter(CarUsageRecord.plate_number == plate_number)
    
    if search:
        query = query.filter(
            (CarUsageRecord.department.ilike(f'%{search}%')) |
            (CarUsageRecord.plate_number.ilike(f'%{search}%')) |
            (CarUsageRecord.destination_purpose.ilike(f'%{search}%')) |
            (CarUsageRecord.driver.ilike(f'%{search}%')) |
            (CarUsageRecord.passengers.ilike(f'%{search}%')) |
            (CarUsageRecord.maintenance.ilike(f'%{search}%')) |
            (CarUsageRecord.accident_violation.ilike(f'%{search}%'))
        )
    
    # 按出车日期和时间降序排序（新记录在上），相同日期和时间的按创建时间降序排序（新创建的在上）
    query = query.order_by(
        CarUsageRecord.departure_date.desc(), 
        CarUsageRecord.departure_time.desc(),
        CarUsageRecord.created_at.desc()
    )
    
    # 获取所有年份
    all_years = db.session.query(db.extract('year', CarUsageRecord.departure_date)).distinct().order_by(db.extract('year', CarUsageRecord.departure_date).desc()).all()
    years = [int(year[0]) for year in all_years if year[0]]
    
    # 获取所有车牌号
    all_plate_numbers = db.session.query(CarUsageRecord.plate_number).distinct().order_by(CarUsageRecord.plate_number).all()
    plate_numbers = [pn[0] for pn in all_plate_numbers if pn[0]]
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page)
    records = pagination.items
    
    return render_template('vehicle/official_car/car_usage.html', 
                          title='车辆使用登记',
                          records=records,
                          pagination=pagination,
                          page=page,
                          per_page=per_page,
                          years=years,
                          plate_numbers=plate_numbers,
                          current_year=year,
                          current_plate_number=plate_number)

@bp.route('/car_maintenance')
@login_required
def car_maintenance():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 获取查询参数
    year = request.args.get('year', '')
    plate_number = request.args.get('plate_number', '')
    search = request.args.get('search', '')
    
    # 构建查询
    query = CarMaintenanceRecord.query
    
    if year:
        query = query.filter(extract('year', CarMaintenanceRecord.application_time) == int(year))
    
    if plate_number:
        query = query.filter(CarMaintenanceRecord.plate_number == plate_number)
    
    if search:
        query = query.filter(
            (CarMaintenanceRecord.plate_number.ilike(f'%{search}%')) |
            (CarMaintenanceRecord.car_type.ilike(f'%{search}%')) |
            (CarMaintenanceRecord.driver.ilike(f'%{search}%')) |
            (CarMaintenanceRecord.sender.ilike(f'%{search}%')) |
            (CarMaintenanceRecord.reason.ilike(f'%{search}%')) |
            (CarMaintenanceRecord.maintenance_location.ilike(f'%{search}%')) |
            (CarMaintenanceRecord.remarks.ilike(f'%{search}%'))
        )
    
    # 按申请时间降序排序（新申请的在上），相同申请时间的按创建时间降序排序（新创建的在上）
    query = query.order_by(
        CarMaintenanceRecord.application_time.desc(),
        CarMaintenanceRecord.created_at.desc()
    )
    
    # 分页
    records = query.paginate(page=page, per_page=per_page)
    
    # 获取所有车辆的车牌号
    all_cars = OfficialCar.query.filter(OfficialCar.status != CarStatus.scrapped).all()
    plate_numbers = [(car.plate_number, car.plate_number) for car in all_cars if car.plate_number]
    
    # 从数据库获取所有存在的申请时间年份
    all_years = db.session.query(db.extract('year', CarMaintenanceRecord.application_time))\
                          .filter(CarMaintenanceRecord.application_time.isnot(None))\
                          .distinct()\
                          .order_by(db.extract('year', CarMaintenanceRecord.application_time).desc())\
                          .all()
    years = [(str(year[0]), str(year[0])) for year in all_years if year[0]]
    
    # 如果数据库中没有年份记录，则提供当前年份作为默认选项
    if not years:
        current_year = datetime.now().year
        years = [(str(current_year), str(current_year))]
    
    return render_template('vehicle/official_car/car_maintenance.html', 
                           title='车辆维修保养',
                           records=records,
                           plate_numbers=plate_numbers,
                           years=years,
                           year=year,
                           plate_number=plate_number,
                           search=search)

@bp.route('/add_maintenance_record', methods=['GET', 'POST'])
@login_required
def add_maintenance_record():
    form = CarMaintenanceRecordForm()
    
    # 获取所有车辆的车牌号
    all_cars = OfficialCar.query.filter(OfficialCar.status != CarStatus.scrapped).all()
    form.plate_number.choices = [('', '请选择车牌号')] + [(car.plate_number, car.plate_number) for car in all_cars if car.plate_number]
    
    if form.validate_on_submit():
        # 获取车型
        car = OfficialCar.query.filter_by(plate_number=form.plate_number.data).first()
        car_type = car.car_type if car else ''
        
        if not car:
            flash('未找到对应车牌号的车辆，请重新选择', 'danger')
            return render_template('vehicle/official_car/add_maintenance_record.html',
                                  title='添加维修保养记录',
                                  form=form,
                                  today=datetime.now())
        
        record = CarMaintenanceRecord(
            car_id=car.id,  # 添加car_id字段
            application_time=form.application_time.data,
            car_type=car_type,
            plate_number=form.plate_number.data,
            driver=form.driver.data,
            sender=form.sender.data,
            reason=form.reason.data,
            maintenance_location=form.maintenance_location.data,
            cost=form.cost.data,
            completion_time=form.completion_time.data,
            remarks=form.remarks.data,
            created_by=current_user.id
        )
        
        db.session.add(record)
        db.session.commit()
        
        flash('维修保养记录已添加', 'success')
        return redirect(url_for('official_car.car_maintenance'))
    
    # 设置默认日期为今天
    if not form.application_time.data:
        form.application_time.data = datetime.now()
    
    return render_template('vehicle/official_car/add_maintenance_record.html',
                           title='添加维修保养记录',
                           form=form,
                           today=datetime.now())

@bp.route('/edit_maintenance_record/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_maintenance_record(id):
    record = CarMaintenanceRecord.query.get_or_404(id)
    form = CarMaintenanceRecordForm(obj=record)
    
    # 获取所有车辆的车牌号
    all_cars = OfficialCar.query.filter(OfficialCar.status != CarStatus.scrapped).all()
    form.plate_number.choices = [('', '请选择车牌号')] + [(car.plate_number, car.plate_number) for car in all_cars if car.plate_number]
    
    if form.validate_on_submit():
        # 获取车型
        car = OfficialCar.query.filter_by(plate_number=form.plate_number.data).first()
        
        if not car:
            flash('未找到对应车牌号的车辆，请重新选择', 'danger')
            return render_template('vehicle/official_car/add_maintenance_record.html',
                                  title='编辑维修保养记录',
                                  form=form,
                                  today=datetime.now())
        
        car_type = car.car_type if car else ''
        
        record.car_id = car.id  # 更新car_id，确保与车牌号匹配
        record.application_time = form.application_time.data
        record.car_type = car_type
        record.plate_number = form.plate_number.data
        record.driver = form.driver.data
        record.sender = form.sender.data
        record.reason = form.reason.data
        record.maintenance_location = form.maintenance_location.data
        record.cost = form.cost.data
        record.completion_time = form.completion_time.data
        record.remarks = form.remarks.data
        record.updated_by = current_user.id
        record.updated_at = datetime.now()
        
        db.session.commit()
        
        flash('维修保养记录已更新', 'success')
        return redirect(url_for('official_car.car_maintenance'))
    
    return render_template('vehicle/official_car/add_maintenance_record.html',
                           title='编辑维修保养记录',
                           form=form,
                           today=datetime.now())

@bp.route('/complete_maintenance_record/<int:id>', methods=['GET', 'POST'])
@login_required
def complete_maintenance_record(id):
    record = CarMaintenanceRecord.query.get_or_404(id)
    form = CarMaintenanceCompleteForm(obj=record)
    
    if form.validate_on_submit():
        record.cost = form.cost.data
        record.completion_time = form.completion_time.data
        record.remarks = form.remarks.data
        record.updated_by = current_user.id
        record.updated_at = datetime.now()
        
        # 更新相关车辆的状态为"空闲"
        if record.car_id:
            car = OfficialCar.query.get(record.car_id)
            if car and car.status == CarStatus.maintenance:
                car.status = CarStatus.idle
                car.updated_by = current_user.id
                car.updated_at = datetime.now()
        
        db.session.commit()
        
        flash('维修保养记录已完成，车辆状态已更新为空闲', 'success')
        return redirect(url_for('official_car.car_maintenance'))
    
    return render_template('vehicle/official_car/complete_maintenance_record.html',
                           title='完成维修保养记录',
                           form=form,
                           record=record,
                           today=datetime.now())

@bp.route('/delete_maintenance_record/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_maintenance_record(id):
    record = CarMaintenanceRecord.query.get_or_404(id)
    
    db.session.delete(record)
    db.session.commit()
    
    flash('维修保养记录已删除', 'success')
    return redirect(url_for('official_car.car_maintenance'))

@bp.route('/export_maintenance_records')
@login_required
def export_maintenance_records():
    # 获取查询参数
    year = request.args.get('year', '')
    plate_number = request.args.get('plate_number', '')
    search = request.args.get('search', '')
    
    # 构建查询
    query = CarMaintenanceRecord.query
    
    if year:
        query = query.filter(extract('year', CarMaintenanceRecord.application_time) == int(year))
    
    if plate_number:
        query = query.filter(CarMaintenanceRecord.plate_number == plate_number)
    
    if search:
        query = query.filter(
            (CarMaintenanceRecord.plate_number.ilike(f'%{search}%')) |
            (CarMaintenanceRecord.car_type.ilike(f'%{search}%')) |
            (CarMaintenanceRecord.driver.ilike(f'%{search}%')) |
            (CarMaintenanceRecord.sender.ilike(f'%{search}%')) |
            (CarMaintenanceRecord.reason.ilike(f'%{search}%')) |
            (CarMaintenanceRecord.maintenance_location.ilike(f'%{search}%')) |
            (CarMaintenanceRecord.remarks.ilike(f'%{search}%'))
        )
    
    # 导出Excel时使用与页面相反的排序逻辑：按申请时间升序排序（越早的越靠前），相同申请时间的按创建时间升序排序（越早提交的越靠前）
    records = query.order_by(
        CarMaintenanceRecord.application_time.asc(),
        CarMaintenanceRecord.created_at.asc()
    ).all()
    
    # 创建DataFrame
    data = []
    for i, record in enumerate(records, 1):
        data.append({
            '序号': i,
            '申请时间': record.application_time.strftime('%Y-%m-%d') if record.application_time else '-',
            '车型': record.car_type or '-',
            '车牌号': record.plate_number or '-',
            '驾驶员': record.driver or '-',
            '送修人': record.sender or '-',
            '送修原因': record.reason or '-',
            '维修厂': record.maintenance_location or '-',
            '维修费用': '{:.2f}'.format(float(record.cost)) if record.cost else '-',
            '完成时间': record.completion_time.strftime('%Y-%m-%d') if record.completion_time else '-',
            '备注': record.remarks or '-'
        })
    
    df = pd.DataFrame(data)
    
    # 创建内存中的Excel文件
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    # 指定sheet名称
    sheet_name = '车辆维修保养记录'
    df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=2)  # 从第3行开始写入数据
    
    # 获取工作簿和工作表对象
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    
    # 设置标题格式
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    # 合并单元格并写入标题
    worksheet.merge_range(0, 0, 0, len(df.columns) - 1, '车辆维修保养记录', title_format)
    
    # 添加导出时间
    date_format = workbook.add_format({
        'align': 'right',
        'font_size': 10
    })
    export_time = f'导出时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    worksheet.merge_range(1, 0, 1, len(df.columns) - 1, export_time, date_format)
    
    # 自动调整列宽
    for idx, col in enumerate(df.columns):
        column_width = max(len(str(col)), df[col].astype(str).map(len).max())
        worksheet.set_column(idx, idx, column_width + 2)
    
    writer.close()
    output.seek(0)
    
    # 生成文件名
    filename = f'车辆维修保养记录_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'
    
    return send_file(
        output, 
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@bp.route('/get_car_type')
@login_required
def get_car_type():
    plate_number = request.args.get('plate_number', '')
    
    print(f"获取车型API被调用，车牌号: '{plate_number}'")
    
    if not plate_number:
        print("错误: 车牌号为空")
        return jsonify({'success': False, 'message': '车牌号不能为空'})
    
    car = OfficialCar.query.filter_by(plate_number=plate_number).first()
    
    if not car:
        print(f"错误: 未找到车辆信息，车牌号: '{plate_number}'")
        return jsonify({'success': False, 'message': '未找到车辆信息'})
    
    car_type = car.car_type or ''
    print(f"成功: 找到车型: '{car_type}'，车牌号: '{plate_number}'")
    
    return jsonify({
        'success': True,
        'car_type': car_type
    })

@bp.route('/car_fuel')
@login_required
def car_fuel():
    return render_template('vehicle/official_car/car_fuel.html', title='车辆加油充值')

@bp.route('/use_car/<int:car_id>', methods=['GET', 'POST'])
@login_required
def use_car(car_id):
    car = OfficialCar.query.get_or_404(car_id)
    form = CarUsageRecordForm()
    
    if form.validate_on_submit():
        # 创建新的用车记录
        record = CarUsageRecord(
            car_id=car.id,
            department=form.department.data,
            plate_number=car.plate_number,
            departure_date=form.departure_date.data,
            departure_time=datetime.strptime(form.departure_time.data, '%H:%M').time(),
            departure_mileage=form.departure_mileage.data,
            destination_purpose=form.destination_purpose.data,
            driver=form.driver.data,
            passengers=form.passengers.data,
            created_by=current_user.id
        )
        
        # 更新车辆状态为派出
        car.status = CarStatus.dispatched
        car.updated_by = current_user.id
        car.updated_at = datetime.now()
        
        db.session.add(record)
        db.session.commit()
        
        flash('用车申请已提交，车辆状态已更新为派出', 'success')
        return redirect(url_for('official_car.car_usage'))
    
    # 预填充车牌号
    form.plate_number.data = car.plate_number
    
    return render_template('vehicle/official_car/use_car.html', 
                          title='用车申请', 
                          form=form, 
                          car=car)

@bp.route('/maintain_car/<int:car_id>', methods=['GET', 'POST'])
@login_required
def maintain_car(car_id):
    car = OfficialCar.query.get_or_404(car_id)
    
    if request.method == 'POST':
        # 创建新的维修保养记录
        record = CarMaintenanceRecord(
            car_id=car.id,
            application_time=datetime.strptime(request.form.get('application_time'), '%Y-%m-%d'),
            car_type=request.form.get('car_type'),
            plate_number=request.form.get('plate_number'),
            driver=request.form.get('driver'),
            sender=request.form.get('sender'),
            reason=request.form.get('reason'),
            maintenance_location=request.form.get('maintenance_location'),
            remarks=request.form.get('remarks'),
            created_by=current_user.id
        )
        
        # 更新车辆状态为维保
        car.status = CarStatus.maintenance
        car.updated_by = current_user.id
        car.updated_at = datetime.now()
        
        db.session.add(record)
        db.session.commit()
        
        flash('维修保养申请已提交，车辆状态已更新为维保', 'success')
        return redirect(url_for('official_car.car_maintenance'))
    
    return render_template('vehicle/official_car/maintain_car.html', title='维修保养申请', car=car, today=datetime.now())

@bp.route('/refuel_car/<int:car_id>')
@login_required
def refuel_car(car_id):
    car = OfficialCar.query.get_or_404(car_id)
    return render_template('vehicle/official_car/refuel_car.html', title='加油充值申请', car=car)

@bp.route('/delete_car/<int:car_id>', methods=['POST'])
@login_required
def delete_car(car_id):
    car = OfficialCar.query.get_or_404(car_id)
    
    # 如果有车辆照片，删除文件
    if car.vehicle_license:
        try:
            file_path = os.path.join(os.getcwd(), 'app', car.vehicle_license.lstrip('/'))
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"删除车辆照片文件失败: {e}")
    
    # 从数据库中删除车辆记录
    db.session.delete(car)
    db.session.commit()
    
    flash('车辆已永久删除', 'success')
    return redirect(url_for('official_car.car_info'))

@bp.route('/import_cars', methods=['POST'])
@login_required
def import_cars():
    if 'file' not in request.files:
        flash('没有文件', 'danger')
        return redirect(url_for('official_car.index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('没有选择文件', 'danger')
        return redirect(url_for('official_car.index'))
    
    if file and (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        try:
            # 读取Excel文件
            df = pd.read_excel(file)
            success_count = 0
            error_count = 0
            
            for _, row in df.iterrows():
                try:
                    # 检查必填字段
                    if pd.isna(row.get('资产编号')):
                        error_count += 1
                        continue
                    
                    # 检查资产编号是否已存在
                    if OfficialCar.query.filter_by(asset_number=row['资产编号']).first():
                        error_count += 1
                        continue
                    
                    # 创建新车辆
                    car = OfficialCar(
                        asset_number=row['资产编号'],
                        card_number=row.get('卡片编号') if not pd.isna(row.get('卡片编号', '')) else None,
                        brand=row.get('品牌') if not pd.isna(row.get('品牌', '')) else None,
                        asset_description=row.get('资产名称') if not pd.isna(row.get('资产名称', '')) else None,
                        model=row.get('规格型号') if not pd.isna(row.get('规格型号', '')) else None,
                        original_value=row.get('原值') if not pd.isna(row.get('原值', '')) else None,
                        is_business_car=row.get('是否为公务车') if not pd.isna(row.get('是否为公务车', '')) else None,
                        plate_number=row.get('车牌号') if not pd.isna(row.get('车牌号', '')) else None,
                        car_model=row.get('车型') if not pd.isna(row.get('车型', '')) else None,
                        car_type=row.get('车型') if not pd.isna(row.get('车型', '')) else None,
                        registration_time=row.get('注册登记时间') if not pd.isna(row.get('注册登记时间', '')) else None,
                        seat_count=row.get('座位数') if not pd.isna(row.get('座位数', '')) else None,
                        displacement=row.get('排量') if not pd.isna(row.get('排量', '')) else None,
                        responsible_person=row.get('负责人') if not pd.isna(row.get('负责人', '')) else None,
                        usage_nature=row.get('使用性质') if not pd.isna(row.get('使用性质', '')) else None,
                        status=CarStatus.idle,
                        created_by=current_user.id
                    )
                    
                    db.session.add(car)
                    success_count += 1
                    
                except Exception as e:
                    print(f"导入行错误: {e}")
                    error_count += 1
            
            db.session.commit()
            flash(f'成功导入 {success_count} 条记录，失败 {error_count} 条', 'info')
            
        except Exception as e:
            flash(f'导入失败: {str(e)}', 'danger')
    else:
        flash('只支持 .xlsx 或 .xls 文件格式', 'danger')
    
    return redirect(url_for('official_car.index'))

@bp.route('/export_scrapped_cars')
@login_required
def export_scrapped_cars():
    # 查询所有报废车辆，按报废时间升序排序
    cars = OfficialCar.query.filter_by(is_scrapped=True).order_by(OfficialCar.scrap_time).all()
    
    # 创建DataFrame
    data = []
    for car in cars:
        data.append({
            '资产编号': car.asset_number,
            '卡片编号': car.card_number,
            '品牌': car.brand,
            '资产描述': car.asset_description,
            '规格型号': car.model,
            '原值': '{:.2f}'.format(float(car.original_value)) if car.original_value else '',
            '经营用车': car.is_business_car,
            '车牌号': car.plate_number,
            '车辆型号': car.car_model,
            '登记时间': car.registration_time.strftime('%Y-%m-%d') if car.registration_time else '',
            '座位数': car.seat_count,
            '排气量': car.displacement,
            '责任人': car.responsible_person,
            '使用性质': car.usage_nature,
            '报废时间': car.scrap_time.strftime('%Y-%m-%d') if car.scrap_time else ''
        })
    
    df = pd.DataFrame(data)
    
    # 创建内存中的Excel文件
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    # 指定sheet名称
    sheet_name = '报废车辆信息'
    df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=2)  # 从第3行开始写入数据
    
    # 获取工作簿和工作表对象
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    
    # 设置标题格式
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    # 合并单元格并写入标题
    worksheet.merge_range(0, 0, 0, len(df.columns) - 1, '报废车辆信息', title_format)
    
    # 添加导出时间
    date_format = workbook.add_format({
        'align': 'right',
        'font_size': 10
    })
    export_time = f'导出时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    worksheet.merge_range(1, 0, 1, len(df.columns) - 1, export_time, date_format)
    
    # 自动调整列宽
    for idx, col in enumerate(df.columns):
        column_width = max(len(str(col)), df[col].astype(str).map(len).max())
        worksheet.set_column(idx, idx, column_width + 2)
    
    writer.close()
    output.seek(0)
    
    # 生成文件名
    filename = f'报废车辆信息_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'
    
    return send_file(
        output, 
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@bp.route('/change_status/<int:car_id>', methods=['POST'])
@login_required
def change_status(car_id):
    car = OfficialCar.query.get_or_404(car_id)
    status = request.form.get('status')
    
    # 验证状态是否有效
    if status not in [s.name for s in CarStatus]:
        flash('无效的状态', 'danger')
        return redirect(url_for('official_car.index'))
    
    # 更新车辆状态
    car.status = CarStatus[status]
    car.updated_by = current_user.id
    car.updated_at = datetime.now()
    db.session.commit()
    
    flash(f'车辆状态已更新为 {CarStatus[status].value}', 'success')
    return redirect(url_for('official_car.index'))

@bp.route('/restore_car/<int:car_id>', methods=['POST'])
@login_required
def restore_car(car_id):
    car = OfficialCar.query.get_or_404(car_id)
    car.status = CarStatus.idle  # 将状态设置为闲置
    car.is_scrapped = False      # 取消报废标记
    car.scrap_time = None        # 清除报废时间
    car.updated_by = current_user.id
    car.updated_at = datetime.now()
    db.session.commit()
    flash('车辆已退回到车辆信息列表', 'success')
    return redirect(url_for('official_car.scrapped_cars'))

@bp.route('/add_usage_record', methods=['GET', 'POST'])
@login_required
def add_usage_record():
    form = CarUsageRecordFullForm()
    
    # 获取所有车辆的车牌号作为选项
    cars = OfficialCar.query.filter(OfficialCar.status != CarStatus.scrapped).all()
    form.plate_number.choices = [(car.plate_number, car.plate_number) for car in cars]
    
    if form.validate_on_submit():
        # 根据车牌号查找车辆
        car = OfficialCar.query.filter_by(plate_number=form.plate_number.data).first()
        
        if not car:
            flash('未找到对应车牌号的车辆', 'danger')
            return render_template('vehicle/official_car/add_usage_record.html', title='添加用车记录', form=form)
        
        # 创建新的用车记录
        record = CarUsageRecord(
            car_id=car.id,
            department=form.department.data,
            plate_number=form.plate_number.data,
            departure_date=form.departure_date.data,
            departure_time=datetime.strptime(form.departure_time.data, '%H:%M').time(),
            departure_mileage=form.departure_mileage.data,
            destination_purpose=form.destination_purpose.data,
            driver=form.driver.data,
            passengers=form.passengers.data,
            created_by=current_user.id
        )
        
        # 处理收车信息
        had_return_time = record.return_time is not None
        
        if form.return_time.data:
            record.return_time = form.return_time.data
            record.return_mileage = form.return_mileage.data
            record.refueling = form.refueling.data
            record.maintenance = form.maintenance.data
            # 修改：只有当toll_fee字段为None时才设置默认值，如果是空字符串则保留用户的输入
            if form.toll_fee.data is None:
                record.toll_fee = 'etc'
            else:
                record.toll_fee = form.toll_fee.data
            record.parking_fee = form.parking_fee.data
            record.accident_violation = form.accident_violation.data
            
            # 计算使用时长
            record.usage_duration = calculate_usage_duration(
                record.departure_date, 
                record.departure_time, 
                form.return_time.data
            )
            
            # 如果提供了收车信息，车辆状态更新为空闲
            car.status = CarStatus.idle
        else:
            # 清除收车信息
            record.return_time = None
            record.return_mileage = None
            record.refueling = False
            record.maintenance = None
            record.toll_fee = None
            record.parking_fee = None
            record.accident_violation = None
            record.usage_duration = None
            
            # 如果没有提供收车信息，车辆状态更新为派出
            car.status = CarStatus.dispatched
        
        # 如果收车状态发生变化，更新车辆状态
        if had_return_time != (form.return_time.data is not None):
            car.updated_by = current_user.id
            car.updated_at = datetime.now()
        
        car.updated_by = current_user.id
        car.updated_at = datetime.now()
        
        db.session.add(record)
        db.session.commit()
        
        flash('用车记录已添加', 'success')
        return redirect(url_for('official_car.car_usage'))
    
    return render_template('vehicle/official_car/add_usage_record.html', title='添加用车记录', form=form)

@bp.route('/edit_usage_record/<int:record_id>', methods=['GET', 'POST'])
@login_required
def edit_usage_record(record_id):
    record = CarUsageRecord.query.get_or_404(record_id)
    car = OfficialCar.query.get_or_404(record.car_id)
    form = CarUsageRecordFullForm()
    
    # 获取所有车辆的车牌号作为选项
    cars = OfficialCar.query.filter(OfficialCar.status != CarStatus.scrapped).all()
    form.plate_number.choices = [(c.plate_number, c.plate_number) for c in cars]
    
    if form.validate_on_submit():
        # 检查车牌号是否变更
        if form.plate_number.data != record.plate_number:
            # 根据新车牌号查找车辆
            new_car = OfficialCar.query.filter_by(plate_number=form.plate_number.data).first()
            
            if not new_car:
                flash('未找到对应车牌号的车辆', 'danger')
                return render_template('vehicle/official_car/edit_usage_record.html', 
                                      title='编辑用车记录', 
                                      form=form, 
                                      record=record)
            
            # 如果原车辆状态为派出，则恢复为空闲
            if car.status == CarStatus.dispatched:
                car.status = CarStatus.idle
                car.updated_by = current_user.id
                car.updated_at = datetime.now()
            
            # 更新记录关联的车辆ID
            record.car_id = new_car.id
            car = new_car
        
        # 更新记录信息
        record.department = form.department.data
        record.plate_number = form.plate_number.data
        record.departure_date = form.departure_date.data
        record.departure_time = datetime.strptime(form.departure_time.data, '%H:%M').time()
        record.departure_mileage = form.departure_mileage.data
        record.destination_purpose = form.destination_purpose.data
        record.driver = form.driver.data
        record.passengers = form.passengers.data
        record.updated_by = current_user.id
        record.updated_at = datetime.now()
        
        # 处理收车信息
        had_return_time = record.return_time is not None
        
        if form.return_time.data:
            record.return_time = form.return_time.data
            record.return_mileage = form.return_mileage.data
            record.refueling = form.refueling.data
            record.maintenance = form.maintenance.data
            # 修改：只有当toll_fee字段为None时才设置默认值，如果是空字符串则保留用户的输入
            if form.toll_fee.data is None:
                record.toll_fee = 'etc'
            else:
                record.toll_fee = form.toll_fee.data
            record.parking_fee = form.parking_fee.data
            record.accident_violation = form.accident_violation.data
            
            # 计算使用时长
            record.usage_duration = calculate_usage_duration(
                record.departure_date, 
                record.departure_time, 
                form.return_time.data
            )
            
            # 如果提供了收车信息，车辆状态更新为空闲
            car.status = CarStatus.idle
        else:
            # 清除收车信息
            record.return_time = None
            record.return_mileage = None
            record.refueling = False
            record.maintenance = None
            record.toll_fee = None
            record.parking_fee = None
            record.accident_violation = None
            record.usage_duration = None
            
            # 如果没有提供收车信息，车辆状态更新为派出
            car.status = CarStatus.dispatched
        
        # 如果收车状态发生变化，更新车辆状态
        if had_return_time != (form.return_time.data is not None):
            car.updated_by = current_user.id
            car.updated_at = datetime.now()
        
        db.session.commit()
        
        flash('用车记录已更新', 'success')
        return redirect(url_for('official_car.car_usage'))
    
    # 预填充表单
    if request.method == 'GET':
        form.department.data = record.department
        form.plate_number.data = record.plate_number
        form.departure_date.data = record.departure_date
        form.departure_time.data = record.departure_time.strftime('%H:%M')
        form.departure_mileage.data = record.departure_mileage
        form.destination_purpose.data = record.destination_purpose
        form.driver.data = record.driver
        form.passengers.data = record.passengers
        form.return_time.data = record.return_time
        form.return_mileage.data = record.return_mileage
        form.refueling.data = record.refueling
        form.maintenance.data = record.maintenance
        form.toll_fee.data = record.toll_fee
        form.parking_fee.data = record.parking_fee
        form.accident_violation.data = record.accident_violation
    
    return render_template('vehicle/official_car/edit_usage_record.html', 
                          title='编辑用车记录', 
                          form=form, 
                          record=record)

@bp.route('/delete_usage_record/<int:record_id>', methods=['POST'])
@login_required
def delete_usage_record(record_id):
    record = CarUsageRecord.query.get_or_404(record_id)
    car = OfficialCar.query.get_or_404(record.car_id)
    
    # 如果车辆状态为派出且没有其他派出记录，则恢复为空闲
    if car.status == CarStatus.dispatched:
        other_records = CarUsageRecord.query.filter(
            CarUsageRecord.car_id == car.id,
            CarUsageRecord.id != record.id,
            CarUsageRecord.return_time.is_(None)
        ).count()
        
        if other_records == 0:
            car.status = CarStatus.idle
            car.updated_by = current_user.id
            car.updated_at = datetime.now()
    
    # 删除记录
    db.session.delete(record)
    db.session.commit()
    
    flash('用车记录已删除', 'success')
    return redirect(url_for('official_car.car_usage'))

@bp.route('/export_usage_records')
@login_required
def export_usage_records():
    # 获取查询参数
    year = request.args.get('year', '')
    plate_number = request.args.get('plate_number', '')
    search = request.args.get('search', '')
    
    # 构建查询
    query = CarUsageRecord.query
    
    if year:
        query = query.filter(db.extract('year', CarUsageRecord.departure_date) == year)
    
    if plate_number:
        query = query.filter(CarUsageRecord.plate_number == plate_number)
    
    if search:
        query = query.filter(
            (CarUsageRecord.department.ilike(f'%{search}%')) |
            (CarUsageRecord.plate_number.ilike(f'%{search}%')) |
            (CarUsageRecord.destination_purpose.ilike(f'%{search}%')) |
            (CarUsageRecord.driver.ilike(f'%{search}%')) |
            (CarUsageRecord.passengers.ilike(f'%{search}%')) |
            (CarUsageRecord.maintenance.ilike(f'%{search}%')) |
            (CarUsageRecord.accident_violation.ilike(f'%{search}%'))
        )
    
    # 按出车日期和时间升序排序（早的记录在前），相同日期和时间的按创建时间升序排序（早创建的在前）
    records = query.order_by(
        CarUsageRecord.departure_date.asc(), 
        CarUsageRecord.departure_time.asc(),
        CarUsageRecord.created_at.asc()
    ).all()
    
    # 创建DataFrame
    data = []
    for i, record in enumerate(records, 1):
        data.append({
            '序号': i,
            '申请使用部门': record.department,
            '使用车牌号': record.plate_number,
            '出车日期': record.departure_date.strftime('%Y-%m-%d'),
            '出车时间': record.departure_time.strftime('%H:%M'),
            '出车里程': record.departure_mileage if record.departure_mileage else '-',
            '出车去向及事由': record.destination_purpose if record.destination_purpose else '-',
            '收车时间': record.return_time.strftime('%Y-%m-%d %H:%M') if record.return_time else '-',
            '收车里程': record.return_mileage if record.return_mileage else '-',
            '使用时长': record.usage_duration if record.usage_duration else '-',
            '驾驶员': record.driver if record.driver else '-',
            '随同人员': record.passengers if record.passengers else '-',
            '加油': '是' if record.refueling else '否',
            '维修': record.maintenance if record.maintenance else '-',
            '过路过桥费': record.toll_fee if record.toll_fee else '-',
            '停车费': record.parking_fee if record.parking_fee else '-',
            '交通事故、违章': record.accident_violation if record.accident_violation else '-'
        })
    
    df = pd.DataFrame(data)
    
    # 创建内存中的Excel文件
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    # 指定sheet名称
    sheet_name = '车辆使用记录'
    df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=2)  # 从第3行开始写入数据
    
    # 获取工作簿和工作表对象
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    
    # 设置标题格式
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    # 合并单元格并写入标题
    worksheet.merge_range(0, 0, 0, len(df.columns) - 1, '车辆使用记录', title_format)
    
    # 添加导出时间
    date_format = workbook.add_format({
        'align': 'right',
        'font_size': 10
    })
    export_time = f'导出时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    worksheet.merge_range(1, 0, 1, len(df.columns) - 1, export_time, date_format)
    
    # 自动调整列宽
    for idx, col in enumerate(df.columns):
        column_width = max(len(str(col)), df[col].astype(str).map(len).max())
        worksheet.set_column(idx, idx, column_width + 2)
    
    writer.close()
    output.seek(0)
    
    # 生成文件名
    filename = f'车辆使用记录_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'
    
    return send_file(
        output, 
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@bp.route('/car_insurance')
@login_required
def car_insurance():
    """车辆保险记录页面"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search = request.args.get('search', '')
    year = request.args.get('year', '')
    
    # 构建查询
    query = CarInsurance.query
    
    if search:
        query = query.filter(
            (CarInsurance.plate_number.ilike(f'%{search}%')) |
            (CarInsurance.car_type.ilike(f'%{search}%'))
        )
    
    if year:
        query = query.filter(db.extract('year', CarInsurance.renewal_date) == year)
    
    # 获取所有年份
    all_years = db.session.query(db.extract('year', CarInsurance.renewal_date)).distinct().order_by(db.extract('year', CarInsurance.renewal_date).desc()).all()
    years = [int(year[0]) for year in all_years if year[0]]
    
    # 按续保日期降序排序，当续保日期相同时，按创建时间降序排序（新添加的在前）
    records = query.order_by(CarInsurance.renewal_date.desc(), CarInsurance.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('vehicle/official_car/car_insurance.html', 
                          title='车辆保险', 
                          records=records.items,
                          pagination=records,
                          years=years,
                          current_year=year)

@bp.route('/add_insurance', methods=['GET', 'POST'])
@login_required
def add_insurance():
    """添加车辆保险记录"""
    form = CarInsuranceForm()
    
    # 获取所有车辆的车牌号作为选项
    cars = OfficialCar.query.filter(OfficialCar.status != CarStatus.scrapped).all()
    form.plate_number.choices = [(car.plate_number, car.plate_number) for car in cars]
    
    # 获取车牌号参数（如果有）
    plate_number = request.args.get('plate_number', '')
    
    # 设置默认值
    today = datetime.now().date()
    
    if request.method == 'GET':
        # 默认设置续保日期为当前日期
        form.renewal_date.data = today
        
        if plate_number and plate_number in [choice[0] for choice in form.plate_number.choices]:
            form.plate_number.data = plate_number
            car = OfficialCar.query.filter_by(plate_number=plate_number).first()
            
            if car:
                # 查找最近的保险记录
                last_insurance = CarInsurance.query.filter_by(car_id=car.id).order_by(CarInsurance.insurance_end_date.desc()).first()
                
                # 设置默认保险期限
                if last_insurance:
                    # 如果有上一次保险记录，使用其结束日期后一天作为开始日期
                    start_date = last_insurance.insurance_end_date + timedelta(days=1)
                    end_date = start_date.replace(year=start_date.year + 1) - timedelta(days=1)
                else:
                    # 如果没有保险记录，使用当前日期作为开始日期
                    start_date = today
                    end_date = start_date.replace(year=start_date.year + 1) - timedelta(days=1)
                    
                form.insurance_period.data = f"{start_date.strftime('%Y-%m-%d')}至{end_date.strftime('%Y-%m-%d')}"
        else:
            # 如果没有指定车牌号（从车辆保险页面点击"添加记录"），设置默认保险期限为一年
            start_date = today
            end_date = start_date.replace(year=start_date.year + 1) - timedelta(days=1)
            form.insurance_period.data = f"{start_date.strftime('%Y-%m-%d')}至{end_date.strftime('%Y-%m-%d')}"
    
    if form.validate_on_submit():
        # 根据车牌号查找车辆
        car = OfficialCar.query.filter_by(plate_number=form.plate_number.data).first()
        
        if not car:
            flash('未找到对应车牌号的车辆', 'danger')
            return render_template('vehicle/official_car/add_insurance.html', 
                                  title='添加车辆保险', 
                                  form=form,
                                  car_types=car_types)
        
        # 解析保险日期
        start_date_str, end_date_str = form.insurance_period.data.split('至')
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # 创建保险记录
        insurance = CarInsurance(
            car_id=car.id,
            plate_number=car.plate_number,
            car_type=car.car_type,  # 从车辆信息中获取车型
            amount=form.amount.data,
            insurance_start_date=start_date,
            insurance_end_date=end_date,
            renewal_date=form.renewal_date.data,
            created_by=current_user.id
        )
        
        db.session.add(insurance)
        db.session.commit()
        
        flash('车辆保险记录已添加', 'success')
        return redirect(url_for('official_car.car_insurance'))
    
    # 获取所有车辆的车型信息，用于前端显示
    car_types = {car.plate_number: car.car_type for car in cars}
    
    return render_template('vehicle/official_car/add_insurance.html', 
                          title='添加车辆保险', 
                          form=form,
                          car_types=car_types)

@bp.route('/edit_insurance/<int:insurance_id>', methods=['GET', 'POST'])
@login_required
def edit_insurance(insurance_id):
    """编辑车辆保险记录"""
    insurance = CarInsurance.query.get_or_404(insurance_id)
    form = CarInsuranceForm()
    
    # 获取所有车辆的车牌号作为选项
    cars = OfficialCar.query.filter(OfficialCar.status != CarStatus.scrapped).all()
    form.plate_number.choices = [(car.plate_number, car.plate_number) for car in cars]
    
    if form.validate_on_submit():
        # 根据车牌号查找车辆
        car = OfficialCar.query.filter_by(plate_number=form.plate_number.data).first()
        
        if not car:
            flash('未找到对应车牌号的车辆', 'danger')
            return render_template('vehicle/official_car/edit_insurance.html', 
                                  title='编辑车辆保险', 
                                  form=form,
                                  insurance=insurance)
        
        # 解析保险日期
        start_date_str, end_date_str = form.insurance_period.data.split('至')
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # 更新保险记录
        insurance.car_id = car.id
        insurance.plate_number = car.plate_number
        insurance.car_type = car.car_type  # 从车辆信息中获取车型
        insurance.amount = form.amount.data
        insurance.insurance_start_date = start_date
        insurance.insurance_end_date = end_date
        insurance.renewal_date = form.renewal_date.data
        insurance.updated_by = current_user.id
        insurance.updated_at = datetime.now()
        
        db.session.commit()
        
        flash('车辆保险记录已更新', 'success')
        return redirect(url_for('official_car.car_insurance'))
    
    elif request.method == 'GET':
        form.plate_number.data = insurance.plate_number
        form.amount.data = insurance.amount
        form.insurance_period.data = f"{insurance.insurance_start_date.strftime('%Y-%m-%d')}至{insurance.insurance_end_date.strftime('%Y-%m-%d')}"
        form.renewal_date.data = insurance.renewal_date
    
    # 获取所有车辆的车型信息，用于前端显示
    car_types = {car.plate_number: car.car_type for car in cars}
    
    return render_template('vehicle/official_car/edit_insurance.html', 
                          title='编辑车辆保险', 
                          form=form,
                          insurance=insurance,
                          car_types=car_types)

@bp.route('/delete_insurance/<int:insurance_id>', methods=['POST'])
@login_required
def delete_insurance(insurance_id):
    """删除车辆保险记录"""
    insurance = CarInsurance.query.get_or_404(insurance_id)
    
    db.session.delete(insurance)
    db.session.commit()
    
    flash('车辆保险记录已删除', 'success')
    return redirect(url_for('official_car.car_insurance'))

@bp.route('/export_insurance')
@login_required
def export_insurance():
    """导出车辆保险记录"""
    # 获取查询参数
    search = request.args.get('search', '')
    year = request.args.get('year', '')
    
    # 构建查询
    query = CarInsurance.query
    
    if search:
        query = query.filter(
            (CarInsurance.plate_number.ilike(f'%{search}%')) |
             (CarInsurance.car_type.ilike(f'%{search}%'))
        )
    
    if year:
        query = query.filter(db.extract('year', CarInsurance.renewal_date) == year)
    
    # 按续保日期升序排序，当续保日期相同时，按创建时间升序排序（旧添加的在前）
    records = query.order_by(CarInsurance.renewal_date.asc(), CarInsurance.created_at.asc()).all()
    
    # 创建DataFrame
    data = []
    for i, record in enumerate(records, 1):
        data.append({
            '序号': i,
            '车牌号': record.plate_number,
            '车型': record.car_type or '-',
            '金额': '{:.2f}'.format(record.amount),
            '保险日期': f"{record.insurance_start_date.strftime('%Y-%m-%d')}至{record.insurance_end_date.strftime('%Y-%m-%d')}",
            '续保日期': record.renewal_date.strftime('%Y-%m-%d')
        })
    
    df = pd.DataFrame(data)
    
    # 创建内存中的Excel文件
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    # 指定sheet名称
    sheet_name = '车辆保险记录'
    df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=2)  # 从第3行开始写入数据
    
    # 获取工作簿和工作表对象
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    
    # 设置标题格式
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    # 合并单元格并写入标题
    worksheet.merge_range(0, 0, 0, len(df.columns) - 1, '车辆保险记录', title_format)
    
    # 添加导出时间
    date_format = workbook.add_format({
        'align': 'right',
        'font_size': 10
    })
    export_time = f'导出时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    worksheet.merge_range(1, 0, 1, len(df.columns) - 1, export_time, date_format)
    
    # 自动调整列宽
    for idx, col in enumerate(df.columns):
        column_width = max(len(str(col)), df[col].astype(str).map(len).max())
        worksheet.set_column(idx, idx, column_width + 2)
    
    writer.close()
    output.seek(0)
    
    # 生成文件名
    filename = f'车辆保险记录_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'
    
    return send_file(
        output, 
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@bp.route('/get_latest_insurance')
@login_required
def get_latest_insurance():
    """获取车辆的最新保险记录并计算下一年的保险时间段"""
    plate_number = request.args.get('plate_number', '')
    
    if not plate_number:
        return jsonify({'success': False, 'message': '未提供车牌号'})
    
    # 查找车辆
    car = OfficialCar.query.filter_by(plate_number=plate_number).first()
    
    if not car:
        return jsonify({'success': False, 'message': '未找到对应车牌号的车辆'})
    
    # 查找最近的保险记录
    last_insurance = CarInsurance.query.filter_by(car_id=car.id).order_by(CarInsurance.insurance_end_date.desc()).first()
    
    today = datetime.now().date()
    
    # 计算保险期限
    if last_insurance:
        # 如果有上一次保险记录，使用其结束日期后一天作为开始日期
        start_date = last_insurance.insurance_end_date + timedelta(days=1)
        end_date = start_date.replace(year=start_date.year + 1) - timedelta(days=1)
    else:
        # 如果没有保险记录，使用当前日期作为开始日期
        start_date = today
        end_date = start_date.replace(year=start_date.year + 1) - timedelta(days=1)
    
    insurance_period = f"{start_date.strftime('%Y-%m-%d')}至{end_date.strftime('%Y-%m-%d')}"
    
    return jsonify({
        'success': True,
        'insurance_period': insurance_period,
        'has_previous_insurance': last_insurance is not None,
        'previous_end_date': last_insurance.insurance_end_date.strftime('%Y-%m-%d') if last_insurance else None
    })

@bp.route('/export_cars')
@login_required
def export_cars():
    """导出车辆信息"""
    # 获取查询参数
    usage_nature = request.args.get('usage_nature', '')
    search = request.args.get('search', '')
    
    # 构建查询
    query = OfficialCar.query.filter(OfficialCar.status != CarStatus.scrapped)
    
    if usage_nature:
        query = query.filter(OfficialCar.usage_nature == usage_nature)
    
    if search:
        query = query.filter(
            (OfficialCar.asset_number.ilike(f'%{search}%')) |
            (OfficialCar.plate_number.ilike(f'%{search}%')) |
            (OfficialCar.brand.ilike(f'%{search}%')) |
            (OfficialCar.asset_description.ilike(f'%{search}%')) |
            (OfficialCar.model.ilike(f'%{search}%')) |
            (OfficialCar.car_model.ilike(f'%{search}%')) |
            (OfficialCar.car_type.ilike(f'%{search}%')) |
            (OfficialCar.responsible_person.ilike(f'%{search}%')) |
            (OfficialCar.usage_nature.ilike(f'%{search}%'))
        )
    
    # 按添加时间升序排序（新添加的在下）
    cars = query.order_by(OfficialCar.created_at).all()
    
    # 获取每辆车的最新保险信息
    car_insurance_info = {}
    for car in cars:
        latest_insurance = CarInsurance.query.filter_by(car_id=car.id).order_by(CarInsurance.insurance_end_date.desc()).first()
        if latest_insurance:
            car_insurance_info[car.id] = f"{latest_insurance.insurance_start_date.strftime('%Y-%m-%d')}至{latest_insurance.insurance_end_date.strftime('%Y-%m-%d')}"
        else:
            car_insurance_info[car.id] = '-'
    
    # 创建DataFrame
    data = []
    for i, car in enumerate(cars, 1):
        data.append({
            '序号': i,
            '资产编号': car.asset_number,
            '卡片编号': car.card_number or '-',
            '品牌': car.brand or '-',
            '资产描述': car.asset_description or '-',
            '规格型号': car.model or '-',
            '原值': '{:.2f}'.format(float(car.original_value)) if car.original_value else '-',
            '经营用车': car.is_business_car or '-',
            '车牌号': car.plate_number or '-',
            '车辆型号': car.car_model or '-',
            '登记时间': car.registration_time.strftime('%Y-%m-%d') if car.registration_time else '-',
            '座位数': car.seat_count or '-',
            '排气量': car.displacement or '-',
            '责任人': car.responsible_person or '-',
            '使用性质': car.usage_nature or '-',
            '车型': car.car_type or '-',
            '保险日期': car_insurance_info[car.id]
        })
    
    df = pd.DataFrame(data)
    
    # 创建内存中的Excel文件
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    # 指定sheet名称
    sheet_name = '车辆信息'
    df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=2)  # 从第3行开始写入数据
    
    # 获取工作簿和工作表对象
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    
    # 设置标题格式
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    # 合并单元格并写入标题
    worksheet.merge_range(0, 0, 0, len(df.columns) - 1, '车辆信息', title_format)
    
    # 添加导出时间
    date_format = workbook.add_format({
        'align': 'right',
        'font_size': 10
    })
    export_time = f'导出时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    worksheet.merge_range(1, 0, 1, len(df.columns) - 1, export_time, date_format)
    
    # 自动调整列宽
    for idx, col in enumerate(df.columns):
        column_width = max(len(str(col)), df[col].astype(str).map(len).max())
        worksheet.set_column(idx, idx, column_width + 2)
    
    writer.close()
    output.seek(0)
    
    # 生成文件名
    filename = f'车辆信息_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'
    
    return send_file(
        output, 
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ) 