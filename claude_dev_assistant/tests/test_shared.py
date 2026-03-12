"""测试公共模块"""

import unittest
import tempfile
import shutil
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.shared import Logger, ProgressReporter


class TestLogger(unittest.TestCase):
    """测试 Logger 类"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir)

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """测试初始化"""
        logger = Logger(self.log_dir)
        self.assertEqual(logger.log_dir, self.log_dir)
        self.assertTrue(self.log_dir.exists())

    def test_write(self):
        """测试写入日志"""
        logger = Logger(self.log_dir)
        logger.write("test message", "INFO")

        log_file = self.log_dir / 'driver.log'
        self.assertTrue(log_file.exists())

        content = log_file.read_text()
        self.assertIn("test message", content)
        self.assertIn("INFO", content)

    def test_info(self):
        """测试 info 方法"""
        logger = Logger(self.log_dir)
        logger.info("info message")

        log_file = self.log_dir / 'driver.log'
        content = log_file.read_text()
        self.assertIn("info message", content)

    def test_error(self):
        """测试 error 方法"""
        logger = Logger(self.log_dir)
        logger.error("error message")

        log_file = self.log_dir / 'driver.log'
        content = log_file.read_text()
        self.assertIn("error message", content)
        self.assertIn("ERROR", content)

    def test_warning(self):
        """测试 warning 方法"""
        logger = Logger(self.log_dir)
        logger.warning("warning message")

        log_file = self.log_dir / 'driver.log'
        content = log_file.read_text()
        self.assertIn("warning message", content)
        self.assertIn("WARNING", content)

    def test_log_rotation(self):
        """测试日志滚动"""
        # 创建一个小的 max_bytes 来触发滚动
        logger = Logger(self.log_dir, max_bytes=10)

        # 写入超过限制的内容
        for i in range(5):
            logger.write(f"message number {i}" * 10, "INFO")

        # 检查是否创建了滚动日志
        self.assertTrue((self.log_dir / 'driver.1.log').exists())


class TestProgressReporter(unittest.TestCase):
    """测试 ProgressReporter 类"""

    def test_init(self):
        """测试初始化"""
        reporter = ProgressReporter(interval=1)
        self.assertEqual(reporter.interval, 1)
        self.assertFalse(reporter.running)

    def test_start_stop(self):
        """测试启动和停止"""
        reporter = ProgressReporter(interval=1)
        reporter.start("测试消息")

        self.assertTrue(reporter.running)
        self.assertEqual(reporter.message, "测试消息")

        reporter.stop()
        self.assertFalse(reporter.running)

    def test_update_message(self):
        """测试更新消息"""
        reporter = ProgressReporter()
        reporter.start("原始消息")
        reporter.update("新消息")

        self.assertEqual(reporter.message, "新消息")


if __name__ == '__main__':
    unittest.main()
