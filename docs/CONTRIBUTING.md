# Contributing Guide

Thank you for your interest in contributing to Clawtest! This document provides guidelines for contributing to the project.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Pull Request Guidelines](#pull-request-guidelines)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Issue Reporting](#issue-reporting)

---

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. We are committed to providing a welcoming experience for everyone.

**Expected behavior:**
- Be respectful and inclusive
- Use welcoming and inclusive language
- Accept constructive criticism gracefully
- Focus on what is best for the community

**Unacceptable behavior:**
- Harassment or discrimination of any kind
- Personal or political attacks
- Publishing others' private information
- Other conduct that could reasonably be considered inappropriate

---

## Getting Started

### Fork the Repository

```bash
# 点击 GitHub 页面上的 "Fork" 按钮

# 克隆你的 fork
git clone https://github.com/YOUR_USERNAME/clawtest.git
cd clawtest

# 添加上游仓库
git remote add upstream https://github.com/original/clawtest.git
```

### Set Up Development Environment

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 如果有

# 安装 pre-commit 钩子
pre-commit install
```

---

## Development Workflow

### 1. Create a Branch

```bash
# 确保在主分支上
git checkout main
git pull upstream main

# 创建新分支
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/bug-description
```

### 2. Make Changes

Make your changes following the coding standards. Keep your changes focused and atomic.

### 3. Test Your Changes

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_api.py

# 带覆盖率
pytest --cov=src --cov-report=html
```

### 4. Commit Changes

```bash
# 查看更改
git status
git diff

# 添加更改
git add -A

# 提交 (使用 Conventional Commits)
git commit -m "feat: add new feature for AI chat"
# 或
git commit -m "fix: resolve code execution timeout issue"
```

**Commit Message Format:**

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style (formatting)
- `refactor`: Code refactoring
- `test`: Testing
- `chore`: Maintenance

### 5. Keep Your Branch Updated

```bash
# 定期从上游获取更新
git fetch upstream
git rebase upstream/main
```

---

## Pull Request Guidelines

### Before Submitting

1. **Run tests** - Ensure all tests pass
2. **Update documentation** - Add docstrings and update docs if needed
3. **Check code style** - Follow the coding standards
4. **Test locally** - Verify your changes work correctly

### Submitting a PR

1. Push your branch:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Open a Pull Request on GitHub

3. Fill in the PR template:

   ```markdown
   ## Description
   Brief description of what this PR does

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Refactoring

   ## Testing
   Describe how you tested this change

   ## Checklist
   - [ ] My code follows the style guidelines
   - [ ] I have performed self-review
   - [ ] I have commented my code where necessary
   - [ ] I have updated the documentation
   - [ ] My changes generate no new warnings
   - [ ] I have added tests that prove my fix works
   - [ ] New and existing tests pass locally
   ```

4. **Wait for review** - Address any feedback promptly

### PR Review Process

- At least one maintainer approval required
- Address all review comments
- Keep PR focused and atomic

---

## Coding Standards

### Python Style

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:

```python
# 使用 Black 进行格式化
# 最大行长度: 100

# 正确的命名
class UserService:  # PascalCase for classes
    def get_user(self):  # snake_case for functions
        user_id = 1  # snake_case for variables
        MAX_RETRY = 3  # SCREAMING_SNAKE_CASE for constants

# 类型注解
def process_data(data: str) -> dict:
    """Process user data.
    
    Args:
        data: Input string data
        
    Returns:
        Processed dictionary
    """
    return {"result": data}
```

### Git Commit Style

- Use imperative mood: "Add feature" not "Added feature"
- First line: max 72 characters
- Reference issues: "Fixes #123"

### File Organization

```
src/
├── __init__.py
├── app.py          # Flask application
├── routes.py       # API routes
├── models.py       # Database models
├── services.py     # Business logic
├── api/            # API clients
│   └── minimax.py
└── handlers/       # Request handlers
    └── codeExecutor.py
```

---

## Testing

### Writing Tests

```python
import pytest
from src.app import create_app

@pytest.fixture
def app():
    app = create_app('testing')
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_health_check(client):
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 200
```

### Test Coverage

- Aim for at least 80% code coverage
- Test edge cases
- Test error conditions

### Running Tests

```bash
# 所有测试
pytest

# 特定文件
pytest tests/test_api.py -v

# 监听模式 (开发)
ptw

# 覆盖率报告
pytest --cov=src --cov-report=html --cov-report=term
```

---

## Documentation

### Code Documentation

- Add docstrings to all public functions and classes
- Use Google-style docstrings:

```python
def execute(code: str, language: str = "python") -> dict:
    """Execute code in the specified language.
    
    Args:
        code: Source code to execute
        language: Programming language (python, javascript, bash)
        
    Returns:
        Dictionary containing execution result with keys:
            - success: bool
            - output: str or None
            - error: str or None
            
    Raises:
        ValueError: If language is not supported
        
    Example:
        >>> result = execute("print('hello')", "python")
        >>> result['success']
        True
    """
```

### API Documentation

- Document all API endpoints
- Include request/response examples
- Document error codes

---

## Issue Reporting

### Bug Reports

Use GitHub Issues to report bugs. Include:

1. **Summary** - Brief description
2. **Steps to reproduce** - Detailed steps
3. **Expected behavior** - What should happen
4. **Actual behavior** - What actually happened
5. **Environment** - OS, Python version, etc.
6. **Logs** - Relevant error logs
7. **Screenshots** - If applicable

### Feature Requests

1. **Description** - What feature you want
2. **Use case** - Why you need it
3. **Alternatives** - Any alternatives considered

---

## Recognition

Contributors will be recognized in:

- CONTRIBUTORS.md file
- Release notes

---

## Questions?

- Open an issue for questions
- Join our community chat (if available)
- Contact maintainers directly

Thank you for contributing!
