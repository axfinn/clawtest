#!/usr/bin/env python3
"""
AutoDev Publish - 文档发布模块
将 autodev 输出的 Markdown 文件自动构建为 MkDocs 文档站

功能:
  - 自动扫描 Markdown 文件，生成 mkdocs.yml 导航
  - Material 主题（支持书本结构、搜索、暗色模式）
  - PDF 导出支持（mkdocs-with-pdf）
  - 本地预览 (mkdocs serve) + 静态构建 (mkdocs build)
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path
from runner import run_phase


# ──────────────────────────────────────────────────────────────
#  环境保障：自动安装 mkdocs 依赖
# ──────────────────────────────────────────────────────────────

# 必须安装的包（核心）
_REQUIRED = ['mkdocs', 'mkdocs-material']
# 可选包（安装失败不阻断流程）
_OPTIONAL = ['mkdocs-with-pdf', 'weasyprint']


def _pip_install(packages: list[str], label: str = '') -> bool:
    tag = f"[{label}] " if label else ""
    pkgs = ' '.join(packages)
    print(f"  📦 {tag}pip install {pkgs} ...", flush=True)
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '--quiet'] + packages,
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  ⚠️  {tag}安装失败: {result.stderr.strip()[-200:]}", flush=True)
        return False
    return True


def ensure_mkdocs() -> bool:
    """
    检查并安装 mkdocs 依赖。
    - 必须包：mkdocs + mkdocs-material（安装失败则整体失败）
    - 可选包：mkdocs-with-pdf / weasyprint（安装失败只警告）
    返回 True 表示核心依赖就绪。
    """
    # 检查 mkdocs 命令是否已存在
    if shutil.which('mkdocs'):
        print("  ✅ mkdocs 已安装", flush=True)
        # 仍然补装 material（可能缺主题）
        _pip_install(['mkdocs-material'], label='material')
    else:
        print("  🔍 未检测到 mkdocs，开始自动安装...", flush=True)
        if not _pip_install(_REQUIRED, label='core'):
            print("  ❌ mkdocs 核心依赖安装失败，PUBLISH 阶段跳过", flush=True)
            return False

    # 可选依赖（PDF 支持），失败不影响主流程
    _pip_install(_OPTIONAL, label='pdf')

    # 最终再确认
    if not shutil.which('mkdocs'):
        # pip 装了但 PATH 里没有，尝试用 python -m mkdocs
        result = subprocess.run(
            [sys.executable, '-m', 'mkdocs', '--version'],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print("  ❌ mkdocs 安装后仍无法运行", flush=True)
            return False

    print("  ✅ mkdocs 环境就绪", flush=True)
    return True


def _ensure_markdown_pkg() -> bool:
    """确保 markdown 包可用（纯本地渲染，不依赖 GitHub API）"""
    try:
        import markdown  # noqa
        return True
    except ImportError:
        r = subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', 'markdown'],
                           capture_output=True)
        return r.returncode == 0


_MD_CSS = """
body{max-width:860px;margin:0 auto;padding:2em 1.5em;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.7;color:#24292e}
h1,h2,h3{border-bottom:1px solid #eaecef;padding-bottom:.3em}
code{background:#f6f8fa;border-radius:3px;padding:.2em .4em;font-size:90%}
pre{background:#f6f8fa;border-radius:6px;padding:1em;overflow:auto}
pre code{background:none;padding:0}
blockquote{border-left:4px solid #dfe2e5;color:#6a737d;margin:0;padding:0 1em}
table{border-collapse:collapse;width:100%}
th,td{border:1px solid #dfe2e5;padding:.4em .8em}
th{background:#f6f8fa}
a{color:#0366d6}
nav{position:fixed;top:0;left:0;width:220px;height:100vh;overflow-y:auto;background:#f6f8fa;border-right:1px solid #e1e4e8;padding:1em .8em;font-size:.85em}
nav h3{margin:.5em 0;font-size:.9em;color:#586069;text-transform:uppercase;letter-spacing:.05em}
nav a{display:block;padding:.25em .4em;color:#24292e;text-decoration:none;border-radius:4px}
nav a:hover,nav a.active{background:#e1e4e8}
main{margin-left:240px}
@media(max-width:700px){nav{display:none}main{margin-left:0}}
"""


def _serve_local_md(cwd: Path, port: int):
    """纯本地 markdown 渲染服务，无需任何外部 API"""
    if not _ensure_markdown_pkg():
        _serve_http(cwd, port)
        return

    import markdown as md_lib
    import http.server, urllib.parse, html

    md_files = sorted(cwd.rglob('*.md'))

    def render_nav(current: Path) -> str:
        items = []
        # 按目录分组
        dirs: dict[str, list] = {}
        for f in md_files:
            rel = f.relative_to(cwd)
            d = str(rel.parent) if str(rel.parent) != '.' else ''
            dirs.setdefault(d, []).append(f)
        for d, files in sorted(dirs.items()):
            if d:
                items.append(f'<h3>{html.escape(d)}</h3>')
            for f in sorted(files):
                rel = f.relative_to(cwd)
                active = ' class="active"' if f == current else ''
                items.append(f'<a href="/{urllib.parse.quote(str(rel))}"{active}>{html.escape(f.stem)}</a>')
        return '\n'.join(items)

    def render_page(path: Path) -> str:
        text = path.read_text(encoding='utf-8')
        body = md_lib.markdown(text, extensions=['tables', 'fenced_code', 'toc'])
        nav  = render_nav(path)
        title = path.stem
        return f"""<!DOCTYPE html><html><head>
<meta charset="utf-8"><title>{html.escape(title)}</title>
<style>{_MD_CSS}</style></head><body>
<nav><b>📁 {html.escape(cwd.name)}</b><br><br>{nav}</nav>
<main>{body}</main></body></html>"""

    def render_index() -> str:
        nav = render_nav(Path('/dev/null'))
        items = ''.join(
            f'<li><a href="/{urllib.parse.quote(str(f.relative_to(cwd)))}">'
            f'{html.escape(str(f.relative_to(cwd)))}</a></li>'
            for f in md_files
        )
        return f"""<!DOCTYPE html><html><head>
<meta charset="utf-8"><title>{html.escape(cwd.name)}</title>
<style>{_MD_CSS}</style></head><body>
<nav><b>📁 {html.escape(cwd.name)}</b><br><br>{nav}</nav>
<main><h1>📁 {html.escape(cwd.name)}</h1><ul>{items}</ul></main>
</body></html>"""

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass  # 静默日志

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            url_path = urllib.parse.unquote(parsed.path).lstrip('/')

            if not url_path:
                content = render_index().encode()
            else:
                target = (cwd / url_path).resolve()
                # 安全：限制在 cwd 内
                try:
                    target.relative_to(cwd)
                except ValueError:
                    self.send_error(403)
                    return
                if not target.exists():
                    self.send_error(404)
                    return
                if target.suffix == '.md':
                    content = render_page(target).encode()
                else:
                    content = target.read_bytes()
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(content)
                    return

            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content)

    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = '0.0.0.0'
    print(f"\n📖 本地 Markdown 预览  http://{local_ip}:{port}  (0.0.0.0 监听)")
    print(f"   目录: {cwd}  ({len(md_files)} 个 md 文件)")
    print(f"   按 Ctrl+C 停止\n")
    with http.server.HTTPServer(('0.0.0.0', port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


def _serve_http(cwd: Path, port: int):
    """用 Python 内置 http.server 兜底，生成简单 HTML 索引"""
    import html, urllib.parse

    # 生成一个简单的 index.html 列出所有 md 文件
    md_files = sorted(cwd.rglob('*.md'))
    items = []
    for f in md_files:
        rel = f.relative_to(cwd)
        items.append(f'<li><a href="{urllib.parse.quote(str(rel))}">{rel}</a></li>')

    index = cwd / '_autodev_index.html'
    index.write_text(f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{cwd.name}</title>
<style>body{{font-family:sans-serif;padding:2em}} li{{margin:.4em 0}}</style>
</head><body>
<h2>📁 {html.escape(cwd.name)}</h2>
<ul>{''.join(items)}</ul>
<p style="color:#888">raw markdown — 建议用 <code>--publish</code> 获得渲染版</p>
</body></html>""", encoding='utf-8')

    print(f"\n📂 简易文件列表  http://127.0.0.1:{port}/_autodev_index.html")
    print(f"   目录: {cwd}")
    print(f"   按 Ctrl+C 停止\n")
    import http.server, functools
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(cwd))
    with http.server.HTTPServer(('0.0.0.0', port), handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
    index.unlink(missing_ok=True)


def serve(cwd: Path, port: int = 8000):
    """
    预览文档，两级策略：
    1. 有 _site/ → mkdocs serve（渲染最好）
    2. 其他      → 纯本地 markdown 渲染（不依赖任何外部 API）
    """
    site_dir = cwd / '_site'

    # 策略1：已构建文档站
    if site_dir.exists() and shutil.which('mkdocs'):
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            local_ip = '0.0.0.0'
        print(f"\n🌐 MkDocs 文档站预览  http://{local_ip}:{port}  (0.0.0.0 监听)")
        print(f"   目录: {cwd}")
        print(f"   按 Ctrl+C 停止\n")
        cmd = ['mkdocs', 'serve', '--dev-addr', f'0.0.0.0:{port}']
        subprocess.run(cmd, cwd=str(cwd))
        return

    # 策略2：纯本地渲染（无需 GitHub API）
    _serve_local_md(cwd, port)


# ──────────────────────────────────────────────────────────────
#  核心：让 claude 完成 MkDocs 的所有配置和构建
# ──────────────────────────────────────────────────────────────

def publish_prompt(task: str, cwd: Path) -> str:
    return f"""你是一个文档工程师，工作目录是 {cwd}。

任务背景: {task}

【PUBLISH - 文档发布阶段】

目标: 将目录下的 Markdown 文档构建为可在线浏览、可导出 PDF 的文档站

请按以下步骤完成:

---

## Step 1: 分析文档结构

用 Glob 工具扫描 {cwd} 下所有 .md 文件，
理解文档结构（RESULT.md、process/、docs/ 等），
规划合理的书本章节顺序。

---

## Step 3: 生成 mkdocs.yml

用 Write 工具在 {cwd}/mkdocs.yml 创建配置，示例结构:

```yaml
site_name: "文档标题（根据任务填写）"
site_description: "描述"
docs_dir: .          # 以当前目录为文档根目录
site_dir: _site

theme:
  name: material
  language: zh
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - navigation.top
    - search.highlight
    - content.code.copy
  palette:
    - scheme: default
      primary: indigo
      toggle:
        icon: material/brightness-7
        name: 切换到暗色
    - scheme: slate
      primary: indigo
      toggle:
        icon: material/brightness-4
        name: 切换到亮色

plugins:
  - search:
      lang: zh
  - with-pdf:
      author: AutoDev
      cover_title: "文档标题"
      cover_subtitle: "自动生成"
      output_path: _pdf/document.pdf
      enabled_if_env: ENABLE_PDF_EXPORT

markdown_extensions:
  - admonition
  - pymdownx.details
  - pymdownx.superfences
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.tabbed:
      alternate_style: true
  - tables
  - toc:
      permalink: true

nav:
  # 根据扫描到的文件填写，例如:
  - 首页: RESULT.md
  - 过程记录:
    - 调研发现: process/01-discover.md
    - 问题定义: process/02-define.md
    - 方案设计: process/03-design.md
    - 执行记录: process/04-do.md
    - 审查报告: process/05-review.md
```

**重要**: nav 要根据实际存在的 .md 文件来填写，不要包含不存在的文件。

---

## Step 4: 处理 docs 目录冲突

检查 {cwd} 下是否有 `docs/` 子目录（autodev 会生成此目录）。
如果有，在 mkdocs.yml 中将 `docs_dir` 改为 `.`（当前目录），
或者将文档文件移动整理到合适位置。

---

## Step 5: 构建文档站

用 Bash 工具在 {cwd} 目录执行:
```bash
cd {cwd} && mkdocs build 2>&1
```

如果报错（文件不存在、配置错误等），用 Edit 工具修复 mkdocs.yml 后重试。

---

## Step 6: 生成 PDF（可选）

用 Bash 工具执行:
```bash
cd {cwd} && ENABLE_PDF_EXPORT=1 mkdocs build 2>&1 | tail -20
```

---

## Step 7: 输出使用说明

构建成功后，用 Bash 输出:
```bash
echo "============================================"
echo "✅ 文档站构建完成"
echo "📂 静态文件: {cwd}/_site/"
echo "📄 PDF 文件: {cwd}/_pdf/document.pdf"
echo ""
echo "本地预览:"
echo "  cd {cwd} && mkdocs serve"
echo "  然后打开 http://127.0.0.1:8000"
echo ""
echo "部署到 GitHub Pages:"
echo "  cd {cwd} && mkdocs gh-deploy"
echo "============================================"
```

---

遇到任何错误，分析原因并修复，直到 mkdocs build 成功。
"""


def publish(task: str, cwd: Path) -> bool:
    """发布文档站（自动保障 mkdocs 环境）"""
    print("\n🔧 检查 mkdocs 环境...", flush=True)
    if not ensure_mkdocs():
        return False
    prompt = publish_prompt(task, cwd)
    return run_phase(prompt, cwd, "PUBLISH  文档发布", timeout=300)


# ──────────────────────────────────────────────────────────────
#  独立运行：对已有目录发布
# ──────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='AutoDev Publish - 将 Markdown 文档构建为 MkDocs 文档站',
        epilog="""
示例:
  # 对 autodev 的输出目录发布
  python3 publish.py --path ./projects/redis-doc --task "Redis 最佳实践文档"

  # 对任意含 Markdown 的目录发布
  python3 publish.py --path ./my-notes --task "学习笔记"
        """
    )
    parser.add_argument('--path', '-p', required=True, help='文档目录')
    parser.add_argument('--task', '-t', default='文档', help='任务/文档描述')
    parser.add_argument('--serve', '-s', action='store_true',
                        help='直接启动本地预览服务器（跳过构建）')
    parser.add_argument('--port', type=int, default=8000, help='预览端口（默认 8000）')
    args = parser.parse_args()

    cwd = Path(args.path).resolve()
    if not cwd.exists():
        print(f"❌ 目录不存在: {cwd}", file=sys.stderr)
        sys.exit(1)

    if args.serve:
        serve(cwd, port=args.port)
        return

    ok = publish(args.task, cwd)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
