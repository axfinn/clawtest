#!/usr/bin/env python3
"""
Claude Dev Assistant - 自驱开发核心
使用 Claude Code CLI 生成真正的可用代码
"""

import subprocess
import json
import sys
import os
import re
import time
import shutil
from pathlib import Path
from datetime import datetime

from core.shared import Logger, ProgressReporter

# 默认路径 - 使用当前文件所在目录作为项目根目录
PROJECT_ROOT = Path(__file__).parent.resolve()
# 注意: LOG_DIR 现在是动态计算的，不再是模块级常量


def find_claude_binary() -> Path:
    """自动检测 Claude CLI 安装位置"""
    # 常见安装位置
    possible_paths = [
        Path('/usr/local/bin/claude'),           # Linux/macOS brew
        Path('/opt/homebrew/bin/claude'),        # macOS ARM brew
        Path('/usr/bin/claude'),                 # Linux 系统
        Path.home() / '.local' / 'bin' / 'claude',  # Linux user local
        Path.home() / 'bin' / 'claude',          # 用户 bin
        Path('/home/linuxbrew/.linuxbrew/bin/claude'),  # Linuxbrew
    ]

    # 首先检查常见路径
    for path in possible_paths:
        if path.exists() and path.is_file():
            return path

    # 尝试通过 which 命令查找
    claude_path = shutil.which('claude')
    if claude_path:
        return Path(claude_path)

    # 都找不到，返回默认路径（让用户自己配置）
    return Path('/usr/local/bin/claude')


DEFAULT_CLAUDE_BIN = find_claude_binary()


