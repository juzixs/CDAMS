from app import create_app
from app.models.user import Module
from app import db

def init_modules():
    # 检查是否已经有模块数据
    if Module.query.first() is not None:
        print("模块数据已存在，跳过初始化")
        return
    
    # 定义模块数据
    modules = [
        # 普通级别模块
        {
            'name': '工单系统',
            'code': 'ticket',
            'description': '处理用户提交的工单请求',
            'permission_level': 'normal'
        },
        
        # 授权级别模块
        {
            'name': '工作汇报',
            'code': 'report',
            'description': '生成和查看工作汇报',
            'permission_level': 'authorized'
        },
        {
            'name': '预算管理',
            'code': 'budget',
            'description': '管理部门预算',
            'permission_level': 'authorized'
        },
        {
            'name': '固定资产',
            'code': 'asset',
            'description': '管理公司固定资产',
            'permission_level': 'authorized'
        },
        {
            'name': '办公用品',
            'code': 'office_supply',
            'description': '管理办公用品',
            'permission_level': 'authorized'
        },
        {
            'name': '饮料管理',
            'code': 'beverage',
            'description': '管理公司饮料',
            'permission_level': 'authorized'
        },
        {
            'name': '车辆管理',
            'code': 'vehicle',
            'description': '管理公司车辆',
            'permission_level': 'authorized'
        },
        {
            'name': '宿舍管理',
            'code': 'dormitory',
            'description': '管理公司宿舍',
            'permission_level': 'authorized'
        },
        {
            'name': '食堂管理',
            'code': 'cafeteria',
            'description': '管理公司食堂',
            'permission_level': 'authorized'
        },
        
        # 管理员级别模块
        {
            'name': '用户管理',
            'code': 'user',
            'description': '管理系统用户',
            'permission_level': 'admin'
        },
        {
            'name': '系统设置',
            'code': 'settings',
            'description': '管理系统设置',
            'permission_level': 'admin'
        }
    ]
    
    # 添加模块数据
    for module_data in modules:
        module = Module(**module_data)
        db.session.add(module)
    
    # 提交到数据库
    db.session.commit()
    print(f"成功创建 {len(modules)} 个模块")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        init_modules() 