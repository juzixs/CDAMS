import pandas as pd
from datetime import datetime
from app import db
from app.models import Vehicle

def export_vehicles_to_excel(vehicles, filename):
    """导出车辆数据到Excel文件"""
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
    df.to_excel(filename, index=False, engine='openpyxl')
    return filename

def import_vehicles_from_excel(file, user_id):
    """从Excel文件导入车辆数据"""
    df = pd.read_excel(file, engine='openpyxl')
    
    # 验证必填字段
    required_fields = ['车牌号', '车辆类型', '车主姓名', '所属部门']
    for field in required_fields:
        if field not in df.columns:
            raise ValueError(f'Excel文件缺少必填字段：{field}')
    
    success_count = 0
    error_messages = []
    
    for index, row in df.iterrows():
        try:
            # 检查车牌号是否为空
            if pd.isna(row['车牌号']) or str(row['车牌号']).strip() == '':
                error_messages.append(f'第{index+2}行：车牌号不能为空')
                continue
                
            # 检查车牌号是否已存在
            if Vehicle.query.filter_by(plate_number=row['车牌号']).first():
                error_messages.append(f'第{index+2}行：车牌号 {row["车牌号"]} 已存在')
                continue
            
            # 创建新车辆记录
            vehicle = Vehicle(
                plate_number=str(row['车牌号']).strip(),  # 确保去除前后空格
                vehicle_type=row['车辆类型'],
                owner_name=row['车主姓名'],
                department=row['所属部门'],
                remarks=row.get('备注', ''),
                status='pending',
                user_id=user_id
            )
            
            db.session.add(vehicle)
            success_count += 1
            
        except Exception as e:
            error_messages.append(f'第{index+2}行：导入失败 - {str(e)}')
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        error_messages.append(f'保存数据时发生错误：{str(e)}')
        return 0, error_messages
    
    return success_count, error_messages 