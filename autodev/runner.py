#!/usr/bin/env python3
"""
AI CLI 调用器
- 支持 Claude Code CLI（cc）和 Codex CLI（codex）
- 流式输出到终端（实时进度）
- 完整日志写入 .autodev/logs/
- 超时/挂起自动终止
"""

import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

CC_MODULE = 'cc'
CODEX_MODULE = 'codex'

# 空闲超时：连续多少秒无输出视为挂起，强制退出
IDLE_TIMEOUT = 180  # 秒（3分钟，原来600s太长）
HEARTBEAT_INTERVAL = 20  # 秒

# 熔断机制（借鉴 Claude Code Auto Mode）
# 连续失败 >= MAX_CONSECUTIVE_FAILURES 或 总失败 >= MAX_TOTAL_FAILURES 时触发熔断
MAX_CONSECUTIVE_FAILURES = 3
MAX_TOTAL_FAILURES = 20

# 全局熔断状态（per-run 重置，避免跨任务污染）
_circuit_state = {
    'consecutive_failures': 0,
    'total_failures': 0,
    'tripped': False,
}
_circuit_lock = threading.Lock()


def reset_circuit_breaker():
    """每次新任务开始时重置熔断状态，避免上一个任务的失败污染下一个"""
    with _circuit_lock:
        _circuit_state['consecutive_failures'] = 0
        _circuit_state['total_failures'] = 0
        _circuit_state['tripped'] = False


def normalize_module(module: str) -> str:
    return CODEX_MODULE if (module or '').strip().lower() == CODEX_MODULE else CC_MODULE


def runtime_display_name(module: str) -> str:
    return 'Codex CLI' if normalize_module(module) == CODEX_MODULE else 'Claude Code CLI'


def _find_binary(name: str, candidates: list, error_message: str) -> Path:
    found = shutil.which(name)
    if found:
        return Path(found)
    for candidate in candidates:
        candidate_path = Path(candidate)
        if candidate_path.exists():
            return candidate_path
    raise FileNotFoundError(error_message)


def find_claude() -> Path:
    return _find_binary(
        'claude',
        [
            '/usr/bin/claude',
            '/usr/local/bin/claude',
            Path.home() / '.local' / 'bin' / 'claude',
        ],
        '找不到 claude 命令，请先安装 Claude Code',
    )


def find_codex() -> Path:
    return _find_binary(
        'codex',
        [
            '/usr/bin/codex',
            '/usr/local/bin/codex',
            Path.home() / '.local' / 'bin' / 'codex',
        ],
        '找不到 codex 命令，请先安装 Codex CLI',
    )


def find_runtime(module: str) -> Path:
    module = normalize_module(module)
    return find_codex() if module == CODEX_MODULE else find_claude()


class PhaseLogger:
    """阶段日志记录器：写入 .autodev/logs/<phase>.log"""

    def __init__(self, cwd: Path, phase_label: str):
        log_dir = cwd / '.autodev' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)

        # 文件名：阶段标签 slug 化
        slug = phase_label.lower().replace(' ', '-').replace('/', '-')
        slug = ''.join(c for c in slug if c.isalnum() or c in '-_')
        self.log_file = log_dir / f"{slug}.log"
        self.main_log = log_dir / 'driver.log'
        self.phase_label = phase_label
        self.start_time = datetime.now()

    def _write(self, text: str, dest: Path):
        with open(dest, 'a', encoding='utf-8') as f:
            f.write(text)

    def header(self, prompt: str, module: str):
        ts = self.start_time.strftime('%Y-%m-%d %H:%M:%S')
        header = (
            f"\n{'=' * 70}\n"
            f"阶段: {self.phase_label}\n"
            f"模块: {runtime_display_name(module)} ({normalize_module(module)})\n"
            f"时间: {ts}\n"
            f"{'=' * 70}\n"
            f"[PROMPT]\n{prompt}\n"
            f"{'─' * 70}\n"
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
            f"\n{'─' * 70}\n"
            f"[RESULT] {'✅ 成功' if success else '⚠️  异常'}"
            f"  耗时: {elapsed:.1f}s"
            + (f"  轮次: {turns}" if turns else "")
            + (f"  费用: ${cost:.4f}" if cost else "")
            + f"\n{'=' * 70}\n"
        )
        self._write(footer, self.log_file)
        self._write(footer, self.main_log)


def _kill(proc: subprocess.Popen):
    """先 terminate，再 kill，确保子进程退出"""
    try:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    except OSError:
        pass


def build_env(module: str) -> dict:
    env = os.environ.copy()
    if normalize_module(module) == CC_MODULE:
        env.pop('CLAUDECODE', None)
    return env


