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


def serve(cwd: Path, port: int = 8000):
    """本地预览文档站（阻塞，Ctrl+C 退出）"""
    mkdocs_cmd = 'mkdocs' if shutil.which('mkdocs') else None
    if not mkdocs_cmd:
        # 尝试 python -m mkdocs
        r = subprocess.run([sys.executable, '-m', 'mkdocs', '--version'],
                           capture_output=True)
        if r.returncode == 0:
            mkdocs_cmd = f"{sys.executable} -m mkdocs"

    if not mkdocs_cmd:
        print("❌ mkdocs 未安装，请先运行 --publish", file=sys.stderr)
        sys.exit(1)

    print(f"\n🌐 启动文档预览服务器 http://127.0.0.1:{port}")
    print(f"   目录: {cwd}")
    print(f"   按 Ctrl+C 停止\n")
    cmd = ['mkdocs', 'serve', '--dev-addr', f'0.0.0.0:{port}']
    if not shutil.which('mkdocs'):
        cmd = [sys.executable, '-m', 'mkdocs', 'serve', '--dev-addr', f'0.0.0.0:{port}']
    subprocess.run(cmd, cwd=str(cwd))


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
