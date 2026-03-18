#!/usr/bin/env python3
"""
autodev init - 为已有项目生成 CLAUDE.md，锁定上下文

作用：
  1. 扫描项目目录，提取已有文件、依赖、技术栈
  2. 读取 process/ 下的设计文档摘要
  3. 生成 CLAUDE.md，让后续 ask/extend 子进程直接冷启动就有完整上下文
  4. 明确写入"禁止重复安装依赖"等约束，避免每次冷启动重新下载
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path


# ──────────────────────────────────────────────────────────────
#  工具函数
# ──────────────────────────────────────────────────────────────

def _read_snippet(path: Path, max_lines: int = 20) -> str:
    """读取文件前 N 行作为摘要"""
    try:
        lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()
        snippet = '\n'.join(lines[:max_lines])
        if len(lines) > max_lines:
            snippet += f'\n... （共 {len(lines)} 行）'
        return snippet
    except Exception:
        return '（读取失败）'


def _list_files(cwd: Path) -> list[str]:
    """列出项目文件（忽略 .autodev/ process/ __pycache__ 等）"""
    ignore = {'.autodev', 'process', '__pycache__', '.git', 'node_modules',
              '_site', '_pdf', '.venv', 'venv', '.mypy_cache'}
    files = []
    for p in sorted(cwd.rglob('*')):
        if p.is_dir():
            continue
        if any(part in ignore for part in p.parts):
            continue
        rel = str(p.relative_to(cwd))
        files.append(rel)
    return files


def _detect_stack(cwd: Path, files: list[str]) -> dict:
    """检测技术栈和已有依赖"""
    stack = {}

    # Python
    req = cwd / 'requirements.txt'
    pyproject = cwd / 'pyproject.toml'
    if req.exists():
        stack['python'] = {'deps_file': 'requirements.txt',
                           'deps': req.read_text(errors='ignore').strip()}
    elif pyproject.exists():
        stack['python'] = {'deps_file': 'pyproject.toml', 'deps': '（见 pyproject.toml）'}
    elif any(f.endswith('.py') for f in files):
        stack['python'] = {'deps_file': None, 'deps': '（仅标准库）'}

    # Go
    gomod = cwd / 'go.mod'
    if gomod.exists():
        stack['go'] = {'deps_file': 'go.mod',
                       'deps': _read_snippet(gomod, 10)}

    # Node
    pkg = cwd / 'package.json'
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text())
            deps = list(data.get('dependencies', {}).keys())
            dev  = list(data.get('devDependencies', {}).keys())
            stack['node'] = {'deps_file': 'package.json',
                             'deps': ', '.join(deps + dev)}
        except Exception:
            stack['node'] = {'deps_file': 'package.json', 'deps': '（解析失败）'}

    # Rust
    if (cwd / 'Cargo.toml').exists():
        stack['rust'] = {'deps_file': 'Cargo.toml', 'deps': '（见 Cargo.toml）'}

    return stack


def _read_process_summaries(cwd: Path) -> dict[str, str]:
    """读取 process/ 下各阶段文档的摘要（前30行）"""
    summaries = {}
    process_dir = cwd / 'process'
    if not process_dir.exists():
        return summaries

    order = [
        ('01-discover.md', 'DISCOVER - 调研'),
        ('02-define.md',   'DEFINE - 问题定义'),
        ('03-design.md',   'DESIGN - 架构设计'),
        ('04-do.md',       'DO - 执行记录'),
        ('05-review.md',   'REVIEW - 审查'),
    ]
    for fname, label in order:
        p = process_dir / fname
        if p.exists():
            summaries[label] = _read_snippet(p, 30)

    # 迭代记录
    for iter_dir in sorted(process_dir.glob('iter-*')):
        result = iter_dir / 'result.md'
        if result.exists():
            summaries[f'迭代 {iter_dir.name}'] = _read_snippet(result, 20)

    return summaries


def _read_result(cwd: Path) -> str:
    """读取 RESULT.md 摘要"""
    r = cwd / 'RESULT.md'
    if r.exists():
        return _read_snippet(r, 40)
    return ''


def _load_state(cwd: Path) -> dict:
    """读取 .autodev/state.json"""
    st = cwd / '.autodev' / 'state.json'
    if st.exists():
        try:
            return json.loads(st.read_text())
        except Exception:
            pass
    return {}


# ──────────────────────────────────────────────────────────────
#  生成 CLAUDE.md
# ──────────────────────────────────────────────────────────────

def generate_claude_md(cwd: Path) -> Path:
    """扫描项目，生成 CLAUDE.md，返回文件路径"""
    files   = _list_files(cwd)
    stack   = _detect_stack(cwd, files)
    process = _read_process_summaries(cwd)
    result  = _read_result(cwd)
    state   = _load_state(cwd)
    ts      = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    task = state.get('task', '（未知任务）')
    iters = state.get('iterations', [])

    # ── 文件列表 ──
    files_section = '\n'.join(f'- {f}' for f in files) if files else '（空）'

    # ── 技术栈 & 依赖 ──
    stack_lines = []
    for lang, info in stack.items():
        deps_file = info.get('deps_file')
        deps      = info.get('deps', '')
        if deps_file:
            stack_lines.append(f'**{lang}** (依赖文件: `{deps_file}`)')
            if deps and len(deps) < 500:
                stack_lines.append(f'```\n{deps}\n```')
        else:
            stack_lines.append(f'**{lang}** (仅标准库，无需安装)')
    stack_section = '\n'.join(stack_lines) if stack_lines else '（未检测到）'

    # ── process 摘要 ──
    process_section = ''
    for label, snippet in process.items():
        process_section += f'\n### {label}\n```\n{snippet}\n```\n'

    # ── 迭代历史 ──
    iter_lines = '\n'.join(
        f'- 迭代 {it["n"]}: {it["requirement"]} ({it["time"][:10]})'
        for it in iters
    ) if iters else '（暂无迭代）'

    # ── RESULT 摘要 ──
    result_section = f'```\n{result}\n```' if result else '（暂无）'

    content = f"""# AutoDev 项目上下文
