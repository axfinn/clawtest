"""工作流引擎 - Workflow Engine"""

import subprocess
import os
import time
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.memory.memory_manager import MemoryManager
from core.state.state_manager import StateManager
from core.review.review_system import ReviewSystem


class Logger:
    """日志记录器 - 支持滚动写入"""

    def __init__(self, log_dir: Path = None, max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5):
        if log_dir is None:
            log_dir = Path.cwd() / '.claude' / 'logs'
        self.log_dir = log_dir
        self.log_file = log_dir / 'workflow.log'
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
        oldest = self.log_dir / f'workflow.{self.backup_count}.log'
        if oldest.exists():
            oldest.unlink()

        for i in range(self.backup_count - 1, 0, -1):
            src = self.log_dir / f'workflow.{i}.log'
            dst = self.log_dir / f'workflow.{i + 1}.log'
            if src.exists():
                src.rename(dst)

        if self.log_file.exists():
            self.log_file.rename(self.log_dir / 'workflow.1.log')

    def info(self, msg: str):
        self.write(msg, "INFO")

    def error(self, msg: str):
        self.write(msg, "ERROR")


class ProgressReporter:
    """定时进度 reporter - 防止卡死"""

    def __init__(self, interval: int = 30, logger: Logger = None):
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


class WorkflowEngine:
    """工作流引擎 - 执行完整开发流程"""

    PHASES = [
        'initialization',
        'requirements_analysis',
        'architecture_design',
        'implementation',
        'testing',
        'deployment',
        'complete'
    ]

    def __init__(self, memory_mgr: MemoryManager, state_mgr: StateManager, project_path: Path = None):
        self.memory_mgr = memory_mgr
        self.state_mgr = state_mgr
        self.review_system = ReviewSystem(memory_mgr)
        self.project_path = project_path or Path.cwd()
        self.logger = Logger(self.project_path / '.claude' / 'logs')
        self.reporter = ProgressReporter(interval=30, logger=self.logger)

        self.generated_files: List[str] = []
        self.quality_gates_passed: Dict[str, bool] = {}

    def log(self, message: str, level: str = "INFO"):
        """输出并记录日志"""
        print(message, flush=True)
        self.logger.write(message, level)
    
    def run_full_workflow(self, requirement: str, no_review: bool = False) -> Dict[str, Any]:
        """运行完整开发工作流"""
        result = {
            'success': False,
            'requirement': requirement,
            'phases_completed': [],
            'files': [],
            'errors': []
        }

        self.log("\n" + "="*50)
        self.log("🚀 启动全流程开发工作流")
        self.log("="*50)

        try:
            # Phase 1: Requirements Analysis
            self.log("\n📋 阶段 1: 需求分析")
            self.reporter.start("分析需求中...")
            req_result = self._phase_requirements_analysis(requirement)
            self.reporter.stop()
            result['phases_completed'].append('requirements_analysis')

            if not req_result['success']:
                result['errors'].append(f"需求分析失败: {req_result.get('error')}")
                return result

            # Phase 2: Architecture Design
            self.log("\n🏗️ 阶段 2: 架构设计")
            self.reporter.start("设计架构中...")
            arch_result = self._phase_architecture_design(req_result)
            self.reporter.stop()
            result['phases_completed'].append('architecture_design')

            # Phase 3: Implementation
            self.log("\n💻 阶段 3: 代码实现")
            self.reporter.start("实现代码中...")
            impl_result = self._phase_implementation(arch_result)
            self.reporter.stop()
            result['phases_completed'].append('implementation')
            result['files'] = self.generated_files

            # Phase 4: Testing
            if not no_review:
                self.log("\n🧪 阶段 4: 测试验证")
                test_result = self._phase_testing()
                result['phases_completed'].append('testing')

            # Phase 5: Quality Review (infinite loop if enabled)
            if not no_review:
                self.log("\n🔍 阶段 5: 质量审查")
                review_result = self._phase_quality_review(infinite=True)
                result['phases_completed'].append('quality_review')
                result['quality_gates'] = self.quality_gates_passed

            result['success'] = len(result['errors']) == 0

        except KeyboardInterrupt:
            result['errors'].append("工作流被用户中断")
            self._save_checkpoint('workflow_interrupted', result)

        except Exception as e:
            result['errors'].append(str(e))
            self._save_checkpoint('workflow_error', result)

        return result
    
    def _phase_requirements_analysis(self, requirement: str) -> Dict[str, Any]:
        """需求分析阶段"""
        self.state_mgr.update_state('requirements_analysis', {'requirement': requirement})
        
        # Parse requirement using Claude
        prompt = self._build_requirement_prompt(requirement)
        
        result = self._call_claude(prompt)
        
        requirements = {
            'original': requirement,
            'parsed': result.get('parsed_requirements', []),
            'user_stories': result.get('user_stories', []),
            'acceptance_criteria': result.get('acceptance_criteria', [])
        }
        
        self.memory_mgr.save_context('requirements_analysis', requirements)
        self.memory_mgr.log_decision('需求解析', '使用AI解析需求为用户故事和验收标准', requirements)
        
        return {'success': True, 'requirements': requirements}
    
    def _phase_architecture_design(self, req_result: Dict[str, Any]) -> Dict[str, Any]:
        """架构设计阶段"""
        self.state_mgr.update_state('architecture_design', req_result)
        
        requirements = req_result.get('requirements', {})
        
        prompt = self._build_architecture_prompt(requirements)
        result = self._call_claude(prompt)
        
        architecture = {
            'tech_stack': result.get('tech_stack', []),
            'architecture_pattern': result.get('architecture_pattern', 'modular'),
            'database_design': result.get('database_design', {}),
            'api_design': result.get('api_design', []),
            'file_structure': result.get('file_structure', {})
        }
        
        self.memory_mgr.save_context('architecture_design', architecture)
        self.memory_mgr.log_decision('技术栈选择', f"选择 {', '.join(architecture.get('tech_stack', []))}", architecture)
        
        return {'success': True, 'architecture': architecture}
    
    def _phase_implementation(self, arch_result: Dict[str, Any]) -> Dict[str, Any]:
        """代码实现阶段"""
        self.state_mgr.update_state('implementation', arch_result)
        
        architecture = arch_result.get('architecture', {})
        
        # Generate code files
        prompt = self._build_implementation_prompt(architecture)
        result = self._call_claude(prompt)
        
        # Save generated files info
        files = result.get('files', [])
        for f in files:
            self.generated_files.append(f.get('path', ''))
        
        self.memory_mgr.save_context('implementation', {'files': files})
        
        return {'success': True, 'files': files}
    
    def _phase_testing(self) -> Dict[str, Any]:
        """测试阶段"""
        self.state_mgr.update_state('testing', {'files': self.generated_files})
        
        # Generate test files
        prompt = self._build_testing_prompt(self.generated_files)
        result = self._call_claude(prompt)
        
        test_files = result.get('test_files', [])
        
        return {'success': True, 'test_files': test_files}
    
    def _phase_quality_review(self, infinite: bool = False, max_cycles: int = 10) -> Dict[str, Any]:
        """质量审查阶段"""
        cycle = 0

        while infinite and cycle < max_cycles:
            cycle += 1
            self.log(f"\n🔄 Review 循环 {cycle}/{max_cycles}")

            # Run review
            self.reporter.start("代码审查中...")
            review_result = self.review_system.run_review(self.generated_files)
            self.reporter.stop()

            # Check quality gates
            gates_passed = self._check_quality_gates(review_result)
            self.quality_gates_passed = gates_passed

            if all(gates_passed.values()):
                self.log("✅ 所有质量门禁通过!")
                break

            # If gates not passed, attempt to fix
            self.log("⚠️ 部分质量门禁未通过，尝试修复...")
            fix_result = self._fix_issues(review_result, gates_passed)

            if not fix_result.get('fixed'):
                self.log("❌ 无法自动修复，请手动处理")
                break

            self.memory_mgr.save_review_result(review_result)

        return {'cycles': cycle, 'gates': self.quality_gates_passed}
    
    def _check_quality_gates(self, review_result: Dict[str, Any]) -> Dict[str, bool]:
        """检查质量门禁"""
        gates = {
            'code_quality': review_result.get('code_quality_score', 0) >= 7,
            'test_coverage': review_result.get('test_coverage', 0) >= 70,
            'security': not review_result.get('security_issues'),
            'performance': review_result.get('performance_score', 0) >= 7
        }
        
        return gates
    
    def _fix_issues(self, review_result: Dict[str, Any], gates_passed: Dict[str, bool]) -> Dict[str, Any]:
        """修复质量问题"""
        issues = []
        for gate, passed in gates_passed.items():
            if not passed:
                issues.append(f"{gate} issues")
        
        prompt = f"""修复以下代码质量问题:
{chr(10).join(issues)}

当前代码问题:
{review_result.get('issues', [])}

请直接修复这些问题。"""
        
        result = self._call_claude(prompt)
        
        return {'fixed': result.get('fixed', False), 'result': result}
    
    def _call_claude(self, prompt: str) -> Dict[str, Any]:
        """调用 Claude CLI - 永不超时"""
        # Check if claude CLI is available
        try:
            # 启动进度报告
            self.reporter.start("等待 Claude 响应...")

            result = subprocess.run(
                ['claude', '--print'],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=None,  # 永不超时
                env={**os.environ, 'CLAUDE_API_KEY': os.environ.get('ANTHROPIC_API_KEY', '')}
            )

            self.reporter.stop()

            if result.returncode == 0:
                # Try to parse JSON response
                try:
                    import json
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {'raw_response': result.stdout}
            else:
                return {'error': result.stderr or 'Claude CLI 调用失败'}

        except FileNotFoundError:
            # Claude CLI not found, use mock for development
            self.reporter.stop()
            return self._mock_claude_response(prompt)
        except subprocess.TimeoutExpired:
            # 永不超时，重试
            self.reporter.update("Claude 响应超时，继续等待...")
            return self._call_claude(prompt)
    
    def _mock_claude_response(self, prompt: str) -> Dict[str, Any]:
        """Mock响应 - 用于开发测试"""
        if '需求' in prompt or 'requirement' in prompt.lower():
            return {
                'parsed_requirements': ['功能模块1', '功能模块2'],
                'user_stories': ['作为用户，我想要...'],
                'acceptance_criteria': ['功能可正常运行', '通过单元测试']
            }
        elif '架构' in prompt or 'architecture' in prompt.lower():
            return {
                'tech_stack': ['Python', 'FastAPI', 'PostgreSQL'],
                'architecture_pattern': 'clean_architecture',
                'file_structure': {'src/': '源代码'}
            }
        elif '实现' in prompt or 'implement' in prompt.lower():
            return {'files': []}
        else:
            return {}
    
    def _build_requirement_prompt(self, requirement: str) -> str:
        return f"""分析以下需求，返回JSON格式:
{{
    "parsed_requirements": ["需求1", "需求2"],
    "user_stories": ["用户故事1", "用户故事2"],
    "acceptance_criteria": ["验收标准1", "验收标准2"]
}}

需求: {requirement}"""
    
    def _build_architecture_prompt(self, requirements: Dict) -> str:
        return f"""根据以下需求设计架构，返回JSON格式:
{{
    "tech_stack": ["技术1", "技术2"],
    "architecture_pattern": "架构模式",
    "database_design": {{}},
    "api_design": [],
    "file_structure": {{}}
}}

需求: {requirements}"""
    
    def _build_implementation_prompt(self, architecture: Dict) -> str:
        return f"""根据以下架构实现代码，返回JSON格式:
{{
    "files": [{{"path": "文件路径", "content": "代码内容"}}]
}}

架构: {architecture}"""
    
    def _build_testing_prompt(self, files: List[str]) -> str:
        return f"""为以下文件生成测试:
{{
    "test_files": [{{"path": "测试文件路径", "content": "测试代码"}}]
}}

文件: {files}"""
    
    def _save_checkpoint(self, name: str, data: Dict[str, Any]):
        """保存检查点"""
        self.memory_mgr.create_checkpoint(name, data)
        self.state_mgr.save_snapshot(name)
