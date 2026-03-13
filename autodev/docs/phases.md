# 阶段详解

AutoDev 基于"DISCOVER → DEFINE → DESIGN → DO → REVIEW → DELIVER"六阶段方法论。

## 方法论来源

| 思想 | 体现 |
|------|------|
| 第一性原理 | DISCOVER 阶段：先观察现实，不做假设 |
| 苏格拉底追问 | DEFINE 阶段：连续追问 Why，找到核心问题 |
| 奥卡姆剃刀 | DESIGN 阶段：优先最简单有效的方案 |
| 设计思维 | DEFINE + DESIGN：先理解问题，再解决 |
| PDCA 循环 | REVIEW 阶段：对照标准检查，发现问题修复 |

## 各阶段说明

### 1. DISCOVER — 发现

**目标**：了解任务的现实背景

- 用 WebSearch 搜索相关知识、参考案例（至少 2-3 次）
- 用 Glob/Read 扫描现有文件
- 记录：现状、外部参考、关键发现、未知项

**产出**：`process/01-discover.md`

---

### 2. DEFINE — 定义

**目标**：明确"为什么做"和"做什么"

- Why：这个任务解决什么痛点？
- Who：谁受益？他们最关心什么？
- What：交付物是什么？成功标准是什么（可量化）？
- Constraints：技术/时间/资源约束

**产出**：`process/02-define.md`，包含明确的**成功标准**（REVIEW 阶段用）

---

### 3. DESIGN — 设计

**目标**：规划最优方案（How）

- 列出 2-3 个可选方案
- 用奥卡姆剃刀选择最简有效的
- 写出具体执行步骤
- 预判风险

**产出**：`process/03-design.md`

---

### 4. DO — 执行

**目标**：全力完成实际工作

根据任务类型 claude 自主选择方式：
- 写代码 → Write/Edit 创建完整可运行文件
- 写文档 → Write 创建完整 Markdown
- 数据分析 → Bash 运行脚本 + Write 保存结果
- 需要安装依赖 → Bash 执行 pip/npm/go get 等

**原则**：完整可用，不留 TODO，遇到问题自主解决

**产出**：所有实际文件 + `process/04-do.md`（执行记录）

---

### 5. REVIEW — 审查

**目标**：对照成功标准验证，发现问题直接修复

- 逐项检查 DEFINE 中的成功标准
- 代码：用 Bash 运行测试
- 文档：通读检查完整性和准确性
- 发现问题：直接用 Edit/Bash 修复，不只列清单

**产出**：`process/05-review.md`

---

### 6. DELIVER — 交付

**目标**：打包产出，生成清晰的交付报告

- 列出所有产出文件
- 生成 `RESULT.md`（交付报告，给人看的）
- git init + git add + git commit

**产出**：`RESULT.md`

---

### BUILD（可选，`--build`）

**触发条件**：任务涉及需要编译的代码

- 自动识别项目类型（Go/Rust/C/Java/Node/Python）
- 生成 `build.sh`
- 执行编译，失败自动修复代码后重试
- 验证产物

**产出**：`build.sh` + `process/06-build.md`

---

### PUBLISH（可选，`--publish`）

**触发条件**：任务产出以文档为主

- 安装 `mkdocs-material` + `mkdocs-with-pdf`
- 扫描所有 `.md` 文件，生成 `mkdocs.yml` 导航
- `mkdocs build` → `_site/`（可部署静态站）
- PDF 导出 → `_pdf/document.pdf`

**产出**：`mkdocs.yml` + `_site/` + `_pdf/document.pdf`
