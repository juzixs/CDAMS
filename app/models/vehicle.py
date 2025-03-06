from datetime import datetime
from app.extensions import db

class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    
    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(20), unique=True, nullable=False)
    vehicle_type = db.Column(db.String(20), nullable=False, default='燃油')
    owner_name = db.Column(db.String(64))
    department = db.Column(db.String(64))
    remarks = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    issued_at = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id')) 