import os
from flask import Flask, redirect, url_for
from flask_login import current_user
from config import Config
from app.extensions import db, migrate, login_manager, csrf

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # 添加hasattr函数到Jinja2环境
    app.jinja_env.globals['hasattr'] = hasattr
    
    # 初始化CSRF保护
    csrf.init_app(app)

    # 注册命令
    from app.commands import init_db, create_admin, create_test_data
    app.cli.add_command(init_db)
    app.cli.add_command(create_admin)
    app.cli.add_command(create_test_data)

    # 注册蓝图
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.settings import bp as settings_bp
    app.register_blueprint(settings_bp, url_prefix='/settings')

    from app.vehicle.license_plate import bp as license_plate_bp
    app.register_blueprint(license_plate_bp, url_prefix='/vehicle/license-plate')

    from app.vehicle.official_car import bp as official_car_bp
    app.register_blueprint(official_car_bp, url_prefix='/vehicle/official-car')

    from app.user import bp as user_bp
    app.register_blueprint(user_bp, url_prefix='/user')

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('license_plate.index'))
        return redirect(url_for('auth.login'))

    return app

from app import models 