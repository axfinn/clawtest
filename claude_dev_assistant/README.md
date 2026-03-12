# Claude Dev Assistant 🤖

全流程自动化开发工具 - 基于 Claude Code CLI 的智能开发助手

## 功能特性

- ✅ 自动需求分析 → 代码生成 → 质量审查
- ✅ 调用 Claude Code CLI 生成真正的可用代码
- ✅ 支持 Chrome 插件、前端、Python 等多种项目
- ✅ 代码质量检查

## 安装

```bash
# 安装依赖
pip install -e .

# 或直接运行
python3 -m claude_dev_assistant.driver develop "需求描述"
```

## 使用

```bash
# 开发新功能
python3 driver.py develop "创建一个用户管理系统"

# 交互模式
python3 driver.py interactive

# 指定项目路径
python3 driver.py develop "需求" --path /path/to/project
```

## 示例

```bash
# 生成 Chrome 插件
python3 driver.py develop "chrome 浏览器插件，支持视频抽帧" --path ../my-chrome-ext/

# 生成 Python API
python3 driver.py develop "用户管理 API" --path ../my-api/

# 生成 React 前端
python3 driver.py develop "待办事项 React 应用" --path ../my-app/
```

## 依赖

- Python 3.8+
- Claude Code CLI (`/home/node/.openclaw/workspace/tools/bin/claude`)

## License

MIT
