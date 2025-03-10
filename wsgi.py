from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

from app import create_app
from config import Config

app = create_app()

if __name__ == '__main__':
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    app.run(host=host, port=port, debug=True) 