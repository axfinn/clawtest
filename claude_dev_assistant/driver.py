#!/usr/bin/env python3
"""
Claude Dev Assistant - 自驱开发核心
使用 Claude Code CLI 生成真正的可用代码
"""

import subprocess
import json
import sys
import os
import time
import threading
from pathlib import Path
from datetime import datetime

# 默认路径
DEFAULT_CLAUDE_BIN = Path('/home/node/.openclaw/workspace/tools/bin/claude')
PROJECT_ROOT = Path('/home/node/.openclaw/workspace/clawtest')
LOG_DIR = PROJECT_ROOT / '.claude' / 'logs'


class Logger:
    """日志记录器 - 支持滚动写入"""

    def __init__(self, log_dir: Path = LOG_DIR, max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5):
        self.log_dir = log_dir
        self.log_file = log_dir / 'driver.log'
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
        # 删除最旧的
        oldest = self.log_dir / f'driver.{self.backup_count}.log'
        if oldest.exists():
            oldest.unlink()

        # 滚动
        for i in range(self.backup_count - 1, 0, -1):
            src = self.log_dir / f'driver.{i}.log'
            dst = self.log_dir / f'driver.{i + 1}.log'
            if src.exists():
                src.rename(dst)

        # 当前日志重命名
        if self.log_file.exists():
            self.log_file.rename(self.log_dir / 'driver.1.log')

    def info(self, msg: str):
        self.write(msg, "INFO")

    def error(self, msg: str):
        self.write(msg, "ERROR")

    def warning(self, msg: str):
        self.write(msg, "WARNING")


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


