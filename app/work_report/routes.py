from flask import render_template, flash, redirect, url_for, request, current_app
from flask_login import login_required, current_user
from app.work_report import bp
from app import db

@bp.route('/')
@login_required
def index():
    """工作汇报首页"""
    return render_template('work_report/index.html', title='工作汇报')

@bp.route('/weekly')
@login_required
def weekly():
    """周报管理"""
    return render_template('work_report/weekly.html', title='周报管理')

@bp.route('/monthly')
@login_required
def monthly():
    """月报管理"""
    return render_template('work_report/monthly.html', title='月报管理') 