# AutoDev 🤖

万能任务助手 — 基于 Claude CLI，支持全流程自驱开发、持续追问和迭代加需求。

---

## 核心能力

| 模式 | 命令 | 适合场景 |
|------|------|---------|
| **全流程开发** | `autodev "任务"` | 新项目，走完整 6 阶段 |
| **初始化上下文** | `autodev init` | 项目完成后执行，生成 CLAUDE.md 锁定上下文 |
| **持续追问** | `autodev ask "问题"` | 已有项目，追问/小任务 |
| **迭代加需求** | `autodev extend "新需求"` | 已有项目，追加功能持续开发 |
| **断点恢复** | `autodev "任务" --from N` | 某阶段失败后重跑 |
| **文档发布** | `autodev "任务" --publish` | 生成 MkDocs 文档站 |
| **Web UI** | `./clawweb` | 浏览器图形化管理任务 |

---

## 快速开始

### 1. 全流程开发（新项目）

```bash
# 自动生成目录（/tmp/autodev/<名称>-<时间戳>/）
python3 autodev/driver.py "用 Flask 实现 JWT 认证"

# 指定固定目录（便于后续追问/迭代）
python3 autodev/driver.py "用 Flask 实现 JWT 认证" --path ./projects/auth

# 后台运行，不怕终端断开
python3 autodev/driver.py "任务描述" --path ./projects/myapp --bg
```

流程：`DISCOVER → DEFINE → DESIGN → DO → REVIEW → DELIVER`

---

### 2. 持续追问（ask）

在**已有项目目录**里追问问题或执行小任务，自动注入项目历史上下文。

```bash
# 追问问题
python3 autodev/driver.py ask "这里为什么用 JWT 而不是 Session？" --path ./projects/auth

# 执行小任务
python3 autodev/driver.py ask "帮我加 login 接口的单元测试" --path ./projects/auth
python3 autodev/driver.py ask "给 /api/user 加限流，每分钟 60 次" --path ./projects/auth

# 后台执行
python3 autodev/driver.py ask "优化数据库查询" --path ./projects/auth --bg
```

- 每次问答自动追加到 `process/qa.md`，带编号和时间戳
- Claude 自动读取 `process/` 下的设计文档、执行记录作为背景

---

### 3. 初始化项目上下文（init）

项目完成（或任意时间）执行一次，扫描项目生成 `CLAUDE.md`，让后续 `ask`/`extend` 冷启动时直接有完整上下文，**避免每次重复调研和安装依赖**。

```bash
python3 autodev/driver.py init --path ./projects/auth
```

生成的 `CLAUDE.md` 包含：
- 技术栈和已安装依赖（Claude 不会重复 `pip install` / `npm install`）
- 项目文件列表（不重新 Glob 扫描）
- `process/` 各阶段文档摘要（不重复 WebSearch 调研）
- 迭代历史记录

> 建议：每次 `extend` 后重跑一次 `init` 刷新文件列表和迭代记录。

---

### 4. 迭代追加需求（extend）

```bash
# 第一次迭代：加新功能
python3 autodev/driver.py extend "加 OAuth2 Google 登录" --path ./projects/auth

# 第二次迭代：继续加
python3 autodev/driver.py extend "支持多租户，每个租户独立数据库" --path ./projects/auth

# 第三次迭代
python3 autodev/driver.py extend "加 Prometheus 监控接口" --path ./projects/auth
```

- 每次迭代结果写入 `process/iter-N/result.md`
- 主报告 `RESULT.md` 自动追加本次迭代摘要
- 最小改动原则：只改必须改的代码，不重构无关部分

---

### 5. 断点恢复

```bash
# 从第 4 阶段（DO）重跑
python3 autodev/driver.py "任务" --path /tmp/autodev/xxx --from 4
```

阶段编号：1=DISCOVER，2=DEFINE，3=DESIGN，4=DO，5=REVIEW，6=DELIVER

---

### 6. 文档发布

```bash
# 生成 MkDocs 文档站
python3 autodev/driver.py "任务" --path ./projects/myapp --publish

# 预览文档
python3 autodev/driver.py serve --path ./projects/myapp --port 8000
```

---

## 项目目录结构

运行后，每个项目目录的结构：

