"""
AutoDev 状态管理
- 记录每个项目当前运行到哪个阶段（.autodev/state.json）
- 支持断点恢复：读取上次进度
- 支持终止：写入 stop 信号，driver 主循环检查后退出
"""

import json
import os
import signal
from datetime import datetime
from pathlib import Path


STATE_FILE = '.autodev/state.json'
STOP_FILE  = '.autodev/STOP'        # 存在即终止


def state_path(cwd: Path) -> Path:
    return cwd / STATE_FILE


def stop_path(cwd: Path) -> Path:
    return cwd / STOP_FILE


# ──────────────────────────────────────────────────────────────
# 读写状态
# ──────────────────────────────────────────────────────────────

def load_state(cwd: Path) -> dict:
    p = state_path(cwd)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return {}


def save_state(cwd: Path, data: dict):
    p = state_path(cwd)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def mark_phase_start(cwd: Path, phase_index: int, phase_label: str):
    state = load_state(cwd)
    state.update({
        'status':        'running',
        'current_phase': phase_index,
        'phase_label':   phase_label,
        'started_at':    datetime.now().isoformat(),
        'pid':           os.getpid(),
    })
    save_state(cwd, state)


def mark_phase_done(cwd: Path, phase_index: int, success: bool):
    state = load_state(cwd)
    completed = state.get('completed_phases', [])
    completed.append({'index': phase_index, 'success': success,
                      'time': datetime.now().isoformat()})
    state['completed_phases'] = completed
    state['last_completed']   = phase_index
    save_state(cwd, state)


def mark_finished(cwd: Path):
    state = load_state(cwd)
    state['status']       = 'finished'
    state['finished_at']  = datetime.now().isoformat()
    state.pop('pid', None)
    save_state(cwd, state)


def last_completed_phase(cwd: Path) -> int:
    """返回上次完成的最后阶段序号（0-indexed），-1 表示未开始"""
    state = load_state(cwd)
    return state.get('last_completed', -1)


# ──────────────────────────────────────────────────────────────
# 终止信号
# ──────────────────────────────────────────────────────────────

def request_stop(cwd: Path):
    """写入 STOP 文件，driver 下次检查时退出"""
    p = stop_path(cwd)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(datetime.now().isoformat())

    # 如果进程还在，发送 SIGTERM
    state = load_state(cwd)
    pid = state.get('pid')
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"✅ 已向进程 {pid} 发送终止信号")
        except ProcessLookupError:
            print("ℹ️  进程已不存在")


def should_stop(cwd: Path) -> bool:
    """检查是否收到终止请求"""
    return stop_path(cwd).exists()


def clear_stop(cwd: Path):
    """清除 STOP 文件（恢复运行前调用）"""
    p = stop_path(cwd)
    if p.exists():
        p.unlink()
