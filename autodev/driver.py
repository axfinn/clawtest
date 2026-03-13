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


# ──────────────────────────────────────────────────────────────
#  工具函数
# ──────────────────────────────────────────────────────────────

def slugify(text: str, max_len: int = 30) -> str:
    """将任务描述转为目录名"""
    # 提取前几个有意义的词
    text = text.strip()
    # 去掉标点，保留中文、字母、数字、空格
    cleaned = re.sub(r'[^\w\u4e00-\u9fff\s]', '', text)
    # 取前 max_len 字符，去掉末尾空格
    slug = cleaned[:max_len].strip()
    # 空格 → 连字符
    slug = re.sub(r'\s+', '-', slug)
    return slug or 'task'


def make_project_dir(task: str) -> Path:
    """自动生成项目目录：/tmp/autodev/<task-slug>-<时间戳>"""
    base = Path('/tmp/autodev')
    slug = slugify(task)
    ts   = datetime.now().strftime('%m%d-%H%M')
    return base / f"{slug}-{ts}"


def write_session_log(cwd: Path, task: str, phases_run: list, results: dict):
    """在 .autodev/logs/session.log 写入本次会话摘要"""
    log_dir = cwd / '.autodev' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    lines = [
        f"\n{'#'*70}",
        f"# AutoDev 会话记录",
        f"# 任务: {task}",
        f"# 时间: {ts}",
        f"# 目录: {cwd}",
        f"{'#'*70}",
        "",
    ]
    for label, ok in results.items():
        lines.append(f"  {'✅' if ok else '⚠️ '} {label}")
    lines.append("")

    with open(log_dir / 'session.log', 'a', encoding='utf-8') as f:
        f.write('\n'.join(lines))


# ──────────────────────────────────────────────────────────────
#  主流程
# ──────────────────────────────────────────────────────────────

def run(task: str, cwd: Path, start_phase: int = 0, publish: bool = False):
    cwd.mkdir(parents=True, exist_ok=True)
    (cwd / 'process').mkdir(exist_ok=True)
    (cwd / '.autodev' / 'logs').mkdir(parents=True, exist_ok=True)

    total = len(PHASE_LIST)
    phases_str = " → ".join(name.split()[0] for name, _, _ in PHASE_LIST)
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

    for i, (label, prompt_fn, timeout) in enumerate(PHASE_LIST):
        if i < start_phase:
            print(f"⏭  跳过: {label}")
            continue

        prompt = prompt_fn(task, cwd)
        ok = run_phase(prompt, cwd, f"{i+1}/{total}  {label}", timeout)
        results[label] = ok

        if not ok:
            print(f"\n⚠️  [{label}] 执行异常，继续下一阶段...", flush=True)

    # 可选：文档发布
    if publish:
        from publish import publish as do_publish
        ok = do_publish(task, cwd)
        results["PUBLISH 文档发布"] = ok

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
    run(args.task, cwd, start_phase=start, publish=args.publish)


if __name__ == '__main__':
    main()