```
./projects/auth/
├── CLAUDE.md              # init 生成的项目上下文（冷启动用）
├── RESULT.md              # 主交付报告（每次迭代自动追加）
├── process/
│   ├── 01-discover.md     # 调研结果
│   ├── 02-define.md       # 问题定义
│   ├── 03-design.md       # 架构设计
│   ├── 04-do.md           # 执行记录
│   ├── 05-review.md       # 质量审查
│   ├── qa.md              # 所有追问记录（ask 命令追加）
│   ├── iter-1/            # 第一次迭代（extend 命令）
│   │   ├── design.md
│   │   └── result.md
│   └── iter-2/            # 第二次迭代
│       ├── design.md
│       └── result.md
└── .autodev/
    └── logs/              # 各阶段详细日志
```

---

## 典型工作流

```bash
# 1. 启动项目
python3 autodev/driver.py "用 Go 实现 Redis 分布式锁" --path ./projects/redis-lock

# 2. 初始化上下文（避免后续重复调研/安装依赖）
python3 autodev/driver.py init --path ./projects/redis-lock

# 3. 持续追问
python3 autodev/driver.py ask "解释一下 Lua 脚本原子解锁的实现" --path ./projects/redis-lock
python3 autodev/driver.py ask "帮我补全 benchmark 测试" --path ./projects/redis-lock

# 4. 加新需求
python3 autodev/driver.py extend "加看门狗自动续期功能" --path ./projects/redis-lock
python3 autodev/driver.py init --path ./projects/redis-lock  # 更新上下文
python3 autodev/driver.py extend "支持可重入锁" --path ./projects/redis-lock

# 5. 发布文档
python3 autodev/driver.py serve --path ./projects/redis-lock
```

---

## Web UI

基于 Go + Gin 后端、Vue 3 前端的图形化界面，用于在浏览器中管理 autodev 任务的全生命周期。

---

### 目录结构

```
web/
├── deploy.sh             # 一键部署脚本（本地 / Docker）
├── Dockerfile            # Docker 镜像定义
├── backend/              # Go + Gin 后端
│   ├── main.go          # 入口
│   ├── handlers/        # HTTP 处理函数
│   ├── models/          # 数据模型和 SQLite
│   ├── config/          # 配置加载
│   ├── middleware/      # 中间件
│   ├── static/          # 编译后的前端资源（前端 build 输出）
│   ├── config.yaml.example  # 配置模板
│   └── go.mod
└── frontend/            # Vue 3 + Vite 前端源码
    ├── src/
    │   ├── views/AutoDevTool.vue
    │   ├── composables/
    │   └── router/
    ├── package.json
    └── vite.config.js
```

---

### 快速启动（本地模式）

```bash
# 复制配置（首次）
cp web/backend/config.yaml.example web/backend/config.yaml
# 按需编辑 config.yaml，填写 admin_password 和 autodev_path

# 一键构建 + 启动
./web/deploy.sh

# 访问
open http://localhost:7991
```

---

### deploy.sh 完整用法

| 命令 | 说明 |
|------|------|
| `./web/deploy.sh` | 本地模式：停止旧进程 + 构建 Go 二进制 + 后台启动 |
| `./web/deploy.sh stop` | 停止本地进程 |
| `./web/deploy.sh docker` | Docker 模式：构建镜像 + 启动容器 |
| `./web/deploy.sh docker stop` | 停止并删除 Docker 容器 |
| `./web/deploy.sh docker build` | 仅构建 Docker 镜像 |
| `./web/deploy.sh docker start` | 仅启动容器（不重新构建镜像） |

**支持的环境变量**：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PORT` | `7991` | 监听端口（本地和 Docker 均有效） |
| `CLAUDE_HOME_MOUNT` | `~/.claude` | Docker 模式下挂载到容器的 `.claude` 目录 |

日志文件：`/tmp/clawweb.log`（本地模式）

---

### config.yaml 配置参考

完整配置模板见 `web/backend/config.yaml.example`：

```yaml
server:
  port: "7991"      # 监听端口，优先级低于环境变量 PORT
  mode: "debug"     # debug | release

security:
  cors_origins:
    - "*"           # 允许的跨域来源，生产环境建议指定域名

autodev:
  admin_password: ""      # 必填。建议通过环境变量 AUTODEV_PASSWORD 传入
  autodev_path: ""        # 必填。autodev driver.py 所在目录的绝对路径
  data_dir: "./data/autodev"  # 任务数据存储目录

  # claude_home 说明（见下节"Claude Skills 支持"）
  # claude_home: ""
