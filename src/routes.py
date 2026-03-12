"""API 路由定义"""

from flask import Blueprint, request, jsonify
from .models import ApiResponse


api_bp = Blueprint('api', __name__, url_prefix='/api/v1')



@api_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify(ApiResponse.success({'status': 'ok'}))
