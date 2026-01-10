"""
Gemini CLI工具集成
支持Google Gemini的CLI命令
"""

import json
from typing import Dict, List, Optional, Any
from .base import BaseCLI


class GeminiCLI(BaseCLI):
    """
    Gemini CLI工具

    Google Gemini的命令行接口封装类。
    提供文本生成、对话、嵌入等功能。

    主要功能:
    - 聊天对话
    - 文本生成
    - 嵌入向量生成
    - 多模态支持

    支持的模型:
    - gemini-1.5-pro
    - gemini-1.5-flash
    - gemini-1.0-pro

    使用示例:
        cli = GeminiCLI()
        result = cli.chat("解释量子计算")
    """


    def __init__(self, config: Optional[Dict] = None):
        """
        初始化Gemini CLI

        Args:
            config: 配置字典
                - api_key: API密钥
                - model: 默认模型
        """
        super().__init__("gemini", config)

    def _check_installation(self) -> bool:
        """检查Gemini CLI是否已安装"""
        try:
            result = self._run_quiet_command("--version")
            return True
        except Exception:
            return False

    def _run_quiet_command(self, args: str) -> str:
        """静默运行命令"""
        import subprocess
        cmd = ["gemini"] + args.split()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except Exception:
            raise RuntimeError("Gemini CLI未安装或不可用")

    def execute(
        self,
        command: str,
        prompt: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行Gemini命令

        Args:
            command: 命令类型
            prompt: 提示词
            model: 模型名称
            **kwargs: 其他参数

        Returns:
            执行结果
        """
        if not self.is_available():
            raise RuntimeError("Gemini CLI未安装或不可用")

        args = [command]

        if prompt:
            args.append(f'"{prompt}"')

        if model:
            args.extend(["--model", model])

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
                "model": model or self.config.get("model", "gemini-1.5-pro")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command
            }

    def chat(self, message: str, model: Optional[str] = None) -> Dict[str, Any]:
        """聊天对话"""
        return self.execute(
            command="chat",
            prompt=message,
            model=model
        )

    def generate(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        """生成文本"""
        return self.execute(
            command="generate",
            prompt=prompt,
            model=model
        )

    def embed(self, text: str) -> Dict[str, Any]:
        """生成嵌入向量"""
        return self.execute(
            command="embed",
            prompt=text
        )

    def get_models(self) -> List[str]:
        """获取可用模型"""
        return [
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.0-pro"
        ]

    def get_status(self) -> Dict[str, Any]:
        """获取CLI状态"""
        return {
            "name": self.name,
            "installed": self.installed,
            "version": self.get_version(),
            "config": self.config,
            "available_models": self.get_models()
        }
