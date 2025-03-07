import click
from flask.cli import with_appcontext
from datetime import datetime, timedelta
from app import db
from app.models.dormitory import Dormitory, Room, Resident, Monitor

@click.command('init-test-data')
@with_appcontext
def init_test_data():
    """初始化测试数据"""
    try:
        # 清空所有表
        Monitor.query.delete()
        Resident.query.delete()
        Room.query.delete()
        Dormitory.query.delete()
        db.session.commit()
        
        # 创建宿舍
        dormitories = [
            {
                'name': '东区1号楼',
                'address': '厂区东门旁',
                'type': '自有'
            },
            {
                'name': '东区2号楼',
                'address': '厂区东门旁',
                'type': '自有'
            },
            {
                'name': '西区宿舍楼',
                'address': '厂区西门内100米',
                'type': '租赁',
                'lease_start_date': datetime.now().date(),
                'lease_end_date': (datetime.now() + timedelta(days=365)).date()
            }
        ]
        
        created_dormitories = []
        for dorm_data in dormitories:
            dorm = Dormitory(**dorm_data)
            db.session.add(dorm)
            db.session.flush()  # 获取ID
            created_dormitories.append(dorm)
        
        # 为每个宿舍创建房间
        room_types = ['男工宿舍', '女工宿舍', '高管间', '访客间']
        facilities_options = [
            '空调,电视,独卫,热水器',
            '空调,独卫,热水器',
            '空调,公共卫浴,热水器',
            '空调,电视,独卫,冰箱,热水器'
        ]
        
        for dorm in created_dormitories:
            # 每层4个房间，共5层
            for floor in range(1, 6):
                for room_num in range(1, 5):
                    # 根据楼层和房间号生成房间类型
                    if floor <= 2:
                        room_type = '男工宿舍' if room_num <= 2 else '女工宿舍'
                        capacity = 4
                        facilities = facilities_options[2]
                    elif floor == 3:
                        room_type = '女工宿舍'
                        capacity = 4
                        facilities = facilities_options[1]
                    elif floor == 4:
                        room_type = '高管间'
                        capacity = 2
                        facilities = facilities_options[0]
                    else:
                        room_type = '访客间'
                        capacity = 2
                        facilities = facilities_options[3]
                    
                    room = Room(
                        room_number=f'{floor}0{room_num}',
                        floor=floor,
                        dormitory_id=dorm.id,
                        room_type=room_type,
                        capacity=capacity,
                        facilities=facilities
                    )
                    db.session.add(room)
        
        # 添加一些住户
        residents_data = [
            {'name': '张三', 'gender': '男', 'department': '生产部', 'position': '技术员', 'phone': '13800138001'},
            {'name': '李四', 'gender': '男', 'department': '生产部', 'position': '操作工', 'phone': '13800138002'},
            {'name': '王五', 'gender': '男', 'department': '生产部', 'position': '技术员', 'phone': '13800138003'},
            {'name': '赵六', 'gender': '男', 'department': '生产部', 'position': '操作工', 'phone': '13800138004'},
            {'name': '小红', 'gender': '女', 'department': '行政部', 'position': '文员', 'phone': '13800138005'},
            {'name': '小芳', 'gender': '女', 'department': '人事部', 'position': '专员', 'phone': '13800138006'},
            {'name': '小明', 'gender': '男', 'department': '技术部', 'position': '工程师', 'phone': '13800138007'},
            {'name': '小李', 'gender': '女', 'department': '财务部', 'position': '会计', 'phone': '13800138008'}
        ]
        
        # 为第一个宿舍的一些房间添加住户
        first_dorm = created_dormitories[0]
        rooms = Room.query.filter_by(dormitory_id=first_dorm.id).all()
        
        for i, room in enumerate(rooms[:4]):  # 只给前4个房间添加住户
            # 根据房间类型选择对应性别的住户
            gender = '男' if room.room_type == '男工宿舍' else '女'
            matching_residents = [r for r in residents_data if r['gender'] == gender][:2]  # 每个房间添加2个住户
            
            for resident_data in matching_residents:
                resident = Resident(
                    **resident_data,
                    room_id=room.id,
                    checkin_date=datetime.now()
                )
                db.session.add(resident)
                
                # 将第一个住户设为宿舍长
                if matching_residents.index(resident_data) == 0 and room.can_have_monitor:
                    monitor = Monitor(
                        employee_id=f'EMP{i+1:03d}',
                        room_id=room.id,
                        **resident_data
                    )
                    db.session.add(monitor)
                    db.session.flush()
                    room.monitor_id = monitor.id
        
        db.session.commit()
        click.echo('测试数据初始化成功！')
        
    except Exception as e:
        db.session.rollback()
        click.echo(f'初始化测试数据失败: {str(e)}')

def init_app(app):
    """注册命令"""
    app.cli.add_command(init_test_data) 