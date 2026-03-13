#!/usr/bin/env python3
"""
AutoDev - 万能任务助手
方法论: DISCOVER → DEFINE → DESIGN → DO → REVIEW → DELIVER [→ PUBLISH]

日志: <项目目录>/.autodev/logs/
默认输出: /tmp/autodev/<自动命名>/
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

from runner import run_phase
from phases import PHASE_LIST
from state import (
    mark_phase_start, mark_phase_done, mark_finished,
    last_completed_phase, should_stop, clear_stop, save_state, load_state,
)


# ──────────────────────────────────────────────────────────────
#  工具函数
# ──────────────────────────────────────────────────────────────

def slugify(text: str, max_len: int = 40) -> str:
    """
    将任务描述转为英文目录名。
    策略：让 claude 翻译（在线），或本地提取关键英文词 + 时间戳。
    这里用本地轻量方案：提取英文字母数字 + 替换空格，
    中文部分通过 pinyin/简单映射忽略（保留已有英文词）。
    """
    text = text.strip()
    # 只保留 ASCII 字母、数字、空格、连字符
    ascii_only = re.sub(r'[^a-zA-Z0-9\s\-]', ' ', text)
    words = ascii_only.split()
    if words:
        slug = '-'.join(w.lower() for w in words[:6])  # 最多6个词
    else:
        # 纯中文：用固定前缀 + 时间戳区分
        slug = 'task'
    # 截断
    slug = slug[:max_len].strip('-')
    return slug or 'task'


def make_project_dir(task: str) -> Path:
    """自动生成项目目录：/tmp/autodev/<英文slug>-<时间戳>"""
    base = Path('/tmp/autodev')
    slug = slugify(task)
    ts   = datetime.now().strftime('%m%d-%H%M')
    name = f"{slug}-{ts}" if slug != 'task' else f"task-{ts}"
    return base / name


def write_session_log(cwd: Path, task: str, phases_run: list, results: dict):
    """在 .autodev/logs/session.log 写入本次会话摘要（含目录名↔任务原文对照）"""
    log_dir = cwd / '.autodev' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    lines = [
        f"\n{'#'*70}",
        f"# AutoDev 会话记录",
        f"# 时间    : {ts}",
        f"# 目录    : {cwd.name}",        # 英文目录名，便于 shell 操作
        f"# 全路径  : {cwd}",
        f"# 任务原文: {task}",             # 中文原始需求，便于回溯
        f"{'#'*70}",
        "",
    ]
    for label, ok in results.items():
        lines.append(f"  {'✅' if ok else '⚠️ '} {label}")
    lines.append("")

    with open(log_dir / 'session.log', 'a', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    # 同时在 /tmp/autodev/.index 维护全局索引（目录名 → 任务原文）
    index_file = cwd.parent / '.index'
    with open(index_file, 'a', encoding='utf-8') as f:
        f.write(f"{ts}\t{cwd.name}\t{task}\n")


# ──────────────────────────────────────────────────────────────
#  主流程
# ──────────────────────────────────────────────────────────────

def run(task: str, cwd: Path, start_phase: int = 0,
        publish: bool = False, build: bool = False):
    cwd.mkdir(parents=True, exist_ok=True)
    (cwd / 'process').mkdir(exist_ok=True)
    (cwd / '.autodev' / 'logs').mkdir(parents=True, exist_ok=True)

    total = len(PHASE_LIST)
    phases_str = " → ".join(name.split()[0] for name, _, _ in PHASE_LIST)
    if build:
        phases_str += " → BUILD"
    if publish:
        phases_str += " → PUBLISH"

    print(f"\n{'='*60}")
    print(f"🤖 AutoDev  万能任务助手")
    print(f"   任务: {task}")
    print(f"   目录: {cwd}")
    print(f"   日志: {cwd / '.autodev' / 'logs'}")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   流程: {phases_str}")
    print('='*60)

    results = {}

    # 记录任务信息到 state（供 autodev-stop 读取）
    st = load_state(cwd)
    st['task'] = task
    st['status'] = 'running'
    save_state(cwd, st)

    # 清除上次遗留的 STOP 信号（新运行时）
    if start_phase == 0:
        clear_stop(cwd)

    for i, (label, prompt_fn, timeout) in enumerate(PHASE_LIST):
        if i < start_phase:
            print(f"⏭  跳过: {label}")
            continue

        # 检查终止信号
        if should_stop(cwd):
            print(f"\n🛑 收到终止信号，在阶段「{label}」前停止", flush=True)
            print(f"   恢复运行: ./autodev \"{task}\" --path {cwd} --from {i+1}")
            break

        mark_phase_start(cwd, i, label)
        prompt = prompt_fn(task, cwd)
        ok = run_phase(prompt, cwd, f"{i+1}/{total}  {label}", timeout)
        mark_phase_done(cwd, i, ok)
        results[label] = ok

        if not ok:
            print(f"\n⚠️  [{label}] 执行异常，继续下一阶段...", flush=True)

    # 可选：编译构建
    if build:
        from build import build as do_build
        ok = do_build(task, cwd)
        results["BUILD 编译构建"] = ok

    # 可选：文档发布
    if publish:
        from publish import publish as do_publish
        ok = do_publish(task, cwd)
        results["PUBLISH 文档发布"] = ok

    mark_finished(cwd)
    # 会话日志
    write_session_log(cwd, task, PHASE_LIST, results)

    # 汇总
    print(f"\n{'='*60}")
    print("📊 执行汇总:")
    for label, ok in results.items():
        print(f"   {'✅' if ok else '⚠️ '} {label}")

    print()
    result_file = cwd / 'RESULT.md'
    site_dir    = cwd / '_site'
    pdf_file    = cwd / '_pdf' / 'document.pdf'
    log_dir     = cwd / '.autodev' / 'logs'

    if result_file.exists():
        print(f"📄 交付报告 : {result_file}")
    build_log = cwd / 'process' / '06-build.md'
    if build_log.exists():
        print(f"🔨 构建报告 : {build_log}")
    if site_dir.exists():
        print(f"🌐 文档站   : {site_dir}/index.html")
        print(f"   本地预览 : cd {cwd} && mkdocs serve")
        print(f"   部署     : cd {cwd} && mkdocs gh-deploy")
    if pdf_file.exists():
        print(f"📚 PDF 文件 : {pdf_file}")
    print(f"📝 执行日志 : {log_dir}/")
    print(f"📁 工作目录 : {cwd}")
    print(f"   完成时间 : {datetime.now().strftime('%H:%M:%S')}")


# ──────────────────────────────────────────────────────────────
#  入口
# ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='AutoDev - 万能任务助手（DISCOVER→DEFINE→DESIGN→DO→REVIEW→DELIVER）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
默认输出目录: /tmp/autodev/<任务名>-<时间戳>/

示例:
  # 不指定目录（自动命名）
  python3 driver.py "写 Redis 集群最佳实践文档" --publish

  # 指定目录
  python3 driver.py "用 Flask 实现 JWT 认证" --path ./projects/auth

  # 文档 + 发布
  python3 driver.py "写一本微服务架构实践手册" --path ./projects/book --publish

  # 断点恢复（从 DO 阶段重跑）
  python3 driver.py "任务" --path /tmp/autodev/xxx --from 4

  # 对已有目录单独发布文档站
  python3 publish.py --path /tmp/autodev/xxx --task "文档描述"
        """,
    )
    parser.add_argument('task', help='任务描述（任何类型）')
    parser.add_argument('--path', '-p', default=None,
                        help='工作目录（默认自动生成 /tmp/autodev/<名称>/）')
    parser.add_argument('--from', dest='start_phase', type=int, default=1, metavar='N',
                        help='从第 N 阶段开始，1=DISCOVER … 6=DELIVER（断点恢复用）')
    parser.add_argument('--build', action='store_true',
                        help='完成后自动编译构建（Go/Rust/C/Java/Node/Python）')
    parser.add_argument('--publish', action='store_true',
                        help='完成后自动生成 MkDocs 文档站（含 PDF 导出）')

    args = parser.parse_args()

    # 确定工作目录
    if args.path:
        cwd = Path(args.path).resolve()
    else:
        cwd = make_project_dir(args.task)
        print(f"📁 自动创建项目目录: {cwd}")

    start = max(0, args.start_phase - 1)
    run(args.task, cwd, start_phase=start, build=args.build, publish=args.publish)


if __name__ == '__main__':
    main()
