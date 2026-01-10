"""
模型配置管理器
用于管理多个模型的配置信息，包括endpoint、API类型、API KEY、模型等
"""

import json
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


logger = logging.getLogger(__name__)


class ModelConfigManager:
    """模型配置管理器"""

    def __init__(self, db_path: str = "models_config.db"):
        """
        初始化模型配置管理器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                provider TEXT NOT NULL,
                endpoint TEXT,
                api_type TEXT DEFAULT 'chat',
                api_key TEXT,
                api_secret_id TEXT,
                model_name TEXT NOT NULL,
                temperature REAL DEFAULT 0.7,
                max_tokens INTEGER DEFAULT 4000,
                use_proxy BOOLEAN DEFAULT 0,
                extra_params TEXT,
                is_active BOOLEAN DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS provider_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider_name TEXT UNIQUE NOT NULL,
                default_endpoint TEXT,
                default_api_type TEXT,
                supported_models TEXT,
                description TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        conn.commit()
        conn.close()

        # 初始化默认提供商配置
        self._init_default_providers()

    def _init_default_providers(self):
        """初始化默认提供商配置"""
        default_providers = [
            {
                "name": "OpenAI",
                "endpoint": "https://api.openai.com/v1",
                "api_type": "chat",
                "models": "gpt-4,gpt-3.5-turbo,gpt-4-turbo",
                "description": "OpenAI兼容格式 (OpenAI, DeepSeek, 智谱清言, 月之暗面等)"
            },
            {
                "name": "Anthropic",
                "endpoint": "https://api.anthropic.com",
                "api_type": "messages",
                "models": "claude-3-opus,claude-3-sonnet,claude-3-haiku",
                "description": "Anthropic兼容格式 (Claude等)"
            },
            {
                "name": "Gemini",
                "endpoint": "https://generativelanguage.googleapis.com/v1",
                "api_type": "generateContent",
                "models": "gemini-pro,gemini-pro-vision",
                "description": "Gemini原生格式"
            },
            {
                "name": "DASHSCOPE",
                "endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "api_type": "chat",
                "models": "qwen-turbo,qwen-plus,qwen-max,qwen2-72b-instruct",
                "description": "阿里巴巴DASHSCOPE (通义千问等)"
            },
            {
                "name": "ZAI",
                "endpoint": "https://open.bigmodel.cn/api/paas/v4",
                "api_type": "chat",
                "models": "glm-4,glm-4v,glm-3-turbo",
                "description": "BIGMODEL ZAI (智谱GLM等)"
            },
            {
                "name": "NEW-API",
                "endpoint": "",
                "api_type": "new_api",
                "models": "gpt-4,claude-3,gemini-pro",
                "description": "NEW-API 代理 (通过一个API兼容三种格式)"
            },
            {
                "name": "Custom",
                "endpoint": "",
                "api_type": "chat",
                "models": "",
                "description": "自定义模型配置"
            }
        ]

        for provider in default_providers:
            self.add_provider_config(
                name=provider["name"],
                endpoint=provider["endpoint"],
                api_type=provider["api_type"],
                supported_models=provider["models"],
                description=provider["description"]
            )

    def add_provider_config(
        self,
        name: str,
        endpoint: Optional[str] = None,
        api_type: Optional[str] = None,
        supported_models: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        添加提供商配置

        Args:
            name: 提供商名称
            endpoint: 默认endpoint
            api_type: 默认API类型
            supported_models: 支持的模型列表（逗号分隔）
            description: 描述

        Returns:
            是否添加成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT OR REPLACE INTO provider_configs
                (provider_name, default_endpoint, default_api_type, supported_models, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, endpoint, api_type, supported_models, description, now, now))

            conn.commit()
            logger.info(f"添加提供商配置: {name}")
            return True

        except Exception as e:
            logger.error(f"添加提供商配置失败: {e}")
            return False

        finally:
            conn.close()

    def get_provider_configs(self) -> List[Dict[str, Any]]:
        """获取所有提供商配置"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM provider_configs ORDER BY provider_name")
        rows = cursor.fetchall()

        columns = [desc[0] for desc in cursor.description]
        providers = [dict(zip(columns, row)) for row in rows]

        conn.close()
        return providers

    def add_model_config(
        self,
        name: str,
        provider: str,
        endpoint: Optional[str] = None,
        api_type: str = "chat",
        api_key: Optional[str] = None,
        api_secret_id: Optional[str] = None,
        model_name: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4000,
        use_proxy: bool = False,
        extra_params: Optional[Dict] = None,
        is_active: bool = False
    ) -> bool:
        """
        添加模型配置

        Args:
            name: 配置名称（唯一标识符）
            provider: 提供商名称
            endpoint: API endpoint（已弃用，使用api_secret_id）
            api_type: API类型 (chat, response, reasoning, thinking等)
            api_key: API密钥（已弃用，使用api_secret_id）
            api_secret_id: API密钥和端点组合ID
            model_name: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            use_proxy: 是否使用代理
            extra_params: 额外参数
            is_active: 是否激活

        Returns:
            是否添加成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO model_configs
                (name, provider, endpoint, api_type, api_key, api_secret_id, model_name, temperature, max_tokens, use_proxy, extra_params, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name, provider, endpoint, api_type, api_key, api_secret_id, model_name,
                temperature, max_tokens, use_proxy, json.dumps(extra_params or {}), is_active,
                now, now
            ))

            conn.commit()
            logger.info(f"添加模型配置: {name}")
            return True

        except Exception as e:
            logger.error(f"添加模型配置失败: {e}")
            return False

        finally:
            conn.close()

    def update_model_config(
        self,
        name: str,
        **kwargs
    ) -> bool:
        """
        更新模型配置

        Args:
            name: 配置名称
            **kwargs: 要更新的字段

        Returns:
            是否更新成功
        """
        if not kwargs:
            return True

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 构建更新语句
            fields = []
            values = []
            for key, value in kwargs.items():
                if key in ['endpoint', 'api_type', 'api_key', 'api_secret_id', 'model_name', 'temperature', 'max_tokens', 'use_proxy', 'extra_params', 'is_active']:
                    fields.append(f"{key} = ?")
                    if key == 'extra_params' and isinstance(value, dict):
                        values.append(json.dumps(value))
                    else:
                        values.append(value)

            if not fields:
                return True

            fields.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(name)

            query = f"UPDATE model_configs SET {', '.join(fields)} WHERE name = ?"
            cursor.execute(query, values)

            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"更新模型配置: {name}")
                return True
            else:
                logger.warning(f"模型配置不存在: {name}")
                return False

        except Exception as e:
            logger.error(f"更新模型配置失败: {e}")
            return False

        finally:
            conn.close()

    def get_model_config(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取模型配置

        Args:
            name: 配置名称

        Returns:
            模型配置字典
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM model_configs WHERE name = ?", (name,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        columns = [desc[0] for desc in cursor.description]
        config = dict(zip(columns, row))

        # 解析extra_params
        if config.get('extra_params'):
            try:
                config['extra_params'] = json.loads(config['extra_params'])
            except:
                config['extra_params'] = {}

        conn.close()
        return config

    def list_model_configs(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """
        列出所有模型配置

        Args:
            active_only: 只返回激活的配置

        Returns:
            模型配置列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if active_only:
            cursor.execute("SELECT * FROM model_configs WHERE is_active = 1 ORDER BY name")
        else:
            cursor.execute("SELECT * FROM model_configs ORDER BY name")

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        configs = []

        for row in rows:
            config = dict(zip(columns, row))
            if config.get('extra_params'):
                try:
                    config['extra_params'] = json.loads(config['extra_params'])
                except:
                    config['extra_params'] = {}
            configs.append(config)

        conn.close()
        return configs

    def delete_model_config(self, name: str) -> bool:
        """
        删除模型配置

        Args:
            name: 配置名称

        Returns:
            是否删除成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM model_configs WHERE name = ?", (name,))
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"删除模型配置: {name}")
                return True
            else:
                logger.warning(f"模型配置不存在: {name}")
                return False

        except Exception as e:
            logger.error(f"删除模型配置失败: {e}")
            return False

        finally:
            conn.close()

    def activate_config(self, name: str) -> bool:
        """
        激活配置（同时停用其他配置）

        Args:
            name: 配置名称

        Returns:
            是否激活成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 先停用所有配置
            cursor.execute("UPDATE model_configs SET is_active = 0")

            # 激活指定配置
            cursor.execute("UPDATE model_configs SET is_active = 1 WHERE name = ?", (name,))

            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"激活模型配置: {name}")
                return True
            else:
                logger.warning(f"模型配置不存在: {name}")
                return False

        except Exception as e:
            logger.error(f"激活模型配置失败: {e}")
            return False

        finally:
            conn.close()

    def get_active_config(self) -> Optional[Dict[str, Any]]:
        """获取当前激活的配置"""
        configs = self.list_model_configs(active_only=True)
        return configs[0] if configs else None

    def get_model_config_with_secret(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取模型配置（包括API密钥和端点信息）

        Args:
            name: 配置名称

        Returns:
            模型配置字典（包含完整的API密钥和端点信息）
        """
        from ai_researcher.secrets_manager import get_secrets_manager

        config = self.get_model_config(name)
        if not config:
            return None

        # 如果有api_secret_id，从secrets_manager获取完整信息
        if config.get('api_secret_id'):
            secrets_manager = get_secrets_manager()
            secret_info = secrets_manager.get_api_secret_by_id(config['api_secret_id'])
            if secret_info:
                config['api_key'] = secret_info['api_key']
                config['endpoint'] = secret_info['base_url']

        return config

    def test_connection(self, name: str) -> Dict[str, Any]:
        """
        测试模型连接

        Args:
            name: 配置名称

        Returns:
            测试结果字典
        """
        config = self.get_model_config(name)
        if not config:
            return {"success": False, "error": "配置不存在"}

        try:
            from ai_researcher.secrets_manager import get_secrets_manager

            # 获取API密钥和端点信息
            secrets_manager = get_secrets_manager()
            api_key = config.get("api_key", "")
            endpoint = config.get("endpoint", "")
            model_name = config.get("model_name", "")
            provider = config.get("provider", "")
            api_type = config.get("api_type", "chat")

            if not api_key:
                return {
                    "success": False,
                    "error": "API密钥未配置"
                }

            if not endpoint:
                return {
                    "success": False,
                    "error": "API端点未配置"
                }

            if not model_name:
                return {
                    "success": False,
                    "error": "模型名称未配置"
                }

            # 使用secrets_manager的test_api_connection方法
            test_result = secrets_manager.test_api_connection(
                provider=provider,
                api_key=api_key,
                base_url=endpoint,
                test_model=model_name
            )

            return test_result

        except Exception as e:
            return {
                "success": False,
                "error": f"测试连接时发生错误: {str(e)[:200]}"
            }
