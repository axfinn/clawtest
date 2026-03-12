"""进度报告器"""

import time
import threading


class ProgressReporter:
    """定时进度 reporter - 防止卡死"""

    def __init__(self, interval: int = 30, logger=None):
        self.interval = interval
        self.running = False
        self.thread = None
        self.message = "运行中..."
        self.start_time = None
        self.logger = logger

    def start(self, message: str = "运行中..."):
        """启动进度报告"""
        self.message = message
        self.start_time = time.time()
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def update(self, message: str):
        """更新消息"""
        self.message = message

    def stop(self):
        """停止报告"""
        self.running = False

    def _run(self):
        """后台报告线程"""
        while self.running:
            elapsed = int(time.time() - self.start_time)
            mins = elapsed // 60
            secs = elapsed % 60
            msg = f"  ⏱️ [{mins:02d}:{secs:02d}] {self.message}"
            print(msg, flush=True)
            if self.logger:
                self.logger.info(msg)
            time.sleep(self.interval)
