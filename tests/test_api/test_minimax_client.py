# -*- coding: utf-8 -*-
"""
MiniMaxClient 测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api.minimax import MiniMaxClient


class TestMiniMaxClient:
    """MiniMaxClient 测试类"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return MiniMaxClient(api_key="test-api-key", model="MiniMax-M2.5")
    
    @pytest.fixture
    def mock_response(self):
        """Mock API 响应"""
        mock = Mock()
        mock.status_code = 200
        mock.json.return_value = {
            "content": [{"text": "Hello, this is a test response"}]
        }
        return mock
    
    # === 正常情况测试 ===
    
    def test_client_initialization(self, client):
        """测试客户端初始化"""
        assert client.api_key == "test-api-key"
        assert client.model == "MiniMax-M2.5"
        assert client.max_tokens == 8192
        assert client.BASE_URL == "https://api.minimaxi.com/anthropic"
    
    def test_client_initialization_with_env(self):
        """测试使用环境变量的初始化"""
        with patch.dict(os.environ, {"MINIMAX_API_KEY": "env-api-key"}):
            client = MiniMaxClient()
            assert client.api_key == "env-api-key"
    
    def test_set_model(self, client):
        """测试切换模型"""
        client.set_model("MiniMax-M2.1")
        assert client.model == "MiniMax-M2.1"
        
        client.set_model("MiniMax-M2.5")
        assert client.model == "MiniMax-M2.5"
    
    def test_get_available_models(self):
        """测试获取可用模型"""
        models = MiniMaxClient.get_available_models()
        assert "MiniMax-M2.1" in models
        assert "MiniMax-M2.5" in models
        assert len(models) == 2
    
    @patch('api.minimax.requests.Session')
    def test_chat_success(self, mock_session_class, client, mock_response):
        """测试正常聊天"""
        # Mock session
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.post.return_value = mock_response
        
        result = client.chat("Hello")
        
        assert result == "Hello, this is a test response"
        mock_session.post.assert_called_once()
    
    @patch('api.minimax.requests.Session')
    def test_chat_with_history(self, mock_session_class, client, mock_response):
        """测试带历史记录的聊天"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.post.return_value = mock_response
        
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello"}
        ]
        
        result = client.chat("How are you?", history=history)
        
        # 验证历史消息被正确添加
        call_args = mock_session.post.call_args
        json_data = call_args[1]['json']
        
        assert len(json_data['messages']) == 3  # 2条历史 + 1条当前
        assert json_data['messages'][0]['role'] == "user"
        assert json_data['messages'][0]['content'] == "Hi"
        assert json_data['messages'][1]['role'] == "assistant"
        assert json_data['messages'][1]['content'] == "Hello"
        assert json_data['messages'][2]['role'] == "user"
        assert json_data['messages'][2]['content'] == "How are you?"
    
    # === 异常情况测试 ===
    
    @patch('api.minimax.requests.Session')
    def test_chat_api_error(self, mock_session_class, client):
        """测试 API 错误处理"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Mock 错误响应
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_session.post.return_value = mock_response
        
        with pytest.raises(Exception) as exc_info:
            client.chat("Hello")
        
        assert "API Error" in str(exc_info.value)
        assert "Internal Server Error" in str(exc_info.value)
    
    @patch('api.minimax.requests.Session')
    def test_chat_timeout_error(self, mock_session_class, client):
        """测试超时错误"""
        import requests
        
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.post.side_effect = requests.Timeout("Request timeout")
        
        with pytest.raises(requests.Timeout):
            client.chat("Hello")
    
    @patch('api.minimax.requests.Session')
    def test_chat_connection_error(self, mock_session_class, client):
        """测试连接错误"""
        import requests
        
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.post.side_effect = requests.ConnectionError("Connection failed")
        
        with pytest.raises(requests.ConnectionError):
            client.chat("Hello")
    
    @patch('api.minimax.requests.Session')
    def test_chat_invalid_json_response(self, mock_session_class, client):
        """测试无效 JSON 响应"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_session.post.return_value = mock_response
        
        with pytest.raises(ValueError):
            client.chat("Hello")
    
    @patch('api.minimax.requests.Session')
    def test_chat_missing_content(self, mock_session_class, client):
        """测试响应缺少 content 字段"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"content": []}  # 空 content
        mock_session.post.return_value = mock_response
        
        with pytest.raises(KeyError):
            client.chat("Hello")
    
    @patch('api.minimax.requests.Session')
    def test_chat_invalid_model_response(self, mock_session_class, client):
        """测试响应中模型不匹配"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"text": "Response"}],
            "model": "wrong-model"  # 模型不匹配
        }
        mock_session.post.return_value = mock_response
        
        # 应该正常返回，不抛出异常
        result = client.chat("Hello")
        assert result == "Response"
    
    def test_chat_empty_message(self, client):
        """测试空消息"""
        with patch.object(client.session, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "content": [{"text": "Response"}]
            }
            mock_post.return_value = mock_response
            
            result = client.chat("")
            
            assert result == "Response"
            # 验证发送的请求
            call_args = mock_post.call_args
            json_data = call_args[1]['json']
            assert len(json_data['messages']) == 1
            assert json_data['messages'][0]['content'] == ""
    
    def test_session_headers(self, client):
        """测试会话头"""
        assert "Content-Type" in client.session.headers
        assert client.session.headers["Content-Type"] == "application/json"
        assert "Authorization" in client.session.headers
        assert client.session.headers["Authorization"] == "Bearer test-api-key"
    
    @patch('api.minimax.requests.Session')
    def test_chat_request_timeout_configured(self, mock_session_class, client):
        """测试请求超时配置"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"text": "Response"}]
        }
        mock_session.post.return_value = mock_response
        
        client.chat("Test")
        
        # 验证超时配置
        call_args = mock_session.post.call_args
        assert call_args[1]['timeout'] == 120


class TestMiniMaxClientEdgeCases:
    """MiniMaxClient 边界情况测试"""
    
    @patch('api.minimax.requests.Session')
    def test_very_long_message(self, mock_session_class):
        """测试非常长的消息"""
        client = MiniMaxClient(api_key="test-key")
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"text": "Response"}]
        }
        mock_session.post.return_value = mock_response
        
        long_message = "a" * 10000  # 10k 字符
        result = client.chat(long_message)
        
        assert result == "Response"
    
    @patch('api.minimax.requests.Session')
    def test_very_long_history(self, mock_session_class):
        """测试非常长的历史记录"""
        client = MiniMaxClient(api_key="test-key")
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"text": "Response"}]
        }
        mock_session.post.return_value = mock_response
        
        # 100 条历史记录
        long_history = [
            {"role": "user", "content": f"Message {i}"}
            for i in range(100)
        ]
        
        result = client.chat("Current message", history=long_history)
        
        assert result == "Response"
        call_args = mock_session.post.call_args
        json_data = call_args[1]['json']
        assert len(json_data['messages']) == 101  # 100历史 + 1当前
    
    def test_custom_max_tokens(self):
        """测试自定义 max_tokens"""
        client = MiniMaxClient(api_key="test-key", model="MiniMax-M2.5")
        # 在初始化后设置 max_tokens
        client.max_tokens = 4096
        
        with patch.object(client.session, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "content": [{"text": "Response"}]
            }
            mock_post.return_value = mock_response
            
            client.chat("Test")
            
            call_args = mock_post.call_args
            json_data = call_args[1]['json']
            assert json_data['max_tokens'] == 4096
