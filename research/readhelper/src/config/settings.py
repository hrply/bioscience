"""
应用配置设置
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用配置
    app_name: str = "文献阅读助手"
    app_version: str = "1.0.0"
    debug: bool = Field(False, env="DEBUG")
    
    # RAGFlow配置
    ragflow_base_url: str = Field("http://localhost:9380", env="RAGFLOW_BASE_URL")
    ragflow_api_key: str = Field("", env="RAGFLOW_API_KEY")
    ragflow_timeout: int = Field(30, env="RAGFLOW_TIMEOUT")
    ragflow_max_retries: int = Field(3, env="RAGFLOW_MAX_RETRIES")
    
    # 大模型配置
    llm_provider: str = Field("qwen", env="LLM_PROVIDER")  # openai, qwen, claude, local
    llm_api_key: str = Field("", env="LLM_API_KEY")
    llm_base_url: str = Field("", env="LLM_BASE_URL")
    llm_model: str = Field("", env="LLM_MODEL")
    llm_temperature: float = Field(0.7, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(2048, env="LLM_MAX_TOKENS")
    llm_timeout: int = Field(60, env="LLM_TIMEOUT")
    llm_max_retries: int = Field(3, env="LLM_MAX_RETRIES")
    
    # 文件处理配置
    max_pdf_size: int = 50 * 1024 * 1024  # 50MB
    supported_formats: list = ["pdf", "txt", "html", "htm", "md"]
    auto_extract_metadata: bool = True
    temp_dir: str = "/tmp/literature_helper"
    
    # 存储配置
    data_dir: str = Field(default_factory=lambda: os.path.expanduser("~/.literature_helper"))
    db_path: str = Field(default_factory=lambda: os.path.expanduser("~/.literature_helper/literature.db"))
    vector_db_path: str = Field(default_factory=lambda: os.path.expanduser("~/.literature_helper/vector_db"))
    knowledge_graph_path: str = Field(default_factory=lambda: os.path.expanduser("~/.literature_helper/knowledge_graph"))
    
    # AI分析配置
    summary_max_length: int = 500
    keywords_max_count: int = 10
    entity_extraction_enabled: bool = True
    auto_classification_enabled: bool = True
    
    # 搜索配置
    search_results_limit: int = 20
    similarity_threshold: float = 0.7
    semantic_search_enabled: bool = True
    
    # 缓存配置
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1小时
    cache_size: int = 1000
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = Field(default_factory=lambda: os.path.expanduser("~/.literature_helper/logs/app.log"))
    
    # UI配置
    page_size: int = 10
    theme: str = "light"
    language: str = "zh"
    
    # 文献挖掘配置
    mining_max_docs: int = 50
    mining_similarity_threshold: float = 0.6
    mining_summary_length: str = "中等长度"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()
        self._set_default_models()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.data_dir,
            os.path.dirname(self.db_path),
            self.vector_db_path,
            self.knowledge_graph_path,
            self.temp_dir,
            os.path.dirname(self.log_file)
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _set_default_models(self):
        """设置默认模型"""
        if not self.llm_model:
            if self.llm_provider == "openai":
                self.llm_model = "gpt-3.5-turbo"
            elif self.llm_provider == "qwen":
                self.llm_model = "qwen-turbo"
            elif self.llm_provider == "claude":
                self.llm_model = "claude-3-sonnet-20240229"
            elif self.llm_provider == "local":
                self.llm_model = "llama2"
        
        if not self.llm_base_url:
            if self.llm_provider == "openai":
                self.llm_base_url = "https://api.openai.com/v1"
            elif self.llm_provider == "qwen":
                self.llm_base_url = "https://dashscope.aliyuncs.com/api/v1"
            elif self.llm_provider == "claude":
                self.llm_base_url = "https://api.anthropic.com/v1"
            elif self.llm_provider == "local":
                self.llm_base_url = "http://localhost:11434"
    
    def get_ragflow_config(self) -> Dict[str, Any]:
        """获取RAGFlow配置"""
        return {
            "base_url": self.ragflow_base_url,
            "api_key": self.ragflow_api_key,
            "timeout": self.ragflow_timeout,
            "max_retries": self.ragflow_max_retries
        }
    
    def get_llm_config(self) -> Dict[str, Any]:
        """获取大模型配置"""
        return {
            "provider": self.llm_provider,
            "api_key": self.llm_api_key,
            "base_url": self.llm_base_url,
            "model": self.llm_model,
            "temperature": self.llm_temperature,
            "max_tokens": self.llm_max_tokens,
            "timeout": self.llm_timeout,
            "max_retries": self.llm_max_retries
        }
    
    def get_db_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return {
            "db_path": self.db_path,
            "vector_db_path": self.vector_db_path,
            "knowledge_graph_path": self.knowledge_graph_path
        }
    
    def get_processing_config(self) -> Dict[str, Any]:
        """获取文档处理配置"""
        return {
            "max_pdf_size": self.max_pdf_size,
            "supported_formats": self.supported_formats,
            "auto_extract_metadata": self.auto_extract_metadata,
            "temp_dir": self.temp_dir
        }
    
    def get_ai_config(self) -> Dict[str, Any]:
        """获取AI分析配置"""
        return {
            "summary_max_length": self.summary_max_length,
            "keywords_max_count": self.keywords_max_count,
            "entity_extraction_enabled": self.entity_extraction_enabled,
            "auto_classification_enabled": self.auto_classification_enabled
        }
    
    def get_search_config(self) -> Dict[str, Any]:
        """获取搜索配置"""
        return {
            "search_results_limit": self.search_results_limit,
            "similarity_threshold": self.similarity_threshold,
            "semantic_search_enabled": self.semantic_search_enabled
        }
    
    def get_cache_config(self) -> Dict[str, Any]:
        """获取缓存配置"""
        return {
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
            "cache_size": self.cache_size
        }
    
    def get_mining_config(self) -> Dict[str, Any]:
        """获取文献挖掘配置"""
        return {
            "max_docs": self.mining_max_docs,
            "similarity_threshold": self.mining_similarity_threshold,
            "summary_length": self.mining_summary_length
        }
    
    def is_ragflow_configured(self) -> bool:
        """检查RAGFlow是否已配置"""
        return bool(self.ragflow_api_key and self.ragflow_base_url)
    
    def is_llm_configured(self) -> bool:
        """检查大模型是否已配置"""
        return bool(self.llm_api_key and self.llm_model)
    
    def validate_config(self) -> Dict[str, Any]:
        """验证配置"""
        issues = []
        warnings = []
        
        # 检查必需配置
        if not self.is_ragflow_configured():
            issues.append("RAGFlow配置不完整，请检查API密钥和URL")
        
        if not self.is_llm_configured():
            issues.append("大模型配置不完整，请检查API密钥和模型")
        
        # 检查可选配置
        if self.llm_temperature < 0 or self.llm_temperature > 2:
            warnings.append("温度参数应在0-2之间")
        
        if self.llm_max_tokens < 100 or self.llm_max_tokens > 8192:
            warnings.append("最大token数应在100-8192之间")
        
        if self.similarity_threshold < 0 or self.similarity_threshold > 1:
            warnings.append("相似度阈值应在0-1之间")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }


# 全局设置实例
settings = Settings()