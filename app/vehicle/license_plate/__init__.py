from flask import Blueprint

bp = Blueprint('license_plate', __name__, url_prefix='/vehicle/license_plate')

from app.vehicle.license_plate import routes 