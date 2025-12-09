"""应用配置设置"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    app_name: str = "实验记录智能助手"
    version: str = "1.0.0"
    debug: bool = False
    
    # API配置
    QWEN_API_KEY: Optional[str] = Field(None, env="QWEN_API_KEY")
    QWEN_API_URL: str = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    QWEN_MODEL: str = "qwen-turbo"
    
    # 本地模型配置（扩展点）
    LOCAL_MODEL_ENABLED: bool = False
    LOCAL_MODEL_PATH: Optional[str] = None
    LOCAL_MODEL_PORT: int = 8000
    
    # 数据存储配置
    data_dir: Path = Field(default_factory=lambda: Path.home() / ".lab_notebook_agent")
    db_path: Path = Field(default_factory=lambda: Path.home() / ".lab_notebook_agent" / "experiments.db")
    vector_db_path: Path = Field(default_factory=lambda: Path.home() / ".lab_notebook_agent" / "vector_db")
    templates_dir: Path = Field(default_factory=lambda: Path(__file__).parent / "templates")
    
    # 防幻觉配置
    validation_enabled: bool = True
    strict_mode: bool = True  # 严格模式：更严格的验证
    conservative_mode: bool = False  # 保守模式：仅应用明确匹配的修改
    
    # MCP配置
    agent_timeout: int = 30  # Agent超时时间（秒）
    max_context_length: int = 8000  # 最大上下文长度
    memory_retention_days: int = 30  # 内存保留天数
    
    # UI配置
    max_file_size_mb: int = 10  # 最大文件上传大小（MB）
    diff_highlight_color: str = "#ffeb3b"  # 差异高亮颜色
    
    # 性能配置
    max_concurrent_requests: int = 3
    cache_enabled: bool = True
    cache_ttl_hours: int = 24
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
    
    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置"""
        if self.LOCAL_MODEL_ENABLED and self.LOCAL_MODEL_PATH:
            return {
                "type": "local",
                "base_url": f"http://localhost:{self.LOCAL_MODEL_PORT}",
                "model": "local"
            }
        elif self.QWEN_API_KEY:
            return {
                "type": "qwen",
                "api_key": self.QWEN_API_KEY,
                "api_url": self.QWEN_API_URL,
                "model": self.QWEN_MODEL
            }
        else:
            raise ValueError("未配置任何可用的AI模型API")
    
    def is_api_configured(self) -> bool:
        """检查API是否已配置"""
        return bool(self.QWEN_API_KEY or (self.LOCAL_MODEL_ENABLED and self.LOCAL_MODEL_PATH))
    
    # EXTENSION_POINT: 未来可扩展其他AI模型配置
    def get_available_models(self) -> Dict[str, str]:
        """获取可用的AI模型列表"""
        models = {}
        if self.QWEN_API_KEY:
            models["qwen"] = "通义千问"
        if self.LOCAL_MODEL_ENABLED:
            models["local"] = "本地模型"
        # 扩展点：可添加其他模型
        return models