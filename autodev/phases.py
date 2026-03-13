"""
开发阶段定义
每个阶段返回一个 prompt，告诉 Claude 直接用自己的工具完成任务
"""

from pathlib import Path


def phase_research(requirement: str, project_path: Path) -> str:
    return f"""你是一个资深软件工程师，正在目录 {project_path} 下工作。

需求: {requirement}

请完成【调研阶段】：
1. 用 WebSearch 搜索该需求的最佳实践、相关库、参考实现（至少搜索 2-3 次）
2. 用 Glob 和 Read 分析目录下已有代码（如果有）
3. 将调研结论写入 docs/00-RESEARCH.md，格式如下：
   - 技术选型建议
   - 相关开源项目/参考
   - 实现思路
   - 注意事项

直接用 Write/Edit 工具创建文件，不要只输出文字。
"""


def phase_requirements(requirement: str, project_path: Path) -> str:
    return f"""你是一个产品经理兼技术架构师，正在目录 {project_path} 下工作。

需求: {requirement}

请阅读 docs/00-RESEARCH.md（如果存在），然后完成【需求规格阶段】：
用 Write 工具将完整需求规格文档写入 docs/01-REQUIREMENTS.md，包含：
1. 项目概述
2. 功能需求列表（用户故事格式）
3. 非功能需求（性能、安全、兼容性）
4. 验收标准
5. 技术约束

直接用 Write 工具创建 docs/01-REQUIREMENTS.md 文件。
"""


def phase_design(requirement: str, project_path: Path) -> str:
    return f"""你是一个软件架构师，正在目录 {project_path} 下工作。

需求: {requirement}

请阅读 docs/00-RESEARCH.md 和 docs/01-REQUIREMENTS.md，然后完成【技术方案阶段】：
用 Write 工具将技术方案写入 docs/02-DESIGN.md，包含：
1. 系统架构图（用 ASCII 或 Mermaid）
2. 目录结构设计
3. 核心模块说明
4. 数据结构 / API 设计
5. 关键技术点

直接用 Write 工具创建 docs/02-DESIGN.md 文件。
"""


def phase_implement(requirement: str, project_path: Path) -> str:
    return f"""你是一个全栈工程师，正在目录 {project_path} 下工作。

需求: {requirement}

请阅读所有 docs/ 下的文档，然后完成【代码实现阶段】：
1. 先用 Glob/Read 检查目录下是否有已有代码，避免覆盖
2. 按照 docs/02-DESIGN.md 的目录结构用 Write/Edit 工具创建所有代码文件
3. 代码要求：
   - 完整可运行，不留 TODO 占位
   - 包含必要的错误处理
   - 重要逻辑加简短注释
4. 如需安装依赖，用 Bash 工具执行（pip install / npm install 等）
5. 创建 README.md（如果不存在）

直接用工具创建/修改文件，完成完整的代码实现。
"""


def phase_test(requirement: str, project_path: Path) -> str:
    return f"""你是一个测试工程师，正在目录 {project_path} 下工作。

需求: {requirement}

请读取已有代码文件，然后完成【测试阶段】：
1. 用 Write 工具创建测试文件（tests/ 目录下）
2. 用 Bash 工具尝试运行测试，查看结果
3. 将测试计划写入 docs/03-TEST_PLAN.md：
   - 测试用例列表
   - 测试结果
   - 已知问题

如果测试失败，用 Edit 工具修复代码直到测试通过（或记录原因）。
"""


def phase_review(requirement: str, project_path: Path) -> str:
    return f"""你是一个高级代码审查员，正在目录 {project_path} 下工作。

需求: {requirement}

请读取所有代码文件，完成【代码审查阶段】：
1. 检查以下问题：
   - 语法错误 / 逻辑漏洞
   - 安全隐患（注入、越权等）
   - 代码规范
   - 是否符合需求
2. 发现问题直接用 Edit 工具修复，不要只列问题
3. 将审查报告写入 docs/04-REVIEW.md

直接修复代码，不要只输出建议。
"""


def phase_commit(requirement: str, project_path: Path) -> str:
    short = requirement[:50].replace('"', "'")
    return f"""你正在目录 {project_path} 下工作。

请完成【Git 提交阶段】：
1. 用 Bash 工具检查 git 状态：git status
2. 如果不是 git 仓库，先执行：git init
3. 创建 .gitignore（如果不存在），排除 __pycache__、.venv、node_modules、*.log 等
4. 执行：git add .
5. 执行：git commit -m "feat: {short}"

如果 git commit 失败，检查原因并解决后重试。
"""
