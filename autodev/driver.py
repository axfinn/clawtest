#!/usr/bin/env python3
"""
AutoDev - 无监管自驱开发工具
串流程：Python 调度各阶段 → claude CLI 自主完成每个阶段
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from runner import run_phase
from phases import (
    phase_research,
    phase_requirements,
    phase_design,
    phase_implement,
    phase_test,
    phase_review,
    phase_commit,
)

# 阶段定义：(名称, prompt生成函数, 超时秒数)
PHASES = [
    ("调研",     phase_research,     180),
    ("需求规格", phase_requirements,  120),
    ("技术方案", phase_design,        120),
    ("代码实现", phase_implement,     None),   # 不限时
    ("测试",     phase_test,          300),
    ("代码审查", phase_review,        300),
    ("Git提交",  phase_commit,        60),
]


def develop(requirement: str, project_path: Path, start_phase: int = 0):
    """
    主流程：依次执行各阶段
    start_phase: 从第几阶段开始（0-indexed），用于断点恢复
    """
    project_path.mkdir(parents=True, exist_ok=True)
    (project_path / 'docs').mkdir(exist_ok=True)

    print(f"\n🤖 AutoDev 启动")
    print(f"   需求: {requirement}")
    print(f"   目录: {project_path}")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   阶段: {len(PHASES)} 个")

    results = {}

    for i, (label, prompt_fn, timeout) in enumerate(PHASES):
        if i < start_phase:
            print(f"⏭  跳过: {label}")
            continue

        prompt = prompt_fn(requirement, project_path)
        success = run_phase(prompt, project_path, f"阶段 {i+1}/{len(PHASES)}: {label}", timeout)
        results[label] = success

        if not success:
            print(f"\n⚠️  阶段「{label}」执行异常，继续下一阶段...", flush=True)

    # 汇总
    print(f"\n{'='*60}")
    print("📊 执行汇总:")
    for label, ok in results.items():
        icon = "✅" if ok else "⚠️ "
        print(f"   {icon} {label}")

    ok_count = sum(results.values())
    print(f"\n完成 {ok_count}/{len(results)} 个阶段")
    print(f"📁 输出目录: {project_path}")


def main():
    parser = argparse.ArgumentParser(
        description='AutoDev - 无监管自驱开发工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 driver.py "创建一个 Flask 用户认证系统" --path ./myproject
  python3 driver.py "Chrome 插件：自动翻译选中文字" --path ./translator
  python3 driver.py "用 React 做一个 Todo 应用" --path ./todo-app --from 3
        """,
    )
    parser.add_argument('requirement', help='需求描述')
    parser.add_argument('--path', '-p', default='.', help='项目目录（默认当前目录）')
    parser.add_argument('--from', dest='start_phase', type=int, default=0,
                        help='从第几阶段开始（1-7，用于断点恢复）')

    args = parser.parse_args()

    project_path = Path(args.path).resolve()
    start = max(0, args.start_phase - 1)  # 转为 0-indexed

    develop(args.requirement, project_path, start_phase=start)


if __name__ == '__main__':
    main()
