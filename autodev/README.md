# AutoDev - 万能任务助手

> 任何任务 → 6阶段哲学方法论 → claude 自主完成 → 产出 + 文档站 + PDF

## 方法论

```
DISCOVER → DEFINE → DESIGN → DO → REVIEW → DELIVER [→ PUBLISH]
  发现       定义     设计    执行   审查      交付        发布
```

**哲学依据**：
- **第一性原理**：从根本出发理解问题，不做假设
- **苏格拉底追问**：不断 Why，直到找到核心问题
- **奥卡姆剃刀**：优先最简单有效的方案
- **设计思维**：先理解人和问题，再解决
- **PDCA 循环**：计划→执行→检查→改进

## 架构

```
用户任务
  │
  ▼
driver.py  ← 调度器（Python，只负责串流程）
  │
  ├─ 1. DISCOVER 发现  → WebSearch调研 + 扫描现状  → process/01-discover.md
  ├─ 2. DEFINE   定义  → Why/Who/What/成功标准     → process/02-define.md
  ├─ 3. DESIGN   设计  → 方案选型 + 执行计划        → process/03-design.md
  ├─ 4. DO       执行  → claude 全权完成实际工作    → process/04-do.md
  ├─ 5. REVIEW   审查  → 对照标准验证 + 直接修复    → process/05-review.md
  ├─ 6. DELIVER  交付  → RESULT.md + git commit
  │
  └─ 7. PUBLISH  发布  → MkDocs 文档站 + PDF（--publish 触发）
         │
         ├── 安装 mkdocs-material + mkdocs-with-pdf
         ├── 自动扫描 .md 文件，生成 mkdocs.yml 导航
         ├── mkdocs build → _site/（可部署静态站）
         ├── ENABLE_PDF_EXPORT=1 → _pdf/document.pdf
         └── mkdocs serve → http://127.0.0.1:8000（本地预览）
```

## 文档工具选型：MkDocs + Material

| 需求 | 实现 |
|------|------|
| 书本结构导航 | Material 主题内置，tabs + sections |
| 在线浏览 | `mkdocs build` → 纯静态 HTML，可部署任意托管 |
| PDF 导出 | `mkdocs-with-pdf` 插件，一键生成 |
| 中文支持 | `language: zh`，搜索支持中文 |
| 安装简单 | `pip install mkdocs-material mkdocs-with-pdf` |
| GitHub Pages | `mkdocs gh-deploy` 一行部署 |

## 使用

```bash
cd autodev

# 普通任务（代码/分析等）
python3 driver.py "用 Flask 实现 JWT 用户认证" --path ./projects/auth

# 文档/书籍任务（自动生成文档站 + PDF）
python3 driver.py "写 Redis 集群最佳实践文档" --path ./projects/redis --publish
python3 driver.py "写一本微服务架构实践手册" --path ./projects/book --publish

# 数据分析
python3 driver.py "分析 sales.csv 找出增长趋势" --path ./projects/sales

# 断点恢复（从第4阶段 DO 开始）
python3 driver.py "任务描述" --path ./projects/xxx --from 4

# 对已有目录单独发布文档站
python3 publish.py --path ./projects/redis --task "Redis 最佳实践"
```

## 输出结构

```
工作目录/
├── RESULT.md              ← 最终交付报告
├── process/
│   ├── 01-discover.md     ← 调研发现
│   ├── 02-define.md       ← 问题定义
│   ├── 03-design.md       ← 方案设计
│   ├── 04-do.md           ← 执行记录
│   └── 05-review.md       ← 审查报告
├── <产出文件（代码/文档等）>
│
│ --publish 后额外生成:
├── mkdocs.yml             ← 文档站配置
├── _site/                 ← 静态 HTML（可直接部署）
│   └── index.html
└── _pdf/
    └── document.pdf       ← 导出的 PDF
```

## 参数

| 参数 | 说明 | 默认 |
|------|------|------|
| `task` | 任务描述 | 必填 |
| `--path` / `-p` | 工作目录 | `./output` |
| `--from N` | 从第 N 阶段开始（1-6） | 1 |
| `--publish` | 完成后生成 MkDocs 文档站 + PDF | 否 |

## 文件清单

```
autodev/
├── driver.py    # 调度器：6阶段 + --publish 标志
├── runner.py    # claude CLI 包装（stream-json 实时输出）
├── phases.py    # 阶段 prompt（哲学方法论内建）
├── publish.py   # MkDocs 文档站生成（可独立运行）
└── README.md
```

## 依赖

- `claude` CLI 已安装并登录
- Python 3.10+，无额外依赖（publish 阶段自动安装 mkdocs-material）
