#!/usr/bin/env python3
"""
AutoDev - 万能任务助手
方法论: DISCOVER → DEFINE → DESIGN → DO → REVIEW → DELIVER
"""

import argparse
from datetime import datetime
from pathlib import Path

from runner import run_phase
from phases import PHASE_LIST


def run(task: str, cwd: Path, start_phase: int = 0):
    cwd.mkdir(parents=True, exist_ok=True)
    (cwd / 'process').mkdir(exist_ok=True)

    total = len(PHASE_LIST)
    phases_str = " → ".join(name.split()[0] for name, _, _ in PHASE_LIST)

    print(f"\n{'='*60}")
    print(f"🤖 AutoDev  万能任务助手")
    print(f"   任务: {task}")
    print(f"   目录: {cwd}")
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

    # 汇总
    print(f"\n{'='*60}")
    print("📊 执行汇总:")
    for label, ok in results.items():
        print(f"   {'✅' if ok else '⚠️ '} {label}")

    result_file = cwd / 'RESULT.md'
    print(f"\n{'📄 交付报告: ' + str(result_file) if result_file.exists() else '⚠️  RESULT.md 未生成'}")
    print(f"📁 工作目录: {cwd}")
    print(f"   完成时间: {datetime.now().strftime('%H:%M:%S')}")


def main():
    parser = argparse.ArgumentParser(
        description='AutoDev - 万能任务助手（无监管，DISCOVER→DEFINE→DESIGN→DO→REVIEW→DELIVER）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 driver.py "用 Flask 实现 JWT 用户认证" --path ./projects/auth
  python3 driver.py "写一份 Kubernetes 入门技术文档" --path ./projects/k8s-doc
  python3 driver.py "分析 sales.csv 找出增长趋势" --path ./projects/analysis
  python3 driver.py "写一篇微服务架构博客" --path ./projects/blog

断点恢复（从 DO 阶段重跑）:
  python3 driver.py "任务" --path ./projects/xxx --from 4
        """,
    )
    parser.add_argument('task', help='任务描述（任何类型）')
    parser.add_argument('--path', '-p', default='./output', help='工作目录（默认 ./output）')
    parser.add_argument('--from', dest='start_phase', type=int, default=1, metavar='N',
                        help='从第 N 阶段开始，1=DISCOVER … 6=DELIVER（断点恢复用）')

    args = parser.parse_args()
    cwd = Path(args.path).resolve()
    start = max(0, args.start_phase - 1)

    run(args.task, cwd, start_phase=start)


if __name__ == '__main__':
    main()
