from app import create_app, db
from app.models.official_car import OfficialCar

app = create_app()

with app.app_context():
    # 查找资产编号为CD-LX-018的车辆
    car = OfficialCar.query.filter_by(asset_number='CD-LX-018').first()
    
    if car:
        # 如果找到了车辆，则删除它
        print(f"找到车辆: ID={car.id}, 资产编号={car.asset_number}, 车牌号={car.plate_number}")
        
        # 删除车辆记录
        db.session.delete(car)
        db.session.commit()
        
        print("车辆数据已成功删除")
    else:
        print("未找到资产编号为CD-LX-018的车辆") 