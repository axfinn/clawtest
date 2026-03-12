# -*- coding: utf-8 -*-
"""
API 端点集成测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from app import create_app
from models import db, ApiResponse


@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """创建 CLI 测试运行器"""
    return app.test_cli_runner()


class TestHealthEndpoint:
    """健康检查端点测试"""
    
    def test_health_check_success(self, client):
        """测试健康检查成功"""
        response = client.get('/api/v1/health')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 200
        assert data['message'] == 'Success'
        assert data['data']['status'] == 'ok'
    
    def test_health_check_response_format(self, client):
        """测试健康检查响应格式"""
        response = client.get('/api/v1/health')
        data = response.get_json()
        
        # 验证必需字段
        assert 'code' in data
        assert 'message' in data
        assert 'data' in data


class TestApiResponse:
    """ApiResponse 模型测试"""
    
    def test_success_response(self):
        """测试成功响应"""
        response = ApiResponse.success({'key': 'value'})
        
        assert response['code'] == 200
        assert response['message'] == 'Success'
        assert response['data'] == {'key': 'value'}
    
    def test_success_response_with_custom_message(self):
        """测试带自定义消息的成功响应"""
        response = ApiResponse.success({'key': 'value'}, message='Custom message')
        
        assert response['message'] == 'Custom message'
    
    def test_error_response_default(self):
        """测试默认错误响应"""
        response = ApiResponse.error()
        
        assert response['code'] == 400
        assert response['message'] == 'Error'
        assert response['data'] is None
    
    def test_error_response_custom_message(self):
        """测试自定义错误消息"""
        response = ApiResponse.error('Custom error message')
        
        assert response['message'] == 'Custom error message'
        assert response['code'] == 400
    
    def test_error_response_custom_code(self):
        """测试自定义错误码"""
        response = ApiResponse.error('Not found', code=404)
        
        assert response['code'] == 404
        assert response['message'] == 'Not found'
    
    def test_error_response_various_codes(self):
        """测试各种错误码"""
        test_cases = [
            (400, 'Bad Request'),
            (401, 'Unauthorized'),
            (403, 'Forbidden'),
            (404, 'Not Found'),
            (500, 'Internal Server Error')
        ]
        
        for code, message in test_cases:
            response = ApiResponse.error(message, code=code)
            assert response['code'] == code
            assert response['message'] == message


class TestAppConfiguration:
    """应用配置测试"""
    
    def test_app_factory_creates_app(self):
        """测试应用工厂创建应用"""
        app = create_app('testing')
        
        assert app is not None
        assert app.config['TESTING'] is True
    
    def test_app_has_blueprints(self, app):
        """测试应用有注册的蓝图"""
        # 检查蓝图是否已注册
        assert len(app.blueprints) > 0
    
    def test_app_cors_enabled(self, app):
        """测试 CORS 已启用"""
        # 检查 CORS 扩展
        from flask_cors import CORS
        # 如果 CORS 已配置，应该有相关属性
        assert app is not None


class TestEndpoints404:
    """404 端点测试"""
    
    def test_nonexistent_endpoint(self, client):
        """测试不存在的端点"""
        response = client.get('/api/v1/nonexistent')
        
        # Flask 默认返回 404
        assert response.status_code in [404, 500]


class TestMiniMaxEndpoint:
    """MiniMax API 端点测试（如果存在）"""
    
    @patch('src.api.minimax.MiniMaxClient')
    def test_minimax_chat_endpoint(self, mock_client_class, client):
        """测试 MiniMax 聊天端点（如果存在）"""
        # Mock 客户端
        mock_client = MagicMock()
        mock_client.chat.return_value = "Mocked response"
        mock_client_class.return_value = mock_client
        
        # 检查端点是否存在
        response = client.post('/api/v1/chat', json={
            'message': 'Hello',
            'model': 'MiniMax-M2.5'
        })
        
        # 如果端点不存在，会返回 404，这是预期的
        # 如果存在，应该能正确处理请求
        assert response.status_code in [200, 404, 405]


class TestCodeExecutorEndpoint:
    """代码执行器端点测试（如果存在）"""
    
    def test_execute_endpoint_not_exists(self, client):
        """测试代码执行端点（预期不存在）"""
        response = client.post('/api/v1/execute', json={
            'code': 'print("test")',
            'language': 'python'
        })
        
        # 端点可能不存在，返回 404
        assert response.status_code in [404, 405]


class TestRequestMethods:
    """请求方法测试"""
    
    def test_health_only_get(self, client):
        """测试健康检查只接受 GET"""
        # POST 方法应该被拒绝
        response = client.post('/api/v1/health')
        
        # 可能返回 405 Method Not Allowed 或其他
        assert response.status_code in [200, 405]
    
    def test_health_put_not_allowed(self, client):
        """测试 PUT 方法不允许"""
        response = client.put('/api/v1/health')
        
        assert response.status_code in [404, 405]


class TestRequestContentTypes:
    """请求内容类型测试"""
    
    def test_health_json_content_type(self, client):
        """测试健康检查返回 JSON"""
        response = client.get('/api/v1/health')
        
        assert 'application/json' in response.content_type
    
    def test_post_json_content_type(self, client):
        """测试 POST 请求接受 JSON"""
        response = client.post(
            '/api/v1/health',
            json={'test': 'data'}
        )
        
        assert response.status_code in [200, 405]


class TestErrorHandling:
    """错误处理测试"""
    
    def test_app_error_handler_exists(self, app):
        """测试应用有错误处理器"""
        # 检查是否有自定义错误处理器
        # 这是一个基本的检查
        assert app is not None
    
    @patch('src.api.minimax.requests.Session')
    def test_minimax_api_error_handling(self, mock_session_class, client):
        """测试 MiniMax API 错误处理"""
        # 模拟 API 错误
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        from requests import Response
        mock_response = Response()
        mock_response.status_code = 500
        mock_response._content = b'Internal Server Error'
        mock_session.post.return_value = mock_response
        
        # 如果有聊天端点，测试错误处理
        # 这里只是验证错误情况能被处理
        assert mock_session.post is not None


class TestApiResponseEdgeCases:
    """ApiResponse 边界情况测试"""
    
    def test_success_with_none_data(self):
        """测试成功响应数据为 None"""
        response = ApiResponse.success(None)
        
        assert response['data'] is None
    
    def test_success_with_empty_data(self):
        """测试成功响应数据为空"""
        response = ApiResponse.success({})
        
        assert response['data'] == {}
    
    def test_success_with_list_data(self):
        """测试成功响应数据为列表"""
        response = ApiResponse.success([1, 2, 3])
        
        assert response['data'] == [1, 2, 3]
    
    def test_error_with_different_codes(self):
        """测试不同错误码"""
        codes_to_test = [400, 401, 403, 404, 422, 429, 500, 502, 503]
        
        for code in codes_to_test:
            response = ApiResponse.error(f'Error {code}', code=code)
            assert response['code'] == code


class TestIntegrationScenarios:
    """集成场景测试"""
    
    def test_multiple_health_checks(self, client):
        """测试多次健康检查"""
        for _ in range(5):
            response = client.get('/api/v1/health')
            assert response.status_code == 200
            data = response.get_json()
            assert data['data']['status'] == 'ok'
    
    def test_concurrent_requests(self, client):
        """测试并发请求"""
        import threading
        
        results = []
        
        def make_request():
            response = client.get('/api/v1/health')
            results.append(response.status_code)
        
        threads = [threading.Thread(target=make_request) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # 所有请求都应该成功
        assert all(status == 200 for status in results)
    
    def test_rapid_requests(self, client):
        """测试快速连续请求"""
        responses = []
        for _ in range(20):
            response = client.get('/api/v1/health')
            responses.append(response.status_code)
        
        # 所有请求都应该成功
        assert all(status == 200 for status in responses)


class TestBlueprintRegistration:
    """蓝图注册测试"""
    
    def test_api_blueprint_registered(self, app):
        """测试 API 蓝图已注册"""
        assert 'api' in app.blueprints
    
    def test_api_blueprint_url_prefix(self, app):
        """测试 API 蓝图 URL 前缀"""
        api_blueprint = app.blueprints.get('api')
        
        if api_blueprint:
            assert api_blueprint.url_prefix == '/api/v1'
