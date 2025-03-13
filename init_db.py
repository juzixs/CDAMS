from app import create_app, db
from flask_migrate import Migrate, upgrade

def init_db():
    """初始化数据库"""
    app = create_app()
    migrate = Migrate(app, db)
    
    with app.app_context():
        # 创建migrations文件夹（如果不存在）
        try:
            upgrade()
            print('数据库迁移完成')
        except Exception as e:
            print('首次初始化，创建数据库表...')
            # 如果没有migrations，则直接创建表
            db.create_all()
            print('数据库初始化完成')

if __name__ == '__main__':
    init_db() 