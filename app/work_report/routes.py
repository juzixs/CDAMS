from datetime import datetime, timedelta, date
import json
from flask import render_template, flash, redirect, url_for, request, current_app, jsonify
from flask_login import login_required, current_user
from app.work_report import bp
from app import db
from app.models.work_report import WeeklyReport, MonthlyReport

@bp.route('/')
@login_required
def index():
    """工作汇报首页"""
    return render_template('work_report/index.html', title='工作汇报')

@bp.route('/weekly')
@login_required
def weekly():
    """周报管理"""
    # 获取当前用户部门的所有周报
    reports = WeeklyReport.query.order_by(WeeklyReport.week_number.desc()).all()
    return render_template('work_report/weekly.html', title='周报管理', reports=reports)

@bp.route('/weekly/create', methods=['GET', 'POST'])
@login_required
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
    
    # 生成可选的周次列表（当前周和前后4周）
    today = date.today()
    # 找到本周的周一
    monday = today - timedelta(days=today.weekday())
    weeks = []
    
    for i in range(-4, 5):  # 前4周到后4周
        week_monday = monday + timedelta(weeks=i)
        week_sunday = week_monday + timedelta(days=6)
        week_number = int(week_monday.strftime('%W')) + 1  # 周数从1开始
        
        weeks.append({
            'number': week_number,
            'start_date': week_monday.strftime('%Y-%m-%d'),
            'end_date': week_sunday.strftime('%Y-%m-%d')
        })
    
    return render_template('work_report/weekly_create.html', title='新建周报', weeks=weeks)

@bp.route('/weekly/<int:report_id>/edit', methods=['GET'])
@login_required
def weekly_edit(report_id):
    """编辑周报"""
    report = WeeklyReport.query.get_or_404(report_id)
    
    # 检查权限
    if report.user_id != current_user.id and not current_user.is_admin:
        flash('您没有权限编辑此周报')
        return redirect(url_for('work_report.weekly'))
    
    return render_template('work_report/weekly_edit.html', title='编辑周报', report=report)

@bp.route('/weekly/<int:report_id>/update', methods=['POST'])
@login_required
def weekly_update(report_id):
    """更新周报内容"""
    report = WeeklyReport.query.get_or_404(report_id)
    
    # 检查权限
    if report.user_id != current_user.id and not current_user.is_admin:
        flash('您没有权限编辑此周报')
        return redirect(url_for('work_report.weekly'))
    
    # 更新基本信息
    if request.form.get('meeting_time'):
        report.meeting_time = datetime.strptime(request.form.get('meeting_time'), '%Y-%m-%dT%H:%M')
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
    
    # 更新报告
    report.key_works = key_works
    report.temp_works = temp_works
    report.coordinations = coordinations
    
    db.session.commit()
    flash('周报已保存')
    
    return redirect(url_for('work_report.weekly_edit', report_id=report.id))

@bp.route('/monthly')
@login_required
def monthly():
    """月报管理"""
    return render_template('work_report/monthly.html', title='月报管理') 