"""
配置管理模块
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# 定义公共 API
__all__ = ['load_config', 'save_config']

# 设置logger
logger = logging.getLogger(__name__)


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        配置字典
    """
    # 默认配置文件路径
    if not config_path:
        config_path = os.environ.get("AI_RESEARCHER_CONFIG", "/app/data/config/config.yaml")

    config_file = Path(config_path)

    # 默认配置
    default_config = {
        "openai": {
            "api_key": os.environ.get("OPENAI_API_KEY"),
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4"
        },
        "gemini": {
            "api_key": os.environ.get("GEMINI_API_KEY"),
            "model": "gemini-pro"
        },
        "anthropic": {
            "api_key": os.environ.get("ANTHROPIC_API_KEY"),
            "model": "claude-3-sonnet-20240229"
        },
        "ragflow": {
            "endpoint": "http://localhost:9380"
        },
        "database": {
            "path": "/app/data/experiments/experiments.db"
        },
        "templates": {
            "dir": "/app/data/templates"
        },
        "results": {
            "dir": "/app/data/results",
            "charts_dir": "/app/data/results/charts"
        }
    }

    # 如果配置文件存在，加载并合并
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f) or {}
            # 合并配置
            _merge_config(default_config, user_config)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")

    return default_config


def _merge_config(default: Dict, user: Dict):
    """递归合并配置"""
    for key, value in user.items():
        if key in default and isinstance(default[key], dict) and isinstance(value, dict):
            _merge_config(default[key], value)
        else:
            default[key] = value


def save_config(config: Dict[str, Any], config_path: Optional[str] = None) -> bool:
    """
    保存配置文件

    Args:
        config: 配置字典
        config_path: 配置文件路径

    Returns:
        是否保存成功
    """
    # 默认配置文件路径
    if not config_path:
        config_path = os.environ.get("AI_RESEARCHER_CONFIG", "/app/data/config/config.yaml")

    config_file = Path(config_path)

    try:
        # 确保目录存在
        config_file.parent.mkdir(parents=True, exist_ok=True)

        # 保存配置
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)

        return True
    except Exception as e:
        logger.error(f"保存配置文件失败: {e}")
        return False
