"""
AI助手工具 - 封装各种AI API调用
"""

import logging
import asyncio
import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class AIHelper:
    """AI助手 - 统一的AI API接口"""
    
    def __init__(self, settings=None):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # API配置
        self.api_config = settings.get_api_config() if settings else {}
        self.timeout = 30
        
        # 统计信息
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0
        }
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """生成AI响应"""
        self.stats["total_requests"] += 1
        
        try:
            if self.api_config.get("type") == "qwen":
                response = await self._call_qwen_api(prompt, **kwargs)
            elif self.api_config.get("type") == "local":
                response = await self._call_local_api(prompt, **kwargs)
            else:
                raise ValueError(f"Unsupported API type: {self.api_config.get('type')}")
            
            self.stats["successful_requests"] += 1
            return response
        
        except Exception as e:
            self.stats["failed_requests"] += 1
            self.logger.error(f"AI API call failed: {e}")
            raise
    
    async def _call_qwen_api(self, prompt: str, **kwargs) -> str:
        """调用通义千问API"""
        if not self.api_config.get("api_key"):
            raise ValueError("Qwen API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_config['api_key']}",
            "Content-Type": "application/json"
        }
        
        # 构建请求体
        data = {
            "model": self.api_config.get("model", "qwen-turbo"),
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            "parameters": {
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 2000),
                "top_p": kwargs.get("top_p", 0.8)
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.api_config["api_url"],
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                error_msg = f"API request failed with status {response.status_code}"
                try:
                    error_detail = response.json().get("message", "")
                    if error_detail:
                        error_msg += f": {error_detail}"
                except:
                    pass
                raise Exception(error_msg)
            
            result = response.json()
            
            # 提取响应内容
            if "output" in result and "text" in result["output"]:
                content = result["output"]["text"]
            elif "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
            else:
                raise Exception("Unexpected API response format")
            
            # 更新统计
            if "usage" in result:
                self.stats["total_tokens"] += result["usage"].get("total_tokens", 0)
            
            return content
    
    async def _call_local_api(self, prompt: str, **kwargs) -> str:
        """调用本地模型API"""
        base_url = self.api_config.get("base_url", "http://localhost:8000")
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # 构建请求体（根据本地API格式调整）
        data = {
            "prompt": prompt,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2000)
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{base_url}/generate",
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                raise Exception(f"Local API request failed with status {response.status_code}")
            
            result = response.json()
            
            # 提取响应内容（根据本地API格式调整）
            if "response" in result:
                content = result["response"]
            elif "text" in result:
                content = result["text"]
            elif "content" in result:
                content = result["content"]
            else:
                raise Exception("Unexpected local API response format")
            
            return content
    
    async def generate_structured_response(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """生成结构化响应"""
        # 添加结构化输出提示
        structured_prompt = f"""
请按照以下JSON格式返回响应：

{json.dumps(schema, indent=2)}

用户请求：
{prompt}

请严格按照上述JSON格式返回，不要添加任何额外的文字说明。
"""
        
        response = await self.generate_response(structured_prompt, **kwargs)
        
        try:
            # 尝试解析JSON响应
            parsed_response = json.loads(response)
            return parsed_response
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse structured response: {e}")
            # 返回原始响应
            return {"raw_response": response}
    
    async def chat_with_history(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """带历史记录的对话"""
        if self.api_config.get("type") == "qwen":
            return await self._qwen_chat(messages, **kwargs)
        elif self.api_config.get("type") == "local":
            return await self._local_chat(messages, **kwargs)
        else:
            raise ValueError(f"Unsupported API type: {self.api_config.get('type')}")
    
    async def _qwen_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """通义千问对话"""
        if not self.api_config.get("api_key"):
            raise ValueError("Qwen API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_config['api_key']}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.api_config.get("model", "qwen-turbo"),
            "input": {
                "messages": messages
            },
            "parameters": {
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 2000),
                "top_p": kwargs.get("top_p", 0.8)
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.api_config["api_url"],
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                raise Exception(f"API request failed with status {response.status_code}")
            
            result = response.json()
            
            if "output" in result and "text" in result["output"]:
                content = result["output"]["text"]
            elif "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
            else:
                raise Exception("Unexpected API response format")
            
            return content
    
    async def _local_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """本地模型对话"""
        base_url = self.api_config.get("base_url", "http://localhost:8000")
        
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2000)
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{base_url}/chat",
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                raise Exception(f"Local API request failed with status {response.status_code}")
            
            result = response.json()
            
            if "response" in result:
                content = result["response"]
            elif "content" in result:
                content = result["content"]
            else:
                raise Exception("Unexpected local API response format")
            
            return content
    
    def is_configured(self) -> bool:
        """检查AI是否已配置"""
        return bool(self.api_config)
    
    def get_api_type(self) -> str:
        """获取API类型"""
        return self.api_config.get("type", "unknown")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """测试API连接"""
        test_prompt = "请回复'连接测试成功'"
        
        try:
            start_time = datetime.now()
            response = await self.generate_response(test_prompt, max_tokens=50)
            end_time = datetime.now()
            
            return {
                "success": True,
                "response": response,
                "response_time_ms": (end_time - start_time).total_seconds() * 1000,
                "api_type": self.get_api_type()
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "api_type": self.get_api_type()
            }
    
    # EXTENSION_POINT: 未来可扩展其他AI模型
    async def _call_openai_api(self, prompt: str, **kwargs) -> str:
        """调用OpenAI API（未来扩展）"""
        pass
    
    async def _call_claude_api(self, prompt: str, **kwargs) -> str:
        """调用Claude API（未来扩展）"""
        pass
    
    async def _call_gemini_api(self, prompt: str, **kwargs) -> str:
        """调用Gemini API（未来扩展）"""
        pass


# 全局AI助手实例
_global_ai_helper = None


def get_ai_helper(settings=None) -> AIHelper:
    """获取全局AI助手实例"""
    global _global_ai_helper
    if _global_ai_helper is None:
        _global_ai_helper = AIHelper(settings)
    return _global_ai_helper