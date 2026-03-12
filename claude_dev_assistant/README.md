# Claude Dev Assistant 🤖

全流程自动化开发工具 - 基于 Claude Code CLI 的智能开发助手

## 功能特性

- ✅ 自动需求分析 → 技术方案 → 代码生成 → 质量审查
- ✅ 调用 Claude Code CLI 生成真正的可用代码
- ✅ 支持 Chrome 插件、前端、Python 等多种项目
- ✅ 代码质量检查 + 循环改进
- ✅ 自动生成文档 (需求规格、技术方案、测试计划)
- ✅ 自动 Git 提交管理

## 7 阶段开发流程

1. **需求调研** - WebSearch 搜索优秀方案
2. **需求分析** - 功能点、用户故事、验收标准
3. **技术方案** - 架构设计、模块设计
4. **代码实现** - Claude 生成完整代码
5. **测试用例** - 单元测试 + 集成测试
6. **测试回归** - 运行测试验证
7. **代码审查** - 循环改进直到通过

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

# 指定项目路径
python3 driver.py develop "需求" --path /path/to/project

# 指定 Claude 路径
python3 driver.py develop "需求" --claude /usr/local/bin/claude
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

## 项目结构

```
claude_dev_assistant/
├── driver.py              # 主入口
├── core/
│   ├── shared/           # 公共模块 (Logger, ProgressReporter)
│   ├── workflow/         # 工作流引擎
│   ├── memory/           # 记忆管理
│   ├── state/            # 状态管理
│   ├── review/           # 质量审查
│   ├── skills/           # GitHub Skills
│   └── config/           # 配置管理
└── setup.py
```

## 生成的文档

每个项目会自动生成以下文档:

```
项目目录/
├── docs/
│   ├── 01-REQUIREMENTS.md   # 需求规格文档
│   ├── 02-DESIGN.md         # 技术方案文档
│   └── 03-TEST_PLAN.md     # 测试计划文档
├── .claude/
│   └── logs/                # 执行日志
└── .git/                    # Git 提交记录
```

## 依赖

- Python 3.10+
- Claude Code CLI (自动检测安装位置)
- pyyaml

## License

MIT
