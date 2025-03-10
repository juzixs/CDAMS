from datetime import datetime, timedelta, date
import json
import io
import xlsxwriter
from flask import render_template, flash, redirect, url_for, request, current_app, jsonify, send_file
from flask_login import login_required, current_user
from app.work_report import bp
from app import db
from app.models.work_report import WeeklyReport, MonthlyReport
from app.decorators import module_permission_required

@bp.route('/')
@login_required
@module_permission_required('report')
def index():
    """工作汇报首页"""
    return render_template('work_report/index.html', title='工作汇报')

@bp.route('/weekly')
@login_required
@module_permission_required('report')
def weekly():
    """周报管理"""
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 15  # 每页显示15行
    
    # 获取当前用户部门的所有周报，并进行分页
    pagination = WeeklyReport.query.order_by(WeeklyReport.week_number.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    reports = pagination.items
    
    return render_template('work_report/weekly.html', title='周报管理', reports=reports, pagination=pagination)

@bp.route('/weekly/create', methods=['GET', 'POST'])
@login_required
@module_permission_required('report')
def weekly_create():
    """创建周报"""
    if request.method == 'POST':
        week_number = request.form.get('week_number', type=int)
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        
        # 检查是否已存在该周的周报
        existing_report = WeeklyReport.query.filter_by(week_number=week_number).first()
        if existing_report:
            flash('该周的周报已存在，请选择其他周次')
            return redirect(url_for('work_report.weekly_create'))
        
        # 创建新周报
        report = WeeklyReport(
            week_number=week_number,
            start_date=start_date,
            end_date=end_date,
            user_id=current_user.id,
            status='draft',
            # 初始化空的工作项列表
            _key_works='[]',
            _temp_works='[]',
            _coordinations='[]'
        )
        
        db.session.add(report)
        db.session.commit()
        
        flash('周报创建成功，请继续编辑内容')
        return redirect(url_for('work_report.weekly_edit', report_id=report.id))
    
    # 生成可选的周次列表（当前周的前3周和后5周）
    today = date.today()
    # 找到本周的周一
    monday = today - timedelta(days=today.weekday())
    weeks = []
    
    for i in range(-3, 6):  # 前3周到后5周
        week_monday = monday + timedelta(weeks=i)
        week_sunday = week_monday + timedelta(days=6)
        week_number = int(week_monday.strftime('%W')) + 1  # 周数从1开始
        
        weeks.append({
            'number': week_number,
            'start_date': week_monday.strftime('%Y-%m-%d'),
            'end_date': week_sunday.strftime('%Y-%m-%d'),
            'is_next_week': (i == 1)  # 标记是否是下一周
        })
    
    return render_template('work_report/weekly_create.html', title='新建周报', weeks=weeks)

@bp.route('/weekly/edit/<int:report_id>', methods=['GET', 'POST'])
@login_required
@module_permission_required('report')
def weekly_edit(report_id):
    """编辑周报"""
    # 获取周报
    report = WeeklyReport.query.get_or_404(report_id)
    
    # 检查权限
    if report.user_id != current_user.id and not current_user.is_admin:
        flash('您没有权限编辑此周报')
        return redirect(url_for('work_report.weekly'))
    
    # 如果周报已提交，不允许编辑
    if report.status == 'approved' and not current_user.is_admin:
        flash('已审批的周报不能编辑')
        return redirect(url_for('work_report.weekly'))
    
    if request.method == 'POST':
        # 处理表单提交
        # 这里应该有处理POST请求的代码
        # 由于目前没有具体实现，我们保留pass但确保缩进正确
        pass
    
    # 准备数据
    # ...
    
    return render_template('work_report/weekly_edit.html', title='编辑周报', report=report)

@bp.route('/weekly/<int:report_id>/update', methods=['POST'])
@login_required
@module_permission_required('report')
def weekly_update(report_id):
    """更新周报内容"""
    report = WeeklyReport.query.get_or_404(report_id)
    
    # 不再检查创建者，因为module_permission_required装饰器已经确保了只有有权限的用户才能访问
    # 所有拥有report模块权限的用户都可以编辑任何周报
    
    # 更新基本信息
    if request.form.get('meeting_time'):
        report.meeting_time = datetime.strptime(request.form.get('meeting_time'), '%Y-%m-%d')
    report.meeting_place = request.form.get('meeting_place', '')
    report.host = request.form.get('host', '')
    report.participants = request.form.get('participants', '')
    report.consensus = request.form.get('consensus', '')
    
    # 更新工作项
    # 1. 重点工作
    key_works = []
    key_work_contents = request.form.getlist('key_work_content[]')
    key_work_persons = request.form.getlist('key_work_person[]')
    key_work_targets = request.form.getlist('key_work_target[]')
    key_work_timelines = request.form.getlist('key_work_timeline[]')
    key_work_completeds = request.form.getlist('key_work_completed[]')
    key_work_checks = request.form.getlist('key_work_check[]')
    key_work_measures = request.form.getlist('key_work_measures[]')
    key_work_expected_dates = request.form.getlist('key_work_expected_date[]')
    
    for i in range(len(key_work_contents)):
        if key_work_contents[i].strip():  # 只添加非空内容
            key_works.append({
                'content': key_work_contents[i],
                'person': key_work_persons[i] if i < len(key_work_persons) else current_user.name,
                'target': key_work_targets[i] if i < len(key_work_targets) else "",
                'timeline': key_work_timelines[i] if i < len(key_work_timelines) else "",
                'completed': key_work_completeds[i] if i < len(key_work_completeds) else "否",
                'check': key_work_checks[i] if i < len(key_work_checks) else "",
                'measures': key_work_measures[i] if i < len(key_work_measures) else "",
                'expected_date': key_work_expected_dates[i] if i < len(key_work_expected_dates) else ""
            })
    
    # 2. 临时工作
    temp_works = []
    temp_work_contents = request.form.getlist('temp_work_content[]')
    temp_work_persons = request.form.getlist('temp_work_person[]')
    temp_work_targets = request.form.getlist('temp_work_target[]')
    temp_work_timelines = request.form.getlist('temp_work_timeline[]')
    temp_work_completeds = request.form.getlist('temp_work_completed[]')
    temp_work_checks = request.form.getlist('temp_work_check[]')
    temp_work_measures = request.form.getlist('temp_work_measures[]')
    temp_work_expected_dates = request.form.getlist('temp_work_expected_date[]')
    
    for i in range(len(temp_work_contents)):
        if temp_work_contents[i].strip():  # 只添加非空内容
            temp_works.append({
                'content': temp_work_contents[i],
                'person': temp_work_persons[i] if i < len(temp_work_persons) else current_user.name,
                'target': temp_work_targets[i] if i < len(temp_work_targets) else "",
                'timeline': temp_work_timelines[i] if i < len(temp_work_timelines) else "",
                'completed': temp_work_completeds[i] if i < len(temp_work_completeds) else "否",
                'check': temp_work_checks[i] if i < len(temp_work_checks) else "",
                'measures': temp_work_measures[i] if i < len(temp_work_measures) else "",
                'expected_date': temp_work_expected_dates[i] if i < len(temp_work_expected_dates) else ""
            })
    
    # 3. 协同事项
    coordinations = []
    coordination_contents = request.form.getlist('coordination_content[]')
    coordination_persons = request.form.getlist('coordination_person[]')
    coordination_targets = request.form.getlist('coordination_target[]')
    coordination_timelines = request.form.getlist('coordination_timeline[]')
    coordination_completeds = request.form.getlist('coordination_completed[]')
    coordination_checks = request.form.getlist('coordination_check[]')
    coordination_measures = request.form.getlist('coordination_measures[]')
    coordination_expected_dates = request.form.getlist('coordination_expected_date[]')
    
    for i in range(len(coordination_contents)):
        if coordination_contents[i].strip():  # 只添加非空内容
            coordinations.append({
                'content': coordination_contents[i],
                'person': coordination_persons[i] if i < len(coordination_persons) else current_user.name,
                'target': coordination_targets[i] if i < len(coordination_targets) else "",
                'timeline': coordination_timelines[i] if i < len(coordination_timelines) else "",
                'completed': coordination_completeds[i] if i < len(coordination_completeds) else "否",
                'check': coordination_checks[i] if i < len(coordination_checks) else "",
                'measures': coordination_measures[i] if i < len(coordination_measures) else "",
                'expected_date': coordination_expected_dates[i] if i < len(coordination_expected_dates) else ""
            })
    
    # 打印排序前的工作项责任人顺序
    print("排序前 - 重点工作责任人顺序:", [item['person'] for item in key_works])
    
    # 获取责任人排序设置
    from app.models import Setting
    person_order = []
    person_order_setting = Setting.query.filter_by(key='work_report_person_order').first()
    if person_order_setting:
        try:
            person_order = json.loads(person_order_setting.value)
            print("责任人排序设置:", person_order)
            
            if person_order:
                # 构建排序字典
                person_order_dict = {name: idx for idx, name in enumerate(person_order)}
                max_order = len(person_order)
                
                # 按责任人排序工作项
                key_works.sort(key=lambda x: person_order_dict.get(x.get('person', ''), max_order))
                temp_works.sort(key=lambda x: person_order_dict.get(x.get('person', ''), max_order))
                coordinations.sort(key=lambda x: person_order_dict.get(x.get('person', ''), max_order))
                
                # 打印排序后的工作项责任人顺序
                print("排序后 - 重点工作责任人顺序:", [item['person'] for item in key_works])
            else:
                print("责任人排序设置为空列表，不进行排序")
        except Exception as e:
            print(f"排序工作项时出错: {e}")
    else:
        print("未找到责任人排序设置")
    
    # 更新报告
    report.key_works = key_works
    report.temp_works = temp_works
    report.coordinations = coordinations
    
    db.session.commit()
    
    # 检查保存后的数据
    saved_report = WeeklyReport.query.get(report_id)
    print("保存后 - 重点工作责任人顺序:", [item['person'] for item in saved_report.key_works])
    
    flash('周报已保存')
    
    return redirect(url_for('work_report.weekly_edit', report_id=report.id))

@bp.route('/weekly/view/<int:report_id>')
@login_required
@module_permission_required('report')
def weekly_view(report_id):
    """查看周报"""
    # 获取周报
    report = WeeklyReport.query.get_or_404(report_id)
    
    # 准备数据
    try:
        key_works = json.loads(report._key_works)
    except:
        key_works = []
    
    try:
        temp_works = json.loads(report._temp_works)
    except:
        temp_works = []
    
    try:
        coordinations = json.loads(report._coordinations)
    except:
        coordinations = []
    
    try:
        next_week_plan = json.loads(report._next_week_plan)
    except:
        next_week_plan = []
    
    # 获取责任人排序
    from app.models import Setting
    person_order = []
    person_order_setting = Setting.query.filter_by(key='work_report_person_order').first()
    if person_order_setting:
        try:
            person_order = json.loads(person_order_setting.value)
        except:
            person_order = []
    
    # 按责任人排序工作项
    sorted_key_works = []
    sorted_temp_works = []
    sorted_coordinations = []
    sorted_next_week_plan = []
    
    if person_order:
        # 对各类工作项按责任人排序
        for person in person_order:
            # 重点工作
            for work in key_works:
                if work.get('person') == person:
                    sorted_key_works.append(work)
            
            # 临时工作
            for work in temp_works:
                if work.get('person') == person:
                    sorted_temp_works.append(work)
            
            # 协调工作
            for work in coordinations:
                if work.get('person') == person:
                    sorted_coordinations.append(work)
            
            # 下周计划
            for plan in next_week_plan:
                if plan.get('person') == person:
                    sorted_next_week_plan.append(plan)
        
        # 添加未在排序列表中的责任人的工作项
        for work in key_works:
            if work.get('person') not in person_order:
                sorted_key_works.append(work)
        
        for work in temp_works:
            if work.get('person') not in person_order:
                sorted_temp_works.append(work)
        
        for work in coordinations:
            if work.get('person') not in person_order:
                sorted_coordinations.append(work)
        
        for plan in next_week_plan:
            if plan.get('person') not in person_order:
                sorted_next_week_plan.append(plan)
    else:
        sorted_key_works = key_works
        sorted_temp_works = temp_works
        sorted_coordinations = coordinations
        sorted_next_week_plan = next_week_plan
    
    # 创建一个带有排序后工作项的报告对象
    report_with_sorted_items = report
    report_with_sorted_items.temp_works = sorted_temp_works
    report_with_sorted_items.coordinations = sorted_coordinations
    report_with_sorted_items.next_week_plan = sorted_next_week_plan
    
    # 确保consensus数据可用
    if not hasattr(report_with_sorted_items, 'consensus') or report_with_sorted_items.consensus is None:
        report_with_sorted_items.consensus = ""
    
    return render_template('work_report/weekly_view.html', 
                          title='查看周报', 
                          report=report_with_sorted_items, 
                          key_works=sorted_key_works)

@bp.route('/weekly/delete/<int:report_id>', methods=['POST'])
@login_required
@module_permission_required('report')
def weekly_delete(report_id):
    """删除周报"""
    # 获取周报
    report = WeeklyReport.query.get_or_404(report_id)
    
    # 检查权限
    if report.user_id != current_user.id and not current_user.is_admin:
        flash('您没有权限删除此周报', 'danger')
        return redirect(url_for('work_report.weekly'))
    
    # 如果周报已审批，普通用户不允许删除
    if report.status == 'approved' and not current_user.is_admin:
        flash('已审批的周报不能删除', 'danger')
        return redirect(url_for('work_report.weekly'))
    
    # 删除周报
    db.session.delete(report)
    db.session.commit()
    
    flash('周报已成功删除', 'success')
    return redirect(url_for('work_report.weekly'))

@bp.route('/monthly')
@login_required
@module_permission_required('report')
def monthly():
    """月报管理"""
    return render_template('work_report/monthly.html', title='月报管理') 

@bp.route('/settings', methods=['GET'])
@login_required
@module_permission_required('report')
def settings():
    """工作汇报设置页面"""
    # 读取当前设置
    from app.models import User, Setting
    
    # 获取工作汇报相关设置
    settings = {}
    db_settings = Setting.query.filter(Setting.key.like('work_report_%')).all()
    for setting in db_settings:
        settings[setting.key.replace('work_report_', '')] = setting.value
    
    # 获取责任人排序列表
    person_order = []
    person_order_setting = Setting.query.filter_by(key='work_report_person_order').first()
    if person_order_setting:
        try:
            person_order = json.loads(person_order_setting.value)
        except:
            person_order = []
    
    # 如果没有责任人排序设置，自动创建一个默认的排序列表
    if not person_order:
        # 获取所有用户
        all_users = User.query.all()
        
        # 区分行政部和非行政部用户
        admin_users = []
        other_users = []
        for user in all_users:
            if user.name:  # 只考虑有名字的用户
                if user.department == '行政部':
                    admin_users.append(user)
                else:
                    other_users.append(user)
        
        # 行政部用户按名字排序
        admin_users.sort(key=lambda x: x.name)
        
        # 非行政部用户按名字排序
        other_users.sort(key=lambda x: x.name)
        
        # 行政部用户排在前面，其他用户排在后面
        person_order = [user.name for user in admin_users] + [user.name for user in other_users]
        
        # 保存默认设置
        if person_order:
            if not person_order_setting:
                person_order_setting = Setting(
                    key='work_report_person_order',
                    value=json.dumps(person_order),
                    description='周报责任人排序设置'
                )
                db.session.add(person_order_setting)
            else:
                person_order_setting.value = json.dumps(person_order)
            
            db.session.commit()
            flash('已创建默认责任人排序设置')
    
    # 为界面准备数据
    # 获取所有用户列表，用于添加责任人
    all_users = User.query.all()
    
    # 分类用户
    admin_users = []
    other_users = []
    for user in all_users:
        if user.name:  # 只考虑有名字的用户
            if user.department == '行政部':
                admin_users.append(user.name)
            else:
                other_users.append(user.name)
                
    # 获取已不存在的用户（可能在列表中但已从系统中删除）
    existing_users = set([u.name for u in all_users if u.name])
    nonexistent_users = [name for name in person_order if name not in existing_users]
    
    return render_template('work_report/settings.html', 
                          title='工作汇报设置',
                          settings=settings,
                          person_order=person_order,
                          admin_users=admin_users,
                          other_users=other_users,
                          nonexistent_users=nonexistent_users)

@bp.route('/settings/template', methods=['POST'])
@login_required
@module_permission_required('report')
def update_template_settings():
    """更新工作汇报模板设置"""
    if request.method == 'POST':
        from app.models import Setting
        
        # 周报模板
        weekly_template = request.form.get('weekly_template', '')
        weekly_setting = Setting.query.filter_by(key='work_report_weekly_template').first()
        if not weekly_setting:
            weekly_setting = Setting(key='work_report_weekly_template', value=weekly_template)
            db.session.add(weekly_setting)
        else:
            weekly_setting.value = weekly_template
        
        # 月报模板
        monthly_template = request.form.get('monthly_template', '')
        monthly_setting = Setting.query.filter_by(key='work_report_monthly_template').first()
        if not monthly_setting:
            monthly_setting = Setting(key='work_report_monthly_template', value=monthly_template)
            db.session.add(monthly_setting)
        else:
            monthly_setting.value = monthly_template
        
        db.session.commit()
        flash('模板设置已更新')
        
    return redirect(url_for('work_report.settings'))

@bp.route('/settings/reminder', methods=['POST'])
@login_required
@module_permission_required('report')
def update_reminder_settings():
    """更新工作汇报提醒设置"""
    if request.method == 'POST':
        from app.models import Setting
        
        # 周报提醒
        enable_weekly = 'enable_weekly_reminder' in request.form
        weekly_setting = Setting.query.filter_by(key='work_report_enable_weekly_reminder').first()
        if not weekly_setting:
            weekly_setting = Setting(key='work_report_enable_weekly_reminder', value=str(enable_weekly))
            db.session.add(weekly_setting)
        else:
            weekly_setting.value = str(enable_weekly)
        
        # 月报提醒
        enable_monthly = 'enable_monthly_reminder' in request.form
        monthly_setting = Setting.query.filter_by(key='work_report_enable_monthly_reminder').first()
        if not monthly_setting:
            monthly_setting = Setting(key='work_report_enable_monthly_reminder', value=str(enable_monthly))
            db.session.add(monthly_setting)
        else:
            monthly_setting.value = str(enable_monthly)
        
        db.session.commit()
        flash('提醒设置已更新')
        
    return redirect(url_for('work_report.settings'))

@bp.route('/settings/person_order', methods=['POST'])
@login_required
@module_permission_required('report')
def update_person_order():
    """更新责任人排序设置"""
    # 不再检查用户部门
    # 任何有report模块权限的用户都可以修改责任人排序设置
    
    if request.method == 'POST':
        from app.models import Setting, User
        
        # 获取表单中的责任人顺序
        person_names = request.form.getlist('person_names[]')
        person_names = [name.strip() for name in person_names if name.strip()]
        
        # 如果没有提交任何责任人，则自动创建排序
        if not person_names:
            # 获取所有用户
            all_users = User.query.all()
            
            # 区分行政部和非行政部用户
            admin_users = []
            other_users = []
            for user in all_users:
                if user.name:  # 只考虑有名字的用户
                    if user.department == '行政部':
                        admin_users.append(user)
                    else:
                        other_users.append(user)
            
            # 行政部用户按名字排序
            admin_users.sort(key=lambda x: x.name)
            
            # 非行政部用户按名字排序
            other_users.sort(key=lambda x: x.name)
            
            # 行政部用户排在前面，其他用户排在后面
            person_names = [user.name for user in admin_users] + [user.name for user in other_users]
        
        # 保存设置
        person_order_setting = Setting.query.filter_by(key='work_report_person_order').first()
        if not person_order_setting:
            person_order_setting = Setting(
                key='work_report_person_order',
                value=json.dumps(person_names),
                description='周报责任人排序设置'
            )
            db.session.add(person_order_setting)
        else:
            person_order_setting.value = json.dumps(person_names)
        
        db.session.commit()
        flash('责任人排序设置已更新')
        
    return redirect(url_for('work_report.settings'))

@bp.route('/weekly/export/<int:report_id>')
@login_required
@module_permission_required('report')
def weekly_export(report_id):
    """导出周报为Excel"""
    # 获取周报
    report = WeeklyReport.query.get_or_404(report_id)
    
    # 创建一个内存中的Excel文件
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet("周报")
    
    # 设置单元格格式
    title_format = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'})
    header_format = workbook.add_format({'bold': True, 'bg_color': '#D9EAD3', 'border': 1, 'align': 'center'})
    cell_format = workbook.add_format({'border': 1, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True})
    # 项目标题格式（靠左显示）
    section_title_format = workbook.add_format({'bold': True, 'bg_color': '#D9EAD3', 'border': 1, 'align': 'left', 'valign': 'vcenter'})
    
    # 设置列宽
    headers = ["序号", "责任人", "工作内容", "目标完成结果", "时间节点", "是否完成", "执行结果检查", "拟采取措施", "预计完成时间"]
    col_widths = [5, 10, 20, 20, 12, 10, 20, 15, 12]
    for i, width in enumerate(col_widths):
        worksheet.set_column(i, i, width)
    
    # 写入标题
    current_row = 0
    title = f"{report.start_date.year}年 第{report.week_number}周 部门周报 ({report.start_date} 至 {report.end_date})"
    worksheet.merge_range(f'A{current_row+1}:I{current_row+1}', title, title_format)
    current_row += 1
    
    # 写入会议信息
    worksheet.merge_range(f'A{current_row+1}:B{current_row+1}', "会议时间", header_format)
    worksheet.merge_range(f'C{current_row+1}:D{current_row+1}', report.meeting_time.strftime('%Y-%m-%d') if report.meeting_time else '未设置', cell_format)
    worksheet.merge_range(f'E{current_row+1}:F{current_row+1}', "会议地点", header_format)
    worksheet.merge_range(f'G{current_row+1}:I{current_row+1}', report.meeting_place or '未设置', cell_format)
    current_row += 1
    
    worksheet.merge_range(f'A{current_row+1}:B{current_row+1}', "主持人", header_format)
    worksheet.merge_range(f'C{current_row+1}:D{current_row+1}', report.host or '未设置', cell_format)
    worksheet.merge_range(f'E{current_row+1}:F{current_row+1}', "参会人员", header_format)
    worksheet.merge_range(f'G{current_row+1}:I{current_row+1}', report.participants or '未设置', cell_format)
    current_row += 1
    
    # 空一行
    current_row += 1
    
    # 写入重点工作标题
    worksheet.merge_range(f'A{current_row+1}:I{current_row+1}', "一、重点工作跟进/风险工作通报", section_title_format)
    current_row += 1
    
    # 写入重点工作表头（紧接着标题行，没有空行）
    for i, header in enumerate(headers):
        worksheet.write(current_row, i, header, header_format)
    current_row += 1
    
    # 写入重点工作内容
    if report.key_works:
        for i, work in enumerate(report.key_works):
            worksheet.write(current_row, 0, i + 1, cell_format)
            worksheet.write(current_row, 1, work.get('person', ''), cell_format)
            worksheet.write(current_row, 2, work.get('content', ''), cell_format)
            worksheet.write(current_row, 3, work.get('target', ''), cell_format)
            worksheet.write(current_row, 4, work.get('timeline', ''), cell_format)
            worksheet.write(current_row, 5, work.get('completed', ''), cell_format)
            worksheet.write(current_row, 6, work.get('check', ''), cell_format)
            worksheet.write(current_row, 7, work.get('measures', ''), cell_format)
            worksheet.write(current_row, 8, work.get('expected_date', ''), cell_format)
            current_row += 1
    else:
        worksheet.merge_range(f'A{current_row+1}:I{current_row+1}', "暂无重点工作记录", cell_format)
        current_row += 1
    
    # 写入临时性工作标题（不空行）
    worksheet.merge_range(f'A{current_row+1}:I{current_row+1}', "二、临时性工作安排", section_title_format)
    current_row += 1
    
    # 写入临时性工作表头（紧接着标题行，没有空行）
    for i, header in enumerate(headers):
        worksheet.write(current_row, i, header, header_format)
    current_row += 1
    
    # 写入临时性工作内容
    if report.temp_works:
        for i, work in enumerate(report.temp_works):
            worksheet.write(current_row, 0, i + 1, cell_format)
            worksheet.write(current_row, 1, work.get('person', ''), cell_format)
            worksheet.write(current_row, 2, work.get('content', ''), cell_format)
            worksheet.write(current_row, 3, work.get('target', ''), cell_format)
            worksheet.write(current_row, 4, work.get('timeline', ''), cell_format)
            worksheet.write(current_row, 5, work.get('completed', ''), cell_format)
            worksheet.write(current_row, 6, work.get('check', ''), cell_format)
            worksheet.write(current_row, 7, work.get('measures', ''), cell_format)
            worksheet.write(current_row, 8, work.get('expected_date', ''), cell_format)
            current_row += 1
    else:
        worksheet.merge_range(f'A{current_row+1}:I{current_row+1}', "暂无临时性工作记录", cell_format)
        current_row += 1
    
    # 写入协调工作标题（不空行）
    worksheet.merge_range(f'A{current_row+1}:I{current_row+1}', "三、协同事项/协调资源/需要决策事项", section_title_format)
    current_row += 1
    
    # 写入协调工作表头（紧接着标题行，没有空行）
    for i, header in enumerate(headers):
        worksheet.write(current_row, i, header, header_format)
    current_row += 1
    
    # 写入协调工作内容
    if report.coordinations:
        for i, work in enumerate(report.coordinations):
            worksheet.write(current_row, 0, i + 1, cell_format)
            worksheet.write(current_row, 1, work.get('person', ''), cell_format)
            worksheet.write(current_row, 2, work.get('content', ''), cell_format)
            worksheet.write(current_row, 3, work.get('target', ''), cell_format)
            worksheet.write(current_row, 4, work.get('timeline', ''), cell_format)
            worksheet.write(current_row, 5, work.get('completed', ''), cell_format)
            worksheet.write(current_row, 6, work.get('check', ''), cell_format)
            worksheet.write(current_row, 7, work.get('measures', ''), cell_format)
            worksheet.write(current_row, 8, work.get('expected_date', ''), cell_format)
            current_row += 1
    else:
        worksheet.merge_range(f'A{current_row+1}:I{current_row+1}', "暂无协调工作记录", cell_format)
        current_row += 1
    
    # 写入会议共识标题（不空行）
    worksheet.merge_range(f'A{current_row+1}:I{current_row+1}', "四、会议达成共识事项/领导指示与建议", section_title_format)
    current_row += 1
    
    # 写入会议共识内容
    if report.consensus:
        paragraph_format = workbook.add_format({
            'border': 1, 
            'align': 'left', 
            'valign': 'top', 
            'text_wrap': True
        })
        
        consensus_text = report.consensus
        
        # 更精确地计算所需行数
        # 计算文本中的字符数和换行符数量
        text_length = len(consensus_text)
        line_breaks = consensus_text.count('\n')
        
        # 估算每行可容纳的字符数（基于总列宽）
        total_width = sum(col_widths)
        chars_per_line = total_width * 1.5  # 更保守的估计每行可容纳的字符数
        
        # 计算实际需要的行数
        content_lines = text_length / chars_per_line
        # 考虑换行符和一些额外空间，但不过度分配
        estimated_lines = max(2, int(content_lines + line_breaks) + 1)
        
        # 合并单元格并写入内容
        merge_range = f'A{current_row+1}:I{current_row+estimated_lines}'
        worksheet.merge_range(merge_range, consensus_text, paragraph_format)
        
        # 设置行高 - 使用固定的标准行高
        standard_row_height = 15  # 标准行高
        for i in range(current_row, current_row+estimated_lines):
            worksheet.set_row(i, standard_row_height)
        
        current_row += estimated_lines
    else:
        worksheet.merge_range(f'A{current_row+1}:I{current_row+1}', "暂无会议达成共识事项/领导指示与建议", cell_format)
        current_row += 1
    
    # 关闭工作簿
    workbook.close()
    
    # 设置文件指针到文件头
    output.seek(0)
    
    # 生成文件名
    filename = f"周报-第{report.week_number}周-{report.start_date}-{report.end_date}.xlsx"
    
    # 返回Excel文件
    return send_file(output, 
                     as_attachment=True,
                     download_name=filename,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') 