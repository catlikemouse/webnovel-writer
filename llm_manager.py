import os
from openai import OpenAI

class LLMManager:
    """封装大模型交互逻辑，对接兼容 OpenAI 接口的模型 (如 Antigravity 代理)"""
    
    def __init__(self):
        # 优先从环境变量读取
        self.api_key = os.environ.get("OPENAI_API_KEY", "sk-4f5fd675bb47490c87490af189cd222a")
        self.base_url = os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:8046/v1")
        self.model = os.environ.get("MODEL", "gemini-3.1-pro-high")
                
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
        
    def chat(self, prompt: str, system_prompt: str = None, max_tokens: int = 8192) -> str:
        """发送单次对话请求"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            # max_tokens=max_tokens # gemini 模型的一些节点可能不支持强制 max_tokens，保守起见去除
        )
        
        return response.choices[0].message.content
