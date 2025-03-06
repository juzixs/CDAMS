import pandas as pd
from datetime import datetime
from app import db
from app.models import Vehicle

def export_vehicles_to_excel(vehicles, filepath):
    """导出车辆信息到Excel文件"""
    data = []
    for vehicle in vehicles:
        data.append({
            '车牌号': vehicle.plate_number,
            '车辆类型': vehicle.vehicle_type,
            '车主姓名': vehicle.owner_name,
            '所属部门': vehicle.department,
            '备注': vehicle.remarks,
            '状态': vehicle.status,
            '创建时间': vehicle.created_at.strftime('%Y-%m-%d %H:%M:%S') if vehicle.created_at else '',
            '发放时间': vehicle.issued_at.strftime('%Y-%m-%d %H:%M:%S') if vehicle.issued_at else ''
        })
    
    df = pd.DataFrame(data)
    df.to_excel(filepath, index=False)

def create_import_template(filepath):
    """创建导入模板"""
    df = pd.DataFrame(columns=['车牌号', '车辆类型', '车主姓名', '所属部门', '备注'])
    df.loc[0] = ['浙A12345', '燃油', '张三', '技术部', '示例数据，导入时请删除此行']
    df.to_excel(filepath, index=False)

def import_vehicles_from_excel(file, user_id):
    """从Excel文件导入车辆信息"""
    df = pd.read_excel(file)
    success_count = 0
    error_messages = []
    
    for index, row in df.iterrows():
        try:
            # 检查必填字段
            if pd.isna(row['车牌号']):
                error_messages.append(f'第{index+2}行：车牌号不能为空')
                continue
            
            # 检查车牌号是否已存在
            if Vehicle.query.filter_by(plate_number=row['车牌号']).first():
                error_messages.append(f'第{index+2}行：车牌号 {row["车牌号"]} 已存在')
                continue
            
            # 创建新车辆记录
            vehicle = Vehicle(
                plate_number=row['车牌号'],
                vehicle_type=row['车辆类型'] if not pd.isna(row['车辆类型']) else '燃油',
                owner_name=row['车主姓名'] if not pd.isna(row['车主姓名']) else None,
                department=row['所属部门'] if not pd.isna(row['所属部门']) else None,
                remarks=row['备注'] if not pd.isna(row['备注']) else None,
                user_id=user_id
            )
            db.session.add(vehicle)
            success_count += 1
            
        except Exception as e:
            error_messages.append(f'第{index+2}行：导入失败 - {str(e)}')
    
    if success_count > 0:
        db.session.commit()
    
    return success_count, error_messages 