def build_command(module: str, prompt: str, cwd: Path) -> list:
    module = normalize_module(module)
    runtime_bin = find_runtime(module)
    if module == CODEX_MODULE:
        return [
            str(runtime_bin),
            'exec',
            '--json',
            '--skip-git-repo-check',
            '--dangerously-bypass-approvals-and-sandbox',
            '-C',
            str(cwd),
            prompt,
        ]
    return [
        str(runtime_bin),
        '--print',
        '--dangerously-skip-permissions',
        '--verbose',
        '--output-format', 'stream-json',
        '-p', prompt,
    ]


def _print_tool_hint(tool: str, hint: str = ''):
    if hint:
        print(f"\n  🔧 {tool}: {str(hint)[:120]}", flush=True)
    else:
        print(f"\n  🔧 {tool}", flush=True)


def handle_claude_event(event: dict, label: str) -> dict:
    outcome = {}
    etype = event.get('type', '')

    if etype == 'assistant':
        for block in event.get('message', {}).get('content', []):
            if block.get('type') == 'text':
                print(block['text'], end='', flush=True)

    elif etype == 'tool_use':
        tool = event.get('tool_name', event.get('name', ''))
        inp = event.get('tool_input', event.get('input', {}))
        hint = inp.get('file_path') or inp.get('query') or inp.get('command', '')
        _print_tool_hint(tool, hint)

    elif etype == 'result':
        outcome['turns'] = event.get('num_turns')
        outcome['cost'] = event.get('cost_usd')
        outcome['success'] = True
        print(f"\n\n✅ {label} 完成", flush=True)
        if outcome['turns']:
            print(f"   轮次: {outcome['turns']}", flush=True)
        if outcome['cost']:
            print(f"   费用: ${outcome['cost']:.4f}", flush=True)

    elif etype == 'error':
        print(f"\n❌ 错误: {event.get('message', event)}", flush=True)

    return outcome


def handle_codex_event(event: dict, label: str) -> dict:
    outcome = {}
    etype = event.get('type', '')

    if etype == 'item.started':
        item = event.get('item', {})
        if item.get('type') == 'command_execution':
            _print_tool_hint('Bash', item.get('command', ''))

    elif etype == 'item.completed':
        item = event.get('item', {})
        item_type = item.get('type')
        if item_type == 'agent_message':
            text = (item.get('text') or '').strip()
            if text:
                print(text, flush=True)
        elif item_type == 'command_execution' and item.get('status') == 'failed':
            command = item.get('command', '')
            output = (item.get('aggregated_output') or '').strip()
            print(f"\n  ⚠️ 命令失败: {command[:120]}", flush=True)
            if output:
                print(output[-2000:], flush=True)

    elif etype == 'turn.completed':
        usage = event.get('usage', {})
        outcome['turns'] = 1
        outcome['success'] = True
        print(f"\n✅ {label} 完成", flush=True)
        input_tokens = usage.get('input_tokens')
        output_tokens = usage.get('output_tokens')
        if input_tokens is not None or output_tokens is not None:
            print(f"   Tokens: in={input_tokens or 0}, out={output_tokens or 0}", flush=True)

    elif etype == 'error':
        print(f"\n❌ 错误: {event.get('message', event)}", flush=True)

    return outcome


def process_event(module: str, event: dict, label: str) -> dict:
    if normalize_module(module) == CODEX_MODULE:
        return handle_codex_event(event, label)
    return handle_claude_event(event, label)


def _check_circuit_breaker() -> tuple[bool, str]:
    """
    检查熔断状态。
    返回 (is_tripped, message)
    """
    with _circuit_lock:
        if _circuit_state['tripped']:
            return True, f"熔断已触发（连续失败 {_circuit_state['consecutive_failures']} 次，总失败 {_circuit_state['total_failures']} 次）"
        return False, ""


def _record_success():
    """记录成功，重置连续失败计数"""
    with _circuit_lock:
        _circuit_state['consecutive_failures'] = 0


def _record_failure() -> bool:
    """
    记录失败，更新熔断状态。
    返回是否触发熔断
    """
    with _circuit_lock:
        _circuit_state['consecutive_failures'] += 1
        _circuit_state['total_failures'] += 1

        if (_circuit_state['consecutive_failures'] >= MAX_CONSECUTIVE_FAILURES or
            _circuit_state['total_failures'] >= MAX_TOTAL_FAILURES):
            _circuit_state['tripped'] = True
            return True
        return False


def get_circuit_state() -> dict:
    """获取当前熔断状态（用于调试）"""
    with _circuit_lock:
        return dict(_circuit_state)


