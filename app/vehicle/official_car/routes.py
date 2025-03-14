from flask import render_template, flash, redirect, url_for, request, jsonify, send_file
from flask_login import login_required, current_user
from app import db
from app.vehicle.official_car import bp
from app.models.official_car import OfficialCar, CarStatus
from app.vehicle.official_car.forms import OfficialCarForm
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import pandas as pd
import uuid
from sqlalchemy import desc

@bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 获取查询参数
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    
    # 构建查询
    query = OfficialCar.query.filter(OfficialCar.status != CarStatus.scrapped)
    
    if status:
        query = query.filter(OfficialCar.status == CarStatus[status])
    
    if search:
        query = query.filter(
            (OfficialCar.asset_number.ilike(f'%{search}%')) |
            (OfficialCar.plate_number.ilike(f'%{search}%'))
        )
    
    # 按添加时间升序排序（新添加的在下）
    query = query.order_by(OfficialCar.created_at)
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page)
    cars = pagination.items
    
    return render_template('vehicle/official_car/index.html', 
                          title='公务车辆',
                          cars=cars,
                          pagination=pagination,
                          page=page,
                          per_page=per_page)

@bp.route('/car_info')
@login_required
def car_info():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 获取查询参数
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    
    # 构建查询
    query = OfficialCar.query.filter(OfficialCar.status != CarStatus.scrapped)
    
    if status:
        query = query.filter(OfficialCar.status == CarStatus[status])
    
    if search:
        query = query.filter(
            (OfficialCar.asset_number.ilike(f'%{search}%')) |
            (OfficialCar.plate_number.ilike(f'%{search}%'))
        )
    
    # 按添加时间升序排序（新添加的在下）
    query = query.order_by(OfficialCar.created_at)
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page)
    cars = pagination.items
    
    return render_template('vehicle/official_car/car_info.html', 
                          title='车辆信息',
                          cars=cars,
                          pagination=pagination,
                          page=page,
                          per_page=per_page)

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
            registration_time=form.registration_time.data,
            seat_count=form.seat_count.data,
            displacement=form.displacement.data,
            responsible_person=form.responsible_person.data,
            usage_nature=form.usage_nature.data,
            status=CarStatus.idle,
            created_by=current_user.id
        )
        
        # 处理车辆照片上传
        if form.vehicle_license.data:
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
        return redirect(url_for('official_car.index'))
    
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
        car.registration_time = form.registration_time.data
        car.seat_count = form.seat_count.data
        car.displacement = form.displacement.data
        car.responsible_person = form.responsible_person.data
        car.usage_nature = form.usage_nature.data
        car.updated_by = current_user.id
        car.updated_at = datetime.now()
        
        # 处理车辆照片上传
        if form.vehicle_license.data:
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
        return redirect(url_for('official_car.index'))
    
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
    
    # 构建查询
    query = OfficialCar.query.filter_by(is_scrapped=True)
    
    if search:
        query = query.filter(
            (OfficialCar.asset_number.ilike(f'%{search}%')) |
            (OfficialCar.plate_number.ilike(f'%{search}%'))
        )
    
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
                          per_page=per_page)

@bp.route('/return_car/<int:car_id>', methods=['POST'])
@login_required
def return_car(car_id):
    car = OfficialCar.query.get_or_404(car_id)
    car.status = CarStatus.idle  # 将状态设置为闲置
    car.is_scrapped = False      # 取消报废标记
    car.scrap_time = None        # 清除报废时间
    car.updated_by = current_user.id
    car.updated_at = datetime.now()
    db.session.commit()
    flash('车辆已退回到车辆信息列表', 'success')
    return redirect(url_for('official_car.scrapped_cars'))

@bp.route('/car_usage')
@login_required
def car_usage():
    return render_template('vehicle/official_car/car_usage.html', title='车辆使用登记')

@bp.route('/car_maintenance')
@login_required
def car_maintenance():
    return render_template('vehicle/official_car/car_maintenance.html', title='车辆维修保养')

@bp.route('/car_fuel')
@login_required
def car_fuel():
    return render_template('vehicle/official_car/car_fuel.html', title='车辆加油充值')

@bp.route('/use_car/<int:car_id>')
@login_required
def use_car(car_id):
    car = OfficialCar.query.get_or_404(car_id)
    return render_template('vehicle/official_car/use_car.html', title='用车申请', car=car)

@bp.route('/maintain_car/<int:car_id>')
@login_required
def maintain_car(car_id):
    car = OfficialCar.query.get_or_404(car_id)
    return render_template('vehicle/official_car/maintain_car.html', title='维修保养申请', car=car)

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
            '原值': car.original_value,
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
    
    # 创建临时文件
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f'报废车辆信息_{timestamp}.xlsx'
    temp_file_path = os.path.join(os.getcwd(), 'app', 'static', 'temp', filename)
    
    # 确保目录存在
    os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
    
    # 使用ExcelWriter添加标题
    with pd.ExcelWriter(temp_file_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='报废车辆信息', index=False, startrow=2)  # 从第3行开始写入数据
        
        # 获取工作簿和工作表对象
        workbook = writer.book
        worksheet = writer.sheets['报废车辆信息']
        
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
    
    # 发送文件
    return send_file(temp_file_path, as_attachment=True, download_name=filename) 