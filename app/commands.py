import click
from flask.cli import with_appcontext
from datetime import datetime
from app.extensions import db
from app.models import User, Vehicle, PDFSettings

@click.command('init-db')
@with_appcontext
def init_db():
    """初始化数据库（删除所有表并重新创建）"""
    click.echo('正在初始化数据库...')
    db.drop_all()
    db.create_all()
    click.echo('数据库初始化完成！')

@click.command('create-admin')
@with_appcontext
def create_admin():
    """创建默认管理员账号"""
    # 检查是否已存在管理员账号
    admin = User.query.filter_by(is_admin=True).first()
    if admin:
        click.echo('管理员账号已存在')
        return
    
    # 创建新的管理员账号
    admin = User(
        username='admin',
        email='admin@example.com',
        employee_id='admin001',
        name='系统管理员',
        department='信息技术部',
        phone='13800000000',
        is_admin=True
    )
    admin.set_password('admin123')
    
    db.session.add(admin)
    db.session.commit()
    
    click.echo('默认管理员账号已创建：')
    click.echo('用户名：admin')
    click.echo('密码：admin123')
    click.echo('邮箱：admin@example.com')
    click.echo('工号：admin001')
    click.echo('姓名：系统管理员')
    click.echo('部门：信息技术部')
    click.echo('电话：13800000000')

@click.command('create-test-data')
@with_appcontext
def create_test_data():
    """创建测试数据"""
    # 检查是否已存在管理员账号
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        click.echo('请先创建管理员账号')
        return

    # 生成时间戳，确保用户名和邮箱唯一
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    # 创建测试用户
    test_users = [
        {
            'username': 'test_user1_' + timestamp,
            'email': 'test1_' + timestamp + '@example.com',
            'employee_id': 'emp001_' + timestamp,
            'name': '张三',
            'department': '技术部',
            'phone': '13811111111',
            'is_admin': False
        },
        {
            'username': 'test_user2_' + timestamp,
            'email': 'test2_' + timestamp + '@example.com',
            'employee_id': 'emp002_' + timestamp,
            'name': '李四',
            'department': '行政部',
            'phone': '13822222222',
            'is_admin': False
        },
        {
            'username': 'test_user3_' + timestamp,
            'email': 'test3_' + timestamp + '@example.com',
            'employee_id': 'emp003_' + timestamp,
            'name': '王五',
            'department': '财务部',
            'phone': '13833333333',
            'is_admin': False
        }
    ]
    
    created_users = []
    for user_data in test_users:
        user = User(**user_data)
        user.set_password('test123')
        db.session.add(user)
        created_users.append(user)
    
    db.session.commit()

    # 创建测试车辆数据
    test_vehicles = [
        {
            'plate_number': '浙A12345',
            'vehicle_type': '燃油',
            'owner_name': '张三',
            'department': '技术部',
            'remarks': '测试数据1',
            'status': 'approved',
            'user_id': created_users[0].id
        },
        {
            'plate_number': '浙A67890',
            'vehicle_type': '新能源',
            'owner_name': '李四',
            'department': '行政部',
            'remarks': '测试数据2',
            'status': 'pending',
            'user_id': created_users[1].id
        },
        {
            'plate_number': '浙B12345',
            'vehicle_type': '燃油',
            'owner_name': '王五',
            'department': '财务部',
            'remarks': '测试数据3',
            'status': 'approved',
            'issued_at': datetime.utcnow(),
            'user_id': created_users[2].id
        }
    ]

    for vehicle_data in test_vehicles:
        vehicle = Vehicle(**vehicle_data)
        db.session.add(vehicle)

    # 创建PDF设置测试数据
    # 暂时注释掉，等待检查PDFSettings模型
    # pdf_settings = PDFSettings(
    #     module='license_plate',
    #     background_image='/static/img/license_bg.jpg',
    #     font_family='SimSun',
    #     font_size=14,
    #     font_bold=True,
    #     text_x=100,
    #     text_y=150,
    #     text_color='#000000'
    # )
    # db.session.add(pdf_settings)

    db.session.commit()
    
    click.echo('测试数据已创建：')
    click.echo('测试用户：')
    for i, user in enumerate(created_users):
        click.echo(f'用户 {i+1}:')
        click.echo(f'  用户名：{user.username}')
        click.echo(f'  密码：test123')
        click.echo(f'  邮箱：{user.email}')
        click.echo(f'  工号：{user.employee_id}')
        click.echo(f'  姓名：{user.name}')
        click.echo(f'  部门：{user.department}')
        click.echo(f'  电话：{user.phone}')
    
    click.echo('\n已创建3条测试车辆数据')
    # click.echo('已创建PDF设置测试数据') 