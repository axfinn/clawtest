#!/usr/bin/env python3
"""
Skills 自动发现与注入模块

自动扫描本地 skill 文件：
  - ~/.claude/commands/*.md         (全局 skills)
  - <project>/.claude/commands/*.md (项目级 skills)

并将匹配的 skill 内容注入到 phase prompt 中。
"""

import re
from pathlib import Path


# ──────────────────────────────────────────────────────────────
#  Skill 数据结构
# ──────────────────────────────────────────────────────────────

class Skill:
    def __init__(self, name: str, path: Path, description: str,
                 content: str, allowed_tools: list, argument_hint: str):
        self.name          = name           # 文件名（不含 .md）
        self.path          = path           # 文件绝对路径
        self.description   = description   # frontmatter description
        self.content       = content       # body（去除 frontmatter）
        self.allowed_tools = allowed_tools # frontmatter allowed-tools
        self.argument_hint = argument_hint # frontmatter argument-hint

    def __repr__(self):
        return f"<Skill {self.name}: {self.description[:40]}>"

    def render(self, arguments: str = '') -> str:
        """将 $ARGUMENTS 替换为实际参数，返回可注入的 prompt 文本"""
        return self.content.replace('$ARGUMENTS', arguments)


# ──────────────────────────────────────────────────────────────
#  解析 frontmatter
# ──────────────────────────────────────────────────────────────

def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """
    解析 YAML frontmatter。
    返回 (meta_dict, body)
    """
    meta = {}
    body = text

    m = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', text, re.DOTALL)
    if not m:
        return meta, body

    front, body = m.group(1), m.group(2)

    for line in front.splitlines():
        if ':' not in line:
            continue
        key, _, val = line.partition(':')
        key = key.strip()
        val = val.strip()

        # 解析列表字段 allowed-tools: [Bash, Read, ...]
        if val.startswith('[') and val.endswith(']'):
            items = [x.strip().strip('"\'') for x in val[1:-1].split(',')]
            meta[key] = [i for i in items if i]
        else:
            meta[key] = val.strip('"\'')

    return meta, body.strip()


# ──────────────────────────────────────────────────────────────
#  发现所有 skills
# ──────────────────────────────────────────────────────────────

def discover(project_root: Path = None) -> list[Skill]:
    """
    扫描 skill 目录，返回所有可用 Skill 列表。

    搜索顺序（后者可覆盖同名 skill）：
      1. ~/.claude/commands/
      2. <project_root>/.claude/commands/
    """
    search_dirs = [
        Path.home() / '.claude' / 'commands',
    ]
    if project_root:
        search_dirs.append(project_root / '.claude' / 'commands')

    skills_map: dict[str, Skill] = {}

    for d in search_dirs:
        if not d.is_dir():
            continue
        for md_file in sorted(d.glob('*.md')):
            name = md_file.stem
            text = md_file.read_text(encoding='utf-8')
            meta, body = _parse_frontmatter(text)

            skill = Skill(
                name          = name,
                path          = md_file,
                description   = meta.get('description', ''),
                content       = body,
                allowed_tools = meta.get('allowed-tools', []),
                argument_hint = meta.get('argument-hint', ''),
            )
            skills_map[name] = skill   # 同名时项目级覆盖全局

    return list(skills_map.values())


# ──────────────────────────────────────────────────────────────
#  技能匹配
# ──────────────────────────────────────────────────────────────

def match(task: str, skills: list[Skill], phase_hint: str = '') -> list[Skill]:
    """
    根据任务描述和阶段提示，返回相关 skill 列表（按相关度排序）。
    使用关键词匹配，不依赖网络/AI。
    """
    task_lower  = task.lower()
    phase_lower = phase_hint.lower()

    scored: list[tuple[int, Skill]] = []
    for sk in skills:
        score = 0
        desc  = sk.description.lower()
        body  = sk.content.lower()

        # 名字直接出现在任务里
        if sk.name.lower() in task_lower:
            score += 10

        # 描述关键词匹配任务
        for word in re.findall(r'\w+', desc):
            if len(word) >= 3 and word in task_lower:
                score += 2

        # 阶段提示匹配
        for word in re.findall(r'\w+', phase_lower):
            if len(word) >= 3 and word in desc:
                score += 1

        if score > 0:
            scored.append((score, sk))

    scored.sort(key=lambda x: -x[0])
    return [sk for _, sk in scored]


# ──────────────────────────────────────────────────────────────
#  注入到 prompt
# ──────────────────────────────────────────────────────────────

def inject_into_prompt(base_prompt: str, skills: list[Skill],
                       task: str, max_skills: int = 2) -> str:
    """
    将匹配的 skill 内容追加到 base_prompt 末尾。
    使用最多 max_skills 个相关 skill。
    """
    if not skills:
        return base_prompt

    chosen = skills[:max_skills]

    lines = [base_prompt, '', '─' * 60,
             '# 可用的 Skills（请按需参考并执行）', '']

    for sk in chosen:
        lines.append(f'## [{sk.name}] {sk.description}')
        lines.append(f'> 来源: {sk.path}')
        lines.append('')
        lines.append(sk.render(task))
        lines.append('')

    return '\n'.join(lines)


# ──────────────────────────────────────────────────────────────
#  便捷函数：一步完成发现 + 匹配 + 注入
# ──────────────────────────────────────────────────────────────

def augment_prompt(base_prompt: str, task: str,
                   project_root: Path = None,
                   phase_hint: str = '',
                   max_skills: int = 2) -> str:
    """
    自动发现本地 skills，匹配任务，注入到 prompt。
    如果没有匹配的 skill，原样返回 base_prompt。
    """
    all_skills     = discover(project_root)
    matched        = match(task, all_skills, phase_hint)
    return inject_into_prompt(base_prompt, matched, task, max_skills)


def list_skills(project_root: Path = None) -> None:
    """打印所有可用 skills（调试用）"""
    skills = discover(project_root)
    if not skills:
        print("  （未发现任何 skill）")
        return
    print(f"  发现 {len(skills)} 个 skill:")
    for sk in skills:
        print(f"    [{sk.name}]  {sk.description or '（无描述）'}  ({sk.path.parent.parent.parent.name}/)")
