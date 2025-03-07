from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, send_file
from flask_login import login_required, current_user
from app.user import bp
from app.forms import ProfileForm, PasswordForm, UserCreateForm, UserSearchForm
from app.extensions import db
from app.models import User, Module
from werkzeug.security import generate_password_hash, check_password_hash
import csv
import io
import os
from werkzeug.utils import secure_filename
from datetime import datetime

@bp.route('/users', methods=['GET'])
@login_required
def users():
    """用户列表"""
    if not current_user.is_admin:
        flash('您没有权限访问此页面')
        return redirect(url_for('license_plate.index'))
        
    # 获取搜索参数
    search_form = UserSearchForm(request.args, meta={'csrf': False})
    keyword = request.args.get('keyword', '')
    field = request.args.get('field', 'username')
    
    # 获取排序参数
    sort_by = request.args.get('sort', 'username')
    order = request.args.get('order', 'asc')

    # 构建排序条件
    if sort_by not in ['username', 'employee_id', 'name', 'department', 'phone', 'email']:
        sort_by = 'username'

    if order not in ['asc', 'desc']:
        order = 'asc'

    # 获取排序字段
    sort_field = getattr(User, sort_by)

    # 构建查询
    query = User.query
    
    # 如果有搜索关键词，添加搜索条件
    if keyword:
        if field == 'username':
            query = query.filter(User.username.like(f'%{keyword}%'))
        elif field == 'employee_id':
            query = query.filter(User.employee_id.like(f'%{keyword}%'))
        elif field == 'name':
            query = query.filter(User.name.like(f'%{keyword}%'))
        elif field == 'department':
            query = query.filter(User.department.like(f'%{keyword}%'))
        elif field == 'phone':
            query = query.filter(User.phone.like(f'%{keyword}%'))
        elif field == 'email':
            query = query.filter(User.email.like(f'%{keyword}%'))
    
    # 应用排序
    if order == 'asc':
        query = query.order_by(sort_field.asc())
    else:
        query = query.order_by(sort_field.desc())
    
    # 获取所有模块
    modules = Module.query.all()
    
    # 获取用户列表
    users = query.all()
    
    return render_template('user/users.html', 
                          users=users, 
                          search_form=search_form,
                          sort_by=sort_by,
                          order=order,
                          modules=modules)

