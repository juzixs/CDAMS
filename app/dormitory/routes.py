from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.dormitory.forms import DormitoryForm, RoomForm, ResidentForm
from app.models import Dormitory, Room, Resident, Monitor

bp = Blueprint('dormitory', __name__)

@bp.route('/')
@login_required
def index():
    """宿舍管理首页"""
    # 获取搜索参数
    search_name = request.args.get('search_name', '')
    floor = request.args.get('floor', '')
    room_type = request.args.get('room_type', '')
    resident_name = request.args.get('resident_name', '')
    available_only = request.args.get('available_only') == 'on'
    
    try:
        # 基本查询
        query = Dormitory.query
        
        # 按宿舍名称筛选
        if search_name:
            query = query.filter(Dormitory.name.like(f'%{search_name}%'))
        
        # 获取所有宿舍，按创建时间升序排序（早添加的在前面）
        dormitories = query.order_by(Dormitory.created_at.asc()).all()
        
        # 存储过滤后的宿舍和房间
        filtered_dormitories = []
        filtered_rooms_by_dormitory = {}
        is_filtered = floor or room_type or resident_name or available_only
        
        # 处理宿舍和房间筛选
        for dormitory in dormitories:
            # 获取宿舍的所有房间
            rooms = Room.query.filter_by(dormitory_id=dormitory.id).all()
            
            # 如果没有应用过滤条件，则所有宿舍都显示，房间使用原始列表
            if not is_filtered:
                filtered_dormitories.append(dormitory)
                filtered_rooms_by_dormitory[dormitory.id] = rooms
                continue
                
            # 以下是应用过滤条件的逻辑
            filtered_rooms = rooms.copy()
            
            # 按楼层筛选
            if floor:
                filtered_rooms = [room for room in filtered_rooms if str(room.floor) == floor]
            
            # 按房间类型筛选
            if room_type:
                filtered_rooms = [room for room in filtered_rooms if room.room_type == room_type]
            
            # 按住户名称筛选
            if resident_name:
                temp_rooms = []
                for room in filtered_rooms:
                    residents = Resident.query.filter_by(room_id=room.id, checkout_date=None).all()
                    if any(resident_name.lower() in resident.name.lower() for resident in residents):
                        temp_rooms.append(room)
                filtered_rooms = temp_rooms
            
            # 只显示未住满的房间
            if available_only:
                filtered_rooms = [room for room in filtered_rooms if not room.is_full]
            
            # 如果宿舍有符合条件的房间，则添加到结果中
            if filtered_rooms:
                filtered_dormitories.append(dormitory)
                filtered_rooms_by_dormitory[dormitory.id] = filtered_rooms
        
        # 获取所有房间类型，用于下拉选择
        room_types = db.session.query(Room.room_type).distinct().all()
        room_types = [r[0] for r in room_types if r[0]]
        
        # 获取所有楼层
        floors = db.session.query(Room.floor).distinct().order_by(Room.floor).all()
        floors = [str(f[0]) for f in floors if f[0]]
        
        current_app.logger.info(f'获取到的宿舍数量: {len(dormitories)}')
        
        form = DormitoryForm()
        return render_template('dormitory/index.html', 
                            dormitories=filtered_dormitories,
                            filtered_rooms_by_dormitory=filtered_rooms_by_dormitory,
                            form=form,
                            search_name=search_name,
                            floor=floor,
                            floors=floors,
                            room_type=room_type,
                            room_types=room_types,
                            resident_name=resident_name,
                            available_only=available_only,
                            Resident=Resident,
                            is_filtered=is_filtered)
    except Exception as e:
        current_app.logger.error(f'获取宿舍列表失败: {str(e)}')
        flash('获取宿舍列表失败，请刷新页面重试', 'danger')
        return render_template('dormitory/index.html',
                            dormitories=[],
                            filtered_rooms_by_dormitory={},
                            form=form,
                            search_name=search_name,
                            floor=floor,
                            floors=[],
                            room_type=room_type,
                            room_types=[],
                            resident_name=resident_name,
                            available_only=available_only,
                            Resident=Resident,
                            is_filtered=False)

