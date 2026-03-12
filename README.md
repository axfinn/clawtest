# 创建一个智能AI对话工具，使用系统

[![CI](https://github.com/${{ github.repository }}/actions/workflows/ci.yml/badge.svg)](https://github.com/${{ github.repository }}/actions/workflows/ci.yml)
[![PyPI Version](https://img.shields.io/pypi/v/clawtest)](https://pypi.org/project/clawtest/)
[![Docker Pulls](https://img.shields.io/docker/pulls/${{ secrets.DOCKERHUB_USERNAME }}/clawtest)](https://hub.docker.com/r/${{ secrets.DOCKERHUB_USERNAME }}/clawtest)
[![License](https://img.shields.io/pypi/l/clawtest)](https://github.com/${{ github.repository }}/blob/main/LICENSE)
[![Python Versions](https://img.shields.io/pypi/pyversions/clawtest)](https://pypi.org/project/clawtest/)

## 技术栈

- 语言: Python
- 框架: Flask
- 数据库: SQLite (开发) / PostgreSQL (生产)

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python -m src.app

# 测试
pytest
```

## API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