def run_phase(prompt: str, cwd: Path, label: str, timeout: int = None, module: str = CC_MODULE) -> bool:
    """
    运行一个阶段。
    - 在 cwd 下直接调用选定的 AI CLI 完成任务
    - 实时输出到终端
    - 完整日志写入 .autodev/logs/
    - timeout: 阶段总超时（秒），None 表示不限（但仍有空闲超时）
    - 若进程挂起（无输出超过 IDLE_TIMEOUT 秒），自动终止
    - 熔断机制：连续失败 >= 3 或 总失败 >= 20 时停止自动重试
    """
    # 检查熔断状态
    tripped, msg = _check_circuit_breaker()
    if tripped:
        print(f"\n🛑 熔断已触发，停止自动执行: {msg}", flush=True)
        print(f"   请检查任务状态或手动重试", flush=True)
        return False

    module = normalize_module(module)
    logger = PhaseLogger(cwd, label)
    logger.header(prompt, module)

    cmd = build_command(module, prompt, cwd)
    env = build_env(module)

    # 获取当前熔断状态用于显示
    circuit = get_circuit_state()

    print(f"\n{'=' * 60}", flush=True)
    print(f"▶  {label}", flush=True)
    print(f"   模块: {runtime_display_name(module)} ({module})", flush=True)
    if timeout:
        print(f"   ⏱  总超时: {timeout}s  空闲超时: {IDLE_TIMEOUT}s", flush=True)
    else:
        print(f"   ⏱  空闲超时: {IDLE_TIMEOUT}s（无总时限）", flush=True)
    print(f"   🔴 熔断: 连续失败 {circuit['consecutive_failures']}/{MAX_CONSECUTIVE_FAILURES}，"
          f"总失败 {circuit['total_failures']}/{MAX_TOTAL_FAILURES}", flush=True)
    print('=' * 60, flush=True)

    turns = None
    cost = None
    success = False

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(cwd),
            env=env,
        )

        line_queue = queue.Queue()

        def _reader():
            try:
                for raw in proc.stdout:
                    line_queue.put(raw)
            finally:
                line_queue.put(None)

        reader_thread = threading.Thread(target=_reader, daemon=True)
        reader_thread.start()

        start_time = time.monotonic()
        last_output = time.monotonic()
        last_heartbeat = time.monotonic()
        timed_out = False

        while True:
            now = time.monotonic()
            elapsed = now - start_time
            idle = now - last_output

            if now - last_heartbeat >= HEARTBEAT_INTERVAL:
                last_heartbeat = now
                circuit = get_circuit_state()
                print(f"   ⏳ 运行中... 已用 {elapsed:.0f}s，空闲 {idle:.0f}s/{IDLE_TIMEOUT}s  "
                      f"连续失败 {circuit['consecutive_failures']}/{MAX_CONSECUTIVE_FAILURES}", flush=True)
                logger.write(f"[HEARTBEAT] elapsed={elapsed:.0f}s idle={idle:.0f}s "
                             f"consecutive={circuit['consecutive_failures']} total={circuit['total_failures']}\n")

            if timeout and elapsed >= timeout:
                timed_out = True
                print(f"\n⏱  总超时 {timeout}s，强制终止 [{label}]", flush=True)
                logger.write(f"TIMEOUT after {elapsed:.0f}s\n")
                _kill(proc)
                break

            if idle >= IDLE_TIMEOUT:
                timed_out = True
                print(f"\n⏱  空闲超时 {IDLE_TIMEOUT}s（进程可能挂起），强制终止 [{label}]", flush=True)
                logger.write(f"IDLE TIMEOUT after {idle:.0f}s idle\n")
                _kill(proc)
                break

            try:
                raw = line_queue.get(timeout=5)
            except queue.Empty:
                continue

            if raw is None:
                break

            last_output = time.monotonic()
            raw = raw.strip()
            if not raw:
                continue

            logger.write(raw + '\n')

            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                print(raw, flush=True)
                continue

            outcome = process_event(module, event, label)
            if 'turns' in outcome:
                turns = outcome['turns']
            if 'cost' in outcome:
                cost = outcome['cost']
            if 'success' in outcome:
                success = outcome['success']

        if not timed_out:
            proc.wait()
            if proc.returncode != 0:
                success = False

    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        logger.write(f"ERROR: {e}\n")
    except KeyboardInterrupt:
        _kill(proc)
        print("\n⚠️  用户中断", flush=True)
        logger.write("INTERRUPTED\n")

    # 更新熔断状态
    if success:
        _record_success()
    else:
        tripped = _record_failure()
        if tripped:
            print(f"\n🛑 熔断触发！连续失败 {circuit['consecutive_failures']}/{MAX_CONSECUTIVE_FAILURES}，"
                  f"总失败 {circuit['total_failures']}/{MAX_TOTAL_FAILURES}", flush=True)
            print(f"   后续阶段将停止自动执行", flush=True)

    logger.footer(success, turns, cost)
    print(f"   📝 日志: {logger.log_file}", flush=True)
    return success
