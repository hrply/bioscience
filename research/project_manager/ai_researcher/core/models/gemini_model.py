"""
Google Gemini模型接口实现
支持自定义配置
"""

import json
from typing import Dict, Any, List, Optional
from .base import BaseModel


class GeminiModel(BaseModel):
    """Gemini模型接口"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-pro",
        endpoint: Optional[str] = None,
        config_manager=None,
        config_name: Optional[str] = None,
        **kwargs
    ):
        """
        初始化Gemini模型

        Args:
            api_key: API密钥
            model_name: 模型名称
            endpoint: API endpoint
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
                endpoint = config.get('endpoint') or endpoint
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
            import google.generativeai as genai
        except ImportError:
            raise ImportError("请安装google-generativeai库: pip install google-generativeai")

        if not api_key:
            raise ValueError("API密钥不能为空")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name

    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        api_type: str = "generateContent",
        **kwargs
    ) -> str:
        """
        生成文本响应

        Args:
            prompt: 用户提示词
            system_message: 系统消息
            temperature: 温度参数
            max_tokens: 最大token数
            api_type: API类型 (generateContent, reasoning等)
            **kwargs: 其他参数

        Returns:
            模型生成的文本
        """
        # 使用配置的默认值
        temperature = temperature if temperature is not None else getattr(self, 'temperature', 0.7)
        max_tokens = max_tokens if max_tokens is not None else getattr(self, 'max_tokens', 4000)

        # 合并参数
        gen_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        gen_config.update(getattr(self, 'extra_params', {}))
        gen_config.update(kwargs)

        # 构建输入文本
        full_prompt = prompt
        if system_message:
            full_prompt = f"{system_message}\n\n{prompt}"

        # 根据api_type选择调用方式
        if api_type == "generateContent" or api_type == "chat":
            return self._generate_content(full_prompt, gen_config)
        elif api_type == "reasoning":
            return self._reasoning(full_prompt, gen_config)
        else:
            return self._generate_content(full_prompt, gen_config)

    def _generate_content(self, prompt: str, gen_config: Dict[str, Any]) -> str:
        """generateContent API"""
        response = self.model.generate_content(
            prompt,
            generation_config=gen_config
        )
        return response.text

    def _reasoning(self, prompt: str, gen_config: Dict[str, Any]) -> str:
        """Reasoning API (如果支持)"""
        # Gemini的推理模式
        response = self.model.generate_content(
            prompt,
            generation_config=gen_config
        )
        return response.text

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

    def embed(self, text: str, model: str = "models/embedding-001") -> List[float]:
        """生成嵌入向量"""
        import google.generativeai as genai

        embed_model = model if model else "models/embedding-001"

        response = genai.embed_content(
            model=embed_model,
            content=text,
            task_type="retrieval_document"
        )
        return response["embedding"]

    def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """对话模式"""
        # 转换消息格式
        history = []
        for msg in messages[:-1]:
            if msg["role"] == "user":
                history.append(f"Human: {msg['content']}")
            else:
                history.append(f"Assistant: {msg['content']}")

        last_message = messages[-1]["content"]
        full_prompt = "\n".join(history) + f"\nHuman: {last_message}\nAssistant:"

        response = self.generate(full_prompt, **kwargs)
        return response
