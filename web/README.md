# clawweb — Web UI

## 简介

clawweb 是 clawtest 的 Web 管理界面，提供基于浏览器的 AutoDev AI 任务提交、监控与管理能力。后端为 Go + Gin，前端为 Vue 3 + Element Plus，通过 SQLite 持久化任务状态，支持本地进程与 Docker 两种部署模式。

---

## 目录结构

```
web/
├── deploy.sh                  # 一键部署脚本（本地 & Docker）
├── frontend/                  # Vue 3 前端源码
│   ├── src/
│   │   └── views/
│   │       └── AutoDevTool.vue
│   ├── package.json
│   └── vite.config.js
└── backend/                   # Go 后端
    ├── main.go                # 入口 + 路由注册
    ├── config.yaml            # 运行时配置（不入库）
    ├── config.yaml.example    # 配置模板（入库）
    ├── config/
    │   └── config.go          # 配置结构 & 加载逻辑
    ├── handlers/
    │   └── autodev.go         # API Handler
    ├── models/
    │   └── autodev.go         # 数据模型 & SQLite 操作
    ├── middleware/
    ├── utils/
    ├── static/                # 前端构建产物（由 deploy.sh 自动复制）
    │   ├── index.html
    │   └── assets/
    └── data/                  # 运行时数据（不入库）
        └── autodev/           # 任务工作目录
```

---

## 快速部署

### 前提条件

- Go 1.21+
- `autodev` 二进制已安装（需在 `config.yaml` 中指定路径）
- 前端静态文件已构建并放置在 `backend/static/`（`deploy.sh` 会自动处理）

### 本地模式（推荐，最简单）

```bash
cd web

./deploy.sh          # 停止旧进程 + 编译后端 + 启动
./deploy.sh stop     # 停止进程
```

启动成功后访问 `http://localhost:7991`（或配置的端口）。

日志路径：`/tmp/clawweb.log`

### Docker 模式

```bash
cd web

./deploy.sh docker          # 构建镜像 + 启动容器（自动挂载 ~/.claude）
./deploy.sh docker stop     # 停止并删除容器
./deploy.sh docker build    # 仅构建镜像，不启动
./deploy.sh docker start    # 仅启动容器（复用已有镜像）
```

### deploy.sh 完整参数表

| 命令 | 说明 |
|------|------|
| `./deploy.sh` | 本地模式：停止旧进程 + 编译 + 启动（默认） |
| `./deploy.sh stop` | 停止本地进程 |
| `./deploy.sh docker` | Docker 模式：构建镜像 + 启动容器 |
| `./deploy.sh docker stop` | 停止并删除 Docker 容器 |
| `./deploy.sh docker build` | 仅构建 Docker 镜像 |
| `./deploy.sh docker start` | 仅启动容器（不重新构建镜像） |

**deploy.sh 支持的环境变量**：

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `PORT` | `7991` | 服务监听端口（本地 & Docker 均有效） |
| `CLAUDE_HOME_MOUNT` | `~/.claude` | Docker 模式：宿主机 `.claude` 目录挂载源路径 |

---

## 手动部署

### 编译 & 运行后端

```bash
cd web/backend

# 确保 config.yaml 存在
cp config.yaml.example config.yaml
# 编辑 config.yaml，填写 admin_password 和 autodev_path

# 编译
go build -o clawweb .

# 启动
./clawweb
# 或指定配置文件路径
CONFIG_PATH=/path/to/config.yaml ./clawweb
```

### 前端开发

```bash
cd web/frontend

# 安装依赖
npm install

# 开发模式（热重载，代理到后端 :7991）
npm run dev

# 构建生产产物
npm run build

# 预览构建结果
npm run preview
```

构建产物输出至 `frontend/dist/`，需手动（或通过 `deploy.sh`）复制到 `backend/static/`。

---

## 配置文件参考

`backend/config.yaml` 完整注释版：

