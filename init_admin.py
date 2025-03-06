from app import create_app, db
from app.models import User
from config import Config

def init_admin():
    """初始化管理员账号"""
    app = create_app()
    with app.app_context():
        # 检查是否已存在管理员账号
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print('管理员账号已存在')
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
        db.session.add(admin)
        db.session.commit()
        print('管理员账号创建成功')

if __name__ == '__main__':
    init_admin() 