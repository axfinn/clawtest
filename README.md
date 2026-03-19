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

项目包含一个 Web UI（clawweb），提供图形化界面管理 autodev 任务。

### 目录结构

```
web/
├── backend/              # Go + Gin 后端
│   ├── main.go          # 入口
│   ├── handlers/        # HTTP 处理函数
│   ├── models/          # 数据模型和 SQLite
│   ├── config/          # 配置加载
│   ├── middleware/      # 中间件
│   ├── static/          # 编译后的前端资源
│   ├── go.mod
│   └── clawweb          # 编译好的二进制（已排除在版本控制外）
└── frontend/            # Vue 3 + Vite 前端源码
    ├── src/
    │   ├── views/AutoDevTool.vue
    │   ├── composables/
    │   └── router/
    ├── package.json
    └── vite.config.js
```

### 启动后端

```bash
cd web/backend
go build -o clawweb .
./clawweb
# 默认监听 0.0.0.0:7991
```

环境变量：
- `PORT`：监听端口（默认 7991）
- `CONFIG_PATH`：配置文件路径（默认 ./config.yaml）
- `DB_PATH`：SQLite 数据库路径（默认 ./data/autodev.db）

### 前端开发

```bash
cd web/frontend
npm install
npm run dev      # 开发模式
npm run build    # 生产构建（输出到 ../backend/static/）
```

### 访问

启动后端后，访问 `http://<主机IP>:7991/static/` 使用 Web UI。

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
