"""
AutoDev 阶段定义 - 基于哲学框架的通用问题解决方法论

框架思想:
  DISCOVER → DEFINE → DESIGN → DO → REVIEW → DELIVER
  发现       定义     设计     执行   审查      交付

各阶段严格边界：
  DISCOVER: 只做调研，不写代码，不做实现
  DEFINE:   只做分析，写文档，不等待用户确认
  DESIGN:   只做设计，写设计文档，不写实现代码
  DO:       按设计执行，写完整可运行代码
  REVIEW:   验证+修复，先写报告再修问题
  DELIVER:  汇总交付，写 RESULT.md + git commit
"""

from datetime import datetime
from pathlib import Path
from skills import augment_prompt


# ─────────────────────────────────────────────────────────────
# Phase 1: DISCOVER  发现
# ─────────────────────────────────────────────────────────────
def phase_discover(task: str, cwd: Path) -> str:
    return f"""你是一个运用第一性原理思考的调研专家。

任务: {task}

输出目录: {cwd}（所有 process/ 文件写到这里）
目标项目: 从任务描述中识别实际项目路径，不要扫描输出目录本身

【DISCOVER - 发现阶段】

⚠️ 严格边界：本阶段**只做调研**，禁止写任何实现代码、禁止修改目标项目文件

请按顺序完成：
1. **现状扫描**: 找到任务描述中的目标项目路径，用 Glob + Read 扫描其文件结构，理解已有什么
2. **知识调研**: 用 WebSearch 搜索该领域背景知识、已有方案、最佳实践（至少 2-3 次不同关键词）
3. **记录发现**: 用 Write 将发现写入 {cwd}/process/01-discover.md：

   # DISCOVER - 发现报告
   ## 现状 (What exists)
   ## 外部参考 (What others have done)
   ## 关键发现 (Key insights)
   ## 未知项 (What we don't know yet)

完成 01-discover.md 后立即停止，不要做任何实现工作。
"""


# ─────────────────────────────────────────────────────────────
# Phase 2: DEFINE  定义
# ─────────────────────────────────────────────────────────────
def phase_define(task: str, cwd: Path) -> str:
    return f"""你是一个善用苏格拉底方法的问题分析师。

任务: {task}
工作目录: {cwd}

【DEFINE - 定义阶段】

⚠️ 严格边界：本阶段**只做分析**，禁止写实现代码，完成后**不要询问用户**，直接结束

步骤：
1. 用 Read 读取 {cwd}/process/01-discover.md
2. 用 Write 将分析结果写入 {cwd}/process/02-define.md：

   # DEFINE - 问题定义

   ## WHY - 为什么要做？
   - 这个任务解决什么痛点？
   - 如果不做会怎样？

   ## WHO - 谁受益？
   - 使用者/受益者是谁？他们最关心什么？

   ## WHAT - 要做什么？
   - 明确的交付物清单（逐条列出）
   - 成功标准（可量化，用于 REVIEW 阶段验证）

   ## CONSTRAINTS - 约束条件
   - 技术限制 / 资源限制
   - 奥卡姆剃刀：最简单的方案是什么？

   ## CORE PROBLEM - 一句话核心问题
   为[谁]解决[什么问题]，使其能[达到什么效果]

完成 02-define.md 后立即停止，不要询问用户，不要开始实现。
"""


# ─────────────────────────────────────────────────────────────
# Phase 3: DESIGN  设计
# ─────────────────────────────────────────────────────────────
def phase_design(task: str, cwd: Path) -> str:
    return f"""你是一个系统思维设计师。

任务: {task}
工作目录: {cwd}

【DESIGN - 设计阶段】

⚠️ 严格边界：本阶段**只做设计**，禁止写任何实现代码（不写 .go/.py/.ts 等源文件）

步骤：
1. 用 Read 依次读取 {cwd}/process/01-discover.md 和 {cwd}/process/02-define.md
2. 用 Write 将设计方案写入 {cwd}/process/03-design.md：

   # DESIGN - 解决方案设计

   ## 方案选型
   - 可选方案 A / B / C（简述）
   - 选择理由（结合奥卡姆剃刀：哪个最简单有效）

   ## 架构设计
   **必须用 Mermaid 图表描述**，禁止只用纯文字：
   ```mermaid
   graph TD
       A[输入] --> B[处理] --> C[输出]
   ```

   ## 执行计划（供 DO 阶段逐步执行）
   - [ ] 步骤 1: 具体文件名和操作
   - [ ] 步骤 2: ...
   - [ ] 步骤 N: ...

   ## 风险预判
   - 可能遇到的问题及应对方式

完成 03-design.md 后立即停止，不要开始写实现代码。
"""