@bp.route('/add_dormitory', methods=['POST'])
@login_required
def add_dormitory():
    """添加宿舍"""
    form = DormitoryForm()
    if form.validate_on_submit():
        try:
            # 创建宿舍对象
            dormitory = Dormitory(
                name=form.name.data,
                address=form.address.data,
                type=form.type.data
            )
            
            # 如果是租赁类型，添加租赁时间
            if form.type.data == '租赁':
                dormitory.lease_start_date = form.lease_start_date.data
                dormitory.lease_end_date = form.lease_end_date.data
            
            # 保存到数据库
            db.session.add(dormitory)
            db.session.commit()
            
            # 返回成功响应
            return jsonify({
                'status': 'success',
                'message': f'宿舍 {form.name.data} 添加成功',
                'dormitory': {
                    'id': dormitory.id,
                    'name': dormitory.name,
                    'address': dormitory.address,
                    'type': dormitory.type
                }
            })
            
        except Exception as e:
            # 回滚数据库
            db.session.rollback()
            current_app.logger.error(f'添加宿舍失败: {str(e)}')
            # 返回错误响应
            return jsonify({
                'status': 'error',
                'message': f'添加宿舍失败: {str(e)}'
            }), 500
    else:
        # 表单验证失败
        errors = []
        for field, field_errors in form.errors.items():
            for error in field_errors:
                errors.append(f'{getattr(form, field).label.text}: {error}')
        
        # 返回验证错误响应
        return jsonify({
            'status': 'error',
            'message': '表单验证失败',
            'errors': errors
        }), 400

@bp.route('/delete_dormitory/<int:dormitory_id>', methods=['POST'])
@login_required
def delete_dormitory(dormitory_id):
    """删除宿舍"""
    dormitory = Dormitory.query.get_or_404(dormitory_id)
    try:
        name = dormitory.name
        db.session.delete(dormitory)
        db.session.commit()
        flash(f'宿舍 {name} 删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除宿舍失败: {str(e)}', 'danger')
    
    return redirect(url_for('dormitory.index'))

@bp.route('/dormitory/<int:dormitory_id>')
@login_required
def view_dormitory(dormitory_id):
    """查看宿舍详情"""
    dormitory = Dormitory.query.get_or_404(dormitory_id)
    room_form = RoomForm()
    
    # 获取搜索参数
    room_number = request.args.get('room_number', '')
    floor = request.args.get('floor', '')
    room_type = request.args.get('room_type', '')
    resident_name = request.args.get('resident_name', '')
    available_only = request.args.get('available_only') == 'on'
    
    # 获取宿舍的所有房间
    rooms = Room.query.filter_by(dormitory_id=dormitory_id)
    
    # 按房间号筛选
    if room_number:
        rooms = rooms.filter(Room.room_number.like(f'%{room_number}%'))
    
    # 按楼层筛选
    if floor:
        rooms = rooms.filter(Room.floor == floor)
    
    # 按房间类型筛选
    if room_type:
        rooms = rooms.filter(Room.room_type == room_type)
    
    # 获取所有符合条件的房间
    rooms = rooms.order_by(Room.room_number).all()
    
    # 如果需要按住户名称筛选或只显示未住满的房间，需要在Python中进行过滤
    if resident_name or available_only:
        filtered_rooms = []
        for room in rooms:
            # 按住户名称筛选
            if resident_name:
                residents = Resident.query.filter_by(room_id=room.id, checkout_date=None).all()
                if not any(resident_name.lower() in resident.name.lower() for resident in residents):
                    continue
            
            # 只显示未住满的房间
            if available_only and room.is_full:
                continue
            
            filtered_rooms.append(room)
        rooms = filtered_rooms
    
    # 获取所有房间类型，用于下拉选择
    room_types = db.session.query(Room.room_type).filter(Room.dormitory_id == dormitory_id).distinct().all()
    room_types = [r[0] for r in room_types if r[0]]
    
    # 获取所有楼层
    floors = db.session.query(Room.floor).filter(Room.dormitory_id == dormitory_id).distinct().order_by(Room.floor).all()
    floors = [str(f[0]) for f in floors if f[0]]
    
    return render_template('dormitory/view.html', 
                          dormitory=dormitory, 
                          rooms=rooms, 
                          room_form=room_form, 
                          Resident=Resident,
                          room_number=room_number,
                          floor=floor,
                          floors=floors,
                          room_type=room_type,
                          room_types=room_types,
                          resident_name=resident_name,
                          available_only=available_only)

