import os
from flask import Flask, redirect, url_for, render_template
from flask_login import current_user
from config import Config
from app.extensions import db, migrate, login_manager, csrf

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 设置运行时配置
    if not app.config.get('HOST'):
        app.config['HOST'] = '0.0.0.0'  # 默认监听所有网络接口
    if not app.config.get('PORT'):
        app.config['PORT'] = 5000       # 默认端口号

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # 添加hasattr函数到Jinja2环境
    app.jinja_env.globals['hasattr'] = hasattr
    
    # 添加nl2br过滤器
    @app.template_filter('nl2br')
    def nl2br_filter(s):
        if s:
            return s.replace('\n', '<br>')
        return s
    
    # 初始化CSRF保护
    csrf.init_app(app)

    # 注册蓝图
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.settings import bp as settings_bp
    app.register_blueprint(settings_bp, url_prefix='/settings')

    from app.vehicle import bp as vehicle_bp
    app.register_blueprint(vehicle_bp, url_prefix='/vehicle')

    from app.vehicle.license_plate import bp as license_plate_bp
    app.register_blueprint(license_plate_bp, url_prefix='/vehicle/license-plate')

    from app.vehicle.official_car import bp as official_car_bp
    app.register_blueprint(official_car_bp, url_prefix='/vehicle/official-car')

    from app.vehicle.vehicle_exit import bp as vehicle_exit_bp
    app.register_blueprint(vehicle_exit_bp, url_prefix='/vehicle/vehicle-exit')

    from app.user import bp as user_bp
    app.register_blueprint(user_bp, url_prefix='/user')

    from app.dormitory import bp as dormitory_bp
    app.register_blueprint(dormitory_bp, url_prefix='/dormitory')
    
    from app.ticket import bp as ticket_bp
    app.register_blueprint(ticket_bp, url_prefix='/ticket')

    from app.work_report import bp as work_report_bp
    app.register_blueprint(work_report_bp, url_prefix='/work_report')

    # 注册命令
    from app import commands
    commands.init_app(app)

    @app.route('/')
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return render_template('index.html', title='首页')

    return app

from app import models 