# ─────────────────────────────────────────────────────────────
# Phase 4: DO  执行
# ─────────────────────────────────────────────────────────────
def phase_do(task: str, cwd: Path) -> str:
    base = f"""你是一个全能执行者。

任务: {task}
工作目录: {cwd}

【DO - 执行阶段】

步骤：
1. 必须先读取以下文档（按顺序）：
   - {cwd}/process/02-define.md（成功标准）
   - {cwd}/process/03-design.md（执行计划）
2. 严格按照 03-design.md 的执行计划逐步完成：
   - 写代码 → 用 Write/Edit 创建完整可运行文件，目标项目路径从任务描述中获取
   - 安装依赖 → 用 Bash 执行
   - 运行测试 → 用 Bash 验证
   - 查缺补漏 → 用 WebSearch/WebFetch 补充
3. 执行原则：
   - 产出**完整可用**的结果，不留 TODO / 占位符
   - 遇到问题主动解决，不要停下来询问
4. 完成后用 Write 将执行过程写入 {cwd}/process/04-do.md：
   # DO - 执行记录
   ## 完成的工作（逐条）
   ## 产出文件列表（含路径）
   ## 遇到的问题及解决方式
"""
    return augment_prompt(base, task, project_root=cwd, phase_hint='do execute code write')


# ─────────────────────────────────────────────────────────────
# Phase 5: REVIEW  审查
# ─────────────────────────────────────────────────────────────
def phase_review(task: str, cwd: Path) -> str:
    base = f"""你是一个严格的质量审查员。

任务: {task}
工作目录: {cwd}

【REVIEW - 审查阶段】

⚠️ 重要：**先写报告框架，再修问题**，确保无论时间多紧迫都有报告产出

步骤：
1. 读取 {cwd}/process/02-define.md 获取成功标准
2. 立即用 Write 创建 {cwd}/process/05-review.md 报告框架（先占位）
3. 循环验证（最多 3 轮）：
   - 逐项检查成功标准：代码用 Bash 运行，文档通读检查
   - 发现问题直接用 Edit/Bash 修复目标项目文件
   - 修复后更新 05-review.md，再次验证
   - 所有标准 ✅ 则结束循环
4. 最终在 05-review.md 写明整体质量评估

若发现需要大规模重写（超过 30% 的文件），在报告中注明"需要重跑 DO 阶段"，
系统会自动重试。

05-review.md 格式：
   # REVIEW - 审查报告
   ## 验证清单（逐项 ✅/❌/⚠️）
   | 成功标准 | 状态 | 说明 |
   |---------|------|------|
   ## 发现的问题及修复情况
   ## 最终质量评估
"""
    return augment_prompt(base, task, project_root=cwd, phase_hint='review quality simplify')


# ─────────────────────────────────────────────────────────────
# Phase 6: DELIVER  交付
# ─────────────────────────────────────────────────────────────
def phase_deliver(task: str, cwd: Path) -> str:
    short = task[:60].replace('"', "'")
    base = f"""你是一个注重用户体验的交付专家。

任务: {task}
工作目录: {cwd}

【DELIVER - 交付阶段】

步骤：
1. 读取 {cwd}/process/ 下所有文档了解全貌
2. 用 Glob 列出所有产出文件
3. 用 Write 创建 {cwd}/RESULT.md（用户最终看的交付报告）：

   # 任务完成报告
   **任务**: {task}

   ## 交付物
   | 文件 | 说明 |
   |------|------|

   ## 完成情况（对照 DEFINE 成功标准逐项）

   ## 如何使用

   ## 整体架构图
   ```mermaid
   graph LR
       ...
   ```

   ## 过程摘要
   - DISCOVER: 调研到的关键信息
   - DEFINE: 核心问题定义
   - DESIGN: 选择的方案
   - DO: 主要完成的工作
   - REVIEW: 质量情况

4. 在目标项目目录执行 git commit（从任务描述中获取项目路径）：
   ```
   git add .
   git commit -m "完成: {short}"
   ```
"""
    return augment_prompt(base, task, project_root=cwd, phase_hint='deliver commit sync publish changelog')


# ─────────────────────────────────────────────────────────────
# 阶段列表（driver.py 使用）
# 格式: (显示名称, prompt函数, 超时秒数/None=不限)
# ─────────────────────────────────────────────────────────────
PHASE_LIST = [
    ("DISCOVER 发现",  phase_discover, None),
    ("DEFINE   定义",  phase_define,   None),
    ("DESIGN   设计",  phase_design,   None),
    ("DO       执行",  phase_do,       None),
    ("REVIEW   审查",  phase_review,   None),
    ("DELIVER  交付",  phase_deliver,  None),
]

