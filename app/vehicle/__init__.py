from flask import Blueprint

bp = Blueprint('vehicle', __name__, url_prefix='/vehicle')

from app.vehicle import routes 