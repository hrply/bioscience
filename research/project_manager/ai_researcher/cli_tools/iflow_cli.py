"""
iFlow CLI工具集成
支持iFlow CLI的所有功能
"""

import json
from typing import Dict, List, Optional, Any
from .base import BaseCLI


class IFlowCLI(BaseCLI):
    """
    iFlow CLI工具

    iFlow命令行接口封装类。
    提供完整的CLI功能，包括工具执行、任务规划等特色功能。

    主要功能:
    - 聊天对话
    - 文本补全
    - 任务计划生成
    - 工具调用执行
    - 工具列表获取

    支持的模型:
    - Qwen3-Coder
    - Qwen3-Instruct
    - deepseek-coder

    支持的工具:
    - read, write, shell, grep, glob, edit

    使用示例:
        cli = IFlowCLI()
        result = cli.chat("设计一个实验")
        plan = cli.generate_plan("蛋白质纯化实验")
    """


    def __init__(self, config: Optional[Dict] = None):
        """
        初始化iFlow CLI

        Args:
            config: 配置字典
                - api_key: API密钥
                - base_url: API基础URL
                - model: 默认模型
        """
        super().__init__("iflow", config)

    def _check_installation(self) -> bool:
        """检查iFlow CLI是否已安装"""
        try:
            result = self._run_quiet_command("--version")
            return True
        except Exception:
            return False

    def _run_quiet_command(self, args: str) -> str:
        """静默运行命令"""
        import subprocess
        cmd = ["iflow"] + args.split()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except Exception:
            raise RuntimeError("iFlow CLI未安装或不可用")

    def execute(
        self,
        command: str,
        prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行iFlow命令

        Args:
            command: 命令类型
            prompt: 提示词
            **kwargs: 其他参数

        Returns:
            执行结果
        """
        if not self.is_available():
            raise RuntimeError("iFlow CLI未安装或不可用")

        args = [command]

        if prompt:
            args.append(f'"{prompt}"')

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
                "command": command
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command
            }

    def chat(self, message: str) -> Dict[str, Any]:
        """聊天对话"""
        return self.execute(
            command="chat",
            prompt=message
        )

    def complete(self, prompt: str) -> Dict[str, Any]:
        """文本补全"""
        return self.execute(
            command="complete",
            prompt=prompt
        )

    def generate_plan(self, objective: str) -> Dict[str, Any]:
        """
        生成任务计划

        Args:
            objective: 任务目标

        Returns:
            计划信息
        """
        return self.execute(
            command="plan",
            prompt=objective
        )

    def use_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        使用工具

        Args:
            tool_name: 工具名称
            **kwargs: 工具参数

        Returns:
            工具执行结果
        """
        args = " ".join([f"--{k} {v}" for k, v in kwargs.items()])
        return self.execute(
            command=f"tool {tool_name}",
            prompt=args
        )

    def configure(self, **config) -> bool:
        """
        配置iFlow CLI

        Args:
            **config: 配置项

        Returns:
            配置是否成功
        """
        try:
            self.update_config(config)
            return True
        except Exception:
            return False

    def get_models(self) -> List[str]:
        """获取可用模型"""
        return [
            "Qwen3-Coder",
            "Qwen3-Instruct",
            "deepseek-coder"
        ]

    def get_tools(self) -> List[str]:
        """获取可用工具列表"""
        return [
            "read",
            "write",
            "shell",
            "grep",
            "glob",
            "edit"
        ]

    def get_status(self) -> Dict[str, Any]:
        """获取CLI状态"""
        return {
            "name": self.name,
            "installed": self.installed,
            "version": self.get_version(),
            "config": self.config,
            "available_models": self.get_models(),
            "available_tools": self.get_tools()
        }
