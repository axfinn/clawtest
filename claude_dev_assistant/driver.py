#!/usr/bin/env python3
"""
Claude Dev Assistant - 自驱开发核心
优先使用 Claude CLI，fallback 到智能生成
"""

import subprocess
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Claude CLI 路径
CLAUDE_BIN = Path('/home/node/.openclaw/workspace/tools/bin/claude')
PROJECT_ROOT = Path('/home/node/.openclaw/workspace/clawtest')


class ClaudeDriver:
    """Claude CLI 驱动核心"""
    
    def __init__(self, project_path: Path = None):
        self.project_path = project_path or PROJECT_ROOT
        self.history = []
        self.use_claude = self._check_claude_available()
    
    def _check_claude_available(self) -> bool:
        """检查 Claude CLI 是否可用"""
        try:
            result = subprocess.run(
                [str(CLAUDE_BIN), '--print', '--dangerously-skip-permissions', 'test'],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.project_path
            )
            # 检查是否返回了有效响应
            if result.returncode == 0 or 'hello' in result.stdout.lower():
                return True
            return False
        except Exception:
            return False
    
    def call(self, prompt: str, system_prompt: str = None) -> str:
        """调用 Claude CLI"""
        if not self.use_claude:
            return None  # 返回 None 使用 fallback
        
        cmd = [str(CLAUDE_BIN), '--print', '--dangerously-skip-permissions', '-p', prompt]
        
        if system_prompt:
            cmd.extend(['--append-system-prompt', system_prompt])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=self.project_path
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"Claude Error: {result.stderr}", file=sys.stderr)
                return None
                
        except subprocess.TimeoutExpired:
            print("⏱️ Claude 调用超时", file=sys.stderr)
            return None
        except Exception as e:
            print(f"❌ 调用失败: {e}", file=sys.stderr)
            return None
    
    def develop(self, requirement: str) -> dict:
        """自动化开发一个需求"""
        print(f"\n🤖 开始自驱开发: {requirement}")
        mode = "🤖 Claude" if self.use_claude else "⚡ 智能生成"
        print(f"   模式: {mode}")
        
        # Step 1: 需求分析
        print("📋 步骤1: 分析需求...")
        
        # 尝试用 Claude，失败则用本地
        analysis_raw = self.call(f"""
分析以下需求，返回 JSON 格式:
{{
    "features": ["功能1", "功能2"],
    "tech_stack": ["Python", "FastAPI"],
    "complexity": "simple|medium|complex"
}}

需求: {requirement}
""")
        
        if analysis_raw:
            analysis = self._parse_json(analysis_raw)
        else:
            analysis = self._local_analyze(requirement)
        
        print(f"  → 技术栈: {analysis.get('tech_stack', [])}")
        print(f"  → 功能点: {analysis.get('features', [])}")
        
        # Step 2: 代码实现
        print("💻 步骤2: 实现代码...")
        
        code_raw = self.call(f"""
根据以下需求实现代码:
需求: {requirement}
技术栈: {analysis.get('tech_stack', [])}
功能点: {analysis.get('features', [])}

返回 JSON:
{{
    "files": [{{"path": "文件名", "content": "代码"}}]
}}
""")
        
        if code_raw:
            files = self._parse_json(code_raw, key='files')
        else:
            files = self._local_generate(analysis)
        
        # 保存文件
        files_created = []
        for f in files:
            path = self.project_path / f['path']
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f['content'])
            files_created.append(f['path'])
            print(f"  ✅ {f['path']}")
        
        # Step 3: 语法检查
        print("🔍 步骤3: 质量检查...")
        review = self._review(files_created)
        
        if not review.get('passed', True):
            print("  ⚠️ 发现问题，尝试修复...")
            review = self._fix_and_review(files_created, review)
        
        print("\n✅ 开发完成!")
        
        return {
            'requirement': requirement,
            'analysis': analysis,
            'files': files_created,
            'review': review,
            'mode': mode
        }
    
    def _local_analyze(self, requirement: str) -> dict:
        """本地需求分析"""
        features = []
        tech_stack = []
        
        # 关键词匹配
        keywords = {
            '用户': ['用户管理', '注册', '登录'],
            'API': ['REST API', '接口'],
            '数据库': ['CRUD', '存储'],
            '前端': ['React', 'Vue', '页面'],
            '博客': ['文章', 'Markdown'],
        }
        
        for kw, feats in keywords.items():
            if kw in requirement:
                features.extend(feats)
        
        if 'Python' in requirement or 'python' in requirement:
            tech_stack = ['Python', 'FastAPI']
        elif '前端' in requirement or 'web' in requirement:
            tech_stack = ['React', 'TypeScript']
        else:
            tech_stack = ['Python', 'FastAPI']
        
        return {
            'requirement': requirement,
            'features': features[:5] or ['基础功能'],
            'tech_stack': tech_stack,
            'complexity': 'medium' if len(features) > 3 else 'simple'
        }
    
    def _local_generate(self, analysis: dict) -> list:
        """本地代码生成"""
        features = analysis.get('features', [])
        tech_stack = analysis.get('tech_stack', [])
        files = []
        
        if 'Python' in tech_stack and 'FastAPI' in tech_stack:
            # FastAPI 项目
            main_content = '''"""FastAPI 应用入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="API Server", version="1.0.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
'''
            
            if any(f in features for f in ['用户管理', '注册', '登录']):
                main_content += '''
class User(BaseModel):
    id: int | None = None
    username: str
    password: str

users_db = {}

# 用户认证
@app.post("/auth/register")
async def register(user: User):
    if user.username in users_db:
        return {"error": "用户已存在"}
    user_id = len(users_db) + 1
    users_db[user.username] = {"id": user_id, "username": user.username, "password": user.password}
    return {"id": user_id, "username": user.username}

@app.post("/auth/login")
async def login(user: User):
    db_user = users_db.get(user.username)
    if not db_user or db_user["password"] != user.password:
        return {"error": "用户名或密码错误"}
    return {"token": f"mock_token_{db_user['id']}", "user": db_user}

@app.get("/users")
async def get_users():
    return list(users_db.values())
'''
            
            if any(f in features for f in ['文章', '博客']):
                main_content += '''
class Article(BaseModel):
    id: int | None = None
    title: str
    content: str

articles_db = {}

@app.post("/articles")
async def create_article(article: Article):
    article_id = len(articles_db) + 1
    articles_db[article_id] = {"id": article_id, **article.dict()}
    return articles_db[article_id]

@app.get("/articles")
async def get_articles():
    return list(articles_db.values())

@app.get("/articles/{article_id}")
async def get_article(article_id: int):
    return articles_db.get(article_id, {"error": "文章不存在"})
'''
            
            if not any(f in features for f in ['用户管理', '注册', '登录', '文章', '博客']):
                main_content += '''
@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.get("/health")
async def health():
    return {"status": "ok"}
'''
            
            main_content += '''
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
            
            files.append({'path': 'main.py', 'content': main_content})
            files.append({'path': 'requirements.txt', 'content': 'fastapi>=0.100.0\nuvicorn>=0.23.0\npydantic>=2.0.0\n'})
            
        else:
            # 通用 Python
            content = f'''"""Generated Application"""