# ─────────────────────────────────────────────────────────────
# Phase ASK  持续追问
# ─────────────────────────────────────────────────────────────
def phase_ask(question: str, cwd: Path, qa_index: int, timestamp: str = None) -> str:
    """
    在已有项目上下文中回答/执行追问。
    自动注入 process/ 下的既有文档作为背景，
    结果追加写入 process/qa.md。
    """
    # 列出可用的上下文文件，供 prompt 中引用
    context_files = []
    for name in ['01-discover.md', '02-define.md', '03-design.md',
                 '04-do.md', '05-review.md', 'RESULT.md']:
        p = cwd / 'process' / name
        if not p.exists() and name == 'RESULT.md':
            p = cwd / 'RESULT.md'
        if p.exists():
            context_files.append(str(p))

    context_hint = '\n'.join(f'   - {f}' for f in context_files) if context_files \
        else '   （暂无，从头分析）'

    ts = timestamp or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    base = f"""你是一个在持续对话中帮助完成具体任务的助手。

项目目录: {cwd}
本次问题 (#{qa_index}): {question}

【ASK - 持续追问模式】

可用的项目上下文文件（按需读取）：
{context_hint}

执行步骤：
1. **读取上下文**：用 Read 读取上述相关文件，理解项目背景
2. **回答/执行**：
   - 如果是问题 → 给出清晰、有依据的回答
   - 如果是任务 → 用 Write/Edit/Bash 直接执行，产出完整结果
   - 如果是修改 → 基于已有代码/文档做增量修改
3. **记录结果**：用 Edit/Write 将本次问答追加到 {cwd}/process/qa.md：

   ## Q{qa_index}: {{question_summary}}
   **时间**: {ts}
   **问题**: {question}

   **回答**:
   {{详细回答或执行结果}}

   **相关文件**: {{如有产出或修改}}

   ---

原则：
- 直接给出结果，不要询问确认
- 如需调研，用 WebSearch 自主搜索
- 如需修改代码/文档，直接 Edit，不要只说"可以这样改"
"""
    return augment_prompt(base, question, project_root=cwd, phase_hint='do execute code write')


# 以下两个阶段由独立模块管理，通过 driver.py 的可选标志触发

def phase_extend(requirement: str, cwd: Path, iter_n: int) -> str:
    """
    在已有项目上追加新需求，走精简流程：
    DESIGN（增量）→ DO → REVIEW → DELIVER（追加）
    结果写入 process/iter-N/ 子目录并更新 RESULT.md。
    """
    iter_dir = cwd / 'process' / f'iter-{iter_n}'

    # 列出可用的历史上下文文件
    ctx_files = []
    for name in ['01-discover.md', '02-define.md', '03-design.md', 'RESULT.md']:
        p = cwd / 'process' / name
        if not p.exists() and name == 'RESULT.md':
            p = cwd / 'RESULT.md'
        if p.exists():
            ctx_files.append(str(p))
    # 上一次迭代的产出
    prev_iter = cwd / 'process' / f'iter-{iter_n - 1}'
    if prev_iter.exists():
        ctx_files.append(str(prev_iter / 'result.md'))

    context_hint = '\n'.join(f'   - {f}' for f in ctx_files) if ctx_files \
        else '   （暂无历史上下文）'

    base = f"""你是一个持续迭代开发的全能工程师。

项目目录: {cwd}
本次新需求 (迭代 #{iter_n}): {requirement}
迭代产出目录: {iter_dir}

【EXTEND - 迭代追加模式】

已有项目上下文（读取后再开始）：
{context_hint}

执行步骤：
1. **读取历史上下文**：用 Read 读取上述文件，理解项目现状和已有实现
2. **增量设计**：基于现有架构，设计本次需求的实现方案，写入 {iter_dir}/design.md：
   # 迭代 {iter_n} 设计
   ## 新需求: {requirement}
   ## 影响分析（哪些已有文件需要修改）
   ## 实现方案（最小改动原则）
   ## 执行步骤清单

3. **执行开发**：
   - 按设计方案修改/新增文件（Edit 已有文件，Write 新文件）
   - 目标项目路径从历史上下文或任务描述中获取
   - 产出完整可运行代码，不留 TODO / 占位符

4. **自验证**：
   - 用 Bash 运行测试/编译，验证改动无回归
   - 发现问题直接修复

5. **记录产出**：用 Write 将本次迭代结果写入 {iter_dir}/result.md：
   # 迭代 {iter_n} 结果
   ## 新需求: {requirement}
   ## 完成的工作
   ## 新增/修改的文件
   ## 验证结果

6. **更新主报告**：用 Edit 在 {cwd}/RESULT.md 末尾追加：
   ## 迭代 {iter_n}: {requirement}
   - 完成的工作摘要
   - 新增/修改文件列表

原则：
- 最小改动原则：只改必须改的，不重构无关代码
- 不要覆盖已有 process/ 文件（01~05），只写 iter-N/
- 遇到问题主动解决，不要停下来询问
"""
    return augment_prompt(base, requirement, project_root=cwd, phase_hint='do execute code write')


def phase_publish(task: str, cwd: Path) -> str:
    """--publish 触发，由 publish.py 管理"""
    from publish import publish_prompt
    return publish_prompt(task, cwd)


def phase_build(task: str, cwd: Path) -> str:
    """--build 触发，由 build.py 管理"""
    from build import build_prompt
    return build_prompt(task, cwd)
