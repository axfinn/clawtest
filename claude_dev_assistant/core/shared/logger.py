"""日志记录器 - 支持滚动写入"""

import threading
from pathlib import Path
from datetime import datetime


class Logger:
    """日志记录器 - 支持滚动写入"""

    def __init__(self, log_dir: Path = None, log_name: str = 'driver.log',
                 max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5):
        if log_dir is None:
            log_dir = Path.cwd() / '.claude' / 'logs'
        self.log_dir = log_dir
        self.log_file = log_dir / log_name
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self._lock = threading.Lock()
        log_dir.mkdir(parents=True, exist_ok=True)

    def write(self, message: str, level: str = "INFO"):
        """写入日志"""
        with self._lock:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"[{timestamp}] [{level}] {message}\n"

            # 滚动日志
            if self.log_file.exists() and self.log_file.stat().st_size >= self.max_bytes:
                self._rotate()

            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_line)

    def _rotate(self):
        """日志滚动"""
        oldest = self.log_dir / f'driver.{self.backup_count}.log'
        if oldest.exists():
            oldest.unlink()

        for i in range(self.backup_count - 1, 0, -1):
            src = self.log_dir / f'driver.{i}.log'
            dst = self.log_dir / f'driver.{i + 1}.log'
            if src.exists():
                src.rename(dst)

        if self.log_file.exists():
            self.log_file.rename(self.log_dir / 'driver.1.log')

    def info(self, msg: str):
        self.write(msg, "INFO")

    def error(self, msg: str):
        self.write(msg, "ERROR")

    def warning(self, msg: str):
        self.write(msg, "WARNING")
