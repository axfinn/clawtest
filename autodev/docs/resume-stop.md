# 断点恢复与终止

## 断点恢复

任意阶段中断后，用 `--from N` 从指定阶段重新开始。

```bash
# 查看上次到哪个阶段
cat /tmp/autodev/<项目>/.autodev/logs/session.log

# 从第 4 阶段 DO 重新开始
./autodev "任务描述" --path /tmp/autodev/<项目> --from 4
```

阶段编号对照：

| N | 阶段 |
|---|------|
| 1 | DISCOVER 发现 |
| 2 | DEFINE 定义 |
| 3 | DESIGN 设计 |
| 4 | DO 执行 |
| 5 | REVIEW 审查 |
| 6 | DELIVER 交付 |

## 终止运行中的任务

```bash
# 查看正在运行的 autodev 任务
autodev-stop --list

# 终止指定项目
autodev-stop --path /tmp/autodev/<项目>

# 终止所有
autodev-stop --all
```

或直接用快捷键：
- `Ctrl+C`：中断当前阶段，记录状态后退出
- 下次用 `--from N` 从中断的阶段重新开始