class ClaudeDriver:
    """Claude 开发驱动"""

    def __init__(self, project_path: Path = None, claude_bin: Path = None):
        self.project_path = project_path or PROJECT_ROOT
        self.claude_bin = claude_bin or DEFAULT_CLAUDE_BIN
        self.logger = Logger(LOG_DIR)
        self.reporter = ProgressReporter(interval=30, logger=self.logger)  # 每30秒报告一次

    def log(self, message: str, level: str = "INFO"):
        """输出并记录日志"""
        print(message, flush=True)
        self.logger.write(message, level)

    def call_claude(self, prompt: str, timeout: int = None) -> str:
        """调用 Claude Code CLI - 永不超时"""
        cmd = [
            str(self.claude_bin),
            '--print',
            '--dangerously-skip-permissions',
            '-p', prompt
        ]

        # 使用干净的环境，避免会话冲突
        env = os.environ.copy()
        env.pop('CLAUDE_AI_SESSION_KEY', None)
        env.pop('CLAUDE_WEB_SESSION_KEY', None)

        # 确保目标目录存在
        if self.project_path:
            self.project_path.mkdir(parents=True, exist_ok=True)

        # 启动进度报告
        self.reporter.start("等待 Claude 响应...")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,  # None 表示永不超时
                cwd=str(self.project_path) if self.project_path.exists() else str(PROJECT_ROOT),
                env=env
            )

            self.reporter.stop()

            output = result.stdout.strip() or result.stderr.strip()

            if result.returncode == 0 or output:
                return output
            else:
                print(f"  ⚠️ Claude Error: {result.stderr[:200]}", file=sys.stderr)
                return None

        except subprocess.TimeoutExpired:
            self.reporter.update("Claude 响应超时，继续等待...")
            # 永不超时，继续等待
            return self.call_claude(prompt, timeout=None)
        except Exception as e:
            self.reporter.stop()
            print(f"  ⚠️ 调用失败: {e}", file=sys.stderr)
            return None
    
    def analyze_requirement(self, requirement: str) -> dict:
        """分析需求"""
        prompt = f"""分析以下需求，返回 JSON:
{{"features": ["功能1"], "tech_stack": ["Python"], "complexity": "simple"}}
需求: {requirement}
只返回 JSON。"""
        
        result = self.call_claude(prompt, timeout=60)
        if result:
            try:
                if '```json' in result:
                    result = result.split('```json')[1].split('```')[0]
                return json.loads(result.strip())
            except:
                pass
        
        return {"features": ["基础功能"], "tech_stack": ["Python"], "complexity": "simple"}
    
    def generate_spec(self, requirement: str, analysis: dict) -> str:
        """生成需求文档"""
        prompt = f"""根据以下需求生成需求规格文档 (Requirements Specification):

需求: {requirement}
技术栈: {analysis.get('tech_stack', [])}
功能点: {analysis.get('features', [])}

请生成详细的 Markdown 格式需求文档，包含:
1. 项目概述
2. 功能需求列表
3. 用户故事
4. 非功能需求 (性能、安全等)

返回格式: Markdown"""
        
        result = self.call_claude(prompt, timeout=120)
        return result or "需求文档生成失败"
    
    def generate_design(self, requirement: str, analysis: dict, spec: str) -> str:
        """生成技术方案"""
        prompt = f"""根据以下需求文档生成技术设计方案 (Technical Design):

需求: {requirement}
技术栈: {analysis.get('tech_stack', [])}
功能点: {analysis.get('features', [])}

需求文档:
{spec[:2000]}

请生成详细的 Markdown 格式技术方案，包含:
1. 系统架构
2. 模块设计
3. 数据结构
4. API 设计 (如有)
5. 技术选型理由

返回格式: Markdown"""
        
        result = self.call_claude(prompt, timeout=120)
        return result or "技术方案生成失败"
    
    def generate_code(self, requirement: str, analysis: dict, existing_files: list = None) -> list:
        """使用 Claude 生成完整代码"""

        # 构建已有文件信息（让 Claude 自己分析）
        existing_info = ""
        if existing_files:
            existing_info = "\n\n已有文件列表:\n" + "\n".join(f"- {f}" for f in existing_files)
            existing_info += "\n请先读取并分析这些已有文件的代码，然后进行增量开发。"

        if 'chrome' in requirement.lower() or '插件' in requirement:
            prompt = f"""你是Chrome插件工程师。需求: {requirement}
{existing_info}
只返回需要新增或修改的文件。
返回JSON: {{"files": [{{"path": "文件名", "content": "代码内容"}}]}}"""

        elif 'react' in requirement.lower() or 'vue' in requirement:
            prompt = f"""你是前端工程师。需求: {requirement}
{existing_info}
只返回需要新增或修改的文件。
返回JSON: {{"files": [{{"path": "文件名", "content": "代码内容"}}]}}"""

        else:
            prompt = f"""你是Python工程师。需求: {requirement}
{existing_info}
只返回需要新增或修改的文件。
返回JSON: {{"files": [{{"path": "文件名", "content": "代码内容"}}]}}"""

        result = self.call_claude(prompt, timeout=None)
        
        if result:
            try:
                if '```json' in result:
                    result = result.split('```json')[1].split('```')[0]
                data = json.loads(result.strip())
                return data.get('files', [])
            except:
                pass
        
        return []
    
    def review_code(self, files: list) -> dict:
        """审查代码"""
        issues = []
        
        for f in files:
            path = self.project_path / f['path']
            if not path.exists():
                issues.append(f"文件未创建: {f['path']}")
                continue
            
            content = path.read_text()
            if len(content) < 50:
                issues.append(f"{f['path']}: 内容太少")
            
            if f['path'].endswith('.py'):
                try:
                    compile(content, f['path'], 'exec')
                except SyntaxError as e:
                    issues.append(f"{f['path']}: 语法错误")
            
            if f['path'].endswith('.json'):
                try:
                    json.loads(content)
                except:
                    issues.append(f"{f['path']}: JSON错误")
        
        return {'score': max(0, 10 - len(issues)), 'issues': issues, 'passed': len(issues) == 0}

    def list_existing_files(self) -> list:
        """列出已有文件（让 Claude 自己分析）"""
        if not self.project_path.exists():
            return []
        return [str(f.relative_to(self.project_path))
                for f in self.project_path.rglob('*')
                if f.is_file() and not f.name.startswith('.')]

    def develop(self, requirement: str) -> dict:
        """自动化开发 - 只负责日志和流程串接"""
        self.log(f"\n🤖 开始自驱开发: {requirement}")
        self.log(f"   模式: ⚡ Claude Code CLI")
        self.log(f"   Claude: {self.claude_bin}")
        self.log(f"   目标: {self.project_path}")

        # 列出已有文件（让 Claude 自己分析）
        existing_files = self.list_existing_files()
        if existing_files:
            self.log(f"\n📂 已有 {len(existing_files)} 个文件:")
            for f in existing_files[:10]:
                self.log(f"   - {f}")
            if len(existing_files) > 10:
                self.log(f"   ... 还有 {len(existing_files) - 10} 个")

        # Step 1: 需求分析（包含已有内容信息，让 Claude 分析）
        self.log("\n📋 步骤1: 需求分析...")
        self.reporter.start("分析需求和已有代码...")
        existing_info = f"\n\n已有文件:\n" + "\n".join(f"- {f}" for f in existing_files) if existing_files else ""
        analysis = self.analyze_requirement(requirement + existing_info)
        self.reporter.stop()
        self.log(f"  → 技术栈: {analysis.get('tech_stack', [])}")
        self.log(f"  → 功能点: {analysis.get('features', [])}")

        # Step 2: 需求文档
        self.log("\n📝 步骤2: 生成需求文档...")
        self.reporter.start("生成需求文档...")
        spec = self.generate_spec(requirement, analysis)
        self.reporter.stop()
        spec_path = self.project_path / 'SPEC.md'
        spec_path.write_text(spec)
        self.log(f"  ✅ SPEC.md ({len(spec)} chars)")

        # Step 3: 技术方案
        self.log("\n🏗️ 步骤3: 生成技术方案...")
        self.reporter.start("生成技术方案...")
        design = self.generate_design(requirement, analysis, spec)
        self.reporter.stop()
        design_path = self.project_path / 'DESIGN.md'
        design_path.write_text(design)
        self.log(f"  ✅ DESIGN.md ({len(design)} chars)")

        # Step 4: 代码生成
        self.log("\n💻 步骤4: 生成代码...")
        self.reporter.start("生成代码中...")
        files = self.generate_code(requirement, analysis, existing_files)
        self.reporter.stop()

        if not files:
            self.log("  ❌ 代码生成失败", "ERROR")
            return {'success': False}

        # 写入文件
        total = len(files)
        for idx, f in enumerate(files):
            self.reporter.start(f"写入文件中 ({idx+1}/{total}): {f['path']}")
            path = self.project_path / f['path']
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f['content'])
            self.reporter.stop()
            self.log(f"  ✅ {f['path']} ({len(f['content'])} bytes)")

        # Step 5: 质量检查
        self.log("\n🔍 步骤5: 质量检查...")
        review = self.review_code(files)

        if review['passed']:
            self.log(f"  ✅ 通过 (score: {review['score']}/10)")
        else:
            self.log(f"  ⚠️ {len(review['issues'])} 个问题")

        self.log("\n✅ 开发完成!")
        self.logger.info("=" * 50)
        self.logger.info("开发完成!")
        return {
            'success': True,
            'files': [f['path'] for f in files],
            'docs': ['SPEC.md', 'DESIGN.md']
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Claude Dev Assistant')
    parser.add_argument('command', nargs='?', help='命令')
    parser.add_argument('args', nargs='*', help='参数')
    parser.add_argument('--path', '-p', type=str, help='项目路径')
    parser.add_argument('--claude', '-c', type=str, help='Claude CLI 路径')
    
    args = parser.parse_args()
    
    project_path = Path(args.path) if args.path else None
    claude_bin = Path(args.claude) if args.claude else None
    
    driver = ClaudeDriver(project_path, claude_bin)
    
    if args.command == 'develop' and args.args:
        requirement = ' '.join(args.args)
        driver.develop(requirement)
    else:
        print("用法:")
        print("  python3 driver.py develop <需求> --path <目录> --claude <claude路径>")


if __name__ == '__main__':
    main()
