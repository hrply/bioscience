"""
CLI工具基础抽象类
定义所有CLI工具的通用接口
"""

import subprocess
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from pathlib import Path


class BaseCLI(ABC):
    """
    CLI工具基类

    定义了所有CLI工具的通用接口和抽象方法。
    所有CLI工具类都应继承此类并实现其抽象方法。

    提供以下通用功能:
    - 安装状态检查
    - 命令执行
    - 版本获取
    - 帮助信息
    - 配置管理

    子类需要实现:
    - _check_installation: 检查CLI是否已安装
    - execute: 执行CLI命令
    """

    def __init__(self, name: str, config: Optional[Dict] = None):
        """
        初始化CLI工具

        Args:
            name: CLI工具名称
            config: 配置字典
        """
        self.name = name
        self.config = config or {}
        self.installed = self._check_installation()

    @abstractmethod
    def _check_installation(self) -> bool:
        """
        检查CLI工具是否已安装

        Returns:
            是否已安装
        """
        pass

    @abstractmethod
    def execute(self, command: str, **kwargs) -> Union[str, Dict[str, Any]]:
        """
        执行CLI命令

        Args:
            command: 要执行的命令
            **kwargs: 其他参数

        Returns:
            命令执行结果
        """
        pass

    def is_available(self) -> bool:
        """
        检查CLI工具是否可用

        Returns:
            是否可用
        """
        return self.installed

    def get_version(self) -> Optional[str]:
        """
        获取CLI工具版本

        Returns:
            版本号，如果无法获取则返回None
        """
        if not self.installed:
            return None

        try:
            version = self._run_command("--version")
            return version
        except Exception:
            return None

    def _run_command(self, args: str, **kwargs) -> str:
        """
        运行CLI命令

        Args:
            args: 命令参数
            **kwargs: 其他subprocess参数

        Returns:
            命令输出
        """
        if not self.installed:
            raise RuntimeError(f"{self.name} CLI未安装或不可用")

        cmd = [self.name] + args.split()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                **kwargs
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"{self.name}命令执行失败: {e}\n"
                f"错误输出: {e.stderr}"
            )
        except FileNotFoundError:
            raise RuntimeError(f"{self.name} CLI未找到，请确保已正确安装")

    def get_help(self) -> str:
        """
        获取CLI帮助信息

        Returns:
            帮助文本
        """
        try:
            return self._run_command("--help")
        except Exception as e:
            return f"无法获取{self.name}帮助: {e}"

    def get_config(self) -> Dict[str, Any]:
        """
        获取当前配置

        Returns:
            配置字典
        """
        return self.config

    def update_config(self, config: Dict[str, Any]) -> None:
        """
        更新配置

        Args:
            config: 新的配置字典
        """
        self.config.update(config)
