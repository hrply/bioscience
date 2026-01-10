"""
统一CLI管理器
管理所有CLI工具的集成
"""

import logging
from typing import Dict, List, Optional, Any, Type
from .base import BaseCLI
from .claude_cli import ClaudeCLI
from .codex_cli import CodexCLI
from .gemini_cli import GeminiCLI
from .opencode_cli import OpenCodeCLI
from .iflow_cli import IFlowCLI

logger = logging.getLogger(__name__)


class CLIManager:
    """
    CLI工具统一管理器

    负责统一管理各种CLI工具的初始化、配置和调用。
    提供一致的接口来访问不同提供商的CLI工具。

    支持的CLI工具:
    - claude: Anthropic Claude CLI工具
    - codex: OpenAI Codex CLI工具
    - gemini: Google Gemini CLI工具
    - opencode: 开源代码生成CLI工具
    - iflow: iFlow CLI工具

    主要功能:
    - 工具注册和发现
    - 统一命令执行接口
    - 批量操作支持
    - 安装状态检查
    - 配置管理

    使用示例:
        cli_manager = CLIManager()
        status = cli_manager.check_installation()
        result = cli_manager.claude("chat", prompt="你好")

        # 通过Agent使用
        agent = ResearchAgent(model_provider="openai", model_name="gpt-4")
        result = agent.cli_claude("complete", prompt="生成代码")
    """

    # CLI工具映射
    CLI_TOOLS = {
        "claude": ClaudeCLI,
        "codex": CodexCLI,
        "gemini": GeminiCLI,
        "opencode": OpenCodeCLI,
        "iflow": IFlowCLI
    }

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化CLI管理器

        Args:
            config: 全局配置字典
        """
        self.config = config or {}
        self._tools: Dict[str, BaseCLI] = {}

    def register_tool(self, name: str, tool_class: Type[BaseCLI]) -> None:
        """
        注册新的CLI工具

        Args:
            name: 工具名称
            tool_class: 工具类
        """
        self.CLI_TOOLS[name] = tool_class
        logger.info(f"已注册CLI工具: {name}")

    def get_tool(self, name: str) -> Optional[BaseCLI]:
        """
        获取CLI工具实例

        Args:
            name: 工具名称

        Returns:
            CLI工具实例，如果不存在则返回None
        """
        if name not in self._tools:
            # 创建工具实例
            tool_class = self.CLI_TOOLS.get(name)
            if tool_class:
                tool_config = self.config.get(name, {})
                self._tools[name] = tool_class(tool_config)
            else:
                logger.error(f"未知的CLI工具: {name}")
                return None

        return self._tools.get(name)

    def execute(
        self,
        tool_name: str,
        command: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行CLI命令

        Args:
            tool_name: 工具名称
            command: 命令
            **kwargs: 其他参数

        Returns:
            执行结果
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"CLI工具 {tool_name} 未找到或未安装",
                "tool": tool_name,
                "command": command
            }

        if not tool.is_available():
            return {
                "success": False,
                "error": f"CLI工具 {tool_name} 不可用（未安装）",
                "tool": tool_name,
                "command": command
            }

        try:
            result = tool.execute(command, **kwargs)
            logger.info(f"CLI命令执行成功: {tool_name} {command}")
            return result
        except Exception as e:
            logger.error(f"CLI命令执行失败: {tool_name} {command} - {e}")
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name,
                "command": command
            }

    def list_tools(self) -> List[str]:
        """列出所有已注册的CLI工具"""
        return list(self.CLI_TOOLS.keys())

    def list_available_tools(self) -> List[str]:
        """
        列出所有可用的CLI工具（已安装且可用）

        Returns:
            可用工具列表
        """
        available = []
        for name in self.CLI_TOOLS.keys():
            tool = self.get_tool(name)
            if tool and tool.is_available():
                available.append(name)
        return available

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有CLI工具的状态

        Returns:
            状态字典
        """
        status = {}
        for name in self.CLI_TOOLS.keys():
            tool = self.get_tool(name)
            if tool:
                status[name] = tool.get_status()
            else:
                status[name] = {
                    "name": name,
                    "installed": False,
                    "error": "工具未注册或创建失败"
                }
        return status

    def check_installation(self) -> Dict[str, bool]:
        """
        检查所有CLI工具的安装状态

        Returns:
            安装状态字典
        """
        installation_status = {}
        for name in self.CLI_TOOLS.keys():
            tool = self.get_tool(name)
            if tool:
                installation_status[name] = tool.is_available()
            else:
                installation_status[name] = False
        return installation_status

    def batch_execute(
        self,
        commands: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        批量执行多个CLI命令

        Args:
            commands: 命令列表，每个元素包含tool_name和command

        Returns:
            执行结果列表
        """
        results = []
        for cmd in commands:
            result = self.execute(
                tool_name=cmd["tool"],
                command=cmd["command"],
                **cmd.get("kwargs", {})
            )
            results.append(result)
        return results

    # 便捷方法

    def claude(self, command: str, **kwargs) -> Dict[str, Any]:
        """使用Claude CLI"""
        return self.execute("claude", command, **kwargs)

    def codex(self, command: str, **kwargs) -> Dict[str, Any]:
        """使用Codex CLI"""
        return self.execute("codex", command, **kwargs)

    def gemini(self, command: str, **kwargs) -> Dict[str, Any]:
        """使用Gemini CLI"""
        return self.execute("gemini", command, **kwargs)

    def opencode(self, command: str, **kwargs) -> Dict[str, Any]:
        """使用OpenCode CLI"""
        return self.execute("opencode", command, **kwargs)

    def iflow(self, command: str, **kwargs) -> Dict[str, Any]:
        """使用iFlow CLI"""
        return self.execute("iflow", command, **kwargs)

    def get_summary(self) -> Dict[str, Any]:
        """
        获取CLI管理器摘要

        Returns:
            摘要信息
        """
        return {
            "total_tools": len(self.CLI_TOOLS),
            "registered_tools": self.list_tools(),
            "available_tools": self.list_available_tools(),
            "installation_status": self.check_installation()
        }
