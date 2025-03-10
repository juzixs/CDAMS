import os
import sys
from datetime import datetime, timedelta, date
import json
import random

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models.work_report import WeeklyReport
from app.models.user import User

app = create_app()

# 测试数据
responsible_persons = [
    "张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十"
]

work_contents = [
    "完成系统需求分析", "编写技术方案文档", "开发用户管理模块", "实现权限控制功能", 
    "开发工单系统", "优化数据库查询性能", "修复已知bug", "进行系统测试",
    "部署系统到测试环境", "编写用户使用手册", "进行用户培训", "收集用户反馈",
    "进行代码审查", "优化前端界面", "实现数据导出功能", "开发报表统计功能"
]

targets = [
    "完成需求文档并获得审批", "形成完整的技术方案", "实现用户的增删改查功能", "基于RBAC模型实现权限控制",
    "实现工单的创建、分配、处理流程", "查询响应时间提升50%", "解决所有已知的高优先级bug", "覆盖90%以上的功能点",
    "系统在测试环境正常运行", "形成完整的用户手册", "80%以上的用户掌握系统使用", "收集并整理用户反馈",
    "发现并修复潜在问题", "提升用户体验", "支持Excel和PDF格式导出", "实现多维度的数据统计"
]

completion_statuses = ["已完成", "未完成", "进行中", "暂停", "终止", "/"]

checks = [
    "已按计划完成", "进度落后，需要加快", "质量符合要求", "存在一些问题需要解决",
    "已完成但需要优化", "未达到预期效果", "按时完成并超出预期", "需要进一步测试",
    "已通过验收", "需要进行修改", "等待其他模块配合", "需要更多资源支持"
]

measures = [
    "继续按计划推进", "调整计划进度", "增加人力资源", "寻求技术支持",
    "进行技术攻关", "优化实现方案", "加强团队协作", "进行风险评估",
    "制定应急预案", "加强质量控制", "进行技术培训", "优化工作流程"
]

consensus_items = [
    "加强团队协作，提高工作效率",
    "优化工作流程，减少不必要的环节",
    "加强技术培训，提升团队技术水平",
    "重视代码质量，减少技术债务",
    "加强需求分析，减少后期变更",
    "注重用户体验，提高产品质量",
    "建立有效的沟通机制，及时解决问题",
    "加强风险管理，提前识别和应对风险",
    "建立健全的测试机制，保证产品质量",
    "重视文档管理，提高知识沉淀和传承"
]

def generate_work_item(person_index, is_admin=False):
    """生成一个工作项"""
    person = responsible_persons[person_index % len(responsible_persons)]
    if is_admin:
        person = "张三"  # 假设张三是行政部人员
        
    today = date.today()
    timeline = today + timedelta(days=random.randint(-30, 30))
    expected_date = timeline + timedelta(days=random.randint(1, 30))
    
    return {
        "person": person,
        "content": random.choice(work_contents),
        "target": random.choice(targets),
        "timeline": timeline.isoformat(),
        "completed": random.choice(completion_statuses),
        "check": random.choice(checks),
        "measures": random.choice(measures),
        "expected_date": expected_date.isoformat()
    }

def create_weekly_report(week_number, start_date, end_date, user_id):
    """创建一个周报"""
    # 生成1-5个重点工作
    key_works = [generate_work_item(i, i % 3 == 0) for i in range(random.randint(1, 5))]
    
    # 生成0-3个临时工作
    temp_works = [generate_work_item(i, i % 4 == 0) for i in range(random.randint(0, 3))]
    
    # 生成0-2个协调工作
    coordinations = [generate_work_item(i, i % 2 == 0) for i in range(random.randint(0, 2))]
    
    # 随机选择1-3个共识项
    selected_consensus = random.sample(consensus_items, random.randint(1, 3))
    consensus = "\n\n".join(selected_consensus)
    
    # 创建周报
    meeting_time = datetime.combine(end_date, datetime.min.time()) - timedelta(days=1)
    
    report = WeeklyReport(
        week_number=week_number,
        start_date=start_date,
        end_date=end_date,
        meeting_time=meeting_time,
        meeting_place="会议室" + str(random.randint(1, 5)),
        host=random.choice(responsible_persons),
        participants=", ".join(random.sample(responsible_persons, random.randint(3, 6))),
        consensus=consensus,
        _key_works=json.dumps(key_works),
        _temp_works=json.dumps(temp_works),
        _coordinations=json.dumps(coordinations),
        user_id=user_id,
        status=random.choice(["draft", "submitted", "archived"]),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    return report

def add_test_data():
    """添加测试数据"""
    with app.app_context():
        # 检查是否有用户
        user = User.query.first()
        if not user:
            print("没有找到用户，请先创建用户")
            return
        
        # 设置时间范围：2024年1月1日至2024年12月31日
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        # 计算周数
        current_date = start_date
        week_number = 1
        
        while current_date <= end_date:
            # 计算本周的开始和结束日期
            week_start = current_date
            week_end = week_start + timedelta(days=6)
            
            # 创建周报
            report = create_weekly_report(week_number, week_start, week_end, user.id)
            db.session.add(report)
            
            # 移动到下一周
            current_date = week_end + timedelta(days=1)
            week_number += 1
        
        # 提交到数据库
        db.session.commit()
        print(f"成功添加了 {week_number - 1} 个周报测试数据")

if __name__ == "__main__":
    add_test_data() 