"""
OpenCode CLI工具集成
支持开源代码生成CLI工具
"""

import json
from typing import Dict, List, Optional, Any
from .base import BaseCLI


class OpenCodeCLI(BaseCLI):
    """
    OpenCode CLI工具

    开源代码生成CLI工具的统一接口。
    支持多种开源代码生成模型。

    主要功能:
    - 代码生成
    - 代码重构
    - 代码优化
    - 多语言支持

    支持的模型:
    - codellama
    - starcoder
    - WizardCoder
    - deepseek-coder

    使用示例:
        cli = OpenCodeCLI()
        result = cli.generate_code("写一个排序算法", language="python")
    """


    def __init__(self, config: Optional[Dict] = None):
        """
        初始化OpenCode CLI

        Args:
            config: 配置字典
                - api_key: API密钥
                - model: 默认模型
        """
        super().__init__("opencode", config)

    def _check_installation(self) -> bool:
        """检查OpenCode CLI是否已安装"""
        try:
            result = self._run_quiet_command("--version")
            return True
        except Exception:
            return False

    def _run_quiet_command(self, args: str) -> str:
        """静默运行命令"""
        import subprocess
        cmd = ["opencode"] + args.split()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except Exception:
            raise RuntimeError("OpenCode CLI未安装或不可用")

    def execute(
        self,
        command: str,
        prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行OpenCode命令

        Args:
            command: 命令类型
            prompt: 提示词
            **kwargs: 其他参数

        Returns:
            执行结果
        """
        if not self.is_available():
            raise RuntimeError("OpenCode CLI未安装或不可用")

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

    def generate_code(
        self,
        prompt: str,
        language: str = "python",
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成代码

        Args:
            prompt: 代码描述
            language: 编程语言
            **kwargs: 其他参数

        Returns:
            生成的代码
        """
        return self.execute(
            command="generate",
            prompt=prompt,
            language=language,
            **kwargs
        )

    def refactor_code(self, code: str, **kwargs) -> Dict[str, Any]:
        """
        重构代码

        Args:
            code: 源代码
            **kwargs: 重构选项

        Returns:
            重构后的代码
        """
        prompt = f"重构以下代码：\n```\n{code}\n```"
        return self.execute(command="refactor", prompt=prompt, **kwargs)

    def optimize_code(self, code: str) -> Dict[str, Any]:
        """
        优化代码

        Args:
            code: 源代码

        Returns:
            优化后的代码
        """
        prompt = f"优化以下代码：\n```\n{code}\n```"
        return self.execute(command="optimize", prompt=prompt)

    def get_models(self) -> List[str]:
        """获取可用模型"""
        # OpenCode可能支持多种开源模型
        return [
            "codellama",
            "starcoder",
            " WizardCoder",
            "deepseek-coder"
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
