"""测试驱动核心功能"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from driver import ClaudeDriver


class TestClaudeDriver(unittest.TestCase):
    """测试 ClaudeDriver 核心功能"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir)
        self.driver = ClaudeDriver(project_path=self.project_path)

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.driver.project_path, self.project_path)
        self.assertIsNotNone(self.driver.logger)
        self.assertIsNotNone(self.driver.reporter)

    def test_list_existing_files_empty(self):
        """测试列出空目录"""
        files = self.driver.list_existing_files()
        self.assertEqual(files, [])

    def test_list_existing_files_with_files(self):
        """测试列出有文件的目录"""
        # 创建测试文件
        (self.project_path / "test.py").write_text("print('hello')")
        (self.project_path / "readme.md").write_text("# Test")

        files = self.driver.list_existing_files()
        self.assertEqual(len(files), 2)
        self.assertIn("test.py", files)

    def test_parse_json_response_valid(self):
        """测试解析有效 JSON"""
        response = '{"key": "value", "count": 42}'
        result = self.driver.parse_json_response(response)
        self.assertEqual(result["key"], "value")
        self.assertEqual(result["count"], 42)

    def test_parse_json_response_with_code_block(self):
        """测试解析带代码块的 JSON"""
        response = '''```json
{"key": "value"}
```'''
        result = self.driver.parse_json_response(response)
        self.assertEqual(result["key"], "value")

    def test_parse_json_response_invalid(self):
        """测试解析无效 JSON"""
        response = 'not valid json'
        result = self.driver.parse_json_response(response, {"default": True})
        self.assertEqual(result["default"], True)

    def test_parse_json_response_empty(self):
        """测试解析空响应"""
        result = self.driver.parse_json_response("")
        self.assertEqual(result, {})

    def test_parse_json_response_none(self):
        """测试解析 None 响应"""
        result = self.driver.parse_json_response(None)
        self.assertEqual(result, {})

    def test_review_code_empty(self):
        """测试审查空文件列表"""
        result = self.driver.review_code([])
        self.assertIn('score', result)
        self.assertIn('issues', result)

    def test_review_code_nonexistent_file(self):
        """测试审查不存在的文件"""
        result = self.driver.review_code([{"path": "nonexistent.py", "content": ""}])
        self.assertEqual(len(result['issues']), 1)
        self.assertIn("文件未创建", result['issues'][0])

    def test_review_code_valid_python(self):
        """测试审查有效 Python 文件"""
        content = "def hello():\n    print('hello')\n"
        (self.project_path / "hello.py").write_text(content)

        result = self.driver.review_code([{"path": "hello.py", "content": content}])
        self.assertGreaterEqual(result['score'], 0)  # 有效代码得分

    def test_review_code_invalid_python(self):
        """测试审查无效 Python 文件"""
        content = "def hello():\n    print('hello'\n"  # 缺少括号
        (self.project_path / "bad.py").write_text(content)

        result = self.driver.review_code([{"path": "bad.py", "content": content}])
        self.assertGreaterEqual(len(result['issues']), 1)

    def test_review_code_valid_json(self):
        """测试审查有效 JSON 文件"""
        content = '{"key": "value"}'
        (self.project_path / "data.json").write_text(content)

        result = self.driver.review_code([{"path": "data.json", "content": content}])
        self.assertGreaterEqual(result['score'], 0)

    def test_review_code_invalid_json(self):
        """测试审查无效 JSON 文件"""
        content = '{"key": "value"'  # 缺少 }
        (self.project_path / "bad.json").write_text(content)

        result = self.driver.review_code([{"path": "bad.json", "content": content}])
        self.assertGreaterEqual(len(result['issues']), 1)


class TestFindClaudeBinary(unittest.TestCase):
    """测试 Claude CLI 检测"""

    @patch('shutil.which')
    def test_find_claude_binary_from_which(self, mock_which):
        """测试从 which 找到 Claude"""
        mock_which.return_value = '/usr/local/bin/claude'

        from driver import find_claude_binary
        result = find_claude_binary()

        self.assertEqual(str(result), '/usr/local/bin/claude')


if __name__ == '__main__':
    unittest.main()
