from app import create_app, db
from app.models import VehicleExit, User

app = create_app()

def fix_approver_data():
    with app.app_context():
        print("开始迁移审批人数据...")
        
        # 获取所有车辆出门记录
        vehicle_exits = VehicleExit.query.all()
        count = 0
        
        for ve in vehicle_exits:
            if hasattr(ve, 'approver_user') and ve.approver_user is not None:
                # 将用户名复制到 approver_text 字段
                ve.approver_text = ve.approver_user.name
                count += 1
            elif ve.approved_by is not None:
                # 如果关系没有正确加载，直接查询用户
                user = User.query.get(ve.approved_by)
                if user:
                    ve.approver_text = user.name
                    count += 1
            
        # 提交所有更改
        db.session.commit()
        print(f"已更新 {count} 条记录的审批人信息")
        
        # 再次检查
        print("\n检查更新后的记录:")
        for ve in VehicleExit.query.limit(3).all():
            print(f"记录ID: {ve.id}, 车牌号: {ve.plate_number}, 审批人: {ve.approver_text}")

if __name__ == "__main__":
    fix_approver_data() 