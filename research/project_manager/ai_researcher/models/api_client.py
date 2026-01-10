"""
统一API客户端工厂
根据模型配置自动选择合适的SDK并设置环境变量
"""

import os
import logging
from typing import Dict, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class SDKType(Enum):
    """支持的SDK类型"""
    OPENAI_COMPATIBLE = "openai"
    ANTHROPIC_COMPATIBLE = "anthropic"
    GEMINI_NATIVE = "gemini"
    DASHSCOPE = "dashscope"
    ZAI = "zai"


class UnifiedAPIClient:
    """
    统一API客户端
    内部使用AI_API_KEY和AI_BASE_URL变量
    根据配置自动映射到对应的SDK变量
    """

    # SDK类型到环境变量映射
    SDK_ENV_MAPPING = {
        SDKType.OPENAI_COMPATIBLE: {
            "api_key": "OPENAI_API_KEY",
            "base_url": "OPENAI_BASE_URL",
        },
        SDKType.ANTHROPIC_COMPATIBLE: {
            "api_key": "ANTHROPIC_API_KEY",
            "base_url": "ANTHROPIC_BASE_URL",
        },
        SDKType.GEMINI_NATIVE: {
            "api_key": "GEMINI_API_KEY",
            "base_url": "GEMINI_BASE_URL",
        },
        SDKType.DASHSCOPE: {
            "api_key": "DASHSCOPE_API_KEY",
            "base_url": "DASHSCOPE_BASE_URL",
        },
        SDKType.ZAI: {
            "api_key": "ZAI_API_KEY",
            "base_url": "ZAI_BASE_URL",
        },
    }

    def __init__(self, config_name: str, model_config_manager, secrets_manager):
        """
        初始化统一API客户端

        Args:
            config_name: 模型配置名称
            model_config_manager: 模型配置管理器实例
            secrets_manager: 密钥管理器实例
        """
        self.config_name = config_name
        self.config_manager = model_config_manager
        self.secrets_manager = secrets_manager
        self.config = None
        self.sdk_type = None

        # 加载配置并设置环境变量
        self._load_and_set_config()

    def _load_and_set_config(self):
        """加载配置并设置统一环境变量"""
        # 从数据库加载配置
        self.config = self.config_manager.get_model_config(self.config_name)
        if not self.config:
            raise ValueError(f"配置 '{self.config_name}' 不存在")

        # 获取基础URL
        base_url = self.config.get("endpoint", "")
        api_type = self.config.get("api_type", "")

        # 如果是NEW-API类型，根据API类型生成完整的URL
        if api_type == "new_api":
            base_url = self._generate_full_url(base_url, api_type, self.config)

        # 设置统一变量
        os.environ["AI_API_KEY"] = self.config.get("api_key", "")
        os.environ["AI_BASE_URL"] = base_url

        logger.info(f"已设置统一变量 - AI_API_KEY: {self.config.get('api_key', '')[:10]}...")
        logger.info(f"已设置统一变量 - AI_BASE_URL: {base_url}")

        # 设置代理（如果启用）
        self._set_proxy()

        # 根据API类型确定SDK类型
        self.sdk_type = self._determine_sdk_type()

        # 映射到对应的SDK环境变量
        self._map_to_sdk_env()

    def _set_proxy(self):
        """
        设置代理环境变量（如果配置中启用了代理）
        """
        use_proxy = self.config.get("use_proxy", False)

        if use_proxy:
            # 从环境变量获取代理地址
            http_proxy = os.environ.get("HTTP_PROXY")
            https_proxy = os.environ.get("HTTPS_PROXY", http_proxy)

            if http_proxy:
                # 设置代理环境变量
                os.environ["HTTP_PROXY"] = http_proxy
                os.environ["HTTPS_PROXY"] = https_proxy
                logger.info(f"已启用代理: {http_proxy}")
            else:
                logger.warning("配置启用了代理，但HTTP_PROXY环境变量未设置")

    def _generate_full_url(self, base_url: str, api_type: str, config: Dict[str, Any]) -> str:
        """
        根据API类型生成完整的URL

        Args:
            base_url: 基础URL
            api_type: API类型
            config: 配置字典

        Returns:
            完整的URL
        """
        if not base_url:
            return ""

        # 移除末尾的斜杠
        base_url = base_url.rstrip("/")

        # 根据API类型生成完整URL
        if api_type == "new_api":
            # NEW-API根据具体的API格式补全路径
            # 这里需要从配置中获取实际要使用的API格式
            model_name = config.get("model_name", "").lower()
            provider = config.get("provider", "").lower()

            # 优先根据提供商判断
            if "claude" in provider or "anthropic" in provider:
                return f"{base_url}/v1/messages"
            elif "gemini" in provider or "google" in provider:
                return f"{base_url}/v1/generateContent"
            elif "openai" in provider or "deepseek" in provider:
                return f"{base_url}/v1/chat/completions"

            # 再根据模型名判断
            if any(keyword in model_name for keyword in ["claude", "anthropic"]):
                return f"{base_url}/v1/messages"
            elif any(keyword in model_name for keyword in ["gemini", "google"]):
                return f"{base_url}/v1/generateContent"
            elif any(keyword in model_name for keyword in ["gpt", "chat"]):
                return f"{base_url}/v1/chat/completions"
            else:
                # 默认使用OpenAI格式
                return f"{base_url}/v1/chat/completions"
        else:
            # 非NEW-API类型，直接返回基础URL
            return base_url

    @staticmethod
    def get_full_url_preview(base_url: str, api_type: str, model_name: str = "") -> str:
        """
        获取完整URL的预览（静态方法，用于前端显示）

        Args:
            base_url: 基础URL
            api_type: API类型
            model_name: 模型名称（可选，用于更准确的预览）

        Returns:
            完整URL的预览
        """
        if not base_url:
            return ""

        # 移除末尾的斜杠
        base_url = base_url.rstrip("/")

        if api_type == "new_api":
            model_name_lower = model_name.lower()
            if any(keyword in model_name_lower for keyword in ["claude", "anthropic"]):
                return f"{base_url}/v1/messages"
            elif any(keyword in model_name_lower for keyword in ["gemini", "google"]):
                return f"{base_url}/v1/generateContent"
            elif any(keyword in model_name_lower for keyword in ["gpt", "chat"]):
                return f"{base_url}/v1/chat/completions"
            else:
                return f"{base_url}/v1/{{API格式路径}}"
        else:
            return base_url

    def _determine_sdk_type(self) -> SDKType:
        """
        根据API类型确定SDK类型

        Returns:
            SDK类型枚举
        """
        api_type = self.config.get("api_type", "").lower()
        provider = self.config.get("provider", "").lower()
        model_name = self.config.get("model_name", "").lower()

        # 如果是NEW-API类型，根据提供商和模型名确定SDK类型
        if api_type == "new_api":
            # 优先根据提供商判断
            if "claude" in provider or "anthropic" in provider:
                return SDKType.ANTHROPIC_COMPATIBLE
            elif "gemini" in provider or "google" in provider:
                return SDKType.GEMINI_NATIVE
            elif "openai" in provider or "deepseek" in provider:
                return SDKType.OPENAI_COMPATIBLE
            # 再根据模型名判断
            elif any(keyword in model_name for keyword in ["claude", "anthropic"]):
                return SDKType.ANTHROPIC_COMPATIBLE
            elif any(keyword in model_name for keyword in ["gemini", "google"]):
                return SDKType.GEMINI_NATIVE
            else:
                return SDKType.OPENAI_COMPATIBLE

        # 先检查特定的提供商（优先级更高）
        if "dashscope" in provider or "阿里巴巴" in provider or "aliyun" in provider:
            # 阿里巴巴DASHSCOPE
            return SDKType.DASHSCOPE
        elif "zai" in provider or "bigmodel" in provider or "智谱" in provider:
            # BIGMODEL ZAI
            return SDKType.ZAI
        elif "anthropic" in provider or "claude" in provider:
            # Anthropic兼容格式
            return SDKType.ANTHROPIC_COMPATIBLE
        elif "gemini" in provider or "google" in provider:
            # Gemini原生格式
            return SDKType.GEMINI_NATIVE
        elif "openai" in provider or "deepseek" in provider:
            # OpenAI兼容格式
            return SDKType.OPENAI_COMPATIBLE

        # 再根据API类型判断
        elif "generatecontent" in api_type:
            # Gemini原生格式
            return SDKType.GEMINI_NATIVE
        elif "messages" in api_type:
            # Anthropic兼容格式
            return SDKType.ANTHROPIC_COMPATIBLE
        elif "chat" in api_type or "completions" in api_type:
            # OpenAI兼容格式
            return SDKType.OPENAI_COMPATIBLE
        else:
            # 默认使用OpenAI兼容格式
            return SDKType.OPENAI_COMPATIBLE

    def _map_to_sdk_env(self):
        """将统一变量映射到对应的SDK环境变量"""
        if self.sdk_type not in self.SDK_ENV_MAPPING:
            raise ValueError(f"不支持的SDK类型: {self.sdk_type}")

        mapping = self.SDK_ENV_MAPPING[self.sdk_type]

        # 设置SDK特定的环境变量
        os.environ[mapping["api_key"]] = os.environ.get("AI_API_KEY", "")
        os.environ[mapping["base_url"]] = os.environ.get("AI_BASE_URL", "")

        logger.info(f"已映射到 {self.sdk_type.value} SDK")
        logger.info(f"  {mapping['api_key']}: {os.environ.get(mapping['api_key'], '')[:10]}...")
        logger.info(f"  {mapping['base_url']}: {os.environ.get(mapping['base_url'], '')}")

    def get_client(self):
        """
        获取对应的SDK客户端实例

        Returns:
            配置好的SDK客户端
        """
        if self.sdk_type == SDKType.OPENAI_COMPATIBLE:
            try:
                from openai import OpenAI
                return OpenAI(
                    api_key=os.environ.get("OPENAI_API_KEY"),
                    base_url=os.environ.get("OPENAI_BASE_URL"),
                )
            except ImportError:
                raise ImportError("请安装 openai 库: pip install openai")

        elif self.sdk_type == SDKType.ANTHROPIC_COMPATIBLE:
            try:
                import anthropic
                return anthropic.Anthropic(
                    api_key=os.environ.get("ANTHROPIC_API_KEY"),
                    base_url=os.environ.get("ANTHROPIC_BASE_URL"),
                )
            except ImportError:
                raise ImportError("请安装 anthropic 库: pip install anthropic")

        elif self.sdk_type == SDKType.GEMINI_NATIVE:
            try:
                import google.generativeai as genai
                genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
                return genai
            except ImportError:
                raise ImportError("请安装 google-generativeai 库: pip install google-generativeai")

        elif self.sdk_type == SDKType.DASHSCOPE:
            try:
                import dashscope
                dashscope.api_key = os.environ.get("DASHSCOPE_API_KEY")
                return dashscope
            except ImportError:
                raise ImportError("请安装 dashscope 库: pip install dashscope")

        elif self.sdk_type == SDKType.ZAI:
            try:
                # ZAI SDK示例
                import zai
                zai.api_key = os.environ.get("ZAI_API_KEY")
                return zai
            except ImportError:
                raise ImportError("请安装 zai 库")

        else:
            raise ValueError(f"未实现的SDK类型: {self.sdk_type}")

    def get_model_name(self) -> str:
        """获取模型名称"""
        return self.config.get("model_name", "")

    def get_temperature(self) -> float:
        """获取温度参数"""
        return self.config.get("temperature", 0.7)

    def get_max_tokens(self) -> int:
        """获取最大token数"""
        return self.config.get("max_tokens", 4000)

    def get_use_proxy(self) -> bool:
        """获取是否使用代理"""
        return self.config.get("use_proxy", False)

    def get_proxy_url(self) -> Optional[str]:
        """获取代理URL"""
        return os.environ.get("HTTP_PROXY")

    @classmethod
    def get_available_sdk_types(cls) -> Dict[str, str]:
        """获取可用的SDK类型列表"""
        return {
            "openai": "OpenAI兼容 (OpenAI, DeepSeek, 智谱等)",
            "anthropic": "Anthropic兼容 (Claude等)",
            "gemini": "Gemini原生格式",
            "dashscope": "阿里巴巴DASHSCOPE",
            "zai": "BIGMODEL ZAI",
        }


