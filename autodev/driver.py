#!/usr/bin/env python3
"""
AutoDev - 万能任务助手
方法论: DISCOVER → DEFINE → DESIGN → DO → REVIEW → DELIVER [→ PUBLISH]

日志: <项目目录>/.autodev/logs/
默认输出: /tmp/autodev/<自动命名>/
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

from runner import CC_MODULE, normalize_module, run_phase, runtime_display_name
from phases import PHASE_LIST, phase_ask, phase_extend
from skills import list_skills
from init import init_project
from state import (
    mark_phase_start, mark_phase_done, mark_finished,
    last_completed_phase, should_stop, clear_stop, save_state, load_state,
)


# ──────────────────────────────────────────────────────────────
#  工具函数
# ──────────────────────────────────────────────────────────────

def slugify(text: str, max_len: int = 40) -> str:
    """
    将任务描述转为英文目录名。
    策略：让 claude 翻译（在线），或本地提取关键英文词 + 时间戳。
    这里用本地轻量方案：提取英文字母数字 + 替换空格，
    中文部分通过 pinyin/简单映射忽略（保留已有英文词）。
    """
    text = text.strip()
    # 只保留 ASCII 字母、数字、空格、连字符
    ascii_only = re.sub(r'[^a-zA-Z0-9\s\-]', ' ', text)
    words = ascii_only.split()
    if words:
        slug = '-'.join(w.lower() for w in words[:6])  # 最多6个词
    else:
        # 纯中文：用固定前缀 + 时间戳区分
        slug = 'task'
    # 截断
    slug = slug[:max_len].strip('-')
    return slug or 'task'


def make_project_dir(task: str) -> Path:
    """自动生成项目目录：/tmp/autodev/<英文slug>-<时间戳>"""
    base = Path('/tmp/autodev')
    slug = slugify(task)
    ts   = datetime.now().strftime('%m%d-%H%M')
    name = f"{slug}-{ts}" if slug != 'task' else f"task-{ts}"
    return base / name


def write_session_log(cwd: Path, task: str, phases_run: list, results: dict):
    """在 .autodev/logs/session.log 写入本次会话摘要（含目录名↔任务原文对照）"""
    log_dir = cwd / '.autodev' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    lines = [
        f"\n{'#'*70}",
        f"# AutoDev 会话记录",
        f"# 时间    : {ts}",
        f"# 目录    : {cwd.name}",        # 英文目录名，便于 shell 操作
        f"# 全路径  : {cwd}",
        f"# 任务原文: {task}",             # 中文原始需求，便于回溯
        f"{'#'*70}",
        "",
    ]
    for label, ok in results.items():
        lines.append(f"  {'✅' if ok else '⚠️ '} {label}")
    lines.append("")

    with open(log_dir / 'session.log', 'a', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    # 同时在 /tmp/autodev/.index 维护全局索引（目录名 → 任务原文）
    index_file = cwd.parent / '.index'
    with open(index_file, 'a', encoding='utf-8') as f:
        f.write(f"{ts}\t{cwd.name}\t{task}\n")


# ──────────────────────────────────────────────────────────────
#  主流程
# ──────────────────────────────────────────────────────────────

def run(task: str, cwd: Path, start_phase: int = 0,
        publish: bool = False, build: bool = False,
        push: bool = False, serve: bool = False,
        module: str = CC_MODULE):
    module = normalize_module(module)

    cwd.mkdir(parents=True, exist_ok=True)
    (cwd / 'process').mkdir(exist_ok=True)
    (cwd / '.autodev' / 'logs').mkdir(parents=True, exist_ok=True)

    total = len(PHASE_LIST)
    phases_str = " → ".join(name.split()[0] for name, _, _ in PHASE_LIST)
    if build:
        phases_str += " → BUILD"
    if publish:
        phases_str += " → PUBLISH"

    print(f"\n{'='*60}")
    print(f"🤖 AutoDev  万能任务助手")
    print(f"   任务: {task}")
    print(f"   目录: {cwd}")
    print(f"   日志: {cwd / '.autodev' / 'logs'}")
    print(f"   模块: {runtime_display_name(module)} ({module})")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   流程: {phases_str}")
    print('='*60)

    results = {}

    # 记录任务信息到 state（供 autodev-stop 读取）
    st = load_state(cwd)
    st['task'] = task
    st['status'] = 'running'
    save_state(cwd, st)

    # 清除上次遗留的 STOP 信号（新运行时）
    if start_phase == 0:
        clear_stop(cwd)

    # DO 和 REVIEW 的索引（用于 DO→REVIEW 重试循环）
    DO_IDX     = next(i for i, (l, _, _) in enumerate(PHASE_LIST) if 'DO' in l)
    REVIEW_IDX = next(i for i, (l, _, _) in enumerate(PHASE_LIST) if 'REVIEW' in l)
    MAX_RETRY  = 2   # REVIEW 失败后最多重试 DO+REVIEW 次数

    retry_count = 0

    for i, (label, prompt_fn, timeout) in enumerate(PHASE_LIST):
        if i < start_phase:
            print(f"⏭  跳过: {label}")
            continue

        # 检查终止信号
        if should_stop(cwd):
            print(f"\n🛑 收到终止信号，在阶段「{label}」前停止", flush=True)
            print(f"   恢复运行: ./autodev \"{task}\" --path {cwd} --from {i+1}")
            break

        mark_phase_start(cwd, i, label)
        prompt = prompt_fn(task, cwd)
        ok = run_phase(prompt, cwd, f"{i+1}/{total}  {label}", timeout, module=module)
        mark_phase_done(cwd, i, ok)
        results[label] = ok

        if not ok:
            print(f"\n⚠️  [{label}] 执行异常，继续下一阶段...", flush=True)

        # REVIEW 失败 → 自动重跑 DO + REVIEW（最多 MAX_RETRY 次）
        if i == REVIEW_IDX and not ok and retry_count < MAX_RETRY:
            retry_count += 1
            print(f"\n🔄 REVIEW 未通过，重跑 DO + REVIEW（第 {retry_count}/{MAX_RETRY} 次）...", flush=True)

            # 重跑 DO
            do_label, do_fn, do_timeout = PHASE_LIST[DO_IDX]
            do_prompt = do_fn(task, cwd)
            do_ok = run_phase(do_prompt, cwd, f"DO retry-{retry_count}  {do_label}", do_timeout, module=module)
            results[f"{do_label} (retry-{retry_count})"] = do_ok

            # 重跑 REVIEW
            rv_label, rv_fn, rv_timeout = PHASE_LIST[REVIEW_IDX]
            rv_prompt = rv_fn(task, cwd)
            ok = run_phase(rv_prompt, cwd, f"REVIEW retry-{retry_count}  {rv_label}", rv_timeout, module=module)
            results[f"{rv_label} (retry-{retry_count})"] = ok

            if ok:
                print(f"\n✅ 第 {retry_count} 次重试后 REVIEW 通过", flush=True)
            elif retry_count >= MAX_RETRY:
                print(f"\n⚠️  已达最大重试次数 {MAX_RETRY}，继续交付...", flush=True)

    # 可选：编译构建
    if build:
        from build import build as do_build
        ok = do_build(task, cwd, module=module)
        results["BUILD 编译构建"] = ok

    # 可选：文档发布
    if publish:
        from publish import publish as do_publish
        ok = do_publish(task, cwd, module=module)
        results["PUBLISH 文档发布"] = ok

    # 可选：推送到远端（无需确认）
    if push:
        import subprocess as _sp
        print(f"\n🚀 git push 到远端...", flush=True)
        r = _sp.run(['git', 'push'], cwd=str(cwd), capture_output=True, text=True)
        if r.returncode == 0:
            print(f"   ✅ push 成功", flush=True)
            results["PUSH 推送远端"] = True
        else:
            # 尝试 push --set-upstream
            branch = _sp.run(['git', 'branch', '--show-current'],
                             cwd=str(cwd), capture_output=True, text=True).stdout.strip()
            r2 = _sp.run(['git', 'push', '--set-upstream', 'origin', branch],
                         cwd=str(cwd), capture_output=True, text=True)
            ok = r2.returncode == 0
            print(f"   {'✅' if ok else '⚠️ '} push {'成功' if ok else '失败: ' + r2.stderr.strip()[-100:]}", flush=True)
            results["PUSH 推送远端"] = ok

    mark_finished(cwd)
    # 会话日志
    write_session_log(cwd, task, PHASE_LIST, results)

    # 汇总
    print(f"\n{'='*60}")
    print("📊 执行汇总:")
    for label, ok in results.items():
        print(f"   {'✅' if ok else '⚠️ '} {label}")

    print()
    result_file = cwd / 'RESULT.md'
    site_dir    = cwd / '_site'
    pdf_file    = cwd / '_pdf' / 'document.pdf'
    log_dir     = cwd / '.autodev' / 'logs'

    if result_file.exists():
        print(f"📄 交付报告 : {result_file}")
    build_log = cwd / 'process' / '06-build.md'
    if build_log.exists():
        print(f"🔨 构建报告 : {build_log}")
    if site_dir.exists():
        print(f"🌐 文档站   : {site_dir}/index.html")
        print(f"   本地预览 : cd {cwd} && mkdocs serve")
        print(f"   部署     : cd {cwd} && mkdocs gh-deploy")

    # --serve：自动启动预览（阻塞）
    if serve and site_dir.exists():
        from publish import serve as do_serve
        do_serve(cwd)
    if pdf_file.exists():
        print(f"📚 PDF 文件 : {pdf_file}")
    print(f"📝 执行日志 : {log_dir}/")
    print(f"📁 工作目录 : {cwd}")
    print(f"   完成时间 : {datetime.now().strftime('%H:%M:%S')}")


# ──────────────────────────────────────────────────────────────
#  ask 子命令：在已有项目中持续追问 / 执行小任务
# ──────────────────────────────────────────────────────────────

def _next_qa_index(cwd: Path) -> int:
    """读取 process/qa.md，返回下一个问答编号"""
    qa_file = cwd / 'process' / 'qa.md'
    if not qa_file.exists():
        return 1
    text = qa_file.read_text(encoding='utf-8')
    import re as _re
    indices = _re.findall(r'^## Q(\d+):', text, _re.MULTILINE)
    return max((int(i) for i in indices), default=0) + 1


def ask_project(question: str, cwd: Path, module: str = CC_MODULE):
    """在已有项目目录中执行一次追问/追加任务"""
    if not cwd.exists():
        print(f"❌ 项目目录不存在: {cwd}", flush=True)
        print(f"   请先用 autodev \"初始任务\" --path {cwd} 创建项目", flush=True)
        return

    module = normalize_module(module)

    qa_index = _next_qa_index(cwd)
    (cwd / 'process').mkdir(parents=True, exist_ok=True)
    (cwd / '.autodev' / 'logs').mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}", flush=True)
    print(f"💬 AutoDev ask  持续追问模式", flush=True)
    print(f"   项目: {cwd}", flush=True)
    print(f"   问题 #{qa_index}: {question}", flush=True)
    print(f"   问答记录: {cwd}/process/qa.md", flush=True)
    print(f"   模块: {runtime_display_name(module)} ({module})", flush=True)
    print('='*60, flush=True)

    prompt = phase_ask(question, cwd, qa_index,
                       timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    ok = run_phase(prompt, cwd, f"ASK #{qa_index}", timeout=None, module=module)

    print(f"\n{'='*60}", flush=True)
    print(f"   {'✅ 完成' if ok else '⚠️  异常'}", flush=True)
    print(f"   问答记录: {cwd}/process/qa.md", flush=True)


# ──────────────────────────────────────────────────────────────
#  extend 子命令：在已有项目上追加新需求（自动迭代开发）
# ──────────────────────────────────────────────────────────────

def _next_iter_index(cwd: Path) -> int:
    """返回下一个迭代编号"""
    process_dir = cwd / 'process'
    if not process_dir.exists():
        return 1
    import re as _re
    max_n = 0
    for p in process_dir.iterdir():
        m = _re.match(r'^iter-(\d+)$', p.name)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return max_n + 1


def extend_project(requirement: str, cwd: Path, module: str = CC_MODULE):
    """在已有项目目录上追加新需求，走精简迭代流程"""
    if not cwd.exists():
        print(f"❌ 项目目录不存在: {cwd}", flush=True)
        print(f"   请先用 autodev \"初始任务\" --path {cwd} 创建项目", flush=True)
        return

    module = normalize_module(module)

    iter_n = _next_iter_index(cwd)
    iter_dir = cwd / 'process' / f'iter-{iter_n}'
    iter_dir.mkdir(parents=True, exist_ok=True)
    (cwd / '.autodev' / 'logs').mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}", flush=True)
    print(f"🔄 AutoDev extend  迭代追加模式", flush=True)
    print(f"   项目: {cwd}", flush=True)
    print(f"   迭代: #{iter_n}", flush=True)
    print(f"   新需求: {requirement}", flush=True)
    print(f"   产出目录: {iter_dir}", flush=True)
    print(f"   模块: {runtime_display_name(module)} ({module})", flush=True)
    print('='*60, flush=True)

    # 记录本次迭代信息
    st = load_state(cwd)
    iters = st.get('iterations', [])
    iters.append({'n': iter_n, 'requirement': requirement,
                  'time': datetime.now().isoformat()})
    st['iterations'] = iters
    save_state(cwd, st)

    prompt = phase_extend(requirement, cwd, iter_n)
    ok = run_phase(prompt, cwd, f"EXTEND iter-{iter_n}", timeout=1800, module=module)

    print(f"\n{'='*60}", flush=True)
    print(f"   {'✅ 迭代完成' if ok else '⚠️  迭代异常'}", flush=True)
    print(f"   迭代产出: {iter_dir}/result.md", flush=True)
    print(f"   主报告  : {cwd}/RESULT.md", flush=True)
    print(f"   问答记录: {cwd}/process/qa.md", flush=True)


# ──────────────────────────────────────────────────────────────
#  入口
# ──────────────────────────────────────────────────────────────

def _spawn_bg_subcmd(subcmd: str, content: str, cwd: Path, module: str = CC_MODULE) -> None:
    """后台运行 ask/extend 子命令"""
    import subprocess as _sp
    log_dir = cwd / '.autodev' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    bg_log = log_dir / f'bg-{subcmd}.log'
    module = normalize_module(module)
    cmd = [sys.executable, __file__, subcmd, content, '--path', str(cwd), '--module', module]
    with open(bg_log, 'a') as log_f:
        proc = _sp.Popen(cmd, stdin=_sp.DEVNULL, stdout=log_f, stderr=log_f,
                         start_new_session=True,
                         cwd=str(Path(__file__).parent))
    print(f"🚀 后台启动 {subcmd} 成功")
    print(f"   PID : {proc.pid}")
    print(f"   内容: {content}")
    print(f"   目录: {cwd}")
    print(f"   日志: {bg_log}")
    print(f"   实时查看: tail -f {bg_log}")


def _spawn_background(args) -> None:
    """
    将自身以后台独立进程重新启动：
    - start_new_session=True  → 新 session，不受终端 SIGHUP 影响
    - stdin=DEVNULL            → 无 stdin，不触发 SIGTTIN
    - stdout/stderr → 日志文件 → 终端断开也不丢输出
    """
    import subprocess as _sp

    # 确定日志目录（提前算好 cwd，方便用户知道去哪里看）
    if args.path:
        cwd_path = Path(args.path).resolve()
    else:
        cwd_path = make_project_dir(args.task)

    log_dir = cwd_path / '.autodev' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    bg_log = log_dir / 'bg.log'

    # 重新组装命令行（去掉 --bg，加上 --path 固定目录）
    cmd = [sys.executable, __file__]
    cmd += ['--path', str(cwd_path)]
    cmd += ['--module', normalize_module(getattr(args, 'module', CC_MODULE))]
    if args.task:
        cmd += [args.task]
    if args.start_phase and args.start_phase != 1:
        cmd += ['--from', str(args.start_phase)]
    if getattr(args, 'build', False):
        cmd.append('--build')
    if getattr(args, 'publish', False):
        cmd.append('--publish')
    if getattr(args, 'push', False):
        cmd.append('--push')

    with open(bg_log, 'a') as log_f:
        proc = _sp.Popen(
            cmd,
            stdin=_sp.DEVNULL,
            stdout=log_f,
            stderr=log_f,
            start_new_session=True,   # setsid：新 session，免疫 SIGHUP
            cwd=str(Path(__file__).parent),
        )

    print(f"🚀 后台启动成功")
    print(f"   PID : {proc.pid}")
    print(f"   目录: {cwd_path}")
    print(f"   日志: {bg_log}")
    print(f"   实时查看: tail -f {bg_log}")


def _parse_subcmd(subcmd: str):
    """解析 ask/extend 子命令：python3 driver.py <subcmd> "内容" [--path dir] [--bg]"""
    sub = argparse.ArgumentParser(prog=f'autodev {subcmd}')
    sub.add_argument('content', nargs='?', default='',
                     help='问题或需求描述')
    sub.add_argument('--path', '-p', default=None, help='项目目录（已有）')
    sub.add_argument('--module', choices=['cc', 'codex'], default=CC_MODULE,
                     help='执行模块（默认: cc）')
    sub.add_argument('--bg', action='store_true', help='后台运行')
    return sub.parse_args(sys.argv[2:])


def main():
    # ── 子命令快速路由（在 argparse 主解析之前处理）──────────────

    # `init` 子命令：扫描项目，生成 CLAUDE.md 锁定上下文
    if len(sys.argv) >= 2 and sys.argv[1] == 'init':
        import argparse as _ap
        sub = _ap.ArgumentParser(prog='autodev init')
        sub.add_argument('--path', '-p', default=None, help='项目目录')
        sub_args = sub.parse_args(sys.argv[2:])
        cwd = Path(sub_args.path).resolve() if sub_args.path else Path.cwd()
        init_project(cwd)
        return

    if len(sys.argv) >= 2 and sys.argv[1] == 'ask':
        sub_args = _parse_subcmd('ask')
        if not sub_args.content:
            print("用法: autodev ask \"你的问题或任务\" --path ./project-dir")
            return
        cwd = Path(sub_args.path).resolve() if sub_args.path else Path.cwd()
        if sub_args.bg:
            # 后台运行 ask
            _spawn_bg_subcmd('ask', sub_args.content, cwd, module=sub_args.module)
        else:
            ask_project(sub_args.content, cwd, module=sub_args.module)
        return

    if len(sys.argv) >= 2 and sys.argv[1] == 'extend':
        sub_args = _parse_subcmd('extend')
        if not sub_args.content:
            print("用法: autodev extend \"新需求描述\" --path ./project-dir")
            return
        cwd = Path(sub_args.path).resolve() if sub_args.path else Path.cwd()
        if sub_args.bg:
            _spawn_bg_subcmd('extend', sub_args.content, cwd, module=sub_args.module)
        else:
            extend_project(sub_args.content, cwd, module=sub_args.module)
        return

    parser = argparse.ArgumentParser(
        description='AutoDev - 万能任务助手（DISCOVER→DEFINE→DESIGN→DO→REVIEW→DELIVER）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
默认输出目录: /tmp/autodev/<任务名>-<时间戳>/

━━━ 基本用法 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  # 不指定目录（自动命名）
  python3 driver.py "写 Redis 集群最佳实践文档" --publish

  # 指定目录
  python3 driver.py "用 Flask 实现 JWT 认证" --path ./projects/auth

  # 文档 + 发布
  python3 driver.py "写一本微服务架构实践手册" --path ./projects/book --publish

  # 断点恢复（从 DO 阶段重跑）
  python3 driver.py "任务" --path /tmp/autodev/xxx --from 4

━━━ 持续追问 (ask) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  # 在已有项目中追问/执行小任务（保留项目上下文）
  python3 driver.py ask "帮我加单元测试" --path ./projects/auth
  python3 driver.py ask "解释一下这里为什么用 JWT" --path ./projects/auth
  python3 driver.py ask "给 login 接口加限流" --path ./projects/auth

  # 所有问答自动追加到 process/qa.md，带编号和时间戳

━━━ 迭代追加需求 (extend) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  # 在已有项目上追加新需求，自动走 DESIGN→DO→REVIEW→DELIVER
  python3 driver.py extend "加 OAuth2 登录" --path ./projects/auth
  python3 driver.py extend "支持多租户" --path ./projects/auth

  # 每次迭代结果写入 process/iter-N/result.md
  # 主报告 RESULT.md 自动追加本次迭代摘要

━━━ 其他 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  # 直接预览已有项目文档（serve 子命令）
  autodev serve --path /tmp/autodev/xxx
  autodev serve --path /tmp/autodev/xxx --port 9000
        """,
    )
    parser.add_argument('task', nargs='?', default='', help='任务描述（任何类型）')
    parser.add_argument('--path', '-p', default=None,
                        help='工作目录（默认自动生成 /tmp/autodev/<名称>/）')
    parser.add_argument('--module', choices=['cc', 'codex'], default=CC_MODULE,
                        help='执行模块（默认: cc）')
    parser.add_argument('--from', dest='start_phase', type=int, default=1, metavar='N',
                        help='从第 N 阶段开始，1=DISCOVER … 6=DELIVER（断点恢复用）')
    parser.add_argument('--list-skills', action='store_true',
                        help='列出所有可用的本地 skills 后退出')
    parser.add_argument('--build', action='store_true',
                        help='完成后自动编译构建（Go/Rust/C/Java/Node/Python）')
    parser.add_argument('--publish', action='store_true',
                        help='完成后自动生成 MkDocs 文档站（含 PDF 导出）')
    parser.add_argument('--push', action='store_true',
                        help='完成后自动 git push 到远端（无需确认）')
    parser.add_argument('--serve', action='store_true',
                        help='--publish 完成后自动启动文档预览服务器')
    parser.add_argument('--port', type=int, default=8000,
                        help='serve 预览端口（默认 8000）')
    parser.add_argument('--process', action='store_true',
                        help='serve 时直接预览 process/ 执行过程目录')
    parser.add_argument('--bg', action='store_true',
                        help='后台运行（自动 setsid + 日志重定向，无需 nohup &）')

    args = parser.parse_args()
    args.module = normalize_module(getattr(args, "module", CC_MODULE))

    # --bg: 后台独立进程运行，防止终端断开导致任务中断
    if getattr(args, 'bg', False):
        _spawn_background(args)
        return

    # `serve <path>` 子命令：直接预览已有项目的文档站
    if args.task == 'serve':
        from publish import serve as do_serve
        target = Path(args.path).resolve() if args.path else None
        if not target:
            print("用法: autodev serve --path /tmp/autodev/<项目名> [--port 8000]")
            return
        if not target.exists():
            print(f"❌ 目录不存在: {target}")
            return
        # --process：直接预览 process/ 子目录
        if getattr(args, 'process', False):
            proc_dir = target / 'process'
            target = proc_dir if proc_dir.exists() else target
        port = getattr(args, 'port', 8000)
        do_serve(target, port=port)
        return

    # --list-skills 模式（无需 task）
    if args.list_skills:
        print("\n📦 本地可用 Skills:")
        list_skills()
        return

    if not args.task:
        parser.print_help()
        return

    # 确定工作目录
    if args.path:
        cwd = Path(args.path).resolve()
    else:
        cwd = make_project_dir(args.task)
        print(f"📁 自动创建项目目录: {cwd}")

    start = max(0, args.start_phase - 1)
    run(args.task, cwd, start_phase=start, build=args.build, publish=args.publish,
        push=args.push, serve=args.serve, module=args.module)


if __name__ == '__main__':
    main()
