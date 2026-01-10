"""
Anthropic模型接口实现
支持Anthropic Claude API调用
"""

import json
from typing import Dict, Any, List, Optional, Union
from .base import BaseModel


class AnthropicModel(BaseModel):
    """Anthropic Claude模型接口"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "claude-3-5-sonnet-20241022",
        base_url: Optional[str] = None,
        config_manager=None,
        config_name: Optional[str] = None,
        **kwargs
    ):
        """
        初始化Anthropic模型

        Args:
            api_key: API密钥
            model_name: 模型名称 (如: claude-3-5-sonnet-20241022)
            base_url: API基础URL
            config_manager: 模型配置管理器
            config_name: 配置名称（从配置管理器加载）
            **kwargs: 其他参数
        """
        super().__init__(model_name, **kwargs)

        # 如果提供了配置管理器，从管理器加载配置
        if config_manager and config_name:
            config = config_manager.get_model_config(config_name)
            if config:
                api_key = config.get('api_key') or api_key
                base_url = config.get('endpoint') or base_url
                model_name = config.get('model_name') or model_name
                self.temperature = config.get('temperature', 0.7)
                self.max_tokens = config.get('max_tokens', 4000)
                self.extra_params = config.get('extra_params', {})
            else:
                raise ValueError(f"配置不存在: {config_name}")
        else:
            self.temperature = kwargs.get('temperature', 0.7)
            self.max_tokens = kwargs.get('max_tokens', 4000)
            self.extra_params = {}

        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("请安装anthropic库: pip install anthropic")

        if not api_key:
            raise ValueError("API密钥不能为空")

        self.client = Anthropic(
            api_key=api_key,
            base_url=base_url or "https://api.anthropic.com"
        )
        self.model_name = model_name

    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        生成文本响应

        Args:
            prompt: 用户提示词
            system_message: 系统消息
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数

        Returns:
            模型生成的文本
        """
        # 使用配置的默认值
        temperature = temperature if temperature is not None else getattr(self, 'temperature', 0.7)
        max_tokens = max_tokens if max_tokens is not None else getattr(self, 'max_tokens', 4000)

        # 构建消息
        messages = []
        if system_message:
            # Anthropic使用system参数而非system消息
            system = system_message
        else:
            system = None

        # 将prompt作为用户消息
        messages.append({
            "role": "user",
            "content": prompt
        })

        # 合并参数
        params = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **getattr(self, 'extra_params', {}),
            **kwargs
        }

        if system:
            params["system"] = system

        try:
            response = self.client.messages.create(**params)
            return response.content[0].text
        except Exception as e:
            raise RuntimeError(f"Anthropic API调用失败: {e}")

    def extract_structured_data(
        self,
        text: str,
        schema: Dict[str, str],
        temperature: float = 0.1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        从文本中提取结构化数据

        Args:
            text: 输入文本
            schema: 数据结构定义
            temperature: 温度参数
            **kwargs: 其他参数

        Returns:
            结构化数据字典
        """
        prompt = f"""
请从以下文本中提取结构化数据，并以JSON格式返回：

文本内容：
{text}

数据结构要求：
{json.dumps(schema, indent=2)}

请只返回JSON数据，不要其他解释。
        """

        response = self.generate(
            prompt=prompt,
            temperature=temperature,
            **kwargs
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "raw_text": text,
                "error": "JSON解析失败",
                "partial_data": response
            }

    def embed(self, text: str) -> List[float]:
        """
        生成文本嵌入向量

        注意：Anthropic当前不直接支持嵌入功能

        Args:
            text: 输入文本

        Returns:
            嵌入向量
        """
        # Anthropic当前不支持嵌入，建议使用其他模型
        raise NotImplementedError(
            "Anthropic当前不支持嵌入功能。"
            "请使用OpenAI或其他模型提供商获取嵌入向量。"
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        对话模式

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Returns:
            响应文本
        """
        # 将消息转换为Anthropic格式
        anthropic_messages = []
        system_message = None

        for msg in messages:
            if msg["role"] == "system":
                # Anthropic使用独立的system参数
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # 构建参数
        params = {
            "model": self.model_name,
            "messages": anthropic_messages,
            **getattr(self, 'extra_params', {})
        }

        if system_message:
            params["system"] = system_message

        # 添加其他参数
        temperature = kwargs.get('temperature', getattr(self, 'temperature', 0.7))
        max_tokens = kwargs.get('max_tokens', getattr(self, 'max_tokens', 4000))
        params["temperature"] = temperature
        params["max_tokens"] = max_tokens

        try:
            response = self.client.messages.create(**params)
            return response.content[0].text
        except Exception as e:
            raise RuntimeError(f"Anthropic对话调用失败: {e}")

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            模型信息字典
        """
        return {
            "provider": "anthropic",
            "model_name": self.model_name,
            "temperature": getattr(self, 'temperature', 0.7),
            "max_tokens": getattr(self, 'max_tokens', 4000)
        }