class ModelConfigResolver:
    """
    模型配置解析器
    提供便捷的方法来使用统一API变量
    """

    def __init__(self, model_config_manager, secrets_manager):
        self.config_manager = model_config_manager
        self.secrets_manager = secrets_manager

    def load_config(self, config_name: str) -> UnifiedAPIClient:
        """
        加载配置并返回统一API客户端

        Args:
            config_name: 配置名称

        Returns:
            配置好的UnifiedAPIClient实例
        """
        return UnifiedAPIClient(config_name, self.config_manager, self.secrets_manager)

    def list_configs(self) -> list:
        """列出所有可用配置"""
        return self.config_manager.list_model_configs()

    def get_active_config(self) -> Optional[UnifiedAPIClient]:
        """
        获取当前激活的配置

        Returns:
            配置好的UnifiedAPIClient实例，如果没有激活的配置则返回None
        """
        active_config = self.config_manager.get_active_config()
        if not active_config:
            return None

        return self.load_config(active_config["name"])


# 全局配置解析器实例
_global_resolver: Optional[ModelConfigResolver] = None


def get_config_resolver() -> ModelConfigResolver:
    """获取全局配置解析器实例"""
    global _global_resolver
    if _global_resolver is None:
        from ai_researcher.models.config_manager import ModelConfigManager
        from ai_researcher.secrets_manager import get_secrets_manager

        _global_resolver = ModelConfigResolver(
            ModelConfigManager(),
            get_secrets_manager()
        )
    return _global_resolver


# 便捷函数
def load_model_config(config_name: str) -> UnifiedAPIClient:
    """便捷函数：加载模型配置"""
    return get_config_resolver().load_config(config_name)


def get_active_model_config() -> Optional[UnifiedAPIClient]:
    """便捷函数：获取当前激活的模型配置"""
    return get_config_resolver().get_active_config()
