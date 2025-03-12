from flask import Blueprint

bp = Blueprint('vehicle', __name__)

from app.vehicle import routes

# 导入子模块蓝图
from app.vehicle.official_car import bp as official_car_bp
from app.vehicle.license_plate import bp as license_plate_bp
from app.vehicle.vehicle_exit import bp as vehicle_exit_bp

# 注册子模块蓝图
bp.register_blueprint(official_car_bp, url_prefix='/official_car')
bp.register_blueprint(license_plate_bp, url_prefix='/license_plate')
bp.register_blueprint(vehicle_exit_bp, url_prefix='/vehicle_exit') 