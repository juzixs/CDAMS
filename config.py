import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app_new.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask运行设置
    HOST = '0.0.0.0'  # 监听所有网络接口
    PORT = 5000       # 默认端口号 