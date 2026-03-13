# 日志说明

AutoDev 会在每个项目目录的 `.autodev/logs/` 下记录完整执行日志。

## 日志文件

```
<项目目录>/
└── .autodev/
    └── logs/
        ├── driver.log          # 全量合并日志（所有阶段）
        ├── session.log         # 会话摘要（多次运行追加）
        ├── 1-discover-发现.log  # 阶段1 独立日志
        ├── 2-define-定义.log    # 阶段2 独立日志
        ├── 3-design-设计.log    # 阶段3 独立日志
        ├── 4-do-执行.log        # 阶段4 独立日志
        ├── 5-review-审查.log    # 阶段5 独立日志
        ├── 6-deliver-交付.log   # 阶段6 独立日志
        ├── build-编译构建.log   # BUILD 阶段（如触发）
        └── publish-文档发布.log # PUBLISH 阶段（如触发）
```

## 日志内容

每个阶段日志包含：

```
======================================================================
阶段: 4/6  DO 执行
时间: 2026-03-13 14:23:01
======================================================================
[PROMPT]
你是一个全能执行者，工作目录是 /tmp/autodev/redis-doc-0313-1423 ...
──────────────────────────────────────────────────────────────────────
[OUTPUT]
{"type":"assistant","message":{"content":[{"type":"text","text":"..."}]}}
{"type":"tool_use","tool_name":"Write","tool_input":{"file_path":"..."}}
...
──────────────────────────────────────────────────────────────────────
[RESULT] ✅ 成功  耗时: 87.3s  轮次: 12  费用: $0.0423
======================================================================
```

## 使用日志排查问题

**查看某阶段完整输出**：
```bash
cat /tmp/autodev/<项目>/.autodev/logs/4-do-执行.log
```

**查看所有阶段摘要**：
```bash
grep -E "^\[RESULT\]|^阶段:" /tmp/autodev/<项目>/.autodev/logs/driver.log
```

**查看历史会话**：
```bash
cat /tmp/autodev/<项目>/.autodev/logs/session.log
```

**实时跟踪（另一终端）**：
```bash
tail -f /tmp/autodev/<项目>/.autodev/logs/driver.log
```
