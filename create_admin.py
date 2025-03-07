from app import create_app, db
from app.models import User

def create_admin(username='admin', password='admin123'):
    app = create_app()
    with app.app_context():
        # 检查用户是否已存在
        user = User.query.filter_by(username=username).first()
        if user:
            print(f'用户 {username} 已存在')
            return
        
        # 创建管理员用户
        admin_user = User(
            username=username,
            is_admin=True,
            department='系统管理',
            position='管理员'
        )
        admin_user.set_password(password)
        
        try:
            db.session.add(admin_user)
            db.session.commit()
            print(f'管理员 {username} 创建成功')
            print(f'用户名: {username}')
            print(f'密码: {password}')
        except Exception as e:
            db.session.rollback()
            print(f'创建管理员失败: {str(e)}')

if __name__ == '__main__':
    create_admin() 