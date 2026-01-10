"""
Codex CLI工具集成
支持OpenAI Codex的CLI命令
"""

import json
from typing import Dict, List, Optional, Any
from .base import BaseCLI


class CodexCLI(BaseCLI):
    """
    Codex CLI工具

    OpenAI Codex的代码生成命令行接口封装类。
    提供代码补全、代码解释、测试生成等开发者友好的功能。

    主要功能:
    - 代码补全
    - 代码解释
    - 测试代码生成
    - 代码重构建议

    支持的模型:
    - code-davinci-002
    - code-davinci-001
    - code-cushman-002
    - code-cushman-001

    使用示例:
        cli = CodexCLI()
        result = cli.complete("def factorial(n):")
    """


    def __init__(self, config: Optional[Dict] = None):
        """
        初始化Codex CLI

        Args:
            config: 配置字典
                - api_key: API密钥
                - base_url: API基础URL
        """
        super().__init__("codex", config)

    def _check_installation(self) -> bool:
        """检查Codex CLI是否已安装"""
        try:
            result = self._run_quiet_command("--version")
            return True
        except Exception:
            return False

    def _run_quiet_command(self, args: str) -> str:
        """静默运行命令"""
        import subprocess
        cmd = ["codex"] + args.split()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except Exception:
            raise RuntimeError("Codex CLI未安装或不可用")

    def execute(
        self,
        command: str,
        prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行Codex命令

        Args:
            command: 命令类型
            prompt: 提示词
            **kwargs: 其他参数

        Returns:
            执行结果
        """
        if not self.is_available():
            raise RuntimeError("Codex CLI未安装或不可用")

        args = [command]

        if prompt:
            args.append(f'"{prompt}"')

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
                "command": command
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command
            }

    def complete(
        self,
        prompt: str,
        model: str = "code-davinci-002",
        **kwargs
    ) -> Dict[str, Any]:
        """
        代码补全

        Args:
            prompt: 提示词
            model: 模型名称
            **kwargs: 其他参数

        Returns:
            补全结果
        """
        return self.execute(
            command="complete",
            prompt=prompt,
            model=model,
            **kwargs
        )

    def explain_code(self, code: str) -> Dict[str, Any]:
        """
        解释代码

        Args:
            code: 要解释的代码

        Returns:
            解释结果
        """
        prompt = f"解释以下代码：\n```\n{code}\n```"
        return self.execute(command="explain", prompt=prompt)

    def generate_tests(self, code: str) -> Dict[str, Any]:
        """
        生成测试代码

        Args:
            code: 源代码

        Returns:
            测试代码
        """
        prompt = f"为以下代码生成单元测试：\n```\n{code}\n```"
        return self.execute(command="test", prompt=prompt)

    def get_models(self) -> List[str]:
        """获取可用模型"""
        return [
            "code-davinci-002",
            "code-davinci-001",
            "code-cushman-002",
            "code-cushman-001"
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
