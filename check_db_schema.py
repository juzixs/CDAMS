from app import create_app, db
from sqlalchemy import inspect

app = create_app()

def check_db_schema():
    with app.app_context():
        inspector = inspect(db.engine)
        
        # 检查 vehicle_exit 表的列
        print("Vehicle Exit 表的列:")
        columns = inspector.get_columns('vehicle_exit')
        for column in columns:
            print(f"  - {column['name']} ({column['type']})")
        
        # 检查是否存在 approver_text 列
        column_names = [col['name'] for col in columns]
        if 'approver_text' in column_names:
            print("\napprover_text 列存在于数据库中")
        else:
            print("\n警告: approver_text 列不存在于数据库中!")
            if 'approver' in column_names:
                print("但找到了 approver 列，可能需要进行迁移")
        
        # 查看表中的几条记录
        print("\n查看 vehicle_exit 表中的记录:")
        from app.models import VehicleExit
        records = VehicleExit.query.limit(2).all()
        if records:
            for record in records:
                print(f"记录 ID: {record.id}")
                print(f"车牌号: {record.plate_number}")
                print(f"审批人属性: {getattr(record, 'approver_text', None)}")
                try:
                    # 尝试访问可能不存在的属性
                    print(f"旧审批人属性: {record.approver if hasattr(record, 'approver') else '不存在'}")
                except Exception as e:
                    print(f"访问旧属性时出错: {str(e)}")
                print("-"*40)
        else:
            print("表中没有记录")

if __name__ == "__main__":
    check_db_schema() 