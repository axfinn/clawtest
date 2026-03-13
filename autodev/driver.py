#!/usr/bin/env python3
"""
AutoDev - 万能任务助手
串流程：Python 调度各阶段 → claude CLI 自主完成任务 → 产出结果 + 过程记录
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from runner import run_phase
from phases import PHASE_LIST


def run(task: str, project_path: Path, start_phase: int = 0):
    """
    主流程：依次执行各阶段，claude 全程自主操作
    start_phase: 0-indexed，用于断点恢复
    """
    project_path.mkdir(parents=True, exist_ok=True)
    (project_path / 'process').mkdir(exist_ok=True)

    print(f"\n{'='*60}")
    print(f"🤖 AutoDev 万能任务助手")
    print(f"   任务: {task}")
    print(f"   目录: {project_path}")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   阶段: {len(PHASE_LIST)} 个")
    print('='*60)

    results = {}

    for i, (label, prompt_fn, timeout) in enumerate(PHASE_LIST):
        if i < start_phase:
            print(f"⏭  跳过: {label}")
            continue

        prompt = prompt_fn(task, project_path)
        success = run_phase(prompt, project_path, f"阶段 {i+1}/{len(PHASE_LIST)}: {label}", timeout)
        results[label] = success

        if not success:
            print(f"\n⚠️  阶段「{label}」执行异常，继续下一阶段...", flush=True)

    # 汇总
    print(f"\n{'='*60}")
    print("📊 执行汇总:")
    for label, ok in results.items():
        icon = "✅" if ok else "⚠️ "
        print(f"   {icon} {label}")

    result_file = project_path / 'RESULT.md'
    if result_file.exists():
        print(f"\n📄 交付报告: {result_file}")

    print(f"📁 工作目录: {project_path}")
    print(f"   完成时间: {datetime.now().strftime('%H:%M:%S')}")


def main():
    parser = argparse.ArgumentParser(
        description='AutoDev - 万能任务助手（无监管自主完成任务）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
任何任务都能完成：

  # 软件开发
  python3 driver.py "用 Flask 创建用户认证系统" --path ./auth-project

  # 文档写作
  python3 driver.py "写一份 Redis 最佳实践技术文档" --path ./docs

  # 数据分析
  python3 driver.py "分析 data.csv，找出销售趋势并生成报告" --path ./analysis

  # 内容创作
  python3 driver.py "写一篇关于微服务架构的技术博客，附代码示例" --path ./blog

  # 断点恢复（从第2阶段开始）
  python3 driver.py "任务描述" --path ./output --from 2
        """,
    )
    parser.add_argument('task', help='任务描述（任何类型都可以）')
    parser.add_argument('--path', '-p', default='./output',
                        help='工作目录（默认 ./output）')
    parser.add_argument('--from', dest='start_phase', type=int, default=1,
                        metavar='N', help='从第 N 阶段开始（1-4，用于断点恢复）')

    args = parser.parse_args()

    project_path = Path(args.path).resolve()
    start = max(0, args.start_phase - 1)  # 转为 0-indexed

    run(args.task, project_path, start_phase=start)


if __name__ == '__main__':
    main()
