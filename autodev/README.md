# AutoDev - 万能任务助手

> 描述任何任务 → Python 串流程 → `claude` 自主完成 → 产出结果 + 过程记录

## 核心理念

不限于软件开发。写代码、写文档、数据分析、内容创作……任何任务，claude 自主选择合适的工具和方式完成，并记录整个过程。

## 架构

```
用户任务描述
      │
      ▼
 driver.py  ← 调度器（Python，只负责串流程）
      │
      ├── 阶段1: 理解与调研  → claude 理解任务 + WebSearch 调研 → process/01-understand.md
      ├── 阶段2: 执行任务    → claude 自主选择工具完成任务（代码/文档/分析/创作…）
      ├── 阶段3: 验证结果    → claude 检查产出 + 直接修复问题
      └── 阶段4: 整理交付    → claude 生成 RESULT.md + git commit
```

**关键设计**：
- `runner.py` 调用 `claude --print --dangerously-skip-permissions --output-format stream-json`
- 每阶段 claude 使用自己的工具（Read/Write/Edit/Bash/WebSearch/WebFetch）**直接操作文件**
- driver.py 只负责调度，不解析 JSON，不管理文件

## 使用

```bash
cd autodev

# 软件开发
python3 driver.py "用 Flask 创建用户认证系统" --path ./projects/auth

# 技术文档
python3 driver.py "写一份 Redis 最佳实践技术文档" --path ./projects/redis-doc

# 数据分析
python3 driver.py "分析 data.csv，找出销售趋势并生成报告" --path ./projects/analysis

# 内容创作
python3 driver.py "写一篇微服务架构的技术博客，附代码示例" --path ./projects/blog

# 断点恢复（从第3阶段开始）
python3 driver.py "任务描述" --path ./projects/xxx --from 3
```

## 输出结构

```
工作目录/
├── process/
│   ├── 01-understand.md   # 任务理解 + 调研 + 计划
│   ├── 02-execution.md    # 执行过程记录
│   └── 03-verify.md       # 验证报告
├── RESULT.md              # 最终交付报告（给用户看的）
└── <所有产出文件>
```

## 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `task` | 任务描述 | 必填 |
| `--path` / `-p` | 工作目录 | `./output` |
| `--from N` | 从第 N 阶段开始（断点恢复） | 1 |

## 依赖

- `claude` CLI 已安装并登录
- Python 3.10+，无需额外依赖
