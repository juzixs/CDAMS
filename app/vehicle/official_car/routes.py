from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.vehicle.official_car import bp

@bp.route('/')
@login_required
def index():
    return render_template('vehicle/official_car/index.html', title='公务车辆管理') 