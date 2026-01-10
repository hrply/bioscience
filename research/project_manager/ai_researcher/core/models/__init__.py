"""
模型接口模块
支持多种模型提供商的统一接口
"""

from .base import BaseModel
from .openai_model import OpenAIModel
from .gemini_model import GeminiModel
from .anthropic_model import AnthropicModel
from .iflow_model import IFlowModel

__all__ = [
    "BaseModel",
    "OpenAIModel",
    "GeminiModel",
    "AnthropicModel",
    "IFlowModel"
]
