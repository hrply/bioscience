"""
模型接口抽象基类
统一不同模型提供商的接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseModel(ABC):
    """
    模型接口基类

    定义了所有模型提供商的统一接口，确保所有模型实现相同的方法。
    继承此类的模型类需要实现所有抽象方法。

    主要方法:
    - generate: 生成文本响应
    - extract_structured_data: 从文本中提取结构化数据
    - embed: 生成文本嵌入向量
    - chat: 对话模式
    """

    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.kwargs = kwargs

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> str:
        """
        生成文本响应

        Args:
            prompt: 用户提示词
            system_message: 系统消息
            temperature: 温度参数
            max_tokens: 最大令牌数
            **kwargs: 其他参数

        Returns:
            模型生成的文本
        """
        pass

    @abstractmethod
    def extract_structured_data(
        self,
        text: str,
        schema: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        从文本中提取结构化数据

        Args:
            text: 输入文本
            schema: 数据结构定义

        Returns:
            结构化数据字典
        """
        pass

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """
        生成文本嵌入向量

        Args:
            text: 输入文本

        Returns:
            嵌入向量
        """
        pass

    @abstractmethod
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
        pass
