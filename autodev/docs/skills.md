# Skills 自动集成

AutoDev 会自动扫描本地 Claude Code skills，在执行阶段动态注入到 prompt 中，让 Claude 按照规范执行任务。

## Skills 来源

按优先级从高到低（项目级覆盖全局）：

```
<project>/.claude/commands/*.md    # 项目级 skills（优先）
~/.claude/commands/*.md            # 全局 skills
```

## 注入时机

| 阶段 | 注入条件 |
|------|---------|
| DO（执行） | 根据任务关键词匹配 skill 名称/内容 |
| REVIEW（审查） | 自动注入 simplify、lint 类 skill |
| DELIVER（交付） | 自动注入 git-commit、docs-sync 类 skill |

## 匹配规则

AutoDev 通过任务描述中的关键词与 skill 文件名/内容进行模糊匹配：

```
任务："用 Go 实现 gRPC 服务"
→ 命中 bili-lib、bili-grpc、git-commit-convention 等 skill
→ 将 skill 内容追加到 DO 阶段 prompt
```

## 查看可用 Skills

```bash
# 列出当前所有可用的 skills
./autodev --list-skills
```

输出示例：
```
全局 skills (~/.claude/commands/):
  bili-lib.md         — Go 中间件统一索引
  bili-biz.md         — 直播业务域参考
  git-commit.md       — commit 规范
  ...

项目 skills (.claude/commands/):
  （无）
```

## 手动指定 Skills

通过 `--skills` 参数强制注入指定 skill：

```bash
./autodev "任务描述" --skills bili-lib,git-commit
```

## Web UI 中的 Skills

Web UI 通过后端调用 `autodev` CLI，Skills 是否生效取决于运行环境：

| 运行方式 | Claude HOME | Skills 是否可用 |
|---------|------------|----------------|
| 本地直接运行 | `$HOME`（当前用户） | ✅ 自动可用 |
| Docker 容器（未配置） | `/home/autodev` | ❌ 默认不可用 |
| Docker 容器（已挂载） | `/home/autodev`（挂载 `~/.claude`） | ✅ 可用 |

详见 [Web UI Skills 配置](../../web/README.md#claude-skills-集成)。

## 最佳实践

1. **全局 skills 放 `~/.claude/commands/`**：对所有项目生效
2. **项目级 skills 放 `<project>/.claude/commands/`**：仅当前项目生效，优先级更高
3. **Docker 部署时挂载 `~/.claude`**：让容器内任务也能使用个人 skills
4. **skill 文件名即触发词**：命名越清晰，匹配越准确（如 `go-redis.md` > `cache.md`）
