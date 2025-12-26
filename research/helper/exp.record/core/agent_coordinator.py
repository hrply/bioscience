"""
MCP协调器 - 简化版模型控制协议实现
支持动态注册Agent和工具，提供统一的调度接口
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Type
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from config.settings import Settings


class AgentStatus(Enum):
    """Agent状态枚举"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class AgentInfo:
    """Agent信息"""
    name: str
    agent_class: Type
    description: str
    capabilities: List[str]
    status: AgentStatus = AgentStatus.IDLE
    last_used: Optional[datetime] = None
    error_count: int = 0
    timeout_count: int = 0


class ToolRegistry:
    """工具注册器"""
    
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._tool_metadata: Dict[str, Dict[str, Any]] = {}
    
    def register(self, name: str, func: Callable, **metadata):
        """注册工具"""
        self._tools[name] = func
        self._tool_metadata[name] = metadata
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """获取工具"""
        return self._tools.get(name)
    
    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """列出所有工具"""
        return self._tool_metadata.copy()


def register_tool(name: str, **metadata):
    """工具注册装饰器"""
    def decorator(func: Callable):
        ToolRegistry().register(name, func, **metadata)
        return func
    return decorator


class AgentCoordinator:
    """MCP协调器 - 管理Agent生命周期和任务调度"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Agent注册表
        self._agents: Dict[str, AgentInfo] = {}
        self._agent_instances: Dict[str, Any] = {}
        
        # 工具注册器
        self.tool_registry = ToolRegistry()
        
        # 任务队列和状态
        self._task_queue = asyncio.Queue()
        self._running_tasks: Dict[str, asyncio.Task] = {}
        
        # 性能监控
        self._performance_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0
        }
    
    def register_agent(self, agent_class: Type, name: str = None, description: str = ""):
        """注册Agent"""
        agent_name = name or agent_class.__name__
        
        if agent_name in self._agents:
            self.logger.warning(f"Agent {agent_name} already registered, overwriting")
        
        agent_info = AgentInfo(
            name=agent_name,
            agent_class=agent_class,
            description=description,
            capabilities=getattr(agent_class, "CAPABILITIES", [])
        )
        
        self._agents[agent_name] = agent_info
        self.logger.info(f"Registered agent: {agent_name}")
        
        return agent_name
    
    async def get_agent_instance(self, agent_name: str) -> Optional[Any]:
        """获取Agent实例（懒加载）"""
        if agent_name not in self._agents:
            self.logger.error(f"Agent {agent_name} not registered")
            return None
        
        if agent_name not in self._agent_instances:
            try:
                agent_info = self._agents[agent_name]
                # 延迟实例化，注入依赖
                instance = agent_info.agent_class(
                    settings=self.settings,
                    tool_registry=self.tool_registry
                )
                self._agent_instances[agent_name] = instance
                self.logger.info(f"Created instance for agent: {agent_name}")
            except Exception as e:
                self.logger.error(f"Failed to create agent instance {agent_name}: {e}")
                return None
        
        return self._agent_instances[agent_name]
    
    async def route_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """路由请求到合适的Agent"""
        start_time = datetime.now()
        
        try:
            # 解析请求
            agent_name = request_data.get("agent")
            if not agent_name:
                # 自动选择Agent
                agent_name = await self._select_best_agent(request_data)
            
            if not agent_name:
                raise ValueError("No suitable agent found for the request")
            
            # 检查Agent状态
            if not await self._check_agent_availability(agent_name):
                raise ValueError(f"Agent {agent_name} is not available")
            
            # 执行请求
            result = await self._execute_agent_request(agent_name, request_data)
            
            # 更新统计
            self._update_performance_stats(start_time, success=True)
            
            return {
                "success": True,
                "agent": agent_name,
                "result": result,
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
            
        except Exception as e:
            self._update_performance_stats(start_time, success=False)
            self.logger.error(f"Request failed: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
    
    async def _select_best_agent(self, request_data: Dict[str, Any]) -> Optional[str]:
        """根据请求内容选择最佳Agent"""
        request_type = request_data.get("type", "")
        
        # 简单的路由逻辑
        for agent_name, agent_info in self._agents.items():
            if request_type.lower() in [cap.lower() for cap in agent_info.capabilities]:
                return agent_name
        
        # 如果没有精确匹配，返回第一个可用的Agent
        for agent_name, agent_info in self._agents.items():
            if await self._check_agent_availability(agent_name):
                return agent_name
        
        return None
    
    async def _check_agent_availability(self, agent_name: str) -> bool:
        """检查Agent是否可用"""
        if agent_name not in self._agents:
            return False
        
        agent_info = self._agents[agent_name]
        
        # 检查错误次数
        if agent_info.error_count > 3:
            return False
        
        # 检查超时次数
        if agent_info.timeout_count > 2:
            return False
        
        return True
    
    async def _execute_agent_request(self, agent_name: str, request_data: Dict[str, Any]) -> Any:
        """执行Agent请求"""
        agent_info = self._agents[agent_name]
        agent_info.status = AgentStatus.BUSY
        agent_info.last_used = datetime.now()
        
        try:
            # 获取Agent实例
            instance = await self.get_agent_instance(agent_name)
            if not instance:
                raise Exception(f"Failed to get agent instance: {agent_name}")
            
            # 执行请求（带超时）
            timeout = self.settings.agent_timeout
            result = await asyncio.wait_for(
                instance.process(request_data),
                timeout=timeout
            )
            
            agent_info.status = AgentStatus.IDLE
            return result
            
        except asyncio.TimeoutError:
            agent_info.status = AgentStatus.TIMEOUT
            agent_info.timeout_count += 1
            raise Exception(f"Agent {agent_name} timed out after {timeout} seconds")
            
        except Exception as e:
            agent_info.status = AgentStatus.ERROR
            agent_info.error_count += 1
            raise e
    
    def _update_performance_stats(self, start_time: datetime, success: bool):
        """更新性能统计"""
        execution_time = (datetime.now() - start_time).total_seconds()
        
        self._performance_stats["total_requests"] += 1
        
        if success:
            self._performance_stats["successful_requests"] += 1
        else:
            self._performance_stats["failed_requests"] += 1
        
        # 更新平均响应时间
        total = self._performance_stats["total_requests"]
        current_avg = self._performance_stats["average_response_time"]
        self._performance_stats["average_response_time"] = (
            (current_avg * (total - 1) + execution_time) / total
        )
    
    def get_agent_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有Agent状态"""
        status = {}
        for name, info in self._agents.items():
            status[name] = {
                "status": info.status.value,
                "description": info.description,
                "capabilities": info.capabilities,
                "last_used": info.last_used.isoformat() if info.last_used else None,
                "error_count": info.error_count,
                "timeout_count": info.timeout_count
            }
        return status
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return self._performance_stats.copy()
    
    async def cleanup(self):
        """清理资源"""
        # 取消所有运行中的任务
        for task_id, task in self._running_tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self._running_tasks.clear()
        self.logger.info("Agent coordinator cleaned up")
    
    # EXTENSION_POINT: 未来可扩展更复杂的路由策略
    async def _advanced_routing(self, request_data: Dict[str, Any]) -> Optional[str]:
        """高级路由策略（未来扩展）"""
        # 可以基于机器学习模型、历史性能等选择最佳Agent
        pass