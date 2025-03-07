import os
from flask import render_template, flash, redirect, url_for, current_app, request
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.settings import bp
from app.forms import PDFSettingsForm
from app.models import PDFSettings, Module
from app.decorators import module_permission_required

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
        flash('设置已更新')
        return redirect(url_for('settings.index'))
    
    # 填充表单数据
    if settings:
        form.font_size.data = settings.font_size
        form.text_x.data = settings.position_x
        form.text_y.data = settings.position_y
        form.text_color.data = settings.text_color
        form.outline_color.data = settings.outline_color
        form.outline_width.data = settings.outline_width
    
    return render_template('settings/index.html', form=form, settings=settings, modules=modules)

@bp.route('/update_global', methods=['POST'])
@login_required
@module_permission_required('settings')
def update_global():
    """更新全局设置"""
    if not current_user.is_admin:
        flash('只有管理员可以访问系统设置')
        return redirect(url_for('index'))
    
    # 更新模块权限级别
    for key, value in request.form.items():
        if key.startswith('module_permission_'):
            module_id = int(key.split('_')[-1])
            module = Module.query.get(module_id)
            if module:
                module.permission_level = value
    
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