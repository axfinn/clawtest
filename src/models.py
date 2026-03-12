"""数据模型定义"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class ApiResponse:
    """通用 API 响应"""
    
    @staticmethod
    def success(data=None, message='Success'):
        return {
            'code': 200,
            'message': message,
            'data': data
        }
    
    @staticmethod
    def error(message='Error', code=400):
        return {
            'code': code,
            'message': message,
            'data': None
        }
