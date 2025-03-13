from flask import Blueprint

bp = Blueprint('vehicle_exit', __name__)

from app.vehicle.vehicle_exit import routes 