```yaml
server:
  # 服务监听端口，默认 8080；可被环境变量 PORT 覆盖
  port: "7991"
  # 运行模式：debug（开发，输出详细日志）或 release（生产，关闭调试日志）
  mode: "debug"

security:
  # 允许跨域的来源列表；"*" 表示允许所有来源
  # 生产环境建议改为具体域名，如 ["https://your-domain.com"]
  cors_origins:
    - "*"

autodev:
  # 访问密码（必填）
  # 安全起见建议通过环境变量传入：AUTODEV_PASSWORD=xxx，此处留空
  admin_password: ""

  # autodev 二进制的绝对路径（必填）
  # 可被环境变量 AUTODEV_PATH 覆盖
  autodev_path: "/opt/autodev/autodev"

  # 任务工作目录，存储每个任务的代码、日志、状态文件
  # 可被环境变量 AUTODEV_DATA_DIR 覆盖
  data_dir: "./data/autodev"

  # Claude Code 运行时的 HOME 目录（可选）
  # 本地模式：留空，自动使用当前用户的 $HOME（skills 开箱即用）
  # Docker 模式：设为容器内挂载路径，如 /home/autodev
  #   需配合 -v ~/.claude:/home/autodev/.claude 挂载
  # 可被环境变量 CLAUDE_HOME 覆盖
  # claude_home: ""
```

---

## Claude Skills 集成

### 原理

Claude Code 启动时读取 `$HOME/.claude/` 目录加载 skills（包括 CLAUDE.md、rules/、skills/ 等）。`claude_home` 配置项用于指定这个 HOME 目录。

### 本地模式

无需任何配置。`claude_home` 留空时，后端自动使用当前进程的 `$HOME`，即运行 `deploy.sh` 的用户的家目录。Skills 开箱即用。

### Docker 模式

容器内没有宿主机的家目录，需要显式挂载：

```bash
docker run -d \
  --name clawweb \
  --restart unless-stopped \
  -p 7991:7991 \
  -v /path/to/backend/config.yaml:/app/config.yaml:ro \
  -v /path/to/backend/data:/app/data \
  -v ~/.claude:/home/autodev/.claude:ro \
  -e CLAUDE_HOME=/home/autodev \
  -e AUTODEV_PASSWORD=your-password \
  clawweb:latest
```

关键点：
- `-v ~/.claude:/home/autodev/.claude:ro` — 将宿主机的 `.claude` 目录只读挂载到容器
- `-e CLAUDE_HOME=/home/autodev` — 告知后端 Claude Code 的 HOME 路径
- `config.yaml` 中 `claude_home` 也可设为 `/home/autodev`（环境变量优先级更高）

`deploy.sh docker` 命令已自动完成上述挂载，默认使用 `$HOME/.claude`，可通过 `CLAUDE_HOME_MOUNT` 环境变量覆盖：

```bash
CLAUDE_HOME_MOUNT=/custom/path/.claude ./deploy.sh docker
```

---

## 环境变量速查表

| 环境变量 | 对应配置字段 | 默认值 | 说明 |
|----------|-------------|--------|------|
| `PORT` | `server.port` | `7991` | 服务监听端口 |
| `AUTODEV_PASSWORD` | `autodev.admin_password` | — | 访问密码（优先级高于配置文件） |
| `AUTODEV_PATH` | `autodev.autodev_path` | `/opt/autodev/autodev` | autodev 二进制路径 |
| `AUTODEV_DATA_DIR` | `autodev.data_dir` | `./data/autodev` | 任务工作目录 |
| `CLAUDE_HOME` | `autodev.claude_home` | `""` (用 $HOME) | Claude Code 运行时 HOME 目录 |
| `CONFIG_PATH` | — | `./config.yaml` | 配置文件路径（仅后端启动时读取） |
| `DB_PATH` | — | `./data/autodev.db` | SQLite 数据库文件路径 |
| `CLAUDE_HOME_MOUNT` | — | `~/.claude` | deploy.sh Docker 模式专用：宿主机 .claude 挂载路径 |

