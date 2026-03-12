"""
MiniMax API 客户端
支持 M2.1 和 M2.5 模型
"""
import os
import requests
from typing import List, Dict, Optional


class MiniMaxClient:
    """MiniMax API 客户端"""
    
    BASE_URL = "https://api.minimaxi.com/anthropic"
    
    def __init__(self, api_key: str = None, model: str = "MiniMax-M2.5"):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        self.model = model
        self.max_tokens = 8192
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        })
    
    def chat(self, message: str, history: List[Dict] = None) -> str:
        """发送对话请求"""
        messages = []
        
        # 添加历史
        if history:
            for h in history:
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        
        # 添加当前消息
        messages.append({"role": "user", "content": message})
        
        # 调用 API
        response = self.session.post(
            f"{self.BASE_URL}/v1/messages",
            json={
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens
            },
            timeout=120
        )
        
        if response.status_code != 200:
            raise Exception(f"API Error: {response.text}")
        
        result = response.json()
        return result["content"][0]["text"]
    
    def set_model(self, model: str):
        """切换模型"""
        self.model = model
    
    @staticmethod
    def get_available_models() -> List[str]:
        """获取可用模型"""
        return ["MiniMax-M2.1", "MiniMax-M2.5"]


# 导出
__all__ = ["MiniMaxClient"]
