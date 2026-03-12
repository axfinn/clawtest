"""
代码执行器
自动执行 AI 生成的代码
"""
import subprocess
import tempfile
import os
import time
from typing import Dict, Optional
from pathlib import Path


class CodeExecutor:
    """代码执行器"""
    
    def __init__(self, timeout: int = 60, workspace: str = None):
        self # 秒.timeout = timeout 
        self.workspace = workspace or os.getcwd()
        self.supported_languages = {
            "js": "node",
            "javascript": "node",
            "py": "python3",
            "python": "python3",
            "sh": "bash",
            "bash": "bash"
        }
    
    def execute(self, code: str, language: str = "python") -> Dict:
        """执行代码字符串"""
        # 获取语言对应的解释器
        interpreter = self.supported_languages.get(language.lower())
        if not interpreter:
            return {
                "success": False,
                "error": f"不支持的语言: {language}",
                "output": None
            }
        
        # 创建临时文件
        suffix = language.lower().replace("javascript", "js")
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=f".{suffix}", delete=False, 
            dir=self.workspace, encoding="utf-8"
        ) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # 执行
            start_time = time.time()
            result = subprocess.run(
                [interpreter, temp_file],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.workspace
            )
            duration = time.time() - start_time
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
                "duration": duration,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "执行超时",
                "output": None,
                "duration": self.timeout
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": None
            }
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file)
            except:
                pass
    
    def execute_file(self, file_path: str) -> Dict:
        """执行文件"""
        path = Path(file_path)
        if not path.exists():
            return {"success": False, "error": "文件不存在"}
        
        language = path.suffix[1:]  # 去掉点
        return self.execute(path.read_text(encoding="utf-8"), language)


# 导出
__all__ = ["CodeExecutor"]
