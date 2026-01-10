"""
Claude CLI工具集成
支持Anthropic Claude的CLI命令
"""

import json
from typing import Dict, List, Optional, Any
from .base import BaseCLI


class ClaudeCLI(BaseCLI):
    """
    Claude CLI工具

    Anthropic Claude的命令行接口封装类。
    提供对Claude AI助手的便捷访问，支持文本生成、对话等操作。

    主要功能:
    - 聊天对话
    - 文本补全
    - 配置管理
    - 模型列表获取

    支持的模型:
    - claude-3-5-sonnet-20241022
    - claude-3-5-haiku-20241022
    - claude-3-opus-20240229
    - claude-3-sonnet-20240229
    - claude-3-haiku-20240307

    使用示例:
        cli = ClaudeCLI()
        result = cli.chat("你好", model="claude-3-5-sonnet-20241022")
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化Claude CLI

        Args:
            config: 配置字典
                - api_key: API密钥
                - model: 默认模型 (如: claude-3-5-sonnet-20241022)
                - base_url: API基础URL
        """
        super().__init__("claude", config)

    def _check_installation(self) -> bool:
        """检查Claude CLI是否已安装"""
        try:
            # 尝试运行claude --version
            result = self._run_quiet_command("--version")
            return True
        except Exception:
            return False

    def _run_quiet_command(self, args: str) -> str:
        """静默运行命令（不抛出异常）"""
        import subprocess
        cmd = ["claude"] + args.split()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except Exception:
            raise RuntimeError("Claude CLI未安装或不可用")

    def execute(
        self,
        command: str,
        prompt: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行Claude命令

        Args:
            command: 命令类型 (chat, complete, etc.)
            prompt: 提示词
            model: 模型名称
            **kwargs: 其他参数

        Returns:
            执行结果
        """
        if not self.is_available():
            raise RuntimeError("Claude CLI未安装或不可用")

        # 构建命令
        args = [command]

        if prompt:
            args.append(prompt)

        if model:
            args.extend(["--model", model])

        # 添加其他参数
        for key, value in kwargs.items():
            if isinstance(value, bool):
                if value:
                    args.append(f"--{key}")
            else:
                args.extend([f"--{key}", str(value)])

        try:
            output = self._run_command(" ".join(args))
            return {
                "success": True,
                "output": output,
                "command": command,
                "model": model or self.config.get("model", "claude-3-5-sonnet-20241022")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command
            }

    def chat(self, message: str, model: Optional[str] = None) -> Dict[str, Any]:
        """
        开始聊天对话

        Args:
            message: 消息内容
            model: 模型名称

        Returns:
            聊天响应
        """
        return self.execute(
            command="chat",
            prompt=message,
            model=model
        )

    def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        生成文本补全

        Args:
            prompt: 提示词
            model: 模型名称
            max_tokens: 最大token数

        Returns:
            补全结果
        """
        params = {"prompt": prompt}
        if max_tokens:
            params["max_tokens"] = max_tokens

        return self.execute(
            command="complete",
            model=model,
            **params
        )

    def configure(self, **config) -> bool:
        """
        配置Claude CLI

        Args:
            **config: 配置项

        Returns:
            配置是否成功
        """
        try:
            # Claude CLI通常使用环境变量或配置文件
            # 这里可以添加配置逻辑
            self.update_config(config)
            return True
        except Exception:
            return False

    def get_models(self) -> List[str]:
        """
        获取可用模型列表

        Returns:
            模型名称列表
        """
        # Claude常用的模型
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]

    def get_status(self) -> Dict[str, Any]:
        """
        获取CLI状态

        Returns:
            状态信息
        """
        return {
            "name": self.name,
            "installed": self.installed,
            "version": self.get_version(),
            "config": self.config,
            "available_models": self.get_models()
        }
