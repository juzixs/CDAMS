from app import create_app
from app.models import Dormitory, Room

app = create_app()

with app.app_context():
    # 查询所有宿舍
    dormitories = Dormitory.query.all()
    print(f"总共有 {len(dormitories)} 个宿舍")
    
    for dorm in dormitories:
        print(f"ID: {dorm.id}, 名称: {dorm.name}, 地址: {dorm.address}, 类型: {dorm.type}")
        rooms = Room.query.filter_by(dormitory_id=dorm.id).all()
        print(f"  - 房间数量: {len(rooms)}") 