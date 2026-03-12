"""记忆管理系统 - Memory Manager"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class MemoryManager:
    """记忆管理系统核心类"""
    
    def __init__(self, project_path: Optional[Path] = None):
        if project_path is None:
            project_path = Path.cwd()
        
        self.project_path = project_path
        self.memory_dir = project_path / '.claude' / 'memory'
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.checkpoints: List[Dict] = []
        self.current_context: Dict[str, Any] = {}
        self.decision_log: List[Dict] = []
        
        self._load_checkpoints()
    
    def _load_checkpoints(self):
        """加载已有检查点"""
        checkpoint_files = sorted(self.memory_dir.glob('checkpoint_*.json'))
        for cf in checkpoint_files:
            try:
                with open(cf, 'r') as f:
                    self.checkpoints.append(json.load(f))
            except Exception:
                pass
    
    def save_context(self, phase: str, context: Dict[str, Any]):
        """保存开发上下文"""
        self.current_context = {
            'phase': phase,
            'timestamp': datetime.now().isoformat(),
            **context
        }
        
        # Save to current context file
        context_file = self.memory_dir / 'current_context.json'
        with open(context_file, 'w') as f:
            json.dump(self.current_context, f, indent=2)
    
    def get_context(self) -> Dict[str, Any]:
        """获取当前上下文"""
        if not self.current_context:
            context_file = self.memory_dir / 'current_context.json'
            if context_file.exists():
                with open(context_file, 'r') as f:
                    self.current_context = json.load(f)
        return self.current_context
    
    def create_checkpoint(self, name: str, data: Dict[str, Any]) -> str:
        """创建检查点"""
        checkpoint_id = f"checkpoint_{len(self.checkpoints)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        checkpoint = {
            'id': checkpoint_id,
            'name': name,
            'timestamp': datetime.now().isoformat(),
            'context': self.get_context(),
            'data': data
        }
        
        self.checkpoints.append(checkpoint)
        
        # Save checkpoint file
        checkpoint_file = self.memory_dir / f'{checkpoint_id}.json'
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        # Cleanup old checkpoints
        self._cleanup_old_checkpoints()
        
        return checkpoint_id
    
    def _cleanup_old_checkpoints(self):
        """清理旧检查点"""
        max_checkpoints = 10  # Default max
        
        while len(self.checkpoints) > max_checkpoints:
            old = self.checkpoints.pop(0)
            checkpoint_file = self.memory_dir / f"{old['id']}.json"
            if checkpoint_file.exists():
                checkpoint_file.unlink()
    
    def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """加载指定检查点"""
        for cp in self.checkpoints:
            if cp['id'] == checkpoint_id or cp['name'] == checkpoint_id:
                return cp
        
        # Try loading from file
        checkpoint_file = self.memory_dir / f'{checkpoint_id}.json'
        if checkpoint_file.exists():
            with open(checkpoint_file, 'r') as f:
                return json.load(f)
        
        return None
    
    def get_latest_checkpoint(self) -> Optional[Dict[str, Any]]:
        """获取最新检查点"""
        if self.checkpoints:
            return self.checkpoints[-1]
        return None
    
    def log_decision(self, decision: str, reason: str, context: Dict[str, Any] = None):
        """记录技术决策"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'decision': decision,
            'reason': reason,
            'context': context or {}
        }
        
        self.decision_log.append(entry)
        
        # Save to decision log file
        log_file = self.memory_dir / 'decisions.json'
        with open(log_file, 'w') as f:
            json.dump(self.decision_log, f, indent=2)
    
    def get_decision_log(self) -> List[Dict[str, Any]]:
        """获取决策日志"""
        return self.decision_log
    
    def save_review_result(self, review_data: Dict[str, Any]):
        """保存review结果"""
        review_file = self.memory_dir / f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(review_file, 'w') as f:
            json.dump(review_data, f, indent=2)
    
    def get_review_history(self) -> List[Dict[str, Any]]:
        """获取review历史"""
        review_files = sorted(self.memory_dir.glob('review_*.json'), reverse=True)
        reviews = []
        for rf in review_files[:10]:  # Last 10 reviews
            try:
                with open(rf, 'r') as f:
                    reviews.append(json.load(f))
            except Exception:
                pass
        return reviews
