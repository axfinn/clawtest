"""配置管理系统"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """配置管理器"""
    
    DEFAULT_CONFIG = {
        'version': '1.0',
        'project': {
            'name': 'project',
            'type': 'default'
        },
        'quality': {
            'review_cycles': 3,
            'gates': {
                'code_quality': 'required',
                'test_coverage': 'required',
                'security': 'required',
                'performance': 'optional'
            }
        },
        'skills': {
            'enabled': ['codeql', 'super-linter'],
            'auto_run': False
        },
        'memory': {
            'auto_save': True,
            'checkpoint_interval': 5,
            'max_checkpoints': 10
        },
        'interrupt': {
            'graceful_timeout': 30,
            'auto_save': True
        }
    }
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self.config_file = self.project_path / '.claude' / 'config.yaml'
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_file.exists():
            # Create default config
            self.save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG
        
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
                return config or self.DEFAULT_CONFIG
        except Exception:
            return self.DEFAULT_CONFIG
    
    def save_config(self, config: Dict[str, Any]):
        """保存配置文件"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        config = self.load_config()
        
        keys = key.split('.')
        value = config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            
            if value is None:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置项"""
        config = self.load_config()
        
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
        
        self.save_config(config)
    
    def update_quality_gates(self, gates: Dict[str, str]):
        """更新质量门禁配置"""
        config = self.load_config()
        config['quality']['gates'].update(gates)
        self.save_config(config)
    
    def update_skills(self, enabled: list):
        """更新skills配置"""
        config = self.load_config()
        config['skills']['enabled'] = enabled
        self.save_config(config)
    
    def to_json(self) -> str:
        """导出JSON格式"""
        return json.dumps(self.load_config(), indent=2)
    
    def validate(self) -> Dict[str, Any]:
        """验证配置"""
        config = self.load_config()
        errors = []
        
        # Validate required fields
        required_fields = ['version', 'project', 'quality', 'memory', 'interrupt']
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        # Validate quality gates
        quality = config.get('quality', {})
        gates = quality.get('gates', {})
        valid_gates = {'required', 'optional', 'disabled'}
        
        for gate, value in gates.items():
            if value not in valid_gates:
                errors.append(f"Invalid gate value for {gate}: {value}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
