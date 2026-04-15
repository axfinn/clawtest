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

Auto Mode 原则（借鉴 Claude Code Auto Mode）:
  1. 立即执行 — 立即开始实现，做合理假设并继续
  2. 最小化中断 — 优先做合理假设而非询问用户
  3. 行动优于计划 — 不要进入计划模式，除非用户明确要求
  4. 做合理决策 — 选择最合理的方案并继续
  5. 全面完成 — 完成完整任务包括测试、lint 和验证
  6. 永不发布到公共服务 — 未经批准不发布内容到公共端点
"""

from datetime import datetime
from pathlib import Path
from skills import augment_prompt


# ─────────────────────────────────────────────────────────────
# Auto Mode 自主执行原则常量
# ─────────────────────────────────────────────────────────────
AUTO_MODE_PRINCIPLES = """
## Auto Mode 自主执行原则

1. **立即执行** — 立即开始实现，做合理假设并继续
2. **最小化中断** — 优先做合理假设而非询问用户，除非任务确实无法继续
3. **行动优于计划** — 不要进入计划模式，除非用户明确要求
4. **做合理决策** — 选择最合理的方案并继续，不要在歧义上阻塞
5. **全面完成** — 完成完整任务包括测试、lint 和验证，不要停下来询问
6. **永不发布到公共服务** — 未经明确书面批准，不发布内容到公共端点
"""


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

   ## 验收条件（ACCEPTANCE CRITERIA）
   ⚠️ 写法强制规范：
   - 每条必须是**陈述句**，描述系统应达到的状态（禁止疑问句）
   - 每条必须对应一个可执行的 shell 命令来验证
   - 测试命令必须**真正运行程序/调用接口**，禁止只检查文件存在

   ❌ 错误示例（禁止这样写）：
   - 是否能正常启动？
   - cmd: test -f main.go
   - cmd: python -c "import app"

   ✅ 正确示例（必须这样写）：
   - 服务启动后在 8080 端口返回 HTTP 200
   - cmd: (cd /path/to/project && go run . &) && sleep 3 && curl -sf http://localhost:8080/ && pkill -f 'go run .'
   - 命令行工具处理输入文件后输出正确结果
   - cmd: cd /path/to/project && echo 'test input' | python main.py | grep 'expected output'

   （至少 2 条，最多 5 条，覆盖核心功能，每条都要真正验证功能可用）

3. 用 Write 创建 {cwd}/process/acceptance_tests.sh：
   #!/bin/bash
   # 验收测试脚本 - 由 DEFINE 阶段生成，DO/REVIEW/DELIVER 阶段执行
   # ⚠️ 每条测试必须真正运行程序/调用接口，禁止只检查文件存在
   PASS=0; FAIL=0
   run_test() {{
     local desc="$1"; local cmd="$2"
     echo -n "  [$desc] "
     if eval "$cmd" > /dev/null 2>&1; then
       echo "✅ PASS"; PASS=$((PASS+1))
     else
       echo "❌ FAIL"; FAIL=$((FAIL+1))
     fi
   }}
   # --- 验收用例（每行一个，必须真正运行程序）---
   # run_test "描述" "shell命令"
   <在此填入从验收条件提取的 run_test 行>
   # ---
   echo ""
   echo "结果: $PASS 通过 / $FAIL 失败"
   [ $FAIL -eq 0 ] && exit 0 || exit 1

完成 02-define.md 和 acceptance_tests.sh 后立即停止，不要询问用户，不要开始实现。
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
   用图表或列表描述（推荐 Mermaid，也可用 ASCII 图或文字列表）：
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
def phase_do(task: str, cwd: Path, review_feedback: str = '') -> str:
    feedback_block = ''
    if review_feedback:
        feedback_block = f"""
⚠️ 上次 REVIEW 发现的问题（本次必须修复）：
---
{review_feedback[:500]}
---
"""
    base = f"""你是一个全能执行者。

任务: {task}
工作目录: {cwd}

{AUTO_MODE_PRINCIPLES}
{feedback_block}
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
   - 立即执行，做合理假设并继续，不要停下来询问
