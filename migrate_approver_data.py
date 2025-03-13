from app import create_app, db
from app.models import VehicleExit
from sqlalchemy import text, inspect

app = create_app()

def migrate_approver_data():
    with app.app_context():
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('vehicle_exit')]
        
        # 检查是否存在旧列
        if 'approver_name' in columns:
            print("找到 approver_name 列，开始迁移数据...")
            
            # 创建一个临时表来存储数据
            db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS vehicle_exit_temp AS
            SELECT id, approver_name
            FROM vehicle_exit
            WHERE approver_name IS NOT NULL
            """))
            
            # 检查是否有数据需要迁移
            result = db.session.execute(text("SELECT COUNT(*) FROM vehicle_exit_temp")).scalar()
            print(f"需要迁移的记录数: {result}")
            
            if result > 0:
                # 将数据从临时表更新到主表
                db.session.execute(text("""
                UPDATE vehicle_exit
                SET approver = (
                    SELECT approver_name 
                    FROM vehicle_exit_temp 
                    WHERE vehicle_exit_temp.id = vehicle_exit.id
                )
                WHERE EXISTS (
                    SELECT 1 
                    FROM vehicle_exit_temp 
                    WHERE vehicle_exit_temp.id = vehicle_exit.id
                )
                """))
                
                print("数据迁移完成")
            
            # 删除临时表
            db.session.execute(text("DROP TABLE IF EXISTS vehicle_exit_temp"))
            
            # 提交事务
            db.session.commit()
        else:
            print("approver_name 列不存在，无需迁移数据")
        
        print("迁移过程完成")

if __name__ == "__main__":
    migrate_approver_data() 