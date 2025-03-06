from flask import Blueprint

bp = Blueprint('official_car', __name__, url_prefix='/vehicle/official_car')

from app.vehicle.official_car import routes

def init_app():
    # Import routes at initialization time to avoid circular imports
    return bp 