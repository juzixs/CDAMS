import os
from flask import render_template, flash, redirect, url_for, current_app, request
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.settings import bp
from app.forms import PDFSettingsForm
from app.models import PDFSettings, Module, Setting, User
from app.decorators import module_permission_required
import json

@bp.route('/', methods=['GET', 'POST'])
@login_required
@module_permission_required('settings')
def index():
    """系统设置"""
    if not current_user.is_admin:
        flash('只有管理员可以访问系统设置')
        return redirect(url_for('index'))
    
    # 获取或创建设置
    settings = PDFSettings.query.first()
    if not settings:
        settings = PDFSettings()
        db.session.add(settings)
        db.session.commit()
    
    # 获取所有模块
    modules = Module.query.all()
    
    # 获取责任人排序设置
    person_order = []
    person_order_setting = Setting.query.filter_by(key='work_report_person_order').first()
    if person_order_setting:
        try:
            person_order = json.loads(person_order_setting.value)
        except:
            person_order = []
    
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
    
    form = PDFSettingsForm()
    if form.validate_on_submit():
        # 处理背景图上传
        if form.background_image.data:
            filename = secure_filename(form.background_image.data.filename)
            filepath = os.path.join(current_app.instance_path, 'uploads', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            form.background_image.data.save(filepath)
            settings.background_image = filepath
        
        # 处理字体文件上传
        if form.font_family.data:
            filename = secure_filename(form.font_family.data.filename)
            filepath = os.path.join(current_app.instance_path, 'uploads', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            form.font_family.data.save(filepath)
            settings.font_path = filepath
        
        # 更新其他设置
        settings.font_size = form.font_size.data
        settings.position_x = form.text_x.data
        settings.position_y = form.text_y.data
        settings.text_color = form.text_color.data
        settings.outline_color = form.outline_color.data
        settings.outline_width = form.outline_width.data
        
        db.session.commit()
        flash('PDF设置已更新')
        return redirect(url_for('settings.index'))
    
    # 设置表单初始值
    if not form.is_submitted():
        form.font_size.data = settings.font_size
        form.text_x.data = settings.position_x
        form.text_y.data = settings.position_y
        form.text_color.data = settings.text_color
        form.outline_color.data = settings.outline_color
        form.outline_width.data = settings.outline_width
    
    return render_template('settings/index.html', 
                          title='系统设置', 
                          form=form, 
                          settings=settings, 
                          modules=modules,
                          person_order=person_order,
                          admin_users=admin_users,
                          other_users=other_users,
                          nonexistent_users=nonexistent_users)

@bp.route('/update_global', methods=['POST'])
@login_required
@module_permission_required('settings')
def update_global():
    """更新全局设置"""
    if not current_user.is_admin:
        flash('只有管理员可以修改系统设置')
        return redirect(url_for('settings.index'))
    
    # 获取所有模块
    modules = Module.query.all()
    
    # 更新模块权限级别
    for module in modules:
        permission_level = request.form.get(f'module_permission_{module.id}')
        if permission_level in ['normal', 'authorized', 'admin']:
            module.permission_level = permission_level
    
    db.session.commit()
    flash('全局设置已更新')
    return redirect(url_for('settings.index'))

@bp.route('/reset_defaults', methods=['POST'])
@login_required
@module_permission_required('settings')
def reset_defaults():
    """恢复默认设置"""
    if not current_user.is_admin:
        flash('只有管理员可以访问系统设置')
        return redirect(url_for('index'))
    
    settings = PDFSettings.query.first()
    if settings:
        settings.reset_to_default()
        db.session.commit()
        flash('已恢复默认设置')
    
    return redirect(url_for('settings.index'))

@bp.route('/update_work_report_paging', methods=['POST'])
@login_required
@module_permission_required('settings')
def update_work_report_paging():
    """更新工作汇报分页设置"""
    # 不再检查用户部门
    # 任何有settings模块权限的用户都可以修改责任人排序设置
    
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
    
    return redirect(url_for('settings.index', _anchor='work-report')) 