# AutoDev - 万能任务助手

> 任何任务 → 6阶段哲学方法论 → claude 自主完成 → 产出 + 过程全记录

## 方法论

```
DISCOVER → DEFINE → DESIGN → DO → REVIEW → DELIVER
  发现       定义     设计    执行   审查      交付
```

**哲学依据**：
- **第一性原理**：从根本出发理解问题，不做假设
- **苏格拉底追问**：不断 Why，直到找到核心问题
- **奥卡姆剃刀**：优先最简单有效的方案
- **设计思维**：先理解人和问题，再解决
- **PDCA循环**：计划→执行→检查→改进

## 架构

```
用户任务
  │
  ▼
driver.py  ←  调度器（Python，只负责串流程）
  │
  ├─ 1. DISCOVER 发现  → WebSearch调研 + 扫描现状  → process/01-discover.md
  ├─ 2. DEFINE   定义  → Why/Who/What/约束/成功标准 → process/02-define.md
  ├─ 3. DESIGN   设计  → 方案选型 + 执行计划        → process/03-design.md
  ├─ 4. DO       执行  → claude 全权完成实际工作     → process/04-do.md
  ├─ 5. REVIEW   审查  → 对照标准验证 + 直接修复     → process/05-review.md
  └─ 6. DELIVER  交付  → RESULT.md + git commit
```

**关键**：每阶段调用 `claude --print --dangerously-skip-permissions`，
claude 用自己的工具（Read/Write/Edit/Bash/WebSearch/WebFetch）**直接操作文件**。
driver.py 只调度，不解析输出，不管理文件。

## 使用

```bash
cd autodev

# 软件开发
python3 driver.py "用 Flask 实现 JWT 用户认证" --path ./projects/auth

# 技术文档
python3 driver.py "写一份 Redis 集群最佳实践文档" --path ./projects/redis

# 数据分析
python3 driver.py "分析 sales.csv，找出增长趋势，生成可视化报告" --path ./projects/sales

# 内容创作
python3 driver.py "写一篇微服务 vs 单体架构的深度对比博客" --path ./projects/blog

# 任何问题
python3 driver.py "帮我设计一套代码 Review 流程规范" --path ./projects/review

# 断点恢复（从第4阶段 DO 开始）
python3 driver.py "任务描述" --path ./projects/xxx --from 4
```

## 输出结构

```
工作目录/
├── RESULT.md              ← 最终交付报告（给用户看的）
├── process/
│   ├── 01-discover.md     ← 调研发现
│   ├── 02-define.md       ← 问题定义（Why/What/成功标准）
│   ├── 03-design.md       ← 方案设计
│   ├── 04-do.md           ← 执行记录
│   └── 05-review.md       ← 审查报告
└── <所有产出文件>
```

## 参数

| 参数 | 说明 | 默认 |
|------|------|------|
| `task` | 任务描述 | 必填 |
| `--path` / `-p` | 工作目录 | `./output` |
| `--from N` | 从第 N 阶段开始（1-6） | 1 |

## 依赖

- `claude` CLI 已安装并登录（`which claude` 可找到）
- Python 3.10+，无额外依赖
