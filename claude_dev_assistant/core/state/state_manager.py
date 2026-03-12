"""状态管理系统 - State Manager"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class StateManager:
    """状态管理器"""
    
    def __init__(self, project_path: Optional[Path] = None):
        if project_path is None:
            project_path = Path.cwd()
        
        self.project_path = project_path
        self.state_file = project_path / '.claude' / 'state.json'
        
        self.state: Dict[str, Any] = {
            'current_phase': 'idle',
            'start_time': None,
            'last_update': None,
            'data': {}
        }
        
        self._load_state()
    
    def _load_state(self):
        """加载状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    self.state = json.load(f)
            except Exception:
                pass
    
    def _save_state(self):
        """保存状态"""
        self.state['last_update'] = datetime.now().isoformat()
        
        # Ensure directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def update_state(self, phase: str, data: Dict[str, Any] = None):
        """更新状态"""
        self.state['current_phase'] = phase
        self.state['start_time'] = self.state.get('start_time') or datetime.now().isoformat()
        
        if data:
            self.state['data'].update(data)
        
        self._save_state()
    
    def get_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return self.state
    
    def get_phase(self) -> str:
        """获取当前阶段"""
        return self.state.get('current_phase', 'idle')
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """获取状态数据"""
        return self.state.get('data', {}).get(key, default)
    
    def set_data(self, key: str, value: Any):
        """设置状态数据"""
        if 'data' not in self.state:
            self.state['data'] = {}
        self.state['data'][key] = value
        self._save_state()
    
    def reset_state(self):
        """重置状态"""
        self.state = {
            'current_phase': 'idle',
            'start_time': None,
            'last_update': datetime.now().isoformat(),
            'data': {}
        }
        self._save_state()
    
    def save_snapshot(self, name: str) -> str:
        """保存状态快照"""
        snapshot = {
            'name': name,
            'timestamp': datetime.now().isoformat(),
            'state': self.state.copy()
        }
        
        snapshot_file = self.project_path / '.claude' / 'memory' / f'snapshot_{name}.json'
        snapshot_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot, f, indent=2)
        
        return str(snapshot_file)
    
    def load_snapshot(self, name: str) -> bool:
        """加载状态快照"""
        snapshot_file = self.project_path / '.claude' / 'memory' / f'snapshot_{name}.json'
        
        if not snapshot_file.exists():
            return False
        
        try:
            with open(snapshot_file, 'r') as f:
                snapshot = json.load(f)
                self.state = snapshot.get('state', {})
                self._save_state()
            return True
        except Exception:
            return False
