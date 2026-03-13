# AutoDev - 无监管自驱开发工具

Python 串流程 + `claude` CLI 自主完成任务。

## 架构

```
你的需求
    │
    ▼
driver.py  ← 流程调度（Python）
    │
    ├── 阶段1: 调研      → claude 使用 WebSearch 调研最佳实践
    ├── 阶段2: 需求规格  → claude 写入 docs/01-REQUIREMENTS.md
    ├── 阶段3: 技术方案  → claude 写入 docs/02-DESIGN.md
    ├── 阶段4: 代码实现  → claude 直接创建所有代码文件
    ├── 阶段5: 测试      → claude 写测试 + 运行 + 写 docs/03-TEST_PLAN.md
    ├── 阶段6: 代码审查  → claude 读代码 + 直接修复 + 写 docs/04-REVIEW.md
    └── 阶段7: Git提交   → claude 执行 git add && git commit
```

**关键设计**：每个阶段调用 `claude --print --dangerously-skip-permissions`，
claude 使用自己的工具（Read/Write/Edit/Bash/WebSearch 等）**直接操作文件**，
不返回 JSON，driver.py 只负责调度。

## 使用

```bash
cd autodev

# 完整流程
python3 driver.py "创建一个 Flask 用户认证系统" --path ./output/myproject

# 断点恢复（从第4阶段开始）
python3 driver.py "创建一个 Flask 用户认证系统" --path ./output/myproject --from 4

# 指定当前目录
python3 driver.py "给这个项目添加单元测试" --path .
```

## 参数

| 参数 | 说明 |
|------|------|
| `requirement` | 需求描述（必填） |
| `--path` / `-p` | 项目目录，默认当前目录 |
| `--from` | 从第几阶段开始（1-7），用于断点恢复 |

## 输出结构

```
project/
├── docs/
│   ├── 00-RESEARCH.md      # 调研结论
│   ├── 01-REQUIREMENTS.md  # 需求规格
│   ├── 02-DESIGN.md        # 技术方案
│   ├── 03-TEST_PLAN.md     # 测试计划
│   └── 04-REVIEW.md        # 审查报告
├── <源代码文件>
├── tests/
└── README.md
```

## 依赖

- `claude` CLI（Claude Code）已安装并登录
- Python 3.10+
- 无需额外 Python 依赖