@bp.route('/add_room/<int:dormitory_id>', methods=['POST'])
@login_required
def add_room(dormitory_id):
    """添加房间"""
    dormitory = Dormitory.query.get_or_404(dormitory_id)
    form = RoomForm()
    
    if form.validate_on_submit():
        try:
            # 检查房间号是否已存在
            existing_room = Room.query.filter_by(dormitory_id=dormitory_id, room_number=form.room_number.data).first()
            if existing_room:
                flash(f'房间号 {form.room_number.data} 已存在', 'danger')
                return redirect(url_for('dormitory.view_dormitory', dormitory_id=dormitory_id))
            
            room = Room(
                room_number=form.room_number.data,
                floor=form.floor.data,
                capacity=form.capacity.data,
                room_type=form.room_type.data,
                facilities=form.facilities.data,
                dormitory_id=dormitory_id
            )
            
            db.session.add(room)
            db.session.commit()
            flash(f'房间 {form.room_number.data} 添加成功', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'添加房间失败: {str(e)}')
            flash(f'添加房间失败: {str(e)}', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('dormitory.view_dormitory', dormitory_id=dormitory_id))

@bp.route('/delete_room/<int:room_id>', methods=['POST'])
@login_required
def delete_room(room_id):
    """删除房间"""
    room = Room.query.get_or_404(room_id)
    dormitory_id = room.dormitory_id
    
    try:
        room_number = room.room_number
        db.session.delete(room)
        db.session.commit()
        flash(f'房间 {room_number} 删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除房间失败: {str(e)}', 'danger')
    
    return redirect(url_for('dormitory.view_dormitory', dormitory_id=dormitory_id))

@bp.route('/room/<int:room_id>')
@login_required
def view_room(room_id):
    """查看房间详情"""
    room = Room.query.get_or_404(room_id)
    resident_form = ResidentForm()
    residents = Resident.query.filter_by(room_id=room_id, checkout_date=None).all()
    history = Resident.query.filter(Resident.room_id==room_id, Resident.checkout_date!=None).order_by(Resident.checkout_date.desc()).all()
    
    return render_template('dormitory/room.html', room=room, residents=residents, history=history, resident_form=resident_form, Resident=Resident)

@bp.route('/add_resident/<int:room_id>', methods=['POST'])
@login_required
def add_resident(room_id):
    """添加住户"""
    room = Room.query.get_or_404(room_id)
    form = ResidentForm()
    
    if form.validate_on_submit():
        try:
            # 检查房间是否已满
            if room.is_full:
                flash(f'房间已满，无法添加新住户', 'danger')
                return redirect(url_for('dormitory.view_room', room_id=room_id))
            
            resident = Resident(
                name=form.name.data,
                gender=form.gender.data,
                department=form.department.data,
                position=form.position.data,
                phone=form.phone.data,
                remarks=form.remarks.data,
                room_id=room_id,
                checkin_date=datetime.utcnow()
            )
            
            db.session.add(resident)
            db.session.commit()
            flash(f'住户 {form.name.data} 添加成功', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'添加住户失败: {str(e)}', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('dormitory.view_room', room_id=room_id))

@bp.route('/checkout_resident/<int:resident_id>', methods=['POST'])
@login_required
def checkout_resident(resident_id):
    """办理退住"""
    resident = Resident.query.get_or_404(resident_id)
    room_id = resident.room_id
    
    try:
        resident.checkout_date = datetime.utcnow()
        db.session.commit()
        flash(f'住户 {resident.name} 已办理退住', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'办理退住失败: {str(e)}', 'danger')
    
    return redirect(url_for('dormitory.view_room', room_id=room_id))

