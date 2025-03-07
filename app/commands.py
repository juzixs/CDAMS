import click
from flask.cli import with_appcontext
from app import db
from app.models import User

@click.command('create-admin')
@with_appcontext
def create_admin_command():
    """创建管理员账号"""
    # 检查是否已存在管理员账号
    admin = User.query.filter_by(username='admin').first()
    if admin:
        click.echo('管理员账号已存在')
        return
    
    # 创建管理员账号
    admin = User()
    admin.username = 'admin'
    admin.email = 'admin@chidafeiji.com'
    admin.employee_id = '86120000'
    admin.name = '管理员'
    admin.department = '系统管理部'
    admin.phone = '13900000000'
    admin.is_admin = True
    admin.set_password('Narbnkh2')
    
    # 保存到数据库
    try:
        db.session.add(admin)
        db.session.commit()
        click.echo('管理员账号创建成功')
        click.echo('用户名: admin')
        click.echo('密码: Narbnkh2')
    except Exception as e:
        db.session.rollback()
        click.echo(f'创建管理员失败: {str(e)}')

def init_app(app):
    """注册命令到Flask应用"""
    app.cli.add_command(create_admin_command) 