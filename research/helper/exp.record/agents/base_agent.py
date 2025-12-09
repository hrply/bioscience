"""
基础Agent接口定义
所有Agent必须继承此基类并实现标准接口
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class AgentStatus(Enum):
    """Agent状态枚举"""
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    COMPLETED = "completed"


@dataclass
class AgentRequest:
    """Agent请求数据结构"""
    request_id: str
    type: str
    data: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AgentResponse:
    """Agent响应数据结构"""
    request_id: str
    status: AgentStatus
    data: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseAgent(ABC):
    """基础Agent抽象类"""
    
    # Agent能力标识
    CAPABILITIES: List[str] = []
    
    def __init__(self, settings=None, tool_registry=None):
        self.settings = settings
        self.tool_registry = tool_registry
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Agent状态
        self.status = AgentStatus.IDLE
        self.current_request = None
        self.start_time = None
        
        # 性能统计
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_execution_time": 0.0
        }
    
    @abstractmethod
    async def process(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理请求的核心方法
        子类必须实现此方法
        
        Args:
            request_data: 请求数据字典
            
        Returns:
            处理结果字典
        """
        pass
    
    async def handle_request(self, request: AgentRequest) -> AgentResponse:
        """
        处理Agent请求的标准流程
        
        Args:
            request: Agent请求对象
            
        Returns:
            Agent响应对象
        """
        self.status = AgentStatus.PROCESSING
        self.current_request = request
        self.start_time = datetime.now()
        
        try:
            self.logger.info(f"Processing request {request.request_id} of type {request.type}")
            
            # 调用子类实现的process方法
            result = await self.process(request.data)
            
            # 计算执行时间
            execution_time = (datetime.now() - self.start_time).total_seconds()
            
            # 更新统计
            self._update_stats(execution_time, success=True)
            
            # 创建响应
            response = AgentResponse(
                request_id=request.request_id,
                status=AgentStatus.COMPLETED,
                data=result,
                execution_time=execution_time,
                metadata={
                    "agent_type": self.__class__.__name__,
                    "capabilities": self.CAPABILITIES,
                    "processed_at": datetime.now().isoformat()
                }
            )
            
            self.status = AgentStatus.IDLE
            self.current_request = None
            
            return response
            
        except Exception as e:
            execution_time = (datetime.now() - self.start_time).total_seconds()
            self._update_stats(execution_time, success=False)
            
            self.logger.error(f"Error processing request {request.request_id}: {e}")
            
            response = AgentResponse(
                request_id=request.request_id,
                status=AgentStatus.ERROR,
                data=None,
                error=str(e),
                execution_time=execution_time
            )
            
            self.status = AgentStatus.ERROR
            self.current_request = None
            
            return response
    
    def _update_stats(self, execution_time: float, success: bool):
        """更新性能统计"""
        self.stats["total_requests"] += 1
        
        if success:
            self.stats["successful_requests"] += 1
        else:
            self.stats["failed_requests"] += 1
        
        # 更新平均执行时间
        total = self.stats["total_requests"]
        current_avg = self.stats["average_execution_time"]
        self.stats["average_execution_time"] = (
            (current_avg * (total - 1) + execution_time) / total
        )
    
    def get_status(self) -> Dict[str, Any]:
        """获取Agent状态"""
        return {
            "status": self.status.value,
            "current_request": self.current_request.request_id if self.current_request else None,
            "capabilities": self.CAPABILITIES,
            "stats": self.stats.copy()
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_execution_time": 0.0
        }
    
    async def cleanup(self):
        """清理资源"""
        self.logger.info(f"Cleaning up agent {self.__class__.__name__}")
        self.status = AgentStatus.IDLE
        self.current_request = None
    
    # 工具方法
    def use_tool(self, tool_name: str, **kwargs) -> Any:
        """使用注册的工具"""
        if not self.tool_registry:
            raise ValueError("No tool registry available")
        
        return self.tool_registry.execute_tool(tool_name, **kwargs)
    
    def log_info(self, message: str):
        """记录信息日志"""
        self.logger.info(message)
    
    def log_error(self, message: str):
        """记录错误日志"""
        self.logger.error(message)
    
    def log_warning(self, message: str):
        """记录警告日志"""
        self.logger.warning(message)
    
    # EXTENSION_POINT: 子类可扩展的钩子方法
    async def before_process(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理前的钩子方法"""
        return request_data
    
    async def after_process(self, request_data: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """处理后的钩子方法"""
        return result
    
    async def on_error(self, request_data: Dict[str, Any], error: Exception) -> Dict[str, Any]:
        """错误处理钩子方法"""
        return {"error": str(error)}


class AgentCapabilityError(Exception):
    """Agent能力不足异常"""
    pass


class AgentTimeoutError(Exception):
    """Agent超时异常"""
    pass