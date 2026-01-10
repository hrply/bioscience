"""
安全密钥管理模块
用于在应用内安全地存储和管理API密钥
"""

import os
import json
import base64
import logging
from pathlib import Path
from typing import Dict, Optional, List, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import getpass

# 设置logger
logger = logging.getLogger(__name__)


class SecretsManager:
    """
    安全密钥管理器
    使用加密方式在本地存储API密钥
    """

    def __init__(self, secrets_dir: Optional[str] = None):
        """
        初始化密钥管理器

        Args:
            secrets_dir: 密钥存储目录，默认在用户主目录的.ai_researcher目录
        """
        if secrets_dir:
            self.secrets_dir = Path(secrets_dir)
        else:
            self.secrets_dir = Path.home() / ".ai_researcher" / "secrets"

        self.secrets_file = self.secrets_dir / "secrets.enc"
        self.secrets_dir.mkdir(parents=True, exist_ok=True)

        # 初始化加密器
        self._init_encryption()

    def _get_master_password(self, is_new: bool = False) -> str:
        """
        获取主密码

        优先级:
        1. 环境变量 'TOKEN'（Docker Compose推荐方式）
        2. 交互式输入（开发和测试）

        Args:
            is_new: 是否为首次设置密码

        Returns:
            主密码
        """
        # 优先从环境变量获取主密码
        master_password = os.environ.get("TOKEN")

        if master_password:
            return master_password

        # 如果环境变量不存在，交互式获取
        if is_new:
            password = getpass.getpass(
                "首次使用，请设置一个主密码用于加密API密钥: "
            )
            confirm = getpass.getpass("确认密码: ")
            if password != confirm:
                raise ValueError("密码不匹配")
            return password
        else:
            return getpass.getpass("请输入主密码: ")

    def _init_encryption(self):
        """初始化加密系统"""
        self.key_file = self.secrets_dir / ".key"

        # 生成或加载加密密钥
        if not self.key_file.exists():
            # 生成新密钥
            password = self._get_master_password(is_new=True)

            # 生成加密密钥
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

            # 保存盐和密钥
            with open(self.key_file, "wb") as f:
                f.write(salt + key)
            os.chmod(self.key_file, 0o600)  # 只允许所有者读写

            logger.info("✓ 加密密钥已生成并保存")
        else:
            # 加载现有密钥
            password = self._get_master_password(is_new=False)
            with open(self.key_file, "rb") as f:
                data = f.read()
                salt = data[:16]
                stored_key = data[16:]

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            try:
                key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
                if key != stored_key:
                    raise ValueError("密码错误")
            except Exception:
                raise ValueError("密码错误")

        # 初始化Fernet加密器
        with open(self.key_file, "rb") as f:
            data = f.read()
            salt = data[:16]
            stored_key = data[16:]

        # 从主密码生成Fernet密钥
        password = self._get_master_password(is_new=False)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.fernet = Fernet(key)

    def _load_secrets(self) -> Dict[str, str]:
        """加载加密的密钥"""
        if not self.secrets_file.exists():
            return {}

        try:
            with open(self.secrets_file, "rb") as f:
                encrypted_data = f.read()

            # 解密
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"加载密钥失败: {e}")
            return {}

    def _save_secrets(self, secrets: Dict[str, str]):
        """保存加密的密钥"""
        try:
            # 序列化并加密
            json_data = json.dumps(secrets).encode()
            encrypted_data = self.fernet.encrypt(json_data)

            # 保存
            with open(self.secrets_file, "wb") as f:
                f.write(encrypted_data)

            # 设置文件权限
            os.chmod(self.secrets_file, 0o600)

        except Exception as e:
            logger.error(f"保存密钥失败: {e}")
            raise

    def add_api_secret(
        self,
        provider: str,
        api_key: str,
        base_url: str,
        tag: str = ""
    ) -> str:
        """
        添加API密钥和端点组合（追加模式）

        Args:
            provider: 提供商名称
            api_key: API密钥
            base_url: API端点URL
            tag: 标签（用于标记用途）

        Returns:
            生成的组合ID
        """
        secrets = self._load_secrets()

        # 初始化api_secrets列表
        if "api_secrets" not in secrets:
            secrets["api_secrets"] = []

        # 生成唯一ID
        import uuid
        secret_id = str(uuid.uuid4())[:8]

        # 添加新的组合
        secrets["api_secrets"].append({
            "id": secret_id,
            "provider": provider,
            "tag": tag,
            "api_key": api_key,
            "base_url": base_url
        })

        self._save_secrets(secrets)
        logger.info(f"✓ {provider.upper()} API密钥和端点组合已添加 (ID: {secret_id})")
        return secret_id

    def set_api_key(self, provider: str, api_key: str):
        """
        添加API密钥（追加模式，已弃用，请使用 add_api_secret）

        Args:
            provider: 提供商名称
            api_key: API密钥
        """
        # 获取现有的base_url
        base_url = self.get_base_url(provider)
        if not base_url:
            base_url = ""

        # 使用新的方法添加
        self.add_api_secret(provider, api_key, base_url, f"default-{provider}")
        logger.warning(f"⚠ 此方法已弃用，请使用 add_api_secret()")

    def get_api_secrets(self, provider: Optional[str] = None) -> List[Dict[str, str]]:
        """
        获取API密钥和端点组合列表

        Args:
            provider: 提供商名称（可选，None表示获取所有）

        Returns:
            组合列表，每个元素包含id, provider, tag, api_key, base_url
        """
        secrets = self._load_secrets()
        all_secrets = secrets.get("api_secrets", [])

        if provider:
            return [s for s in all_secrets if s["provider"] == provider]
        return all_secrets

    def get_api_keys(self, provider: str) -> List[Dict[str, str]]:
        """
        获取提供商的所有API密钥（兼容旧版本）

        Args:
            provider: 提供商名称

        Returns:
            API密钥列表，每个元素包含id和key
        """
        secrets = self._load_secrets()
        # 兼容旧版本：从新的api_secrets结构提取
        api_secrets = secrets.get("api_secrets", [])
        provider_secrets = [s for s in api_secrets if s["provider"] == provider]
        return [{"id": s["id"], "key": s["api_key"]} for s in provider_secrets]

    def delete_api_secret_by_id(self, secret_id: str) -> bool:
        """
        通过ID删除API密钥和端点组合

        Args:
            secret_id: 组合ID

        Returns:
            是否删除成功
        """
        secrets = self._load_secrets()

        if "api_secrets" not in secrets:
            logger.warning(f"✗ 没有找到API密钥组合")
            return False

        api_secrets = secrets["api_secrets"]
        for i, secret in enumerate(api_secrets):
            if secret["id"] == secret_id:
                provider = secret["provider"]
                del api_secrets[i]
                self._save_secrets(secrets)
                logger.info(f"✓ {provider.upper()} API密钥组合已删除 (ID: {secret_id})")
                return True

        logger.warning(f"✗ API密钥组合不存在")
        return False

    def delete_api_key_by_id(self, provider: str, key_id: str) -> bool:
        """
        通过ID删除API密钥（兼容旧版本）

        Args:
            provider: 提供商名称
            key_id: 密钥ID

        Returns:
            是否删除成功
        """
        return self.delete_api_secret_by_id(key_id)

    def get_all_providers(self) -> List[str]:
        """
        获取所有已配置的提供商名称

        Returns:
            提供商名称列表
        """
        secrets = self._load_secrets()
        api_secrets = secrets.get("api_secrets", [])
        providers = set(s["provider"] for s in api_secrets)
        return list(providers)

    def get_api_secret_by_id(self, secret_id: str) -> Optional[Dict[str, str]]:
        """
        通过ID获取API密钥和端点组合

        Args:
            secret_id: 组合ID

        Returns:
            组合信息字典，如果不存在则返回None
        """
        secrets = self._load_secrets()
        api_secrets = secrets.get("api_secrets", [])

        for secret in api_secrets:
            if secret["id"] == secret_id:
                return secret

        return None

    def update_api_secret(
        self,
        secret_id: str,
        tag: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> bool:
        """
        更新API密钥和端点组合

        Args:
            secret_id: 组合ID
            tag: 新标签（可选）
            api_key: 新API密钥（可选）
            base_url: 新端点（可选）

        Returns:
            是否更新成功
        """
        secrets = self._load_secrets()
        api_secrets = secrets.get("api_secrets", [])

        for secret in api_secrets:
            if secret["id"] == secret_id:
                if tag is not None:
                    secret["tag"] = tag
                if api_key is not None:
                    secret["api_key"] = api_key
                if base_url is not None:
                    secret["base_url"] = base_url

                self._save_secrets(secrets)
                logger.info(f"✓ API密钥组合已更新 (ID: {secret_id})")
                return True

        logger.warning(f"✗ API密钥组合不存在")
        return False

    def set_base_url(self, provider: str, base_url: str):
        """
        设置或更新API端点

        Args:
            provider: 提供商名称
            base_url: API端点URL
        """
        secrets = self._load_secrets()

        # 初始化base_urls字典
        if "base_urls" not in secrets:
            secrets["base_urls"] = {}

        secrets["base_urls"][provider] = base_url
        self._save_secrets(secrets)
        logger.info(f"✓ {provider.upper()} 端点已保存")

    def get_base_url(self, provider: str) -> Optional[str]:
        """
        获取API端点

        Args:
            provider: 提供商名称

        Returns:
            API端点URL
        """
        secrets = self._load_secrets()
        return secrets.get("base_urls", {}).get(provider)

    def get_all_base_urls(self) -> Dict[str, str]:
        """
        获取所有API端点

        Returns:
            提供商名称到端点的映射
        """
        secrets = self._load_secrets()
        return secrets.get("base_urls", {})

    def delete_base_url(self, provider: str) -> bool:
        """
        删除API端点

        Args:
            provider: 提供商名称

        Returns:
            是否删除成功
        """
        secrets = self._load_secrets()

        if "base_urls" in secrets and provider in secrets["base_urls"]:
            del secrets["base_urls"][provider]
            self._save_secrets(secrets)
            logger.info(f"✓ {provider.upper()} 端点已删除")
            return True

        return False

    def list_api_keys(self) -> Dict[str, bool]:
        """
        列出所有API密钥状态（兼容性方法）

        Returns:
            字典，键为提供商名称，值为是否已设置
        """
        secrets = self._load_secrets()
        api_keys = secrets.get("api_keys", {})
        return {
            provider: len(keys) > 0
            for provider, keys in api_keys.items()
        }

    def has_api_key(self, provider: str) -> bool:
        """
        检查是否已设置API密钥（兼容性方法）

        Args:
            provider: 提供商名称

        Returns:
            是否已设置
        """
        return len(self.get_api_keys(provider)) > 0

    def setup_interactive(self):
        """交互式设置API密钥"""
        print("\n=== API密钥配置向导 ===\n")

        providers = {
            "1": ("openai", "OpenAI (GPT-4, GPT-3.5)"),
            "2": ("gemini", "Google Gemini"),
            "3": ("anthropic", "Anthropic (Claude)"),
        }

        print("支持的模型提供商:")
        for key, (name, desc) in providers.items():
            print(f"  {key}. {name} - {desc}")

        while True:
            print("\n请选择要配置的提供商 (输入数字)，或输入 'q' 退出:")
            choice = input("> ").strip().lower()

            if choice == "q":
                break

            if choice not in providers:
                print("无效选择，请重新输入")
                continue

            provider, desc = providers[choice]

            print(f"\n正在配置: {desc}")
            print(f"请输入 {provider.upper()} API密钥:")
            api_key = getpass.getpass("(输入密钥，键盘输入不会显示)")

            if not api_key.strip():
                print("✗ 密钥不能为空")
                continue

            try:
                self.set_api_key(provider, api_key.strip())
            except Exception as e:
                print(f"✗ 保存密钥失败: {e}")
                continue

            # 询问是否继续配置其他提供商
            if not input("\n是否继续配置其他提供商? (y/n): ").lower().startswith('y'):
                break

        print("\n=== 配置完成 ===")
        self.show_status()

    def show_status(self):
        """显示当前密钥状态"""
        print("\n=== API密钥状态 ===")
        all_secrets = self.get_api_secrets()

        if not all_secrets:
            print("  没有配置任何API密钥组合")
            return {}

        # 按提供商分组显示
        providers = {}
        for secret in all_secrets:
            provider = secret["provider"]
            if provider not in providers:
                providers[provider] = []
            providers[provider].append(secret)

        for provider, secrets in providers.items():
            print(f"\n  [{provider.upper()}]")
            for secret in secrets:
                tag = secret["tag"] if secret["tag"] else "(无标签)"
                key_preview = secret["api_key"][:10] + "..." if len(secret["api_key"]) > 10 else secret["api_key"]
                endpoint = secret["base_url"] if secret["base_url"] else "(无端点)"
                print(f"    ID: {secret['id']} | TAG: {tag} | KEY: {key_preview} | ENDPOINT: {endpoint}")

        return {provider: len(secrets) > 0 for provider in providers.keys()}

    def test_api_connection(
        self,
        provider: str,
        api_key: str,
        base_url: str,
        test_model: str = "gpt-3.5-turbo"
    ) -> Dict[str, Any]:
        """
        测试API密钥连通性

        Args:
            provider: 提供商名称
            api_key: API密钥
            base_url: API端点URL
            test_model: 测试用模型名称

        Returns:
            测试结果字典，包含success、message等信息
        """
        try:
            import requests
            import json

            # 根据提供商确定API类型和测试参数
            provider_lower = provider.lower()

            # 默认测试参数
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "AI-Researcher/1.0"
            }
            test_payload = {
                "model": test_model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }

            # 根据提供商类型设置headers和URL
            if provider_lower in ["openai", "dashscope", "zai"] or "openai" in provider_lower:
                # OpenAI兼容格式
                headers["Authorization"] = f"Bearer {api_key}"
                url = f"{base_url.rstrip('/')}/chat/completions"
                if "dashscope" in provider_lower:
                    headers["Authorization"] = f"Bearer {api_key}"
                elif "zai" in provider_lower:
                    headers["Authorization"] = f"Bearer {api_key}"
            elif provider_lower in ["anthropic"] or "claude" in provider_lower:
                # Anthropic格式
                headers["x-api-key"] = api_key
                headers["anthropic-version"] = "2023-06-01"
                url = f"{base_url.rstrip('/')}/messages"
                test_payload = {
                    "model": test_model,
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "Hello"}]
                }
            elif provider_lower in ["gemini"] or "gemini" in provider_lower:
                # Gemini格式
                headers["x-goog-api-key"] = api_key
                url = f"{base_url.rstrip('/')}/models/{test_model}:generateContent"
                test_payload = {
                    "contents": [{
                        "parts": [{"text": "Hello"}]
                    }],
                    "generationConfig": {
                        "maxOutputTokens": 10
                    }
                }
            else:
                # 尝试使用OpenAI兼容格式
                headers["Authorization"] = f"Bearer {api_key}"
                url = f"{base_url.rstrip('/')}/chat/completions"

            # 发送测试请求
            response = requests.post(
                url,
                headers=headers,
                json=test_payload,
                timeout=10
            )

            # 检查响应
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": f"✅ {provider} 连接成功",
                    "status_code": response.status_code,
                    "response_preview": response.text[:200]
                }
            else:
                return {
                    "success": False,
                    "message": f"❌ {provider} 连接失败",
                    "status_code": response.status_code,
                    "error": response.text[:200]
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": f"❌ {provider} 连接超时",
                "error": "请求超时（10秒）"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": f"❌ {provider} 连接错误",
                "error": "无法连接到服务器，请检查端点URL"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ {provider} 测试失败",
                "error": str(e)[:200]
            }


# 全局密钥管理器实例
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """获取全局密钥管理器实例"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


def get_api_key(provider: str) -> Optional[str]:
    """便捷函数：获取API密钥"""
    return get_secrets_manager().get_api_key(provider)


def set_api_key(provider: str, api_key: str):
    """便捷函数：设置API密钥"""
    get_secrets_manager().set_api_key(provider, api_key)


def check_api_keys() -> Dict[str, bool]:
    """便捷函数：检查所有API密钥状态"""
    return get_secrets_manager().list_api_keys()
