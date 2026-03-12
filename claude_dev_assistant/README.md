# Claude Dev Assistant 🤖

全流程自动化开发工具 - 基于 Claude CLI 的智能开发助手

## 功能特性

- ✅ 自动需求分析 → 代码生成 → 质量审查
- ✅ 调用 Claude CLI (MiniMax API)
- ✅ 检查点保存/恢复
- ✅ 无限循环质量审查
- ✅ 支持编译为二进制

## 安装

```bash
# 安装依赖
pip install -e .

# 或直接运行
python -m claude_dev_assistant.driver develop "需求描述"
```

## 使用

```bash
# 开发新功能
claude-dev develop "创建一个用户管理系统"

# 交互模式
claude-dev interactive

# 指定项目路径
claude-dev develop "需求" --path /path/to/project
```

## 编译二进制

```bash
# 安装 PyInstaller
pip install pyinstaller

# 编译
pyinstaller --onefile --name claude-dev claude_dev_assistant/driver.py

# 输出: dist/claude-dev
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