@bp.route('/edit_dormitory/<int:dormitory_id>', methods=['GET', 'POST'])
@login_required
def edit_dormitory(dormitory_id):
    """编辑宿舍信息"""
    dormitory = Dormitory.query.get_or_404(dormitory_id)
    form = DormitoryForm(obj=dormitory)
    
    if form.validate_on_submit():
        try:
            form.populate_obj(dormitory)
            db.session.commit()
            flash('宿舍信息更新成功！', 'success')
            return redirect(url_for('dormitory.view_dormitory', dormitory_id=dormitory.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'更新宿舍信息失败: {str(e)}')
            flash('更新宿舍信息失败，请稍后重试', 'danger')
    
    return render_template('dormitory/edit_dormitory.html', form=form, dormitory=dormitory)

@bp.route('/edit_room/<int:room_id>', methods=['GET', 'POST'])
@login_required
def edit_room(room_id):
    """编辑房间信息"""
    room = Room.query.get_or_404(room_id)
    form = RoomForm(obj=room)
    
    if form.validate_on_submit():
        try:
            form.populate_obj(room)
            db.session.commit()
            flash('房间信息更新成功！', 'success')
            return redirect(url_for('dormitory.view_room', room_id=room.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'更新房间信息失败: {str(e)}')
            flash('更新房间信息失败，请稍后重试', 'danger')
    
    return render_template('dormitory/edit_room.html', form=form, room=room)

@bp.route('/edit_resident/<int:resident_id>', methods=['GET', 'POST'])
@login_required
def edit_resident(resident_id):
    """编辑住户信息"""
    resident = Resident.query.get_or_404(resident_id)
    form = ResidentForm(obj=resident)
    
    if form.validate_on_submit():
        try:
            form.populate_obj(resident)
            db.session.commit()
            flash('住户信息更新成功！', 'success')
            return redirect(url_for('dormitory.view_room', room_id=resident.room_id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'更新住户信息失败: {str(e)}')
            flash('更新住户信息失败，请稍后重试', 'danger')
    
    return render_template('dormitory/edit_resident.html', form=form, resident=resident)

@bp.route('/set_monitor/<int:room_id>', methods=['POST'])
@login_required
def set_monitor(room_id):
    """设置宿舍长"""
    room = Room.query.get_or_404(room_id)
    
    # 检查房间类型
    if not room.can_have_monitor:
        flash('该房间类型不支持设置宿舍长', 'error')
        return redirect(url_for('dormitory.view_room', room_id=room_id))
    
    resident_id = request.form.get('employee_id')
    if not resident_id:
        flash('请选择宿舍长', 'error')
        return redirect(url_for('dormitory.view_room', room_id=room_id))
    
    # 验证住户是否属于该宿舍
    resident = Resident.query.get_or_404(resident_id)
    if resident.room_id != room_id:
        flash('只能选择该宿舍的住户作为宿舍长', 'error')
        return redirect(url_for('dormitory.view_room', room_id=room_id))
    
    try:
        # 创建或更新宿舍长记录
        monitor = Monitor.query.filter_by(room_id=room_id).first()
        if not monitor:
            monitor = Monitor(
                employee_id=resident.employee_id if hasattr(resident, 'employee_id') else f'EMP{resident.id:03d}',
                name=resident.name,
                gender=resident.gender,
                department=resident.department,
                position=resident.position,
                phone=resident.phone,
                room_id=room_id
            )
            db.session.add(monitor)
        else:
            monitor.employee_id = resident.employee_id if hasattr(resident, 'employee_id') else f'EMP{resident.id:03d}'
            monitor.name = resident.name
            monitor.gender = resident.gender
            monitor.department = resident.department
            monitor.position = resident.position
            monitor.phone = resident.phone
        
        room.monitor_id = monitor.id
        db.session.commit()
        flash(f'已将 {resident.name} 设置为宿舍长', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'设置宿舍长失败: {str(e)}')
        flash('设置宿舍长失败', 'error')
    
    return redirect(url_for('dormitory.view_room', room_id=room_id)) 