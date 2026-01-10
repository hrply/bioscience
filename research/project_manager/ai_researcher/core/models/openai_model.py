"""
OpenAI模型接口实现
支持OpenAI兼容的API和自定义配置
"""

import json
from typing import Dict, Any, List, Optional
from .base import BaseModel


class OpenAIModel(BaseModel):
    """OpenAI模型接口"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-4",
        base_url: Optional[str] = None,
        config_manager=None,
        config_name: Optional[str] = None,
        **kwargs
    ):
        """
        初始化OpenAI模型

        Args:
            api_key: API密钥
            model_name: 模型名称
            base_url: API base URL
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
            from openai import OpenAI
        except ImportError:
            raise ImportError("请安装openai库: pip install openai")

        if not api_key:
            raise ValueError("API密钥不能为空")

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url or "https://api.openai.com/v1"
        )
        self.model_name = model_name

    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        api_type: str = "chat",
        **kwargs
    ) -> str:
        """
        生成文本响应

        Args:
            prompt: 用户提示词
            system_message: 系统消息
            temperature: 温度参数
            max_tokens: 最大token数
            api_type: API类型 (chat, response, reasoning等)
            **kwargs: 其他参数

        Returns:
            模型生成的文本
        """
        # 使用配置的默认值
        temperature = temperature if temperature is not None else getattr(self, 'temperature', 0.7)
        max_tokens = max_tokens if max_tokens is not None else getattr(self, 'max_tokens', 4000)

        # 合并参数
        params = {
            'temperature': temperature,
            'max_tokens': max_tokens,
            **getattr(self, 'extra_params', {}),
            **kwargs
        }

        # 根据api_type选择不同的调用方式
        if api_type == "chat" or api_type == "chat.completions":
            return self._chat_completions(prompt, system_message, **params)
        elif api_type == "response":
            return self._response_api(prompt, system_message, **params)
        elif api_type == "reasoning":
            return self._reasoning_api(prompt, system_message, **params)
        else:
            # 默认使用chat
            return self._chat_completions(prompt, system_message, **params)

    def _chat_completions(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs
    ) -> str:
        """Chat Completions API"""
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            **kwargs
        )

        return response.choices[0].message.content

    def _response_api(self, prompt: str, system_message: Optional[str] = None, **kwargs):
        """Response API (较新的API)"""
        # 构建输入文本
        input_text = prompt
        if system_message:
            input_text = f"{system_message}\n\n{prompt}"

        response = self.client.responses.create(
            model=self.model_name,
            input=input_text,
            **kwargs
        )

        return response.output_text

    def _reasoning_api(self, prompt: str, system_message: Optional[str] = None, **kwargs):
        """Reasoning API"""
        # 对于支持推理的模型
        input_text = prompt
        if system_message:
            input_text = f"{system_message}\n\n{prompt}"

        response = self.client.responses.create(
            model=self.model_name,
            input=input_text,
            reasoning={"effort": "medium"},
            **kwargs
        )

        return response.output_text

    def extract_structured_data(
        self,
        text: str,
        schema: Dict[str, str],
        temperature: float = 0.1,
        **kwargs
    ) -> Dict[str, Any]:
        """提取结构化数据"""
        prompt = f"""
请从以下文本中提取结构化数据，并以JSON格式返回：

文本内容：
{text}

数据结构要求：
{json.dumps(schema, indent=2)}

请只返回JSON数据，不要其他解释。
        """

        response = self.generate(prompt, temperature=temperature, **kwargs)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "raw_text": text,
                "error": "JSON解析失败",
                "partial_data": response
            }

    def embed(self, text: str, model: str = "text-embedding-ada-002") -> List[float]:
        """生成嵌入向量"""
        # 如果模型名不匹配，使用默认嵌入模型
        embed_model = model if model else "text-embedding-ada-002"

        response = self.client.embeddings.create(
            model=embed_model,
            input=text
        )
        return response.data[0].embedding

    def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """对话模式"""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            **getattr(self, 'extra_params', {})
        )
        return response.choices[0].message.content
