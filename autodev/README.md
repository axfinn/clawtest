# AutoDev

无监管万能任务助手。给它一句话需求，它自主完成并交付结果。

```bash
./autodev "写一份 Redis 集群最佳实践文档" --publish
./autodev "用 Go 实现一个 HTTP 文件服务器" --build
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
| DO | 全力执行，直接操作文件 |
| REVIEW | 对照标准验证，发现问题直接修复 |
| DELIVER | 生成 RESULT.md + git commit |

可选扩展阶段（通过参数触发）：

| 参数 | 阶段 | 说明 |
|------|------|------|
| `--build` | BUILD | 编译构建，生成二进制/产物 |
| `--publish` | PUBLISH | 生成 MkDocs 文档站 + PDF |

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

# 文档类任务 → 自动生成文档站 + PDF
./autodev "写 K8s 入门手册" --publish

# 需要编译的项目 → 自动构建
./autodev "用 Rust 写 CLI 工具" --build

# 断点恢复（从第 4 阶段 DO 开始）
./autodev "任务描述" --path /tmp/autodev/xxx --from 4
```

## 输出

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
├── autodev      # Shell 入口（直接运行）
├── driver.py    # 流程调度器
├── runner.py    # Claude CLI 包装 + 日志
├── phases.py    # 各阶段 Prompt
├── build.py     # 编译构建模块
└── publish.py   # 文档发布模块
```

## 文档

- [架构说明](docs/architecture.md)
- [阶段详解](docs/phases.md)
- [日志说明](docs/logs.md)
