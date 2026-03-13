#!/usr/bin/env python3
"""
AutoDev Build - 构建模块
让 claude 根据项目类型自动完成：
  - Shell 脚本生成 + 执行
  - 编译二进制（Go/Rust/C/C++/Java）
  - 构建脚本（Makefile/CMake/Gradle/Maven/cargo/go build）
  - 打包产物（zip/tar/deb/rpm）

可独立运行: python3 build.py --path <dir> --task "描述"
也可通过 driver.py --build 触发
"""

import sys
from pathlib import Path
from runner import run_phase


def build_prompt(task: str, cwd: Path) -> str:
    return f"""你是一个构建工程师，工作目录是 {cwd}。

任务背景: {task}

【BUILD - 构建阶段】

目标: 对已有代码进行编译/构建，产出可执行的二进制或打包产物。

请按以下步骤完成:

---

## Step 1: 识别项目类型

用 Glob + Read 扫描 {cwd}，识别：
- 有 `*.go` / `go.mod`           → Go 项目
- 有 `Cargo.toml` / `*.rs`       → Rust 项目
- 有 `*.c` / `*.cpp` / `CMakeLists.txt` / `Makefile` → C/C++ 项目
- 有 `pom.xml` / `build.gradle`  → Java 项目
- 有 `package.json`              → Node.js 项目
- 有 `*.py` / `setup.py` / `pyproject.toml` → Python 项目
- 有 `Makefile`                  → 通用 Make 项目
- 其他                           → 分析后决定

---

## Step 2: 生成构建脚本

如果项目没有构建脚本，用 Write 工具创建 `build.sh`：

```bash
#!/bin/bash
set -e   # 遇错即退

echo "=== AutoDev Build ==="
cd {cwd}

# 根据项目类型填写实际构建命令，例如:
# Go:    go build -o bin/app ./...
# Rust:  cargo build --release
# C:     mkdir -p build && cd build && cmake .. && make -j$(nproc)
# Java:  mvn package -DskipTests  或  gradle build
# Node:  npm install && npm run build
# Python: pip install -e .  或  python setup.py bdist_wheel
```

根据实际项目类型填写正确的构建命令。

---

## Step 3: 安装依赖

用 Bash 执行必要的依赖安装：
- Go: `go mod download`（如果有 go.mod）
- Rust: `cargo fetch`
- Node: `npm install` 或 `yarn`
- Python: `pip install -r requirements.txt`（如果有）
- C/C++: `apt-get install -y build-essential cmake`（如果需要）

---

## Step 4: 执行构建

用 Bash 工具运行构建：
```bash
chmod +x {cwd}/build.sh && bash {cwd}/build.sh 2>&1
```

**如果构建失败**：
1. 阅读错误信息
2. 用 Edit 工具修复代码或构建脚本
3. 再次运行，直到构建成功

---

## Step 5: 验证产物

构建成功后，用 Bash 验证产物：
```bash
# 列出产出文件
find {cwd} -name "*.so" -o -name "*.a" -o -name "*.whl" \
     -o -type f -executable 2>/dev/null | grep -v ".git" | head -20
```

如果是可执行文件，运行一次验证：`./bin/app --help` 或 `./app --version` 等。

---

## Step 6: 记录构建结果

用 Write 工具将结果写入 `process/06-build.md`：

```markdown
# BUILD - 构建报告

## 项目类型
[识别到的类型]

## 构建命令
[使用的命令]

## 产出文件
[列出所有产物路径和大小]

## 构建状态
[✅ 成功 / ⚠️ 部分成功 + 说明]
```

---

遇到编译错误，直接修复代码后重试，直到构建成功。
"""


def build(task: str, cwd: Path) -> bool:
    """执行构建阶段"""
    prompt = build_prompt(task, cwd)
    return run_phase(prompt, cwd, "BUILD  编译构建", timeout=600)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='AutoDev Build - 自动编译构建（Shell/Go/Rust/C/Java/Node/Python）',
        epilog="""
示例:
  python3 build.py --path ./projects/myapp --task "Go HTTP 服务"
  python3 build.py --path ./projects/cli   --task "Rust CLI 工具"
  python3 build.py --path /tmp/autodev/xxx --task "任务描述"
        """
    )
    parser.add_argument('--path', '-p', required=True, help='项目目录')
    parser.add_argument('--task', '-t', default='项目构建', help='任务/项目描述')
    args = parser.parse_args()

    cwd = Path(args.path).resolve()
    if not cwd.exists():
        print(f"❌ 目录不存在: {cwd}", file=sys.stderr)
        sys.exit(1)

    ok = build(args.task, cwd)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
