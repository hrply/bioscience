"""
大模型调用接口模块
"""

import json
import requests
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """大模型配置"""
    provider: str = "openai"  # openai, qwen, claude, local
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 60
    max_retries: int = 3


@dataclass
class Message:
    """消息对象"""
    role: str  # system, user, assistant
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class LLMResponse:
    """大模型响应"""
    content: str
    usage: Dict[str, int] = None
    finish_reason: str = ""
    model: str = ""
    
    def __post_init__(self):
        if self.usage is None:
            self.usage = {}


class BaseLLMClient(ABC):
    """大模型客户端基类"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.session = requests.Session()
        self._setup_session()
    
    @abstractmethod
    def _setup_session(self):
        """设置会话"""
        pass
    
    @abstractmethod
    def chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        """对话接口"""
        pass
    
    @abstractmethod
    def stream_chat(self, messages: List[Message], **kwargs):
        """流式对话接口"""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI客户端"""
    
    def _setup_session(self):
        """设置会话"""
        self.session.headers.update({
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        })
        
        if not self.config.base_url:
            self.config.base_url = "https://api.openai.com/v1"
    
    def chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        """对话接口"""
        url = f"{self.config.base_url}/chat/completions"
        
        data = {
            "model": kwargs.get("model", self.config.model),
            "messages": [msg.to_dict() for msg in messages],
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens)
        }
        
        try:
            response = self.session.post(url, json=data, timeout=self.config.timeout)
            response.raise_for_status()
            result = response.json()
            
            choice = result["choices"][0]
            return LLMResponse(
                content=choice["message"]["content"],
                usage=result.get("usage", {}),
                finish_reason=choice.get("finish_reason", ""),
                model=result.get("model", "")
            )
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            return LLMResponse(content=f"API调用失败: {e}")
    
    def stream_chat(self, messages: List[Message], **kwargs):
        """流式对话接口"""
        url = f"{self.config.base_url}/chat/completions"
        
        data = {
            "model": kwargs.get("model", self.config.model),
            "messages": [msg.to_dict() for msg in messages],
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "stream": True
        }
        
        try:
            response = self.session.post(url, json=data, timeout=self.config.timeout, stream=True)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"OpenAI流式API调用失败: {e}")
            yield f"API调用失败: {e}"


class QwenClient(BaseLLMClient):
    """通义千问客户端"""
    
    def _setup_session(self):
        """设置会话"""
        self.session.headers.update({
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        })
        
        if not self.config.base_url:
            self.config.base_url = "https://dashscope.aliyuncs.com/api/v1"
    
    def chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        """对话接口"""
        url = f"{self.config.base_url}/services/aigc/text-generation/generation"
        
        # 转换消息格式
        qwen_messages = []
        system_msg = None
        for msg in messages:
            if msg.role == "system":
                system_msg = msg.content
            else:
                qwen_messages.append({"role": msg.role, "content": msg.content})
        
        data = {
            "model": kwargs.get("model", self.config.model),
            "input": {
                "messages": qwen_messages
            },
            "parameters": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens)
            }
        }
        
        if system_msg:
            data["input"]["system"] = system_msg
        
        try:
            response = self.session.post(url, json=data, timeout=self.config.timeout)
            response.raise_for_status()
            result = response.json()
            
            if result.get("output"):
                return LLMResponse(
                    content=result["output"].get("text", ""),
                    usage=result.get("usage", {}),
                    finish_reason=result.get("output", {}).get("finish_reason", ""),
                    model=result.get("model", "")
                )
            else:
                error_msg = result.get("message", "未知错误")
                return LLMResponse(content=f"API调用失败: {error_msg}")
        except Exception as e:
            logger.error(f"通义千问API调用失败: {e}")
            return LLMResponse(content=f"API调用失败: {e}")
    
    def stream_chat(self, messages: List[Message], **kwargs):
        """流式对话接口"""
        url = f"{self.config.base_url}/services/aigc/text-generation/generation"
        
        # 转换消息格式
        qwen_messages = []
        system_msg = None
        for msg in messages:
            if msg.role == "system":
                system_msg = msg.content
            else:
                qwen_messages.append({"role": msg.role, "content": msg.content})
        
        data = {
            "model": kwargs.get("model", self.config.model),
            "input": {
                "messages": qwen_messages
            },
            "parameters": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "incremental_output": True
            }
        }
        
        if system_msg:
            data["input"]["system"] = system_msg
        
        try:
            response = self.session.post(url, json=data, timeout=self.config.timeout, stream=True)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data:'):
                        data_str = line[5:].strip()
                        if data_str:
                            try:
                                data = json.loads(data_str)
                                if data.get("output") and data["output"].get("text"):
                                    yield data["output"]["text"]
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"通义千问流式API调用失败: {e}")
            yield f"API调用失败: {e}"


