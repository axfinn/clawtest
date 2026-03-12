# Claude Dev Assistant 🤖

自驱开发工具 - 基于 Claude CLI 的智能开发助手

## 功能

- ✅ 自动需求分析 → 代码生成 → 质量审查
- ✅ 调用 Claude CLI (MiniMax API)
- ✅ 检查点保存/恢复
- ✅ 无限循环质量审查

## 使用

```bash
# 开发新功能
python3 -m claude_dev_assistant.driver develop "创建一个用户系统"

# 交互模式
python3 -m claude_dev_assistant.driver interactive
```

## 配置

Claude CLI 配置: `~/.claude/settings.json`

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.minimaxi.com/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "your-token",
    "ANTHROPIC_MODEL": "MiniMax-M2.5"
  }
}
```

## License

MIT
