from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.ticket import bp
from app.ticket.forms import TicketForm, TicketReplyForm, TicketCategoryForm
from app.ticket.models import Ticket, TicketReply, TicketCategory

@bp.route('/')
@login_required
def index():
    """工单系统首页"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    
    # 构建查询
    query = Ticket.query
    
    # 根据状态筛选
    if status != 'all':
        query = query.filter_by(status=status)
    
    # 非管理员只能看到自己的工单
    if not current_user.is_admin:
        query = query.filter_by(user_id=current_user.id)
    
    # 按创建时间倒序排列
    tickets = query.order_by(Ticket.created_at.desc()).paginate(page=page, per_page=10)
    
    # 获取所有工单分类
    categories = TicketCategory.query.all()
    
    return render_template('ticket/index.html', tickets=tickets, status=status, categories=categories)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建工单"""
    form = TicketForm()
    
    # 获取所有可用的工单分类
    categories = TicketCategory.query.all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    
    if form.validate_on_submit():
        ticket = Ticket(
            title=form.title.data,
            content=form.content.data,
            priority=form.priority.data,
            category_id=form.category_id.data,
            user_id=current_user.id
        )
        db.session.add(ticket)
        db.session.commit()
        flash('工单已创建', 'success')
        return redirect(url_for('ticket.index'))
    
    return render_template('ticket/create.html', form=form)

@bp.route('/view/<int:id>', methods=['GET', 'POST'])
@login_required
def view(id):
    """查看工单详情"""
    ticket = Ticket.query.get_or_404(id)
    
    # 检查权限：只有工单创建者和管理员可以查看
    if ticket.user_id != current_user.id and not current_user.is_admin:
        flash('您没有权限查看此工单', 'danger')
        return redirect(url_for('ticket.index'))
    
    # 回复表单
    form = TicketReplyForm()
    
    if form.validate_on_submit():
        reply = TicketReply(
            content=form.content.data,
            ticket_id=ticket.id,
            user_id=current_user.id
        )
        db.session.add(reply)
        
        # 如果是管理员回复，更新工单状态为"处理中"
        if current_user.is_admin and ticket.status == 'pending':
            ticket.status = 'processing'
        
        db.session.commit()
        flash('回复已提交', 'success')
        return redirect(url_for('ticket.view', id=ticket.id))
    
    # 获取工单的所有回复
    replies = TicketReply.query.filter_by(ticket_id=ticket.id).order_by(TicketReply.created_at.asc()).all()
    
    return render_template('ticket/view.html', ticket=ticket, replies=replies, form=form)

@bp.route('/close/<int:id>')
@login_required
def close(id):
    """关闭工单"""
    ticket = Ticket.query.get_or_404(id)
    
    # 检查权限：只有工单创建者和管理员可以关闭工单
    if ticket.user_id != current_user.id and not current_user.is_admin:
        flash('您没有权限关闭此工单', 'danger')
        return redirect(url_for('ticket.index'))
    
    ticket.status = 'closed'
    db.session.commit()
    flash('工单已关闭', 'success')
    return redirect(url_for('ticket.index'))

@bp.route('/reopen/<int:id>')
@login_required
def reopen(id):
    """重新打开工单"""
    ticket = Ticket.query.get_or_404(id)
    
    # 检查权限：只有工单创建者和管理员可以重新打开工单
    if ticket.user_id != current_user.id and not current_user.is_admin:
        flash('您没有权限重新打开此工单', 'danger')
        return redirect(url_for('ticket.index'))
    
    ticket.status = 'processing'
    db.session.commit()
    flash('工单已重新打开', 'success')
    return redirect(url_for('ticket.index'))

@bp.route('/categories')
@login_required
def categories():
    """工单分类管理"""
    if not current_user.is_admin:
        flash('只有管理员可以管理工单分类', 'danger')
        return redirect(url_for('ticket.index'))
    
    categories = TicketCategory.query.all()
    return render_template('ticket/categories.html', categories=categories)

@bp.route('/category/add', methods=['GET', 'POST'])
@login_required
def add_category():
    """添加工单分类"""
    if not current_user.is_admin:
        flash('只有管理员可以添加工单分类', 'danger')
        return redirect(url_for('ticket.index'))
    
    form = TicketCategoryForm()
    
    if form.validate_on_submit():
        category = TicketCategory(
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(category)
        db.session.commit()
        flash('工单分类已添加', 'success')
        return redirect(url_for('ticket.categories'))
    
    return render_template('ticket/add_category.html', form=form)

@bp.route('/category/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    """编辑工单分类"""
    if not current_user.is_admin:
        flash('只有管理员可以编辑工单分类', 'danger')
        return redirect(url_for('ticket.index'))
    
    category = TicketCategory.query.get_or_404(id)
    form = TicketCategoryForm(obj=category)
    
    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data
        db.session.commit()
        flash('工单分类已更新', 'success')
        return redirect(url_for('ticket.categories'))
    
    return render_template('ticket/edit_category.html', form=form, category=category)

@bp.route('/category/delete/<int:id>')
@login_required
def delete_category(id):
    """删除工单分类"""
    if not current_user.is_admin:
        flash('只有管理员可以删除工单分类', 'danger')
        return redirect(url_for('ticket.index'))
    
    category = TicketCategory.query.get_or_404(id)
    
    # 检查是否有工单使用此分类
    if Ticket.query.filter_by(category_id=id).first():
        flash('无法删除此分类，因为有工单正在使用它', 'danger')
        return redirect(url_for('ticket.categories'))
    
    db.session.delete(category)
    db.session.commit()
    flash('工单分类已删除', 'success')
    return redirect(url_for('ticket.categories')) 