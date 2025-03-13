import os
import sys
from datetime import datetime, timedelta, date
import json
import random

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import VehicleExit, User

app = create_app()

# 测试数据
departments = ['生产部', '研发部', '质量部', '采购部', '物流部', '行政部']
initiators = ['张三', '李四', '王五', '赵六', '钱七', '孙八']
companies = ['上海XX公司', '北京XX科技', '广州XX物流', '深圳XX电子', '杭州XX科技', '南京XX制造']
vehicle_types = ['truck', 'tractor', 'express', 'other']
vehicle_type_names = {'truck': '货车', 'tractor': '拖拉机', 'express': '快递', 'other': '其他'}
logistics_types = ['company', 'logistics', 'outsourcing', 'other']
logistics_type_names = {
    'company': '公司自有车辆', 
    'logistics': '物流公司车辆', 
    'outsourcing': '外协车辆', 
    'other': '其他车辆'
}
logistics_companies = ['顺丰物流', '京东物流', '德邦物流', '圆通速递', '申通快递', '韵达快递']
item_categories = ['product', 'outsourcing', 'material', 'other']
item_category_names = {
    'product': '产成品交付', 
    'outsourcing': '外协', 
    'material': '园区物料周转', 
    'other': '其他'
}
drivers = [
    {'name': '刘一', 'phone': '13800138001', 'id': '110101199001011234'},
    {'name': '陈二', 'phone': '13800138002', 'id': '110101199001021234'},
    {'name': '张三', 'phone': '13800138003', 'id': '110101199001031234'},
    {'name': '李四', 'phone': '13800138004', 'id': '110101199001041234'},
    {'name': '王五', 'phone': '13800138005', 'id': '110101199001051234'},
    {'name': '赵六', 'phone': '13800138006', 'id': '110101199001061234'},
]
plate_numbers = ['京A12345', '京B12345', '京C12345', '京D12345', '京E12345', '京F12345']
reviewers = ['审核员A', '审核员B', '审核员C']
issuers = ['发放员A', '发放员B', '发放员C']
approvers = ['审批员A', '审批员B', '审批员C']
guards = ['门卫A', '门卫B', '门卫C']

def generate_random_date(start_date, end_date):
    """生成两个日期之间的随机日期"""
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    random_date = start_date + timedelta(days=random_number_of_days)
    return random_date

def create_test_data():
    """创建测试数据"""
    with app.app_context():
        # 清空现有数据
        VehicleExit.query.delete()
        db.session.commit()
        
        # 获取一个用户作为创建者
        user = User.query.first()
        if not user:
            print("没有找到用户，请先创建用户")
            return
        
        # 创建外协出门记录
        print("创建外协出门记录...")
        for i in range(10):
            exit_date = generate_random_date(datetime.now() - timedelta(days=30), datetime.now())
            confirmed_date = exit_date + timedelta(hours=random.randint(1, 5))
            
            driver = random.choice(drivers)
            
            record = VehicleExit(
                exit_type='outsourcing',
                department=random.choice(departments),
                initiator=random.choice(initiators),
                certificate_number=f'WX{datetime.now().strftime("%Y%m%d")}{i+1:02d}',
                plate_number=random.choice(plate_numbers),
                driver_name=driver['name'],
                id_number=driver['id'],
                phone=driver['phone'],
                vehicle_type=random.choice(vehicle_types),
                logistics_type=random.choice(logistics_types),
                logistics_company=random.choice(logistics_companies),
                logistics_number=f'LG{random.randint(10000, 99999)}',
                company=random.choice(companies),
                item_category='outsourcing',
                destination=f'目的地{i+1}',
                items=f'外协物品{i+1}',
                purpose=f'外协加工{i+1}',
                exit_time=exit_date,
                expected_return_time=exit_date + timedelta(days=random.randint(1, 7)),
                confirmed_exit_time=confirmed_date,
                reviewer=random.choice(reviewers),
                issuer=random.choice(issuers),
                approver_text=random.choice(approvers),
                guard=random.choice(guards),
                remarks=f'外协出门记录{i+1}',
                created_by=user.id,
                status='completed',
                created_at=datetime.now() - timedelta(days=30-i),
                updated_at=datetime.now() - timedelta(days=30-i)
            )
            db.session.add(record)
        
        # 创建产成品出门记录
        print("创建产成品出门记录...")
        for i in range(10):
            exit_date = generate_random_date(datetime.now() - timedelta(days=30), datetime.now())
            confirmed_date = exit_date + timedelta(hours=random.randint(1, 5))
            
            driver = random.choice(drivers)
            
            # 产成品记录的物流方式不包括"外协车辆"
            product_logistics_types = ['company', 'logistics', 'other']
            
            record = VehicleExit(
                exit_type='product',
                department=random.choice(departments),
                initiator=random.choice(initiators),
                certificate_number=f'CP{datetime.now().strftime("%Y%m%d")}{i+1:02d}',
                plate_number=random.choice(plate_numbers),
                driver_name=driver['name'],
                id_number=driver['id'],
                phone=driver['phone'],
                vehicle_type=random.choice(vehicle_types),
                logistics_type=random.choice(product_logistics_types),
                logistics_company=random.choice(logistics_companies),
                logistics_number=f'LG{random.randint(10000, 99999)}',
                company=random.choice(companies),
                item_category='product',
                destination=f'目的地{i+1}',
                items=f'产成品{i+1}',
                purpose=f'产成品交付{i+1}',
                exit_time=exit_date,
                expected_return_time=exit_date + timedelta(days=random.randint(1, 7)),
                confirmed_exit_time=confirmed_date,
                reviewer=random.choice(reviewers),
                issuer=random.choice(issuers),
                approver_text=random.choice(approvers),
                guard=random.choice(guards),
                remarks=f'产成品出门记录{i+1}',
                created_by=user.id,
                status='completed',
                created_at=datetime.now() - timedelta(days=30-i),
                updated_at=datetime.now() - timedelta(days=30-i)
            )
            db.session.add(record)
        
        db.session.commit()
        print("测试数据创建完成！")

if __name__ == '__main__':
    create_test_data() 