4. **自测（强制，不可跳过）**：实现完成后必须执行：
   - 若 {cwd}/process/acceptance_tests.sh 不存在：立即创建（参考 DEFINE 阶段格式），写入真正运行程序的测试命令
   - 用 Bash 执行 `bash {cwd}/process/acceptance_tests.sh`
   - 若有 FAIL：直接修复，修复后再次运行，直到全部通过
   - 04-do.md 中必须记录"验收测试全部通过"才算本阶段完成，有 FAIL 不能结束
5. 完成后用 Write 将执行过程写入 {cwd}/process/04-do.md：
   # DO - 执行记录
   ## 完成的工作（逐条）
   ## 产出文件列表（含路径）
   ## 自测结果（acceptance_tests.sh 通过率）
   ## 遇到的问题及解决方式
6. **写文件摘要缓存**（供 REVIEW 阶段复用，避免重复读取）：
   用 Write 创建 {cwd}/process/file-cache.md，格式：
   # 已读文件摘要（DO 阶段）
   ## <文件路径>
   <该文件的关键内容摘要，50字以内>
   （每个本阶段读取或修改过的关键文件写一条）
"""
    return augment_prompt(base, task, project_root=cwd, phase_hint='do execute code write')


# ─────────────────────────────────────────────────────────────
# Phase 5: REVIEW  审查
# ─────────────────────────────────────────────────────────────
def phase_review(task: str, cwd: Path, stage: str = 'stage1') -> str:
    if stage == 'stage2':
        stage_instruction = """**当前：Stage2 深度验证**
逐项检查 02-define.md 里的每一条成功标准，全部验证，不能跳过。"""
    else:
        stage_instruction = """**当前：Stage1 快速验证**
只验证核心功能是否能跑通，不需要逐项检查所有标准。"""

    base = f"""你是一个专门找 bug 的破坏者。你的唯一目标是证明代码有问题。
你和写代码的人没有任何关系，你只对客观质量负责。不要手软。

任务: {task}
工作目录: {cwd}

{AUTO_MODE_PRINCIPLES}

【REVIEW - 审查阶段】

{stage_instruction}

⚠️ 重要：**先写报告框架，再修问题**，确保无论时间多紧迫都有报告产出

步骤：
1. 立即用 Write 创建 {cwd}/process/05-review.md 报告框架（先占位）
2. **复用文件摘要缓存**（如果存在 {cwd}/process/file-cache.md，先读取它，避免重复读取已知文件）
3. **运行验收脚本**（客观评分，不可跳过）：
   - 检查 {cwd}/process/acceptance_tests.sh 是否存在
   - 若存在：用 Bash 执行 `bash {cwd}/process/acceptance_tests.sh`
   - 记录每条测试的 PASS/FAIL 结果到报告
3. 读取 {cwd}/process/02-define.md 获取成功标准，按 {stage} 要求逐项检查：
   - 代码用 Bash 运行验证
   - 发现问题直接用 Edit/Bash 修复目标项目文件
   - 修复后重新运行验收脚本验证
4. 更新 05-review.md 写明整体质量评估

05-review.md 格式：
   # REVIEW - 审查报告（{stage}）

   ## 验收脚本结果
   通过: X / 失败: Y
   | 测试 | 结果 |
   |------|------|

   ## 验证清单（逐项 ✅/❌/⚠️）
   | 成功标准 | 状态 | 说明 |
   |---------|------|------|

   ## 发现的问题及修复情况

   ## 最终质量评估
   验收测试通过率: P/T（P=通过数，T=总数）
   评分规则（不可主观调整）：
   - 基础分 = floor(P/T * 10)
   - 若 acceptance_tests.sh 不存在或无法运行：基础分 = 0
   - 可在基础分上 ±1 调整（代码质量/边界情况），但不能超过 ±1
   SCORE: X/10（必须是最后一行，格式固定）
"""
    return augment_prompt(base, task, project_root=cwd, phase_hint='review quality simplify')


# ─────────────────────────────────────────────────────────────
# Phase 6: DELIVER  交付
# ─────────────────────────────────────────────────────────────
def phase_deliver(task: str, cwd: Path, project_path: str = '') -> str:
    short = task[:60].replace('"', "'")
    # 只读关键文件，避免 context 爆炸
    key_files = []
    for name in ['02-define.md', '04-do.md', '05-review.md']:
        p = cwd / 'process' / name
        if p.exists():
            key_files.append(str(p))
    key_files_hint = '\n'.join(f'   - {f}' for f in key_files) if key_files else f'   - {cwd}/process/'

    # git commit 目标路径：优先用传入的 project_path，否则用 cwd
    git_target = project_path if project_path else str(cwd)

    base = f"""你是一个注重用户体验的交付专家。

