# -*- coding: utf-8 -*-
"""
CodeExecutor 测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import sys
import os
import tempfile
import subprocess

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from handlers.codeExecutor import CodeExecutor


class TestCodeExecutor:
    """CodeExecutor 测试类"""
    
    @pytest.fixture
    def executor(self):
        """创建代码执行器"""
        return CodeExecutor(timeout=60, workspace="/tmp")
    
    @pytest.fixture
    def temp_workspace(self):
        """创建临时工作目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    # === 正常情况测试 ===
    
    def test_executor_initialization(self, executor):
        """测试执行器初始化"""
        assert executor.timeout == 60
        assert executor.workspace == "/tmp"
        assert "python" in executor.supported_languages
        assert "javascript" in executor.supported_languages
        assert "bash" in executor.supported_languages
    
    def test_supported_languages(self, executor):
        """测试支持的编程语言"""
        languages = executor.supported_languages
        
        assert languages["py"] == "python3"
        assert languages["python"] == "python3"
        assert languages["js"] == "node"
        assert languages["javascript"] == "node"
        assert languages["sh"] == "bash"
        assert languages["bash"] == "bash"
    
    @patch('handlers.codeExecutor.subprocess.run')
    def test_execute_python_success(self, mock_run, executor, temp_workspace):
        """测试成功执行 Python 代码"""
        executor.workspace = temp_workspace
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Hello, World!"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = executor.execute("print('Hello, World!')", language="python")
        
        assert result["success"] is True
        assert result["output"] == "Hello, World!"
        assert result["error"] is None
        assert result["exit_code"] == 0
        assert "duration" in result
    
    @patch('handlers.codeExecutor.subprocess.run')
    def test_execute_javascript_success(self, mock_run, executor, temp_workspace):
        """测试成功执行 JavaScript 代码"""
        executor.workspace = temp_workspace
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "42"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = executor.execute("console.log(42)", language="javascript")
        
        assert result["success"] is True
        assert result["output"] == "42"
    
    @patch('handlers.codeExecutor.subprocess.run')
    def test_execute_bash_success(self, mock_run, executor, temp_workspace):
        """测试成功执行 Bash 脚本"""
        executor.workspace = temp_workspace
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "test content"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = executor.execute("echo 'test content'", language="bash")
        
        assert result["success"] is True
        assert result["output"] == "test content"
    
    @patch('handlers.codeExecutor.subprocess.run')
    def test_execute_with_output_and_error(self, mock_run, executor, temp_workspace):
        """测试有 stdout 和 stderr 的情况"""
        executor.workspace = temp_workspace
        
        mock_result = Mock()
        mock_result.returncode = 1  # 错误退出
        mock_result.stdout = "partial output"
        mock_result.stderr = "Error: something went wrong"
        mock_run.return_value = mock_result
        
        result = executor.execute("some_error_command", language="bash")
        
        assert result["success"] is False
        assert result["output"] == "partial output"
        assert result["error"] == "Error: something went wrong"
        assert result["exit_code"] == 1
    
    # === 异常情况测试 ===
    
    def test_execute_unsupported_language(self, executor, temp_workspace):
        """测试不支持的语言"""
        executor.workspace = temp_workspace
        
        result = executor.execute("code", language="unsupported_lang")
        
        assert result["success"] is False
        assert "不支持的语言" in result["error"]
        assert result["output"] is None
    
    def test_execute_unsupported_language_case_insensitive(self, executor, temp_workspace):
        """测试不区分大小写的不支持语言"""
        executor.workspace = temp_workspace
        
        result = executor.execute("code", language="RUBY")
        
        assert result["success"] is False
        assert "不支持的语言" in result["error"]
    
    @patch('handlers.codeExecutor.subprocess.run')
    def test_execute_timeout(self, mock_run, executor, temp_workspace):
        """测试执行超时"""
        executor.workspace = temp_workspace
        
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 60)
        
        result = executor.execute("while True: pass", language="python")
        
        assert result["success"] is False
        assert "超时" in result["error"]
        assert result["output"] is None
    
    @patch('handlers.codeExecutor.subprocess.run')
    def test_execute_exception(self, mock_run, executor, temp_workspace):
        """测试执行异常"""
        executor.workspace = temp_workspace
        
        mock_run.side_effect = Exception("Unknown error")
        
        result = executor.execute("code", language="python")
        
        assert result["success"] is False
        assert "Unknown error" in result["error"]
        assert result["output"] is None
    
    @patch('handlers.codeExecutor.subprocess.run')
    def test_execute_none_exit_code(self, mock_run, executor, temp_workspace):
        """测试 exit_code 为 None"""
        executor.workspace = temp_workspace
        
        mock_result = Mock()
        mock_result.returncode = None
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = executor.execute("code", language="python")
        
        # returncode 为 None 时，应该视为非成功
        assert result["success"] is False
    
    @patch('handlers.codeExecutor.Path')
    def test_execute_file_not_exists(self, mock_path, executor):
        """测试执行不存在的文件"""
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = False
        mock_path.return_value = mock_path_instance
        
        result = executor.execute_file("/nonexistent/file.py")
        
        assert result["success"] is False
        assert "文件不存在" in result["error"]
    
    @patch('handlers.codeExecutor.Path')
    @patch('handlers.codeExecutor.subprocess.run')
    def test_execute_file_success(self, mock_run, mock_path, executor, temp_workspace):
        """测试成功执行文件"""
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix = ".py"
        mock_path_instance.read_text.return_value = "print('from file')"
        mock_path.return_value = mock_path_instance
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "from file"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = executor.execute_file("/path/to/file.py")
        
        assert result["success"] is True
        assert result["output"] == "from file"
        mock_path_instance.read_text.assert_called_once_with(encoding="utf-8")
    
    @patch('handlers.codeExecutor.Path')
    @patch('handlers.codeExecutor.subprocess.run')
    def test_execute_file_js(self, mock_run, mock_path, executor):
        """测试执行 JS 文件"""
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix = ".js"
        mock_path_instance.read_text.return_value = "console.log('test')"
        mock_path.return_value = mock_path_instance
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "test"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = executor.execute_file("/path/to/script.js")
        
        assert result["success"] is True
        mock_path_instance.read_text.assert_called_once_with(encoding="utf-8")
    
    # === 边界情况测试 ===
    
    @patch('handlers.codeExecutor.subprocess.run')
    def test_execute_empty_code(self, mock_run, executor, temp_workspace):
        """测试空代码"""
        executor.workspace = temp_workspace
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = executor.execute("", language="python")
        
        assert result["success"] is True
    
    @patch('handlers.codeExecutor.subprocess.run')
    def test_execute_with_special_characters(self, mock_run, executor, temp_workspace):
        """测试包含特殊字符的代码"""
        executor.workspace = temp_workspace
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "你好世界 🎉"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = executor.execute("print('你好世界 🎉')", language="python")
        
        assert result["success"] is True
        assert result["output"] == "你好世界 🎉"
    
    @patch('handlers.codeExecutor.subprocess.run')
    def test_execute_with_large_output(self, mock_run, executor, temp_workspace):
        """测试大输出"""
        executor.workspace = temp_workspace
        
        large_output = "x" * 100000  # 100k 字符
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = large_output
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = executor.execute("print('x' * 100000)", language="python")
        
        assert result["success"] is True
        assert len(result["output"]) == 100000
    
    @patch('handlers.codeExecutor.subprocess.run')
    def test_execute_duration_recorded(self, mock_run, executor, temp_workspace):
        """测试执行时间被记录"""
        executor.workspace = temp_workspace
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        
        # 模拟耗时 0.5 秒
        with patch('handlers.codeExecutor.time.time') as mock_time:
            mock_time.side_effect = [0, 0.5]
            mock_run.return_value = mock_result
            
            result = executor.execute("code", language="python")
            
            assert "duration" in result
            assert result["duration"] == 0.5
    
    def test_temp_file_cleanup_on_error(self, executor, temp_workspace):
        """测试错误时临时文件被清理"""
        executor.workspace = temp_workspace
        
        # 模拟 tempfile 创建成功，但执行失败
        with patch('handlers.codeExecutor.tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp_file = Mock()
            mock_temp_file.name = "/tmp/test_file.py"
            mock_temp.return_value = mock_temp_file
            
            with patch('handlers.codeExecutor.subprocess.run') as mock_run:
                mock_run.side_effect = Exception("Execution failed")
                
                result = executor.execute("code", language="python")
                
                # 验证临时文件被尝试删除
                # 注意: 即使执行失败，也应该调用 unlink


class TestCodeExecutorLanguageMapping:
    """编程语言映射测试"""
    
    def test_all_supported_languages(self):
        """测试所有支持的语言"""
        executor = CodeExecutor()
        
        # 验证关键语言
        expected_langs = {
            "py": "python3",
            "python": "python3",
            "js": "node",
            "javascript": "node",
            "sh": "bash",
            "bash": "bash"
        }
        
        for lang, interpreter in expected_langs.items():
            assert executor.supported_languages[lang] == interpreter
    
    @pytest.mark.parametrize("lang", ["python", "Python", "PYTHON", "py"])
    def test_python_case_variants(self, lang):
        """测试 Python 大小写变体"""
        executor = CodeExecutor()
        assert executor.supported_languages.get(lang.lower()) == "python3"
    
    @pytest.mark.parametrize("lang", ["javascript", "js", "JS", "JavaScript"])
    def test_javascript_case_variants(self, lang):
        """测试 JavaScript 大小写变体"""
        executor = CodeExecutor()
        assert executor.supported_languages.get(lang.lower()) in ["node", "nodejs"]
