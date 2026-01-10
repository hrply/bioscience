"""
CLI工具集成模块
统一管理各种CLI工具：Claude、Codex、Gemini、OpenCode、iFlow等
"""

from .manager import CLIManager
from .claude_cli import ClaudeCLI
from .codex_cli import CodexCLI
from .gemini_cli import GeminiCLI
from .opencode_cli import OpenCodeCLI
from .iflow_cli import IFlowCLI

__all__ = [
    "CLIManager",
    "ClaudeCLI",
    "CodexCLI",
    "GeminiCLI",
    "OpenCodeCLI",
    "IFlowCLI"
]
