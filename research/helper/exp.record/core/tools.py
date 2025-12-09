工具注册和管理模块
提供统一的工具接口和注册机制
"""

import logging
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
from functools import wraps
import inspect


@dataclass
class ToolInfo:
    """工具信息"""
    name: str
    description: str
    function: Callable
    parameters: Dict[str, Any]
    category: str = "general"
    enabled: bool = True


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, ToolInfo] = {}
        self._categories: Dict[str, List[str]] = {}
        self.logger = logging.getLogger(__name__)
    
    def register(self, name: str, func: Callable, description: str = "", parameters: Dict[str, Any] = None, category: str = "general"):
        """注册工具"""
        if name in self._tools:
            self.logger.warning(f"Tool {name} already registered, overwriting")
        
        # 自动提取参数信息
        if parameters is None:
            parameters = self._extract_parameters(func)
        
        tool_info = ToolInfo(
            name=name,
            description=description or func.__doc__ or "",
            function=func,
            parameters=parameters,
            category=category
        )
        
        self._tools[name] = tool_info
        
        # 更新分类
        if category not in self._categories:
            self._categories[category] = []
        if name not in self._categories[category]:
            self._categories[category].append(name)
        
        self.logger.info(f"Registered tool: {name} in category: {category}")
    
    def get_tool(self, name: str) -> Optional[ToolInfo]:
        """获取工具"""
        return self._tools.get(name)
    
    def list_tools(self, category: str = None) -> Dict[str, ToolInfo]:
        """列出工具"""
        if category:
            return {name: info for name, info in self._tools.items() if info.category == category}
        return self._tools.copy()
    
    def get_categories(self) -> Dict[str, List[str]]:
        """获取工具分类"""
        return self._categories.copy()
    
    def execute_tool(self, name: str, **kwargs) -> Any:
        """执行工具"""
        tool_info = self.get_tool(name)
        if not tool_info:
            raise ValueError(f"Tool {name} not found")
        
        if not tool_info.enabled:
            raise ValueError(f"Tool {name} is disabled")
        
        try:
            return tool_info.function(**kwargs)
        except Exception as e:
            self.logger.error(f"Error executing tool {name}: {e}")
            raise
    
    def enable_tool(self, name: str):
        """启用工具"""
        if name in self._tools:
            self._tools[name].enabled = True
    
    def disable_tool(self, name: str):
        """禁用工具"""
        if name in self._tools:
            self._tools[name].enabled = False
    
    def _extract_parameters(self, func: Callable) -> Dict[str, Any]:
        """提取函数参数信息"""
        sig = inspect.signature(func)
        parameters = {}
        
        for param_name, param in sig.parameters.items():
            param_info = {
                "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "any",
                "required": param.default == inspect.Parameter.empty,
                "default": param.default if param.default != inspect.Parameter.empty else None,
                "description": ""
            }
            parameters[param_name] = param_info
        
        return parameters


def register_tool(name: str, description: str = "", category: str = "general"):
    """工具注册装饰器"""
    def decorator(func: Callable):
        # 获取全局工具注册表
        from core.agent_coordinator import ToolRegistry as GlobalToolRegistry
        registry = GlobalToolRegistry()
        registry.register(name, func, description, category=category)
        return func
    return decorator


# 常用工具函数
@register_tool("text_length", description="计算文本长度", category="text")
def calculate_text_length(text: str) -> int:
    """计算文本长度"""
    return len(text)


@register_tool("word_count", description="计算单词数量", category="text")
def count_words(text: str) -> int:
    """计算单词数量"""
    return len(text.split())


@register_tool("extract_numbers", description="提取文本中的数字", category="text")
def extract_numbers(text: str) -> List[float]:
    """提取文本中的数字"""
    import re
    numbers = re.findall(r'\d+\.?\d*', text)
    return [float(num) for num in numbers]


@register_tool("current_time", description="获取当前时间", category="utility")
def get_current_time() -> str:
    """获取当前时间"""
    from datetime import datetime
    return datetime.now().isoformat()


@register_tool("format_datetime", description="格式化日期时间", category="utility")
def format_datetime(dt_string: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化日期时间"""
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
        return dt.strftime(format_str)
    except Exception:
        return dt_string


@register_tool("safe_divide", description="安全除法运算", category="math")
def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """安全除法运算，避免除零错误"""
    if b == 0:
        return default
    return a / b


@register_tool("percentage", description="计算百分比", category="math")
def calculate_percentage(part: float, total: float, decimals: int = 2) -> float:
    """计算百分比"""
    if total == 0:
        return 0.0
    return round((part / total) * 100, decimals)


# EXTENSION_POINT: 未来可扩展更多工具
@register_tool("search_template", description="搜索模板", category="template")
def search_template(query: str, template_store=None) -> List[Dict[str, Any]]:
    """搜索实验模板"""
    if template_store is None:
        from storage.template_manager import TemplateManager
        template_store = TemplateManager()
    
    return template_store.search_templates(query)


@register_tool("validate_format", description="验证文档格式", category="validation")
def validate_document_format(content: str, format_type: str = "markdown") -> Dict[str, Any]:
    """验证文档格式"""
    result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    if format_type == "markdown":
        # 简单的Markdown格式验证
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if line.startswith('#') and not re.match(r'^#{1,6}\s+.+$', line):
                result["warnings"].append(f"行 {i}: 标题格式可能不正确")
    
    return result