class ClaudeClient(BaseLLMClient):
    """Claude客户端"""
    
    def _setup_session(self):
        """设置会话"""
        self.session.headers.update({
            "x-api-key": self.config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        })
        
        if not self.config.base_url:
            self.config.base_url = "https://api.anthropic.com/v1"
    
    def chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        """对话接口"""
        url = f"{self.config.base_url}/messages"
        
        # Claude的消息格式转换
        claude_messages = []
        system_msg = None
        
        for msg in messages:
            if msg.role == "system":
                system_msg = msg.content
            else:
                claude_messages.append({"role": msg.role, "content": msg.content})
        
        data = {
            "model": kwargs.get("model", self.config.model),
            "messages": claude_messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature)
        }
        
        if system_msg:
            data["system"] = system_msg
        
        try:
            response = self.session.post(url, json=data, timeout=self.config.timeout)
            response.raise_for_status()
            result = response.json()
            
            if result.get("content"):
                return LLMResponse(
                    content=result["content"][0]["text"],
                    usage=result.get("usage", {}),
                    finish_reason=result.get("stop_reason", ""),
                    model=result.get("model", "")
                )
            else:
                error_msg = result.get("error", {}).get("message", "未知错误")
                return LLMResponse(content=f"API调用失败: {error_msg}")
        except Exception as e:
            logger.error(f"Claude API调用失败: {e}")
            return LLMResponse(content=f"API调用失败: {e}")
    
    def stream_chat(self, messages: List[Message], **kwargs):
        """流式对话接口"""
        url = f"{self.config.base_url}/messages"
        
        # Claude的消息格式转换
        claude_messages = []
        system_msg = None
        
        for msg in messages:
            if msg.role == "system":
                system_msg = msg.content
            else:
                claude_messages.append({"role": msg.role, "content": msg.content})
        
        data = {
            "model": kwargs.get("model", self.config.model),
            "messages": claude_messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "stream": True
        }
        
        if system_msg:
            data["system"] = system_msg
        
        try:
            response = self.session.post(url, json=data, timeout=self.config.timeout, stream=True)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            if data.get("type") == "content_block_delta" and data.get("delta", {}).get("text"):
                                yield data["delta"]["text"]
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Claude流式API调用失败: {e}")
            yield f"API调用失败: {e}"


class LocalLLMClient(BaseLLMClient):
    """本地模型客户端（如Ollama）"""
    
    def _setup_session(self):
        """设置会话"""
        self.session.headers.update({
            "Content-Type": "application/json"
        })
        
        if not self.config.base_url:
            self.config.base_url = "http://localhost:11434"
    
    def chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        """对话接口"""
        url = f"{self.config.base_url}/api/chat"
        
        # 转换消息格式
        ollama_messages = []
        for msg in messages:
            ollama_messages.append({"role": msg.role, "content": msg.content})
        
        data = {
            "model": kwargs.get("model", self.config.model),
            "messages": ollama_messages,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens)
            }
        }
        
        try:
            response = self.session.post(url, json=data, timeout=self.config.timeout)
            response.raise_for_status()
            result = response.json()
            
            return LLMResponse(
                content=result.get("message", {}).get("content", ""),
                usage=result.get("usage", {}),
                finish_reason=result.get("done_reason", ""),
                model=result.get("model", "")
            )
        except Exception as e:
            logger.error(f"本地模型API调用失败: {e}")
            return LLMResponse(content=f"API调用失败: {e}")
    
    def stream_chat(self, messages: List[Message], **kwargs):
        """流式对话接口"""
        url = f"{self.config.base_url}/api/chat"
        
        # 转换消息格式
        ollama_messages = []
        for msg in messages:
            ollama_messages.append({"role": msg.role, "content": msg.content})
        
        data = {
            "model": kwargs.get("model", self.config.model),
            "messages": ollama_messages,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens)
            },
            "stream": True
        }
        
        try:
            response = self.session.post(url, json=data, timeout=self.config.timeout, stream=True)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    try:
                        data = json.loads(line)
                        if data.get("done"):
                            break
                        if data.get("message", {}).get("content"):
                            yield data["message"]["content"]
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"本地模型流式API调用失败: {e}")
            yield f"API调用失败: {e}"


class LLMClientFactory:
    """大模型客户端工厂"""
    
    @staticmethod
    def create_client(config: LLMConfig) -> BaseLLMClient:
        """创建大模型客户端"""
        provider = config.provider.lower()
        
        if provider == "openai":
            return OpenAIClient(config)
        elif provider == "qwen":
            return QwenClient(config)
        elif provider == "claude":
            return ClaudeClient(config)
        elif provider == "local":
            return LocalLLMClient(config)
        else:
            raise ValueError(f"不支持的模型提供商: {provider}")


# 全局大模型客户端实例
llm_client = None


def get_llm_client(config: Optional[LLMConfig] = None) -> BaseLLMClient:
    """获取大模型客户端实例"""
    global llm_client
    if llm_client is None or config is not None:
        if config is None:
            raise ValueError("首次调用需要提供配置")
        llm_client = LLMClientFactory.create_client(config)
    return llm_client


def chat_with_llm(messages: List[Message], config: Optional[LLMConfig] = None, **kwargs) -> LLMResponse:
    """便捷的对话接口"""
    client = get_llm_client(config)
    return client.chat(messages, **kwargs)


def stream_chat_with_llm(messages: List[Message], config: Optional[LLMConfig] = None, **kwargs):
    """便捷的流式对话接口"""
    client = get_llm_client(config)
    return client.stream_chat(messages, **kwargs)