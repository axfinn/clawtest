# Deployment Guide

## 环境要求

| 环境 | 要求 |
|------|------|
| Python | 3.8+ |
| 数据库 | SQLite (开发) / PostgreSQL (生产) |
| 内存 | 至少 512MB |
| 系统 | Linux / macOS / Windows |

---

## 本地开发

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/clawtest.git
cd clawtest
```

### 2. 创建虚拟环境

```bash
# 使用 venv
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 或使用 conda
conda create -n clawtest python=3.10
conda activate clawtest
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# Linux/macOS
export SECRET_KEY="your-secret-key-here"
export DATABASE_URL="sqlite:///app.db"
export MINIMAX_API_KEY="your-minimax-api-key"

# Windows (PowerShell)
$env:SECRET_KEY="your-secret-key-here"
$env:DATABASE_URL="sqlite:///app.db"
$env:MINIMAX_API_KEY="your-minimax-api-key"
```

### 5. 运行开发服务器

```bash
python -m src.app
```

服务将在 `http://localhost:5000` 启动。

### 6. 运行测试

```bash
pytest
# 或带覆盖率
pytest --cov=src
```

---

## Docker 部署

### 1. 构建镜像

```bash
docker build -t clawtest:latest .
```

### 2. 运行容器

```bash
docker run -d \
  --name clawtest \
  -p 5000:5000 \
  -e SECRET_KEY="your-secret-key" \
  -e DATABASE_URL="sqlite:///app.db" \
  -e MINIMAX_API_KEY="your-api-key" \
  clawtest:latest
```

### 3. 使用 Docker Compose

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - MINIMAX_API_KEY=${MINIMAX_API_KEY}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

启动服务:

```bash
docker-compose up -d
```

---

## 生产环境配置

### 1. 环境要求

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 1 Core | 2+ Cores |
| 内存 | 512MB | 1GB+ |
| 磁盘 | 5GB | 20GB+ |

### 2. PostgreSQL 数据库配置

```bash
# 安装 PostgreSQL (Ubuntu)
sudo apt update
sudo apt install postgresql postgresql-contrib

# 创建数据库
sudo -u postgres createdb clawtest
sudo -u postgres createuser clawtest_user
sudo -u postgres psql -c "ALTER USER clawtest_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE clawtest TO clawtest_user;"
```

### 3. 生产环境变量

```bash
# 必需的环境变量
export SECRET_KEY="生成一个强随机密钥"
export DATABASE_URL="postgresql://clawtest_user:password@localhost:5432/clawtest"
export MINIMAX_API_KEY="your-production-api-key"
export FLASK_ENV="production"
```

生成安全密钥:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. 使用 Gunicorn 运行

```bash
pip install gunicorn

# 运行 (4 个 worker 进程)
gunicorn -w 4 -b 0.0.0.0:5000 "src.app:create_app()"
```

创建 `gunicorn.conf.py`:

```python
import multiprocessing

bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 120
keepalive = 5

# 日志
accesslog = "-"
errorlog = "-"
loglevel = "info"

# 进程名
proc_name = "clawtest"
```

启动:

```bash
gunicorn -c gunicorn.conf.py "src.app:create_app()"
```

### 5. Nginx 反向代理

安装 Nginx:

```bash
sudo apt install nginx
```

创建配置文件 `/etc/nginx/sites-available/clawtest`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }

    # 静态文件 (如果有)
    location /static {
        alias /var/www/clawtest/static;
    }
}
```

启用站点:

```bash
sudo ln -s /etc/nginx/sites-available/clawtest /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. HTTPS 配置 (Let's Encrypt)

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期测试
sudo certbot renew --dry-run
```

### 7. Systemd 服务 (Linux)

创建 `/etc/systemd/system/clawtest.service`:

```ini
[Unit]
Description=Clawtest AI Service
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/clawtest
Environment="PATH=/opt/clawtest/venv/bin"
Environment="SECRET_KEY=your-secret-key"
Environment="DATABASE_URL=postgresql://..."
Environment="MINIMAX_API_KEY=..."
ExecStart=/opt/clawtest/venv/bin/gunicorn -c gunicorn.conf.py "src.app:create_app()"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务:

```bash
sudo systemctl daemon-reload
sudo systemctl enable clawtest
sudo systemctl start clawtest
```

---

## 性能优化

### 1. 数据库连接池

使用 ProductionConfig:

```python
class ProductionConfig(Config):
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }
```

### 2. 缓存

可以使用 Flask-Caching:

```bash
pip install flask-caching redis
```

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'RedisCache', 
                            'CACHE_REDIS_URL': 'redis://localhost:6379/0'})
```

### 3. 限流

使用 Flask-Limiter:

```bash
pip install flask-limiter
```

```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=get_remote_address)

@app.route("/api/v1/chat", methods=["POST"])
@limiter.limit("10/minute")
def chat():
    ...
```

---

## 监控与日志

### 1. 日志配置

```python
import logging

if not app.debug:
    logging.basicConfig(
        filename='app.log',
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )
```

### 2. 健康检查端点

确保负载均衡器和监控使用 `/api/v1/health` 端点。

---

## 备份与恢复

### 数据库备份

```bash
# PostgreSQL
pg_dump -U clawtest_user -h localhost clawtest > backup_$(date +%Y%m%d).sql

# 恢复
psql -U clawtest_user -h localhost clawtest < backup_20240101.sql
```

---

## 故障排查

| 问题 | 解决方案 |
|------|----------|
| 502 Bad Gateway | 检查 Gunicorn 是否运行 |
| 连接数据库失败 | 验证 DATABASE_URL 配置 |
| API 调用失败 | 检查 MINIMAX_API_KEY |
| 内存不足 | 增加 worker 内存或减少并发 |
| 超时错误 | 增加 Gunicorn timeout |
