#!/usr/bin/env python3
"""
Claude CLI 调用器
- 流式输出到终端（实时进度）
- 完整日志写入 .autodev/logs/
- 移除嵌套检测，允许在任意环境运行
"""

import subprocess
import os
import json
import sys
import shutil
from datetime import datetime
from pathlib import Path


def find_claude() -> Path:
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


class PhaseLogger:
    """阶段日志记录器：写入 .autodev/logs/<phase>.log"""

    def __init__(self, cwd: Path, phase_label: str):
        log_dir = cwd / '.autodev' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)

        # 文件名：阶段标签 slug 化
        slug = phase_label.lower().replace(' ', '-').replace('/', '-')
        slug = ''.join(c for c in slug if c.isalnum() or c in '-_')
        self.log_file  = log_dir / f"{slug}.log"
        self.main_log  = log_dir / "driver.log"
        self.phase_label = phase_label
        self.start_time  = datetime.now()

    def _write(self, text: str, dest: Path):
        with open(dest, 'a', encoding='utf-8') as f:
            f.write(text)

    def header(self, prompt: str):
        ts = self.start_time.strftime('%Y-%m-%d %H:%M:%S')
        header = (
            f"\n{'='*70}\n"
            f"阶段: {self.phase_label}\n"
            f"时间: {ts}\n"
            f"{'='*70}\n"
            f"[PROMPT]\n{prompt}\n"
            f"{'─'*70}\n"
            f"[OUTPUT]\n"
        )
        self._write(header, self.log_file)
        self._write(header, self.main_log)

    def write(self, text: str):
        self._write(text, self.log_file)
        self._write(text, self.main_log)

    def footer(self, success: bool, turns: int = None, cost: float = None):
        elapsed = (datetime.now() - self.start_time).total_seconds()
        footer = (
            f"\n{'─'*70}\n"
            f"[RESULT] {'✅ 成功' if success else '⚠️  异常'}"
            f"  耗时: {elapsed:.1f}s"
            + (f"  轮次: {turns}" if turns else "")
            + (f"  费用: ${cost:.4f}" if cost else "")
            + f"\n{'='*70}\n"
        )
        self._write(footer, self.log_file)
        self._write(footer, self.main_log)


def run_phase(prompt: str, cwd: Path, label: str, timeout: int = None) -> bool:
    """
    运行一个阶段。
    - claude 在 cwd 下直接用工具完成任务
    - 实时输出到终端
    - 完整日志写入 .autodev/logs/
    """
    claude_bin = find_claude()
    logger = PhaseLogger(cwd, label)
    logger.header(prompt)

    # 移除嵌套检测变量
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

    turns = None
    cost  = None
    success = False

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

            logger.write(raw + '\n')   # 原始 JSON 行写入日志

            try:
                event = json.loads(raw)
                etype = event.get('type', '')

                if etype == 'assistant':
                    for block in event.get('message', {}).get('content', []):
                        if block.get('type') == 'text':
                            text = block['text']
                            print(text, end='', flush=True)

                elif etype == 'tool_use':
                    tool = event.get('tool_name', event.get('name', ''))
                    inp  = event.get('tool_input', event.get('input', {}))
                    hint = inp.get('file_path') or inp.get('query') or inp.get('command', '')
                    if hint:
                        msg = f"\n  🔧 {tool}: {str(hint)[:80]}"
                    else:
                        msg = f"\n  🔧 {tool}"
                    print(msg, flush=True)

                elif etype == 'result':
                    turns   = event.get('num_turns')
                    cost    = event.get('cost_usd')
                    success = True
                    print(f"\n\n✅ {label} 完成", flush=True)
                    if turns:
                        print(f"   轮次: {turns}", flush=True)
                    if cost:
                        print(f"   费用: ${cost:.4f}", flush=True)

                elif etype == 'error':
                    print(f"\n❌ 错误: {event.get('message', raw)}", flush=True)

            except json.JSONDecodeError:
                print(raw, flush=True)

        proc.wait()
        if proc.returncode != 0 and not success:
            success = False

    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        logger.write(f"ERROR: {e}\n")
    except KeyboardInterrupt:
        proc.terminate()
        print("\n⚠️  用户中断", flush=True)
        logger.write("INTERRUPTED\n")

    logger.footer(success, turns, cost)

    log_path = logger.log_file
    print(f"   📝 日志: {log_path}", flush=True)

    return success
