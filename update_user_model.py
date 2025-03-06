#!/usr/bin/env python
# 临时脚本，用于更新User模型

user_model_content = '''from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    employee_id = db.Column(db.String(20), nullable=True)
    name = db.Column(db.String(20), nullable=True)
    department = db.Column(db.String(64), nullable=True)
    phone = db.Column(db.String(11), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
'''

with open('app/models/user.py', 'w') as f:
    f.write(user_model_content)

print("User模型已更新！") 