# Features: {", ".join(features)}

def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
'''
            files.append({'path': 'app.py', 'content': content})
        
        return files
    
    def _parse_json(self, text: str, key: str = None) -> dict:
        """解析 JSON 响应"""
        if not text:
            return {}
        
        # 提取 JSON 块
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0]
        elif '```' in text:
            text = text.split('```')[1].split('```')[0]
        
        try:
            data = json.loads(text.strip())
            if key:
                return data.get(key, [])
            return data
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
            return {}
    
    def _review(self, files: list) -> dict:
        """质量审查"""
        issues = []
        
        for f in files:
            path = self.project_path / f
            if not path.exists():
                continue
            
            content = path.read_text()
            
            # 基础检查
            if len(content) > 5000:
                issues.append(f"{f}: 文件过大 ({len(content)} chars)")
            
            if 'password' in content.lower() and '=' in content:
                if 'password=' in content.lower():
                    issues.append(f"{f}: 包含明文密码")
            
            # Python 语法检查
            if f.endswith('.py'):
                try:
                    compile(content, f, 'exec')
                except SyntaxError as e:
                    issues.append(f"{f}: 语法错误 - {e}")
        
        score = max(0, 10 - len(issues))
        
        return {
            'score': score,
            'issues': issues,
            'passed': len(issues) == 0
        }
    
    def _fix_and_review(self, files: list, review: dict) -> dict:
        """修复问题"""
        issues = review.get('issues', [])
        
        for issue in issues:
            # 简单修复
            if '语法错误' in issue:
                # 提取文件名
                f = issue.split(':')[0]
                path = self.project_path / f
                if path.exists():
                    content = path.read_text()
                    # 尝试修复常见语法错误
                    content = content.replace('\t', '    ')
                    path.write_text(content)
                    print(f"  🔧 已修复: {f}")
        
        return self._review(files)
    
    def interactive(self):
        """交互模式"""
        print("\n🤖 Claude Dev Assistant - 交互模式")
        print("输入需求开始开发，输入 'quit' 退出\n")
        
        while True:
            try:
                req = input("需求> ").strip()
                
                if not req:
                    continue
                if req.lower() in ['quit', 'exit', 'q']:
                    print("👋 再见!")
                    break
                
                self.develop(req)
                print()
                
            except KeyboardInterrupt:
                print("\n👋 再见!")
                break


def main():
    """CLI 入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Claude Dev Assistant - 自驱开发')
    parser.add_argument('command', nargs='?', help='命令: develop, interactive')
    parser.add_argument('args', nargs='*', help='参数')
    parser.add_argument('--path', '-p', type=str, help='项目路径')
    
    args = parser.parse_args()
    
    project_path = Path(args.path) if args.path else None
    driver = ClaudeDriver(project_path)
    
    if args.command == 'develop' and args.args:
        requirement = ' '.join(args.args)
        driver.develop(requirement)
    
    elif args.command == 'interactive' or not args.command:
        driver.interactive()
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