class ClaudeDriver:
    """Claude 开发驱动"""

    def __init__(self, project_path: Path = None, claude_bin: Path = None):
        self.project_path = project_path or PROJECT_ROOT
        self.claude_bin = claude_bin or DEFAULT_CLAUDE_BIN
        # 日志写到目标项目目录的 .claude/logs/ 下
        log_dir = self.project_path / '.claude' / 'logs'
        self.logger = Logger(log_dir)
        self.reporter = ProgressReporter(interval=30, logger=self.logger)  # 每30秒报告一次

    def log(self, message: str, level: str = "INFO"):
        """输出并记录日志"""
        print(message, flush=True)
        self.logger.write(message, level)

    def call_claude(self, prompt: str, timeout: int = None, max_retries: int = 3) -> str:
        """调用 Claude Code CLI - 使用循环重试而非递归"""
        retry_count = 0

        while retry_count < max_retries:
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
            if retry_count == 0:
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
                retry_count += 1
                if retry_count >= max_retries:
                    self.reporter.stop()
                    print(f"  ⚠️ Claude 响应超时，已重试 {max_retries} 次", file=sys.stderr)
                    return None
                self.reporter.update(f"Claude 响应超时，重试 {retry_count}/{max_retries}...")
                time.sleep(2)  # 短暂等待后重试
                continue

            except Exception as e:
                self.reporter.stop()
                print(f"  ⚠️ 调用失败: {e}", file=sys.stderr)
                return None

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

    def _is_mcp_available(self) -> bool:
        """检测 MCP 工具是否可用 - 通过检查环境变量"""
        # MCP 工具只在 Claude Code CLI 运行时可用
        # 检查是否在正确的环境中
        return os.environ.get('CLAUDE_API_KEY') is not None

    def list_existing_files(self) -> list:
        """列出已有文件（让 Claude 自己分析）"""
        if not self.project_path.exists():
            return []
        return [str(f.relative_to(self.project_path))
                for f in self.project_path.rglob('*')
                if f.is_file() and not f.name.startswith('.')]

    def develop(self, requirement: str) -> dict:
        """自动化开发 - 每个阶段都是 Claude 干活"""
        self.log(f"\n🤖 开始自驱开发: {requirement}")
        self.log(f"   模式: ⚡ Claude Code CLI")
        self.log(f"   Claude: {self.claude_bin}")
        self.log(f"   目标: {self.project_path}")

        # ========== 阶段 0: 扫描已有文件 ==========
        existing_files = self.list_existing_files()
        if existing_files:
            self.log(f"\n📂 已有 {len(existing_files)} 个文件:")
            for f in existing_files[:10]:
                self.log(f"   - {f}")
            if len(existing_files) > 10:
                self.log(f"   ... 还有 {len(existing_files) - 10} 个")

        # ========== 阶段 1: 需求调研 + WebSearch (Claude 干活) ==========
        self.log("\n" + "="*50)
        self.log("📋 阶段 1: 需求调研 + WebSearch")
        self.log("="*50)
        self.reporter.start("Claude 调研需求 + 搜索优秀方案中...")

        # 先搜索相关优秀方案
        search_keywords = requirement[:50] + " best practices implementation"
        self.log(f"  🔍 WebSearch: {search_keywords[:30]}...")

        # 使用 MCP 工具搜索
        search_info = ""
        try:
            # 检查是否在 Claude Code 环境中
            if 'mcp__MiniMax__web_search' in globals() or self._is_mcp_available():
                # 直接调用 MCP 工具，不需要 import
                search_results = mcp__MiniMax__web_search(query=search_keywords)
                if search_results and search_results.get('organic'):
                    for item in search_results['organic'][:3]:
                        search_info += f"- {item.get('title', '')}: {item.get('snippet', '')[:100]}...\n"
                    self.log(f"  → 找到 {len(search_results.get('organic', []))} 个相关结果")
            else:
                self.log("  ⚠️ WebSearch (MCP) 不可用（非 Claude Code 环境），跳过")
        except NameError:
            self.log("  ⚠️ WebSearch (MCP) 不可用，跳过")
        except Exception as e:
            self.log(f"  ⚠️ WebSearch 调用失败: {e}")

        research_prompt = f"""你是软件工程师。请根据以下需求进行调研。

需求: {requirement}

已有文件:
{chr(10).join(f"- {f}" for f in existing_files) if existing_files else "（无）"}

WebSearch 参考结果:
{search_info if search_info else "（无可用搜索结果）"}

请调研:
1. 分析已有文件的代码，理解现有架构
2. 参考 WebSearch 结果，调研类似项目的最佳实现方式
3. 确定技术选型

返回 JSON:
{{"research": "调研结论", "tech_stack": ["技术1", "技术2"], "existing_analysis": "已有代码分析", "references": ["参考1", "参考2"]}}"""

        research_result = self.call_claude(research_prompt)
        self.reporter.stop()

        research_data = {}
        if research_result:
            try:
                if '```json' in research_result:
                    research_result = research_result.split('```json')[1].split('```')[0]
                research_data = json.loads(research_result.strip())
                self.log(f"  → 技术栈: {research_data.get('tech_stack', [])}")
                self.log(f"  → 调研结论: {research_data.get('research', '')[:100]}...")
                refs = research_data.get('references', [])
                if refs:
                    self.log(f"  → 参考: {refs[:3]}")
            except:
                pass

        # ========== 阶段 2: 需求分析 (Claude 干活) ==========
        self.log("\n" + "="*50)
        self.log("📝 阶段 2: 需求分析")
        self.log("="*50)
        self.reporter.start("Claude 分析需求中...")

        analysis_prompt = f"""你是软件工程师。请分析以下需求。

需求: {requirement}

请生成:
1. 功能需求列表
2. 用户故事
3. 验收标准
4. 复杂度评估

返回 JSON:
{{"features": ["功能1", "功能2"], "user_stories": ["故事1"], "acceptance_criteria": ["标准1"], "complexity": "simple/medium/complex"}}"""

        analysis_result = self.call_claude(analysis_prompt)
        self.reporter.stop()

        analysis_data = {}
        if analysis_result:
            try:
                if '```json' in analysis_result:
                    analysis_result = analysis_result.split('```json')[1].split('```')[0]
                analysis_data = json.loads(analysis_result.strip())
                self.log(f"  → 功能点: {analysis_data.get('features', [])}")
                self.log(f"  → 复杂度: {analysis_data.get('complexity', 'unknown')}")

                # 调用 Claude 生成详细的需求规格文档
                self.reporter.start("Claude 生成需求规格文档...")
                spec_content = self.generate_spec(requirement, analysis_data)
                self.reporter.stop()

                # 保存详细需求文档到 docs/
                docs_dir = self.project_path / 'docs'
                docs_dir.mkdir(parents=True, exist_ok=True)
                requirements_path = docs_dir / '01-REQUIREMENTS.md'
                requirements_path.write_text(spec_content)
                self.log(f"  ✅ docs/01-REQUIREMENTS.md")
            except:
                pass

        # ========== 阶段 3: 技术方案 (Claude 干活) ==========
        self.log("\n" + "="*50)
        self.log("🏗️ 阶段 3: 技术方案设计")
        self.log("="*50)
        self.reporter.start("Claude 设计技术方案中...")

        design_prompt = f"""你是软件架构师。请根据以下需求设计技术方案。

需求: {requirement}
功能点: {analysis_data.get('features', [])}
技术栈: {research_data.get('tech_stack', []) if research_data else []}
已有文件: {existing_files}

请生成:
1. 系统架构
2. 模块设计
3. 数据结构
4. API 设计 (如有)

返回 JSON:
{{"architecture": "架构描述", "modules": ["模块1", "模块2"], "files": [{{"path": "文件", "content": "代码"}}]}}"""

        design_result = self.call_claude(design_prompt)
        self.reporter.stop()

        design_data = {}
        if design_result:
            try:
                if '```json' in design_result:
                    design_result = design_result.split('```json')[1].split('```')[0]
                design_data = json.loads(design_result.strip())
                self.log(f"  → 架构: {design_data.get('architecture', '')[:80]}...")
                self.log(f"  → 模块: {design_data.get('modules', [])}")
            except:
                pass

        # 调用 Claude 生成详细的技术方案文档
        self.reporter.start("Claude 生成技术方案文档...")
        spec = ""
        if analysis_data and docs_dir:
            spec_path = docs_dir / '01-REQUIREMENTS.md'
            if spec_path.exists():
                spec = spec_path.read_text()
        design_content = self.generate_design(requirement, analysis_data or {}, spec)
        self.reporter.stop()

        # 保存详细技术方案文档到 docs/
        if design_content:
            docs_dir = self.project_path / 'docs'
            docs_dir.mkdir(parents=True, exist_ok=True)
            design_path = docs_dir / '02-DESIGN.md'
            design_path.write_text(design_content)
            self.log(f"  ✅ docs/02-DESIGN.md")

        # ========== 阶段 4: 代码实现 (Claude 干活) ==========
        self.log("\n" + "="*50)
        self.log("💻 阶段 4: 代码实现")
        self.log("="*50)
        self.reporter.start("Claude 编写代码中...")

        code_prompt = f"""你是软件工程师。请根据以下需求和方案实现代码。

需求: {requirement}
技术方案: {design_data.get('architecture', '') if design_data else ''}
功能点: {analysis_data.get('features', []) if analysis_data else []}
已有文件: {existing_files}

重要:
1. 必须先读取分析已有文件代码
2. 增量开发，只返回需要新增或修改的文件
3. 如果修改已有文件，请包含完整内容

返回 JSON:
{{"files": [{{"path": "文件名", "content": "代码内容"}}]}}"""

        result = self.call_claude(code_prompt)

        # 解析结果
        files = []
        try:
            if '```json' in result:
                result = result.split('```json')[1].split('```')[0]
            data = json.loads(result.strip())
            files = data.get('files', [])
        except:
            self.log("  ⚠️ 解析失败，尝试其他方式", "WARNING")
            # 尝试提取文件（re 已在文件顶部导入）
            file_matches = re.findall(r'"path"\s*:\s*"([^"]+)"\s*,\s*"content"\s*:\s*"([^"]+)"', result, re.DOTALL)
            for path, content in file_matches:
                files.append({'path': path, 'content': content})

        if not files:
            self.log("  ❌ 未生成任何文件", "ERROR")
            return {'success': False}

        # 写入文件
        self.reporter.stop()
        self.log(f"\n💾 写入 {len(files)} 个文件:")
        total = len(files)
        for idx, f in enumerate(files):
            self.reporter.start(f"写入文件中 ({idx+1}/{total}): {f['path']}")
            path = self.project_path / f['path']
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f['content'])
            self.reporter.stop()
            self.log(f"  ✅ {f['path']} ({len(f['content'])} bytes)")

        # ========== 阶段 5: 测试用例 (Claude 干活) ==========
        self.log("\n" + "="*50)
        self.log("🧪 阶段 5: 生成测试用例")
        self.log("="*50)
        self.reporter.start("Claude 生成测试用例中...")

        test_prompt = f"""你是测试工程师。请为以下代码生成测试用例。

需求: {requirement}
功能点: {analysis_data.get('features', []) if analysis_data else []}
代码文件:
{chr(10).join(f"- {f['path']}" for f in files)}

请生成:
1. 单元测试
2. 集成测试用例
3. 测试覆盖点

返回 JSON:
{{"test_files": [{{"path": "测试文件路径", "content": "测试代码"}}]}}"""

        test_result = self.call_claude(test_prompt)
        self.reporter.stop()

        test_files = []
        test_plan_content = ""
        if test_result:
            try:
                if '```json' in test_result:
                    test_result = test_result.split('```json')[1].split('```')[0]
                test_data = json.loads(test_result.strip())
                test_files = test_data.get('test_files', [])

                # 生成测试计划文档内容
                test_plan_content = f"""# 测试计划

## 测试目标
验证 {requirement} 的功能实现

## 功能点
{chr(10).join(f"- {f}" for f in analysis_data.get('features', [])) if analysis_data else ''}

## 测试文件
{chr(10).join(f"- {tf['path']}" for tf in test_files)}

## 测试覆盖点
{test_data.get('coverage_points', []) if isinstance(test_data, dict) else ''}
"""

                # 保存测试计划文档到 docs/
                docs_dir = self.project_path / 'docs'
                docs_dir.mkdir(parents=True, exist_ok=True)
                test_plan_path = docs_dir / '03-TEST_PLAN.md'
                test_plan_path.write_text(test_plan_content)
                self.log(f"  ✅ docs/03-TEST_PLAN.md")

                # 保存测试文件
                for tf in test_files:
                    path = self.project_path / tf['path']
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(tf['content'])
                    self.log(f"  ✅ {tf['path']} ({len(tf['content'])} bytes)")
            except:
                pass

        # ========== 阶段 6: 测试回归 (Claude 干活) ==========
        self.log("\n" + "="*50)
        self.log("🔁 阶段 6: 测试回归验证")
        self.log("="*50)
        self.reporter.start("Claude 运行测试回归中...")

        regression_prompt = f"""你是测试工程师。请运行测试并验证代码。

已生成的代码文件:
{chr(10).join(f"- {f['path']}" for f in files)}

测试文件:
{chr(10).join(f"- {tf['path']}" for tf in test_files) if test_files else "（无）"}

请:
1. 运行测试用例
2. 检查测试是否通过
3. 如有问题，返回需要修复的文件

返回 JSON:
{{"passed": true/false, "test_results": ["测试结果"], "fix_needed": true/false, "fix_files": [{{"path": "文件", "content": "修复代码"}}]}}"""

        regression_result = self.call_claude(regression_prompt)
        self.reporter.stop()

        if regression_result:
            try:
                if '```json' in regression_result:
                    regression_result = regression_result.split('```json')[1].split('```')[0]
                regression_data = json.loads(regression_result.strip())
                passed = regression_data.get('passed', False)
                if passed:
                    self.log("  ✅ 测试回归通过!")
                else:
                    self.log(f"  ⚠️ 测试有问题: {regression_data.get('test_results', [])}")
            except:
                pass

        # ========== 阶段 7: 代码审查 (Claude 干活) - 循环 ==========
        self.log("\n" + "="*50)
        self.log("🔍 阶段 7: 代码审查循环")
        self.log("="*50)

        for cycle in range(1, 6):  # 最多5轮
            self.log(f"\n🔄 审查循环 {cycle}/5")
            self.reporter.start(f"Claude 审查代码中 ({cycle}/5)...")

            review_prompt = f"""你是代码审查专家。请审查以下代码。

需求: {requirement}
已生成的文件:
{chr(10).join(f"- {f['path']}" for f in files)}

请检查:
1. 语法错误
2. 逻辑问题
3. 安全性问题
4. 代码规范
5. 是否符合需求

返回 JSON:
{{"issues": ["问题1", "问题2"], "passed": true/false, "improved_files": [{{"path": "文件", "content": "改进代码"}}]}}"""

            review_result = self.call_claude(review_prompt)
            self.reporter.stop()

            if not review_result:
                break

            try:
                if '```json' in review_result:
                    review_result = review_result.split('```json')[1].split('```')[0]
                review_data = json.loads(review_result.strip())
            except:
                break

            issues = review_data.get('issues', [])
            improved = review_data.get('improved_files', [])
            passed = review_data.get('passed', False)

            if passed or not issues:
                self.log("  ✅ 代码审查通过!")
                break

            self.log(f"  ⚠️ 发现 {len(issues)} 个问题，Claude 正在改进...")
            for f in improved:
                path = self.project_path / f['path']
                path.write_text(f['content'])
                self.log(f"  ✅ 改进: {f['path']}")

            # 更新文件列表
            files = [f for f in files if f['path'] not in [i['path'] for i in improved]] + improved

        # ========== Git 提交 ==========
        self.log("\n" + "="*50)
        self.log("📦 Git 提交")
        self.log("="*50)

        import subprocess
        try:
            # 检查是否是 git 仓库
            result = subprocess.run(['git', 'rev-parse', '--git-dir'],
                                    cwd=self.project_path, capture_output=True)
            is_git_repo = result.returncode == 0

            if not is_git_repo:
                # 初始化 git 仓库
                subprocess.run(['git', 'init'], cwd=self.project_path, check=True)
                self.log("  ✅ Git 仓库初始化")

                # 创建 .gitignore
                gitignore_content = """# Dependencies
node_modules/
__pycache__/
*.pyc
.venv/
venv/

# IDE
.vscode/
.idea/

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# Claude
.claude/
"""
                gitignore_path = self.project_path / '.gitignore'
                gitignore_path.write_text(gitignore_content)
                self.log("  ✅ .gitignore 已创建")

            # 选择性添加文件（代码文件和文档）
            # 只添加代码文件、配置文件、文档，不添加日志和临时文件
            subprocess.run(['git', 'add',
                '*.py', '*.js', '*.ts', '*.jsx', '*.tsx',
                '*.json', '*.yaml', '*.yml', '*.md',
                '*.html', '*.css', '*.txt',
                'docs/',
                '-f'],  # 强制添加即使在 .gitignore 中
                cwd=self.project_path, check=True, capture_output=True)

            # 检查是否有要提交的文件
            result = subprocess.run(['git', 'status', '--porcelain'],
                                    cwd=self.project_path, capture_output=True)
            if result.stdout.strip():
                # 提交代码
                commit_msg = f"feat: 开发 {requirement[:50]}..."
                subprocess.run(['git', 'commit', '-m', commit_msg],
                             cwd=self.project_path, check=True)
                self.log("  ✅ 代码已提交")
            else:
                self.log("  ℹ️ 没有需要提交的新文件")

        except subprocess.CalledProcessError as e:
            self.log(f"  ⚠️ Git 操作失败: {e}")
        except Exception as e:
            self.log(f"  ⚠️ Git 提交失败: {e}")

        self.log("\n✅ 开发完成!")
        self.logger.info("=" * 50)
        self.logger.info("开发完成!")
        return {
            'success': True,
            'files': [f['path'] for f in files],
            'docs': ['docs/01-REQUIREMENTS.md', 'docs/02-DESIGN.md', 'docs/03-TEST_PLAN.md']
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