任务: {task}
工作目录: {cwd}

{AUTO_MODE_PRINCIPLES}

【DELIVER - 交付阶段】

步骤：
1. 读取以下关键文档（不要读所有文件，只读这几个）：
{key_files_hint}
2. 用 Glob 列出所有产出文件
3. 用 Write 创建 {cwd}/RESULT.md（用户最终看的交付报告）：

   # 任务完成报告
   **任务**: {task}

   ## 交付物
   | 文件 | 说明 |
   |------|------|

   ## 完成情况（对照 DEFINE 成功标准逐项）
   验收测试通过率: X/Y（从步骤 3.5 的结果填入）

   ## 如何使用

   ## 过程摘要
   - DEFINE: 核心问题定义
   - DESIGN: 选择的方案
   - DO: 主要完成的工作
   - REVIEW: 质量情况

3.5 **交付前最终验证（强制，不可跳过，必须在 git commit 之前执行）**：
   - 用 Bash 执行 `bash {cwd}/process/acceptance_tests.sh`
   - 若全部通过：继续步骤 4
   - 若有 FAIL：停止，直接修复目标项目文件，修复后重新运行，直到全部通过才能继续
   - 将通过率写入 RESULT.md 的"完成情况"中

4. 在项目目录 {git_target} 执行 git 操作，严格按以下顺序：

   a. 检查是否是 git 仓库（`git status`），不是则 `git init`
   b. **拉取远端最新（必须在 commit 之前）**：
      ```
      git fetch origin
      ```
      若 fetch 失败（无远端/网络问题）跳过 b~d，直接到 e
   c. **检查是否有冲突或落后**：
      ```
      git status
      git log HEAD..origin/$(git branch --show-current) --oneline
      ```
   d. **若远端有新提交，必须先合并再 commit**：
      - 优先用 rebase：`git rebase origin/$(git branch --show-current)`
      - 若 rebase 有冲突：逐个文件用 Edit 解决冲突标记（<<<<<<< / ======= / >>>>>>>），然后 `git rebase --continue`
      - 若 rebase 失败：改用 merge：`git merge origin/$(git branch --show-current)`，同样解决冲突后 `git merge --continue`
      - 冲突解决后验证：`git diff --check`（无输出才算干净）
   e. **提交本次变更**：
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

    # 方案B：检测是否有 CLAUDE.md，有则注入约束
    claude_md = cwd / 'CLAUDE.md'
    if claude_md.exists():
        init_hint = f"""⚠️ 本项目已执行 autodev init，存在 {claude_md}。
**必须先用 Read 读取 {claude_md}**，其中包含：
- 完整的技术栈和已安装依赖（禁止重复安装）
- 项目文件列表（直接用，不要重新 Glob 扫描）
- 过程文档摘要（不要重复 WebSearch 调研）"""
    else:
        init_hint = f"""提示：建议执行 `autodev init --path {cwd}` 生成项目上下文，
可避免每次冷启动重复调研和安装依赖。"""

    base = f"""你是一个在持续对话中帮助完成具体任务的助手。

项目目录: {cwd}
本次问题 (#{qa_index}): {question}

【ASK - 持续追问模式】

{init_hint}

可用的项目上下文文件（按需读取）：
{context_hint}

执行步骤：
1. **读取上下文**：{'先读 CLAUDE.md，再按需读取以下文件' if claude_md.exists() else '用 Read 读取上述相关文件，理解项目背景'}
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
- **禁止重复安装依赖**（除非用户明确要求安装新包）
- **禁止无谓调研**（除非用户明确要求查最新资料）
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

    # 方案B：检测 CLAUDE.md
    claude_md = cwd / 'CLAUDE.md'
    if claude_md.exists():
        init_hint = f"""⚠️ 本项目已执行 autodev init，存在 {claude_md}。