```

其他环境变量：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `CONFIG_PATH` | `./config.yaml` | 配置文件路径 |
| `DB_PATH` | `./data/autodev.db` | SQLite 数据库路径 |
| `CLAUDE_HOME` | — | 覆盖 `claude_home` 配置（优先级更高） |

---

### Claude Skills 支持

Web UI 在执行任务时会将 `claude_home` 作为 Claude Code 的 `HOME` 目录，从而加载对应的 Skills（`~/.claude/`）。

**本地模式（推荐）**：

`claude_home` 留空，后端自动使用 `$HOME`，开箱即用：

```yaml
autodev:
  # claude_home: ""  # 留空即可，自动使用 $HOME/.claude/
```

**Docker 模式**：

容器内 Claude Code 的 `HOME` 需要显式指定，并挂载宿主机的 `.claude` 目录：

```yaml
autodev:
  claude_home: "/home/autodev"
```

`deploy.sh docker` 会自动完成以下挂载：

```
~/.claude  →  /home/autodev/.claude  (只读)
```

也可以用环境变量覆盖（优先级高于配置文件）：

```bash
CLAUDE_HOME=/home/autodev ./web/deploy.sh docker
```

---

### Docker 手动部署

如需在不使用 `deploy.sh` 的情况下手动部署：

```bash
# 1. 构建镜像（在项目根目录执行）
docker build -t clawweb:latest -f web/Dockerfile .

# 2. 启动容器
docker run -d \
  --name clawweb \
  --restart unless-stopped \
  -p 7991:7991 \
  -v "$(pwd)/web/backend/config.yaml:/app/config.yaml:ro" \
  -v "$(pwd)/web/backend/data:/app/data" \
  -v "$HOME/.claude:/home/autodev/.claude:ro" \
  -e CLAUDE_HOME=/home/autodev \
  clawweb:latest

# 查看日志
docker logs -f clawweb
```

---

### 前端开发

```bash
cd web/frontend
npm install
npm run dev      # 开发服务器（热重载，默认 :5173，代理 API 到 :7991）
npm run build    # 生产构建，输出到 ../backend/static/
```

---

### API 路由表

所有接口均以 `/api/autodev` 为前缀：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/autodev/verify` | 验证管理员密码 |
| GET | `/api/autodev/capabilities` | 查询后端能力（版本/功能） |
| POST | `/api/autodev/tasks` | 提交新任务（全流程开发） |
| GET | `/api/autodev/tasks` | 列出所有任务 |
| GET | `/api/autodev/projects` | 列出所有项目目录 |
| GET | `/api/autodev/tasks/:id` | 获取任务详情 |
| GET | `/api/autodev/tasks/:id/state` | 获取任务运行状态 |
| GET | `/api/autodev/tasks/:id/logs` | 获取任务日志（实时） |
| GET | `/api/autodev/tasks/:id/files` | 列出任务输出文件 |
| GET | `/api/autodev/tasks/:id/file` | 读取指定文件内容 |
| GET | `/api/autodev/tasks/:id/download` | 下载任务输出（ZIP） |
| GET | `/api/autodev/tasks/:id/site/*filepath` | 访问发布的文档站 |
| POST | `/api/autodev/tasks/:id/stop` | 停止运行中的任务 |
| DELETE | `/api/autodev/tasks/:id` | 删除任务记录 |
| POST | `/api/autodev/ask` | 提交追问（ask） |
| GET | `/api/autodev/ask/:id` | 获取追问结果 |
| POST | `/api/autodev/extend` | 提交迭代需求（extend） |
| GET | `/api/autodev/init/stream` | 初始化项目上下文（流式） |
| GET | `/api/autodev/sshkey` | 获取 SSH 公钥 |
| POST | `/api/autodev/sshkey/regenerate` | 重新生成 SSH 密钥对 |
| GET | `/api/autodev/claude/version` | 查询 Claude CLI 版本 |
| GET | `/api/autodev/claude/test` | 测试 Claude 模型连通性 |
| GET | `/api/autodev/claude/update/stream` | 更新 Claude CLI（流式） |
| GET | `/api/autodev/clawtest/version` | 查询 clawtest 版本 |
| GET | `/api/autodev/clawtest/update/stream` | 更新 clawtest（流式） |

---

## 配置

Claude CLI 配置：`~/.claude/settings.json`

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.minimaxi.com/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "your-token",
    "ANTHROPIC_MODEL": "MiniMax-M2.5"
  }
}
```

---

## License

MIT
