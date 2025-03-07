from flask import Blueprint

bp = Blueprint('work_report', __name__, template_folder='templates')

from app.work_report import routes 