**必须先用 Read 读取 {claude_md}**，其中包含技术栈、依赖、文件列表和过程摘要。
- 禁止重复安装依赖（除非明确需要新包）
- 禁止重复 WebSearch 调研（除非明确需要最新资料）"""
    else:
        init_hint = f"提示：建议执行 `autodev init --path {cwd}` 生成项目上下文。"

    base = f"""你是一个持续迭代开发的全能工程师。

项目目录: {cwd}
本次新需求 (迭代 #{iter_n}): {requirement}
迭代产出目录: {iter_dir}

【EXTEND - 迭代追加模式】

{init_hint}

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

4. **自验证（强制，不可跳过）**：
   - 若 {cwd}/process/acceptance_tests.sh 存在：用 Bash 执行 `bash {cwd}/process/acceptance_tests.sh`
     - 若有 FAIL：直接修复，修复后再次运行，直到全部通过
     - 若确实无法修复（尝试 2 次以上仍失败）：在 {iter_dir}/result.md 中明确写 `BLOCKED: <具体原因>`，停止本次迭代
   - 若不存在：用 Bash 运行编译/单元测试验证改动无回归，发现问题直接修复

5. **记录产出**：用 Write 将本次迭代结果写入 {iter_dir}/result.md：
   # 迭代 {iter_n} 结果
   ## 新需求: {requirement}
   ## 完成的工作
   ## 新增/修改的文件
   ## 验证结果（验收测试通过率，或 BLOCKED: 原因）

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


def phase_evolve(task: str, cwd: Path, iter_n: int, status_summary: str = '', review_score: int = -1) -> str:
    """
    EVOLVE 阶段：评估本次成果，决定下一步。
    prompt 故意保持简短，兼容弱模型。
    status_summary 由 driver 预提取注入，避免模型自己读文件出错。
    review_score: 从 05-review.md 提取的 SCORE (0-10)，-1 表示未知
    """
    evolve_file = cwd / 'process' / f'evolve-{iter_n}.md'
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    summary_block = f"""当前状态（已为你提取）：
---
{status_summary[:600]}
---""" if status_summary else f"请用 Read 读取 {cwd}/RESULT.md 了解当前状态。"

    # 分数决策提示
    if review_score >= 8:
        score_hint = f"REVIEW 评分: {review_score}/10 ✅ 质量良好，除非有明显 bug 否则可以考虑 DONE"
    elif review_score >= 6:
        score_hint = f"REVIEW 评分: {review_score}/10 ⚠️ 质量中等，找最重要的一个问题继续优化"
    elif review_score >= 0:
        score_hint = f"REVIEW 评分: {review_score}/10 ❌ 质量不足，必须继续改进"
    else:
        score_hint = "REVIEW 评分: 未知，根据状态摘要判断"

    return f"""原始任务: {task}
工作目录: {cwd}
当前迭代: #{iter_n}
{score_hint}

{summary_block}

你的工作：判断下一步最重要的改进是什么。

优先级（从高到低）：
1. acceptance_tests.sh 有 FAIL，或未运行过 acceptance_tests.sh → 必须写修复任务，禁止 DONE
2. 有 bug 或报错 → 写修复任务
3. 功能明显缺失 → 写补充任务
4. 体验或性能问题 → 写优化任务
5. acceptance_tests.sh 全部通过 且 评分 >= 8 且无明显问题 → 写 DONE

注意：没有运行 acceptance_tests.sh 的结果 = 视为有 FAIL，不能 DONE

用 Write 将结果写入 {evolve_file}，内容如下：

## 评估 #{iter_n}
时间: {ts}
评分: {review_score}/10
状态: {{一句话描述现在的状态}}
下一步: {{一句话描述最重要的改进，或"已完成"}}

NEXT_TASK: {{具体任务，或 DONE}}

注意：
- NEXT_TASK 必须是最后一行
- 只写一个任务，要具体（例如"修复登录返回500"，不要写"优化代码"）
- 不要重复上一轮已做过的事
"""


def phase_publish(task: str, cwd: Path) -> str:
    """--publish 触发，由 publish.py 管理"""
    from publish import publish_prompt
    return publish_prompt(task, cwd)


def phase_build(task: str, cwd: Path) -> str:
    """--build 触发，由 build.py 管理"""
    from build import build_prompt
    return build_prompt(task, cwd)
