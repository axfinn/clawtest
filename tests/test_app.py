"""基本测试"""

import pytest
from app import create_app
from models import db


@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """测试客户端"""
    return app.test_client()


def test_health_check(client):
    """测试健康检查"""
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 200


def test_create_user(client):
    """测试创建用户"""
    response = client.post('/api/v1/users', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['code'] == 200
    assert data['data']['username'] == 'testuser'


def test_get_users(client):
    """测试获取用户列表"""
    response = client.get('/api/v1/users')
    assert response.status_code == 200
    data = response.get_json()
    assert 'users' in data['data']
