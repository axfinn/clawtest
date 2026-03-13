# AutoDev

无监管万能任务助手。给它一句话需求，它自主完成并交付结果。

```bash
./autodev "写一份 Redis 集群最佳实践文档" --publish --push --serve
./autodev "用 Go 实现一个 HTTP 文件服务器" --build --push
./autodev "分析 sales.csv 找出增长趋势"
```

## 工作方式

Python 调度流程，每个阶段调用 `claude` CLI 独立完成。

```
DISCOVER → DEFINE → DESIGN → DO → REVIEW → DELIVER
```

| 阶段 | 做什么 |
|------|--------|
| DISCOVER | WebSearch 调研 + 扫描现有文件 |
| DEFINE | 追问 Why/What，明确成功标准 |
| DESIGN | 选方案，写执行计划 |
| DO | 全力执行，直接操作文件（**自动注入匹配的本地 skills**） |
| REVIEW | 对照标准验证，发现问题直接修复（自动注入 simplify 等 skills） |
| DELIVER | 生成 RESULT.md + git commit（自动注入 live-dev/sync 等 skills） |

可选扩展阶段（通过参数触发）：

| 参数 | 阶段 | 说明 |
|------|------|------|
| `--build` | BUILD | 编译构建，生成二进制/产物 |
| `--publish` | PUBLISH | 生成 MkDocs 文档站 + PDF（**自动安装 mkdocs**） |
| `--push` | — | 完成后无确认直接 `git push` 到远端 |
| `--serve` | — | `--publish` 完成后自动启动本地预览服务器 |

## 安装

无需安装，依赖只有两个：

```bash
# 1. Python 3.10+
python3 --version

# 2. Claude Code CLI（已登录）
claude --version
```

```bash
git clone git@github.com:axfinn/clawtest.git
cd clawtest/autodev
chmod +x autodev
```

## 使用

```bash
# 最简（目录自动生成到 /tmp/autodev/<名称>-<时间>/）
./autodev "任务描述"

# 指定输出目录
./autodev "任务描述" --path ./output

# 文档类任务 → 自动生成文档站（mkdocs 没装会自动安装）
./autodev "写 K8s 入门手册" --publish

# 完成后预览文档（--serve 启动本地服务器，监听 0.0.0.0:8000）
./autodev "写 K8s 入门手册" --publish --serve

# 完成后直接推送到远端（无需确认）
./autodev "任务描述" --push

# 全家桶：文档 + 推送 + 预览
./autodev "写 Redis 最佳实践" --publish --push --serve

# 需要编译的项目
./autodev "用 Rust 写 CLI 工具" --build

# 断点恢复（从第 4 阶段 DO 开始）
./autodev "任务描述" --path /tmp/autodev/xxx --from 4

# 查看所有可用的本地 skills
./autodev --list-skills
```

## Skills 自动集成

AutoDev 会自动扫描本地 Claude Code skills，在合适的阶段注入到 prompt 中。

**Skills 来源**（按优先级，项目级覆盖全局）：
```
~/.claude/commands/*.md         # 全局 skills
<project>/.claude/commands/*.md # 项目级 skills
```

**查看当前可用 skills：**
```bash
./autodev --list-skills
```

**工作原理：** DO / REVIEW / DELIVER 阶段会根据任务关键词自动匹配相关 skill，将 skill 内容追加到 prompt，让 claude 按 skill 规范执行。无需任何配置，把优秀的 skill 放到 `~/.claude/commands/` 即可自动生效。

## 单独预览文档

```bash
# 预览文档站（有 _site/ 用 mkdocs，否则自动降级）
./autodev serve --path /tmp/autodev/<项目名>

# 直接预览 process/ 执行过程（01-discover ~ 05-review）
./autodev serve --path /tmp/autodev/<项目名> --process

# 自定义端口
./autodev serve --path /tmp/autodev/<项目名> --port 9000

# 启动后终端显示真实 IP，如：http://10.23.29.11:8000
```

**降级策略**（自动选择最佳方式，监听 `0.0.0.0` 局域网可访问）：
1. 有 `_site/` → `mkdocs serve`（渲染最好）
2. 无 `_site/` → 纯本地 markdown 渲染（`python-markdown`，自动安装，**不依赖 GitHub API**）

## 独立使用 publish 模块

```bash
# 对已有目录发布文档站（会自动安装 mkdocs）
python3 publish.py --path /tmp/autodev/my-project --task "项目名"

# 直接启动预览（跳过构建）
python3 publish.py --path /tmp/autodev/my-project --serve

# 自定义端口
python3 publish.py --path /tmp/autodev/my-project --serve --port 9000
```

## 中断与恢复

```bash
# 另一个终端发送中断信号
./autodev-stop /tmp/autodev/<项目名>

# 从断点恢复
./autodev "原始任务" --path /tmp/autodev/<项目名> --from 4
```

## 输出结构

```
/tmp/autodev/<项目名>/
├── RESULT.md              # 交付报告（给人看的）
├── process/               # 全过程记录
│   ├── 01-discover.md
│   ├── 02-define.md
│   ├── 03-design.md
│   ├── 04-do.md
│   └── 05-review.md
├── .autodev/logs/         # 完整执行日志
│   ├── driver.log         # 全量合并日志
│   ├── session.log        # 会话摘要
│   └── <phase>.log        # 每阶段独立日志
├── <产出文件>
│
│  --build 时额外生成:
├── build.sh               # 构建脚本
└── process/06-build.md    # 构建报告
│
│  --publish 时额外生成:
├── mkdocs.yml             # 文档站配置
├── _site/                 # 静态 HTML（可部署）
└── _pdf/document.pdf      # PDF 导出
```

## 文件

```
autodev/
├── autodev       # Shell 入口（直接运行）
├── driver.py     # 流程调度器
├── runner.py     # Claude CLI 包装 + 日志
├── phases.py     # 各阶段 Prompt（集成 skills 注入）
├── skills.py     # Skills 自动发现、匹配、注入模块
├── build.py      # 编译构建模块
├── publish.py    # 文档发布模块（含 mkdocs 自动安装）
└── autodev-stop  # 中断控制脚本
```

## 文档

- [架构说明](docs/architecture.md)
- [阶段详解](docs/phases.md)
- [日志说明](docs/logs.md)
