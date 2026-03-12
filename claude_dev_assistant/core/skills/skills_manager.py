"""GitHub Skills 集成系统"""

import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class SkillsManager:
    """GitHub Skills 管理器"""
    
    SUPPORTED_SKILLS = {
        'codeql': {
            'name': 'CodeQL',
            'category': 'security',
            'description': '代码安全漏洞扫描',
            'command': 'codeql'
        },
        'super-linter': {
            'name': 'Super Linter',
            'category': 'quality',
            'description': '多语言代码规范检查',
            'command': 'super-linter'
        },
        'trivy': {
            'name': 'Trivy',
            'category': 'security',
            'description': '容器和文件系统安全扫描',
            'command': 'trivy'
        },
        'eslint': {
            'name': 'ESLint',
            'category': 'quality',
            'description': 'JavaScript代码规范',
            'command': 'npx eslint'
        },
        'pytest': {
            'name': 'Pytest',
            'category': 'testing',
            'description': 'Python测试框架',
            'command': 'pytest'
        },
        'jest': {
            'name': 'Jest',
            'category': 'testing',
            'description': 'JavaScript测试框架',
            'command': 'npx jest'
        },
        'lighthouse': {
            'name': 'Lighthouse',
            'category': 'performance',
            'description': 'Web性能分析',
            'command': 'lighthouse'
        }
    }
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
    
    def get_available_skills(self) -> List[str]:
        """获取可用skills列表"""
        return list(self.SUPPORTED_SKILLS.keys())
    
    def get_skill_info(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """获取skill信息"""
        return self.SUPPORTED_SKILLS.get(skill_name)
    
    def run_skill(self, skill_name: str, target: str = None) -> Dict[str, Any]:
        """运行指定skill"""
        skill_info = self.SUPPORTED_SKILLS.get(skill_name)
        
        if not skill_info:
            return {
                'success': False,
                'error': f'Unknown skill: {skill_name}'
            }
        
        command = skill_info.get('command', '')
        target = target or str(self.project_path)
        
        # Check if command is available
        if not self._is_command_available(command):
            return {
                'success': False,
                'error': f'命令不可用: {command}。请先安装 {skill_info.get("name")}'
            }
        
        try:
            # Run the skill tool
            result = subprocess.run(
                command.split() + [target] if target else command.split(),
                capture_output=True,
                text=True,
                timeout=300,
                cwd=self.project_path
            )
            
            return {
                'success': result.returncode == 0,
                'message': f'{skill_info.get("name")} 执行完成',
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'{skill_info.get("name")} 执行超时'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def run_all_skills(self) -> Dict[str, Dict[str, Any]]:
        """运行所有启用的skills"""
        from core.config.config_manager import ConfigManager
        
        config_mgr = ConfigManager(self.project_path)
        config = config_mgr.load_config()
        
        enabled_skills = config.get('skills', {}).get('enabled', [])
        
        results = {}
        for skill in enabled_skills:
            results[skill] = self.run_skill(skill)
        
        return results
    
    def _is_command_available(self, command: str) -> bool:
        """检查命令是否可用"""
        try:
            # Get the base command (first word)
            base_cmd = command.split()[0]
            
            if 'npx' in base_cmd:
                # For npx commands, just check if node is available
                result = subprocess.run(
                    ['which', 'node'],
                    capture_output=True
                )
                return result.returncode == 0
            
            result = subprocess.run(
                ['which', base_cmd],
                capture_output=True
            )
            return result.returncode == 0
            
        except Exception:
            return False
    
    def discover_skills(self) -> List[Dict[str, Any]]:
        """发现已安装的skills"""
        discovered = []
        
        for skill_name, skill_info in self.SUPPORTED_SKILLS.items():
            if self._is_command_available(skill_info.get('command', '')):
                discovered.append({
                    'name': skill_name,
                    **skill_info,
                    'installed': True
                })
            else:
                discovered.append({
                    'name': skill_name,
                    **skill_info,
                    'installed': False
                })
        
        return discovered