@bp.route('/profile', methods=['GET', 'POST'])
@bp.route('/profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
def profile(user_id=None):
    """个人资料设置"""
    # 如果指定了用户ID且当前用户是管理员，则编辑该用户的资料
    if user_id and current_user.is_admin:
        user = User.query.get_or_404(user_id)
    else:
        user = current_user
    
    form = ProfileForm()
    if form.validate_on_submit():
        # 检查用户名是否被修改且是否已存在
        if form.username.data != user.username:
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user and existing_user.id != user.id:
                flash('该用户名已被使用')
                return redirect(url_for('user.profile', user_id=user_id))

        # 检查邮箱是否被修改且是否已存在
        if form.email.data != user.email:
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user and existing_user.id != user.id:
                flash('该邮箱已被使用')
                return redirect(url_for('user.profile', user_id=user_id))

        # 检查工号是否被修改且是否已存在
        if form.employee_id.data != user.employee_id:
            existing_user = User.query.filter_by(employee_id=form.employee_id.data).first()
            if existing_user and existing_user.id != user.id:
                flash('该工号已被使用')
                return redirect(url_for('user.profile', user_id=user_id))

        try:
            # 更新所有字段
            user.username = form.username.data
            user.email = form.email.data
            user.employee_id = form.employee_id.data
            user.name = form.name.data
            user.department = form.department.data
            user.phone = form.phone.data
            
            # 如果是管理员编辑其他用户且提供了密码，则更新密码
            if user_id and current_user.is_admin and form.password.data:
                user.set_password(form.password.data)
                
            db.session.commit()
            flash('个人资料已更新')
        except Exception as e:
            db.session.rollback()
            flash('更新失败，请稍后重试')
            print(f"错误: {str(e)}")
        
        if user_id and current_user.is_admin:
            return redirect(url_for('user.users'))
        else:
            return redirect(url_for('user.profile'))

    # GET请求时预填表单
    if request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.employee_id.data = user.employee_id
        form.name.data = user.name
        form.department.data = user.department
        form.phone.data = user.phone

    return render_template('user/profile.html', form=form, user=user)

@bp.route('/password', methods=['GET', 'POST'])
@login_required
def password():
    """密码修改"""
    form = PasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('当前密码错误')
            return redirect(url_for('user.password'))
        
        try:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('密码修改成功')
        except Exception as e:
            db.session.rollback()
            flash('修改失败，请稍后重试')
        return redirect(url_for('user.password'))

    return render_template('user/password.html', form=form)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_user():
    """创建用户"""
    if not current_user.is_admin:
        flash('您没有权限访问此页面')
        return redirect(url_for('license_plate.index'))
        
    form = UserCreateForm()
    if form.validate_on_submit():
        # 检查用户名是否已存在
        if User.query.filter_by(username=form.username.data).first():
            flash('该用户名已被使用')
            return redirect(url_for('user.create_user'))
            
        # 检查邮箱是否已存在
        if User.query.filter_by(email=form.email.data).first():
            flash('该邮箱已被使用')
            return redirect(url_for('user.create_user'))
            
        # 检查工号是否已存在
        if User.query.filter_by(employee_id=form.employee_id.data).first():
            flash('该工号已被使用')
            return redirect(url_for('user.create_user'))
            
        try:
            user = User(
                username=form.username.data,
                email=form.email.data,
                employee_id=form.employee_id.data,
                name=form.name.data,
                department=form.department.data,
                phone=form.phone.data,
                is_admin=form.is_admin.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('用户创建成功')
            return redirect(url_for('user.users'))
        except Exception as e:
            db.session.rollback()
            flash(f'创建用户失败: {str(e)}')
            
    return render_template('user/create_user.html', form=form)

@bp.route('/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """删除用户"""
    if not current_user.is_admin:
        flash('权限不足', 'danger')
        return redirect(url_for('license_plate.index'))

    user = User.query.get_or_404(user_id)

    # 不能删除自己
    if user.id == current_user.id:
        flash('不能删除自己', 'danger')
        return redirect(url_for('user.users'))

    try:
        username = user.username
        db.session.delete(user)
        db.session.commit()
        flash(f'用户 {username} 已删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'错误: {str(e)}', 'danger')

    return redirect(url_for('user.users'))

@bp.route('/batch-delete', methods=['POST'])
@login_required
def batch_delete_users():
    """批量删除用户"""
    if not current_user.is_admin:
        flash('您没有权限删除用户')
        return redirect(url_for('user.users'))
    
    user_ids = request.form.getlist('user_ids')
    if not user_ids:
        flash('请选择要删除的用户')
        return redirect(url_for('user.users'))
    
    # 确保不会删除当前用户
    if str(current_user.id) in user_ids:
        flash('不能删除当前登录的用户')
        user_ids.remove(str(current_user.id))
    
    if user_ids:
        users = User.query.filter(User.id.in_(user_ids)).all()
        for user in users:
            db.session.delete(user)
        db.session.commit()
        flash(f'已删除 {len(users)} 个用户')
    
    return redirect(url_for('user.users'))

@bp.route('/get-user-modules/<int:user_id>', methods=['GET'])
@login_required
def get_user_modules(user_id):
    """获取用户的模块权限"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '您没有权限执行此操作'})
    
    user = User.query.get_or_404(user_id)
    module_ids = [module.id for module in user.authorized_modules]
    
    return jsonify({
        'success': True,
        'module_ids': module_ids
    })

@bp.route('/auth-user', methods=['POST'])
@login_required
def auth_user():
    """用户授权"""
    if not current_user.is_admin:
        flash('您没有权限修改用户权限')
        return redirect(url_for('user.users'))
    
    user_id = request.form.get('user_id')
    is_admin = 'is_admin' in request.form
    module_ids = request.form.getlist('module_ids')
    
    if not user_id:
        flash('用户ID不能为空')
        return redirect(url_for('user.users'))
    
    user = User.query.get_or_404(user_id)
    
    # 不能修改自己的管理员权限
    if int(user_id) == current_user.id:
        flash('不能修改自己的管理员权限')
        return redirect(url_for('user.users'))
    
    try:
        # 更新管理员权限
        user.is_admin = is_admin
        
        # 更新模块权限
        user.authorized_modules = []
        if module_ids:
            modules = Module.query.filter(Module.id.in_(module_ids)).all()
            user.authorized_modules = modules
        
        db.session.commit()
        flash(f'用户 {user.username} 的权限已更新')
    except Exception as e:
        db.session.rollback()
        flash(f'更新失败: {str(e)}')
    
    return redirect(url_for('user.users'))

@bp.route('/export', methods=['GET'])
@login_required
def export_users():
    """导出用户数据"""
    if not current_user.is_admin:
        flash('您没有权限访问此页面')
        return redirect(url_for('license_plate.index'))
        
    # 创建CSV文件
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    writer.writerow(['用户名', '邮箱', '工号', '姓名', '部门', '手机', '管理员权限'])
    
    # 写入用户数据
    users = User.query.all()
    for user in users:
        writer.writerow([
            user.username,
            user.email,
            user.employee_id,
            user.name,
            user.department,
            user.phone,
            '是' if user.is_admin else '否'
        ])
    
    # 设置响应
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'用户数据_{timestamp}.csv'
    )

@bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_users():
    """导入用户数据"""
    if not current_user.is_admin:
        flash('您没有权限访问此页面')
        return redirect(url_for('license_plate.index'))
        
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('没有选择文件')
            return redirect(request.url)
            
        file = request.files['file']
        if file.filename == '':
            flash('没有选择文件')
            return redirect(request.url)
            
        if file and file.filename.endswith('.csv'):
            try:
                # 读取CSV文件
                stream = io.StringIO(file.stream.read().decode('utf-8-sig'))
                csv_reader = csv.reader(stream)
                
                # 跳过表头
                next(csv_reader)
                
                success_count = 0
                error_count = 0
                error_messages = []
                
                # 处理每一行数据
                for row in csv_reader:
                    if len(row) < 7:
                        error_count += 1
                        error_messages.append(f'行数据不完整: {",".join(row)}')
                        continue
                        
                    username, email, employee_id, name, department, phone, is_admin = row
                    
                    # 检查必填字段
                    if not all([username, email, employee_id, name, department, phone]):
                        error_count += 1
                        error_messages.append(f'缺少必填字段: {",".join(row)}')
                        continue
                        
                    # 检查用户是否已存在
                    if User.query.filter_by(username=username).first():
                        error_count += 1
                        error_messages.append(f'用户名已存在: {username}')
                        continue
                        
                    if User.query.filter_by(email=email).first():
                        error_count += 1
                        error_messages.append(f'邮箱已存在: {email}')
                        continue
                        
                    if User.query.filter_by(employee_id=employee_id).first():
                        error_count += 1
                        error_messages.append(f'工号已存在: {employee_id}')
                        continue
                        
                    # 创建新用户
                    try:
                        user = User(
                            username=username,
                            email=email,
                            employee_id=employee_id,
                            name=name,
                            department=department,
                            phone=phone,
                            is_admin=True if is_admin == '是' else False
                        )
                        # 设置默认密码为工号
                        user.set_password(employee_id)
                        db.session.add(user)
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        error_messages.append(f'创建用户失败: {str(e)}')
                
                # 提交事务
                if success_count > 0:
                    db.session.commit()
                    
                flash(f'导入完成: 成功 {success_count} 条, 失败 {error_count} 条')
                if error_messages:
                    for msg in error_messages[:10]:  # 只显示前10条错误信息
                        flash(msg, 'error')
                    if len(error_messages) > 10:
                        flash(f'还有 {len(error_messages) - 10} 条错误信息未显示', 'error')
                        
                return redirect(url_for('user.users'))
            except Exception as e:
                flash(f'导入失败: {str(e)}')
        else:
            flash('只支持CSV文件格式')
            
    return render_template('user/import_users.html') 