from datetime import datetime
from app import db

class OfficialCar(db.Model):
    """公务车辆信息模型"""
    __tablename__ = 'official_cars'

    id = db.Column(db.Integer, primary_key=True)
    card_number = db.Column(db.String(50))
    asset_number = db.Column(db.String(50), nullable=False)
    brand = db.Column(db.String(50))
    asset_description = db.Column(db.String(200))
    model = db.Column(db.String(50))
    original_value = db.Column(db.Float)
    is_business_car = db.Column(db.String(10))
    plate_number = db.Column(db.String(20))
    car_model = db.Column(db.String(50))
    car_type = db.Column(db.String(50))
    registration_time = db.Column(db.DateTime)
    seat_count = db.Column(db.Integer)
    displacement = db.Column(db.String(20))
    responsible_person = db.Column(db.String(50))
    usage_nature = db.Column(db.String(50))
    vehicle_license_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<OfficialCar {self.plate_number}>' 