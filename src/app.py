"""Flask 应用入口"""

from flask import Flask
from flask_cors import CORS
from .models import db
from .routes import api_bp
import os


def create_app(config_name='default'):
    """应用工厂"""
    app = Flask(__name__)
    
    # 配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 
        'sqlite:///app.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化扩展
    db.init_app(app)
    CORS(app)
    
    # 注册蓝图
    app.register_blueprint(api_bp)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    return app


# 开发服务器入口
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
