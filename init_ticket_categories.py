from app import create_app, db
from app.ticket.models import TicketCategory

def init_ticket_categories():
    app = create_app()
    with app.app_context():
        # 检查是否已存在分类
        if TicketCategory.query.count() > 0:
            print('工单分类已存在，无需初始化')
            return
        
        # 创建初始分类
        categories = [
            {'name': '系统问题', 'description': '系统功能异常、错误或建议'},
            {'name': '账号问题', 'description': '账号登录、权限或信息修改相关问题'},
            {'name': '数据问题', 'description': '数据错误、丢失或导入导出相关问题'},
            {'name': '使用咨询', 'description': '系统使用方法咨询'},
            {'name': '功能建议', 'description': '系统功能改进或新功能建议'},
            {'name': '其他', 'description': '其他类型问题'}
        ]
        
        for category_data in categories:
            category = TicketCategory(**category_data)
            db.session.add(category)
        
        db.session.commit()
        print(f'成功创建 {len(categories)} 个工单分类')

if __name__ == '__main__':
    init_ticket_categories() 