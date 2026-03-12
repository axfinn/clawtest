# Clawtest - 智能 AI 对话工具

[![CI](https://github.com/${{ github.repository }}/actions/workflows/ci.yml/badge.svg)](https://github.com/${{ github.repository }}/actions/workflows/ci.yml)
[![PyPI Version](https://img.shields.io/pypi/v/clawtest)](https://pypi.org/project/clawtest/)
[![Docker Pulls](https://img.shields.io/docker/pulls/${{ secrets.DOCKERHUB_USERNAME }}/clawtest)](https://hub.docker.com/r/${{ secrets.DOCKERHUB_USERNAME }}/clawtest)
[![License](https://img.shields.io/pypi/l/clawtest)](https://github.com/${{ github.repository }}/blob/main/LICENSE)
[![Python Versions](https://img.shields.io/pypi/pyversions/clawtest)](https://pypi.org/project/clawtest/)

Clawtest 是一个基于 MiniMax API 的智能 AI 对话工具，支持对话和自动代码执行功能。

## 特性

- 🤖 AI 对话 - 基于 MiniMax M2.1/M2.5 模型
- ⚡ 代码执行 - 支持 Python、JavaScript、Bash
- 🔌 RESTful API - 易于集成
- 🐳 Docker 支持
- 📦 生产级部署配置

## 技术栈

- **语言**: Python 3.8+
- **框架**: Flask
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **API**: MiniMax API

## 快速开始

```bash
# 克隆项目
git clone https://github.com/yourusername/clawtest.git
cd clawtest

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
export SECRET_KEY="your-secret-key"
export MINIMAX_API_KEY="your-minimax-api-key"

# 运行
python -m src.app

# 测试
pytest
```

服务运行在 `http://localhost:5000`

## API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查 |
| POST | `/api/v1/chat` | AI 对话 |
| POST | `/api/v1/execute` | 代码执行 |
| GET | `/api/v1/models` | 获取可用模型 |

详细 API 文档请查看 [API.md](docs/API.md)

## 文档

- [API 文档](docs/API.md) - 完整的 API 参考
- [部署指南](docs/DEPLOY.md) - 本地开发、Docker、生产环境
- [变更日志](docs/CHANGELOG.md) - 版本历史
- [贡献指南](docs/CONTRIBUTING.md) - 如何贡献代码
- [许可证](LICENSE) - MIT 许可证

## 项目结构

```
clawtest/
├── src/
│   ├── __init__.py
│   ├── app.py           # Flask 应用入口
│   ├── routes.py        # API 路由
│   ├── models.py        # 数据模型
│   ├── services.py      # 业务逻辑
│   ├── api/
│   │   └── minimax.py   # MiniMax API 客户端
│   └── handlers/
│       └── codeExecutor.py  # 代码执行器
├── tests/               # 测试用例
├── docs/                # 文档
├── config.py            # 配置文件
├── requirements.txt     # Python 依赖
└── LICENSE              # MIT 许可证
```

## Docker 部署

```bash
# 构建镜像
docker build -t clawtest:latest .

# 运行容器
docker run -d -p 5000:5000 \
  -e SECRET_KEY="your-secret-key" \
  -e MINIMAX_API_KEY="your-api-key" \
  clawtest:latest
```

或使用 Docker Compose:

```bash
docker-compose up -d
```

详细部署说明请查看 [DEPLOY.md](docs/DEPLOY.md)

## 配置

| 环境变量 | 描述 | 默认值 |
|----------|------|--------|
| SECRET_KEY | 应用密钥 | dev-secret-key |
| DATABASE_URL | 数据库连接 | sqlite:///app.db |
| MINIMAX_API_KEY | MiniMax API 密钥 | - |
| FLASK_ENV | 运行环境 | development |

## 测试

```bash
# 运行所有测试
pytest

# 带覆盖率
pytest --cov=src --cov-report=html
```

## 许可证

本项目基于 MIT 许可证 - 查看 [LICENSE](LICENSE) 了解详情

---

欢迎贡献代码！请查看 [贡献指南](docs/CONTRIBUTING.md) 了解如何参与项目开发。
