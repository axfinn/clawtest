# 架构说明

## 整体结构

```
用户输入（一句话需求）
        │
        ▼
   autodev (shell)
        │
        ▼
   driver.py  ──────────────── 调度器
        │
        ├─ run_phase(prompt, cwd)
        │        │
        │        ▼
        │   runner.py  ────── claude CLI 包装
        │        │
        │        ▼
        │   claude --print --dangerously-skip-permissions
        │        │  --output-format stream-json
        │        │  -p "<prompt>"
        │        │
        │        ▼
        │   claude 使用内置工具直接操作文件：
        │   Read / Write / Edit / Bash
        │   WebSearch / WebFetch / Glob / Grep
        │
        ├─ phases.py  ──────── 各阶段 Prompt 定义
        ├─ build.py   ──────── 编译构建（可选）
        └─ publish.py ──────── 文档发布（可选）
```

## 关键设计原则

**driver.py 只调度，不干活**

driver.py 不解析 claude 的输出，不管理文件内容，只负责：
1. 按顺序调用各阶段
2. 传递正确的 cwd（工作目录）
3. 记录每阶段成功/失败
4. 汇总输出结果路径

**claude 直接操作文件**

每个阶段的 prompt 都明确告诉 claude：
- 使用 Write/Edit 工具创建/修改文件
- 使用 Bash 工具执行命令
- 不要只输出文字，要直接操作

这与旧方案（让 claude 返回 JSON，Python 解析再写文件）的本质区别在于：
- 旧方案：claude → JSON → Python 解析 → 写文件（易出错，格式依赖）
- 新方案：claude → 直接写文件（利用 claude 自身工具，更可靠）

**移除嵌套检测**

runner.py 在启动子进程前会移除 `CLAUDECODE` 环境变量，
确保即使在 Claude Code 环境内运行也不会被嵌套检测阻断。

## 数据流

```
任务描述
  │
  ▼ phases.py 生成 prompt
  │
  ▼ runner.py 调用 claude CLI（stream-json 模式）
  │
  ▼ 实时解析事件流：
  │   assistant → 打印文本到终端
  │   tool_use  → 打印工具调用提示
  │   result    → 记录轮次/费用
  │
  ▼ 同时写入日志：
      .autodev/logs/<phase>.log  （单阶段）
      .autodev/logs/driver.log   （全量合并）
      .autodev/logs/session.log  （会话摘要）
```
