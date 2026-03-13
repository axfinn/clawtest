#!/usr/bin/env python3
"""
Claude CLI 调用器
- 流式输出进度
- 直接操作文件（不解析 JSON）
- 允许在任意环境运行
"""

import subprocess
import os
import json
import sys
import shutil
from pathlib import Path


def find_claude() -> Path:
    """自动找 claude 命令"""
    p = shutil.which('claude')
    if p:
        return Path(p)
    for candidate in [
        '/usr/bin/claude',
        '/usr/local/bin/claude',
        Path.home() / '.local' / 'bin' / 'claude',
    ]:
        if Path(candidate).exists():
            return Path(candidate)
    raise FileNotFoundError("找不到 claude 命令，请先安装 Claude Code")


def run_phase(prompt: str, cwd: Path, label: str, timeout: int = None) -> bool:
    """
    运行一个开发阶段。

    Claude 直接在 cwd 目录下使用其工具（Read/Write/Edit/Bash/WebSearch 等）
    完成任务，不返回 JSON，流式输出到终端。

    返回 True 表示成功。
    """
    claude_bin = find_claude()

    # 移除嵌套检测变量，允许在 Claude Code 环境内调用
    env = os.environ.copy()
    env.pop('CLAUDECODE', None)

    cmd = [
        str(claude_bin),
        '--print',
        '--dangerously-skip-permissions',
        '--output-format', 'stream-json',
        '-p', prompt,
    ]

    print(f"\n{'='*60}", flush=True)
    print(f"▶  {label}", flush=True)
    print('='*60, flush=True)

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(cwd),
            env=env,
        )

        for raw in proc.stdout:
            raw = raw.strip()
            if not raw:
                continue
            try:
                event = json.loads(raw)
                etype = event.get('type', '')

                # 助手消息文本
                if etype == 'assistant':
                    for block in event.get('message', {}).get('content', []):
                        if block.get('type') == 'text':
                            print(block['text'], end='', flush=True)

                # 工具调用提示
                elif etype == 'tool_use':
                    tool = event.get('tool_name', event.get('name', ''))
                    inp  = event.get('tool_input', event.get('input', {}))
                    hint = inp.get('file_path') or inp.get('query') or inp.get('command', '')
                    if hint:
                        print(f"\n  🔧 {tool}: {str(hint)[:80]}", flush=True)
                    else:
                        print(f"\n  🔧 {tool}", flush=True)

                # 最终结果
                elif etype == 'result':
                    result_text = event.get('result', '')
                    cost = event.get('cost_usd')
                    turns = event.get('num_turns')
                    print(f"\n\n✅ {label} 完成", flush=True)
                    if turns:
                        print(f"   轮次: {turns}", flush=True)
                    if cost:
                        print(f"   费用: ${cost:.4f}", flush=True)

                # 系统错误
                elif etype == 'error':
                    print(f"\n❌ 错误: {event.get('message', raw)}", flush=True)

            except json.JSONDecodeError:
                # 非 JSON 行直接输出
                print(raw, flush=True)

        proc.wait()
        return proc.returncode == 0

    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        return False
    except KeyboardInterrupt:
        proc.terminate()
        print("\n⚠️  用户中断", flush=True)
        return False
