"""质量审查系统 - Review System"""

import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from core.memory.memory_manager import MemoryManager


class ReviewSystem:
    """无限循环质量审查系统"""
    
    def __init__(self, memory_mgr: MemoryManager):
        self.memory_mgr = memory_mgr
        self.quality_gates = {
            'code_quality': {'weight': 0.3, 'threshold': 7},
            'test_coverage': {'weight': 0.25, 'threshold': 70},
            'security': {'weight': 0.25, 'threshold': 0},  # 0 issues
            'performance': {'weight': 0.2, 'threshold': 7}
        }
    
    def run_review(self, files: List[str], strict: bool = False) -> Dict[str, Any]:
        """运行质量审查"""
        result = {
            'timestamp': None,
            'files_reviewed': len(files),
            'code_quality_score': 0,
            'test_coverage': 0,
            'security_issues': [],
            'performance_score': 0,
            'issues': [],
            'overall_score': 0
        }
        
        # Code quality check
        print("  🔍 检查代码质量...")
        quality_result = self._check_code_quality(files)
        result['code_quality_score'] = quality_result['score']
        result['issues'].extend(quality_result.get('issues', []))
        
        # Test coverage check
        print("  🔍 检查测试覆盖率...")
        coverage_result = self._check_test_coverage(files)
        result['test_coverage'] = coverage_result['coverage']
        
        # Security check
        print("  🔍 检查安全问题...")
        security_result = self._check_security(files)
        result['security_issues'] = security_result.get('issues', [])
        
        # Performance check
        print("  🔍 检查性能...")
        perf_result = self._check_performance(files)
        result['performance_score'] = perf_result['score']
        
        # Calculate overall score
        result['overall_score'] = self._calculate_overall_score(result)
        
        return result
    
    def _check_code_quality(self, files: List[str]) -> Dict[str, Any]:
        """检查代码质量"""
        issues = []
        total_score = 0
        scored_files = 0
        
        for file_path in files:
            if not Path(file_path).exists():
                continue
            
            # Run basic quality checks
            score = self._analyze_file_quality(file_path)
            total_score += score
            scored_files += 1
            
            if score < 7:
                issues.append(f"{file_path}: 代码质量分数 {score}/10")
        
        avg_score = total_score / scored_files if scored_files > 0 else 0
        
        return {
            'score': avg_score,
            'issues': issues
        }
    
    def _analyze_file_quality(self, file_path: str) -> float:
        """分析单个文件质量"""
        try:
            path = Path(file_path)
            if not path.exists():
                return 5.0
            
            content = path.read_text()
            
            # Basic checks
            score = 8.0  # Start with good score
            
            # Check for common issues
            if len(content) > 10000:  # File too large
                score -= 1
            
            if content.count('TODO') > 5:
                score -= 1
            
            if 'password' in content.lower() or 'secret' in content.lower():
                score -= 2
            
            # Check for complexity (basic)
            lines = content.split('\n')
            avg_line_length = sum(len(l) for l in lines) / len(lines) if lines else 0
            if avg_line_length > 120:
                score -= 0.5
            
            return max(0, min(10, score))
            
        except Exception:
            return 5.0
    
    def _check_test_coverage(self, files: List[str]) -> Dict[str, Any]:
        """检查测试覆盖率"""
        # Find test files
        test_files = []
        for f in files:
            path = Path(f)
            if 'test' in path.name.lower() or path.name.startswith('test_'):
                test_files.append(f)
        
        # Calculate mock coverage
        src_files = [f for f in files if 'test' not in Path(f).name.lower()]
        
        if not src_files:
            return {'coverage': 0}
        
        # Estimate coverage based on test files existence
        estimated_coverage = (len(test_files) / len(src_files)) * 100 if src_files else 0
        
        # In real implementation, run actual coverage tools
        return {'coverage': min(100, estimated_coverage)}
    
    def _check_security(self, files: List[str]) -> Dict[str, Any]:
        """检查安全问题"""
        issues = []
        
        security_patterns = [
            ('password', '明文密码'),
            ('secret', '硬编码密钥'),
            ('api_key', 'API密钥泄露'),
            ('token', 'Token泄露'),
            ('eval(', 'eval使用'),
            ('exec(', 'exec使用'),
            ('os.system(', '系统命令执行')
        ]
        
        for file_path in files:
            try:
                path = Path(file_path)
                if not path.exists():
                    continue
                
                content = path.read_text()
                
                for pattern, desc in security_patterns:
                    if pattern in content.lower():
                        issues.append(f"{file_path}: {desc}")
                        
            except Exception:
                pass
        
        return {'issues': issues}
    
    def _check_performance(self, files: List[str]) -> Dict[str, Any]:
        """检查性能"""
        issues = []
        score = 8.0
        
        for file_path in files:
            try:
                path = Path(file_path)
                if not path.exists():
                    continue
                
                content = path.read_text()
                
                # Check for performance anti-patterns
                if 'sleep(' in content and 'time.sleep' in content:
                    issues.append(f"{file_path}: 使用time.sleep可能影响性能")
                    score -= 0.5
                
                # Check for N+1 queries (basic)
                if 'for ' in content and 'query' in content.lower():
                    score -= 0.5
                
            except Exception:
                pass
        
        return {
            'score': max(0, min(10, score)),
            'issues': issues
        }
    
    def _calculate_overall_score(self, result: Dict[str, Any]) -> float:
        """计算综合分数"""
        weights = {
            'code_quality': 0.3,
            'test_coverage': 0.25,
            'security': 0.25,
            'performance': 0.2
        }
        
        # Normalize test coverage to 10
        coverage_score = result['test_coverage'] / 10
        
        # Security score (10 if no issues, lower otherwise)
        security_score = 10 if not result['security_issues'] else max(0, 10 - len(result['security_issues']) * 2)
        
        overall = (
            result['code_quality_score'] * weights['code_quality'] +
            coverage_score * weights['test_coverage'] +
            security_score * weights['security'] +
            result['performance_score'] * weights['performance']
        )
        
        return round(overall, 2)
    
    def check_gates(self, result: Dict[str, Any], strict: bool = False) -> Dict[str, bool]:
        """检查质量门禁"""
        gates = {}
        
        gates['code_quality'] = result['code_quality_score'] >= self.quality_gates['code_quality']['threshold']
        gates['test_coverage'] = result['test_coverage'] >= self.quality_gates['test_coverage']['threshold']
        gates['security'] = len(result['security_issues']) == 0 if not strict else len(result['security_issues']) <= 2
        gates['performance'] = result['performance_score'] >= self.quality_gates['performance']['threshold']
        
        return gates
    
    def generate_report(self, result: Dict[str, Any], format: str = 'markdown') -> str:
        """生成审查报告"""
        if format == 'markdown':
            return self._generate_markdown_report(result)
        elif format == 'json':
            return json.dumps(result, indent=2)
        elif format == 'html':
            return self._generate_html_report(result)
        
        return str(result)
    
    def _generate_markdown_report(self, result: Dict[str, Any]) -> str:
        """生成Markdown报告"""
        report = """# Code Quality Review Report

## Summary
"""
        report += f"- **Overall Score**: {result['overall_score']}/10\n"
        report += f"- **Files Reviewed**: {result['files_reviewed']}\n"
        report += f"- **Timestamp**: {result.get('timestamp', 'N/A')}\n\n"
        
        report += """## Quality Gates

| Gate | Score | Threshold | Status |
|------|-------|-----------|--------|
"""
        
        gates = self.check_gates(result)
        report += f"| Code Quality | {result['code_quality_score']}/10 | 7 | {'✅' if gates['code_quality'] else '❌'} |\n"
        report += f"| Test Coverage | {result['test_coverage']}% | 70% | {'✅' if gates['test_coverage'] else '❌'} |\n"
        report += f"| Security | {len(result['security_issues'])} issues | 0 | {'✅' if gates['security'] else '❌'} |\n"
        report += f"| Performance | {result['performance_score']}/10 | 7 | {'✅' if gates['performance'] else '❌'} |\n"
        
        if result['issues']:
            report += "\n## Issues\n\n"
            for issue in result['issues']:
                report += f"- {issue}\n"
        
        return report
    
    def _generate_html_report(self, result: Dict[str, Any]) -> str:
        """生成HTML报告"""
        gates = self.check_gates(result)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Code Quality Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .score {{ font-size: 24px; font-weight: bold; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Code Quality Review Report</h1>
    <div class="score">Overall Score: {result['overall_score']}/10</div>
    <table>
        <tr><th>Gate</th><th>Score</th><th>Status</th></tr>
        <tr><td>Code Quality</td><td>{result['code_quality_score']}/10</td><td class="{'pass' if gates['code_quality'] else 'fail'}">{'✅ PASS' if gates['code_quality'] else '❌ FAIL'}</td></tr>
        <tr><td>Test Coverage</td><td>{result['test_coverage']}%</td><td class="{'pass' if gates['test_coverage'] else 'fail'}">{'✅ PASS' if gates['test_coverage'] else '❌ FAIL'}</td></tr>
        <tr><td>Security</td><td>{len(result['security_issues'])} issues</td><td class="{'pass' if gates['security'] else 'fail'}">{'✅ PASS' if gates['security'] else '❌ FAIL'}</td></tr>
        <tr><td>Performance</td><td>{result['performance_score']}/10</td><td class="{'pass' if gates['performance'] else 'fail'}">{'✅ PASS' if gates['performance'] else '❌ FAIL'}</td></tr>
    </table>
</body>
</html>"""
        return html
