"""
阶段 Prompt 定义
万能助手：不限于软件开发，任何任务都能自主完成
"""

from pathlib import Path


def phase_understand(task: str, project_path: Path) -> str:
    return f"""你是一个万能任务助手，工作目录是 {project_path}。

用户任务: {task}

请完成【理解与调研阶段】：
1. 分析这个任务的本质：是写代码？写文档？数据分析？内容创作？还是其他？
2. 用 WebSearch 搜索相关背景知识、参考案例、最佳实践（至少搜索 2 次）
3. 如果目录下已有文件，用 Glob + Read 读取理解现有内容
4. 用 Write 工具将以下内容写入 process/01-understand.md：
   - 任务理解（用自己的话重新描述任务目标）
   - 调研发现（关键信息、参考资料）
   - 执行计划（分几步完成，每步做什么）
   - 预期产出（最终交付什么）

直接用工具操作文件，不要只输出文字。
"""


def phase_execute(task: str, project_path: Path) -> str:
    return f"""你是一个万能任务助手，工作目录是 {project_path}。

用户任务: {task}

请先读取 process/01-understand.md 了解计划，然后完成【执行阶段】：

根据任务类型选择合适的方式：
- 如果是写代码 → 用 Write/Edit 工具创建完整可运行的代码文件
- 如果是写文档/报告 → 用 Write 工具创建完整的 Markdown 文档
- 如果是数据分析 → 用 Bash 运行分析，Write 保存结果
- 如果是内容创作 → 用 Write 工具创建内容文件
- 如果是配置/脚本 → 用 Write/Bash 完成

要求：
1. 产出完整可用的结果，不留占位符或 TODO
2. 需要执行命令就用 Bash 工具（安装依赖、运行程序等）
3. 需要联网查资料就用 WebSearch / WebFetch
4. 所有产出文件放在 {project_path} 目录下

完成后用 Write 工具将执行过程记录写入 process/02-execution.md。
"""


def phase_verify(task: str, project_path: Path) -> str:
    return f"""你是一个严格的质量检查员，工作目录是 {project_path}。

用户任务: {task}

请读取所有产出文件，完成【验证阶段】：
1. 对照任务目标检查产出是否完整、正确
2. 如果是代码：用 Bash 工具运行/测试，修复发现的问题
3. 如果是文档：检查内容完整性、准确性，直接用 Edit 补充不足之处
4. 如果是其他：用适合的方式验证结果符合预期
5. 直接修复问题，不要只列清单

用 Write 工具将验证结果写入 process/03-verify.md：
- 验证方式
- 发现的问题及修复情况
- 最终状态（通过/部分通过/说明）
"""


def phase_deliver(task: str, project_path: Path) -> str:
    return f"""你是一个任务总结专家，工作目录是 {project_path}。

用户任务: {task}

请读取 process/ 下所有过程记录和产出文件，完成【交付阶段】：
1. 用 Glob 列出所有产出文件
2. 用 Write 工具创建 RESULT.md，包含：
   ## 任务完成报告
   - **任务**: {task}
   - **产出文件**: 列出所有交付物及说明
   - **完成情况**: 对每个目标的完成情况
   - **使用说明**: 如何使用/查看产出（如有需要）
   - **过程摘要**: 简述完成过程中的关键步骤

3. 用 Bash 执行 git init（如果不是 git 仓库）
4. 用 Bash 执行 git add . 和 git commit -m "完成: {task[:50]}"

最终 RESULT.md 就是给用户的交付报告。
"""


# 阶段列表：供 driver.py 使用
PHASE_LIST = [
    ("理解与调研", phase_understand, 180),
    ("执行任务",   phase_execute,   None),   # 不限时，任务可能很复杂
    ("验证结果",   phase_verify,    300),
    ("整理交付",   phase_deliver,   120),
]