<!-- 由 autodev init 自动生成，时间: {ts} -->
<!-- 作用：为 ask/extend 子命令提供冷启动上下文，避免重复调研和安装依赖 -->

## 基本信息

- **项目目录**: `{cwd}`
- **原始任务**: {task}
- **初始化时间**: {ts}

## 🚫 重要约束（必须遵守）

1. **禁止重复安装依赖**：项目依赖已在下方列出，直接使用，不要执行 `pip install` / `npm install` / `go get` 等命令，除非用户明确要求安装新包
2. **禁止重复调研**：已有 process/ 文档覆盖了调研内容，不要重复 WebSearch，除非用户明确要求查最新资料
3. **直接操作文件**：基于下方文件列表直接 Read/Edit，不要先 Glob 扫描整个目录
4. **最小改动原则**：ask/extend 模式下只改必要的文件，不重构无关代码

## 技术栈 & 依赖

{stack_section}

## 项目文件列表

{files_section}

## 过程文档摘要

{process_section}

## 迭代历史

{iter_lines}

## 最终交付报告摘要

{result_section}
"""

    out = cwd / 'CLAUDE.md'
    out.write_text(content, encoding='utf-8')
    return out


# ──────────────────────────────────────────────────────────────
#  入口（供 driver.py 调用）
# ──────────────────────────────────────────────────────────────

def init_project(cwd: Path):
    """autodev init 主逻辑"""
    print(f"\n{'='*60}", flush=True)
    print(f"🔧 AutoDev init  初始化项目上下文", flush=True)
    print(f"   目录: {cwd}", flush=True)

    if not cwd.exists():
        print(f"❌ 目录不存在: {cwd}", flush=True)
        return

    out = generate_claude_md(cwd)

    # 统计
    files = _list_files(cwd)
    stack = _detect_stack(cwd, files)
    process_count = len(_read_process_summaries(cwd))

    print(f"\n✅ 生成完成: {out}", flush=True)
    print(f"   项目文件: {len(files)} 个", flush=True)
    print(f"   技术栈  : {', '.join(stack.keys()) or '未检测到'}", flush=True)
    print(f"   过程文档: {process_count} 份", flush=True)
    print(f"\n后续 ask/extend 将自动读取 CLAUDE.md，无需重复调研和安装依赖。", flush=True)
    print('='*60, flush=True)