所有环境变量均覆盖 `config.yaml` 中的对应字段（优先级：环境变量 > 配置文件 > 代码默认值）。

---

## API 接口

所有接口前缀：`/api/autodev/`

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/autodev/verify` | 验证访问密码 |

### 任务管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/autodev/tasks` | 提交新任务 |
| GET | `/api/autodev/tasks` | 获取任务列表 |
| GET | `/api/autodev/tasks/:id` | 获取任务详情 |
| GET | `/api/autodev/tasks/:id/state` | 获取任务运行状态 |
| GET | `/api/autodev/tasks/:id/logs` | 获取任务日志 |
| GET | `/api/autodev/tasks/:id/files` | 获取任务文件列表 |
| GET | `/api/autodev/tasks/:id/file` | 获取单个文件内容 |
| GET | `/api/autodev/tasks/:id/download` | 下载任务产物（ZIP） |
| GET | `/api/autodev/tasks/:id/site/*filepath` | 预览任务生成的静态站点 |
| POST | `/api/autodev/tasks/:id/stop` | 停止任务 |
| DELETE | `/api/autodev/tasks/:id` | 删除任务 |

### 项目与能力

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/autodev/projects` | 获取项目列表 |
| GET | `/api/autodev/capabilities` | 获取后端能力信息 |

### 对话与扩展

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/autodev/ask` | 提交追问（在已有任务上继续对话） |
| GET | `/api/autodev/ask/:id` | 获取追问结果 |
| POST | `/api/autodev/extend` | 扩展任务（延长超时 / 追加指令） |

### 项目初始化

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/autodev/init/stream` | 初始化项目（SSE 流式输出） |

### SSH Key

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/autodev/sshkey` | 获取当前 SSH 公钥 |
| POST | `/api/autodev/sshkey/regenerate` | 重新生成 SSH Key |

### Claude & clawtest 版本管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/autodev/claude/version` | 获取 Claude Code 版本 |
| GET | `/api/autodev/claude/test` | 测试 Claude 模型连通性 |
| GET | `/api/autodev/claude/update/stream` | 更新 Claude Code（SSE 流式） |
| GET | `/api/autodev/clawtest/version` | 获取 clawtest 版本 |
| GET | `/api/autodev/clawtest/update/stream` | 更新 clawtest（SSE 流式） |

---

## 常见问题

### 端口被占用如何处理

先停止旧进程，再重新启动：

```bash
./deploy.sh stop
./deploy.sh
```

或指定其他端口：

```bash
PORT=8080 ./deploy.sh
```

Docker 模式同理：

```bash
./deploy.sh docker stop
PORT=8080 ./deploy.sh docker
```

### Docker 里 skills 不生效怎么办

检查以下几点：

1. 确认宿主机 `~/.claude` 目录存在且包含 skills 文件；
2. 确认容器启动时挂载了该目录（`docker inspect clawweb` 查看 Mounts）；
3. 确认 `CLAUDE_HOME` 环境变量指向容器内挂载点的父目录（如 `/home/autodev`，而非 `/home/autodev/.claude`）；
4. 挂载使用 `:ro`（只读），确认宿主机目录有读权限。

用 `deploy.sh docker` 启动时，上述配置已自动完成。若手动 `docker run`，参考"Claude Skills 集成 - Docker 模式"章节的完整命令。

### config.yaml 不存在怎么办

`deploy.sh` 会自动检测：若 `backend/config.yaml` 不存在，则从 `backend/config.yaml.example` 复制一份。

手动处理：

```bash
cd web/backend
cp config.yaml.example config.yaml
# 编辑 config.yaml，至少填写：
#   autodev.admin_password  — 访问密码
#   autodev.autodev_path    — autodev 二进制路径
```

也可以完全跳过配置文件，通过环境变量传入关键参数：

```bash
AUTODEV_PASSWORD=yourpassword AUTODEV_PATH=/usr/local/bin/autodev ./clawweb
```
