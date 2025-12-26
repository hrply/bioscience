"""
内存管理模块 - 自动修剪过期上下文，优化内存使用
"""

import logging
import pickle
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict
import threading


@dataclass
class MemoryItem:
    """内存项"""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    size_bytes: int = 0
    tags: List[str] = field(default_factory=list)
    
    def touch(self):
        """更新访问时间和计数"""
        self.last_accessed = datetime.now()
        self.access_count += 1


class LRUMemory:
    """LRU内存管理器"""
    
    def __init__(self, max_size_mb: int = 100, ttl_days: int = 30):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.ttl_seconds = ttl_days * 24 * 3600
        
        self._memory: OrderedDict[str, MemoryItem] = OrderedDict()
        self._current_size_bytes = 0
        self._lock = threading.RLock()
        
        self.logger = logging.getLogger(__name__)
        
        # 统计信息
        self._stats = {
            "total_items": 0,
            "total_accesses": 0,
            "evictions": 0,
            "hits": 0,
            "misses": 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """获取内存项"""
        with self._lock:
            if key not in self._memory:
                self._stats["misses"] += 1
                return None
            
            item = self._memory[key]
            
            # 检查是否过期
            if self._is_expired(item):
                del self._memory[key]
                self._current_size_bytes -= item.size_bytes
                self._stats["misses"] += 1
                return None
            
            # 更新访问信息并移到末尾
            item.touch()
            self._memory.move_to_end(key)
            self._stats["hits"] += 1
            self._stats["total_accesses"] += 1
            
            return item.value
    
    def put(self, key: str, value: Any, tags: List[str] = None) -> bool:
        """存储内存项"""
        with self._lock:
            # 计算对象大小
            try:
                size_bytes = len(pickle.dumps(value))
            except Exception:
                size_bytes = 1024  # 默认大小
            
            # 检查是否超过单个项大小限制
            if size_bytes > self.max_size_bytes // 2:
                self.logger.warning(f"Item {key} too large: {size_bytes} bytes")
                return False
            
            # 如果键已存在，更新大小
            if key in self._memory:
                old_item = self._memory[key]
                self._current_size_bytes -= old_item.size_bytes
            
            # 创建新项
            item = MemoryItem(
                key=key,
                value=value,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                size_bytes=size_bytes,
                tags=tags or []
            )
            
            # 添加到内存
            self._memory[key] = item
            self._current_size_bytes += size_bytes
            self._memory.move_to_end(key)
            
            # 清理过期项和空间管理
            self._cleanup_expired()
            self._ensure_size_limit()
            
            self._stats["total_items"] = len(self._memory)
            
            return True
    
    def remove(self, key: str) -> bool:
        """删除内存项"""
        with self._lock:
            if key not in self._memory:
                return False
            
            item = self._memory.pop(key)
            self._current_size_bytes -= item.size_bytes
            self._stats["total_items"] = len(self._memory)
            
            return True
    
    def clear(self, tags: List[str] = None):
        """清空内存或按标签清空"""
        with self._lock:
            if tags is None:
                # 清空所有
                self._memory.clear()
                self._current_size_bytes = 0
            else:
                # 按标签清空
                keys_to_remove = []
                for key, item in self._memory.items():
                    if any(tag in item.tags for tag in tags):
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    item = self._memory.pop(key)
                    self._current_size_bytes -= item.size_bytes
            
            self._stats["total_items"] = len(self._memory)
    
    def _is_expired(self, item: MemoryItem) -> bool:
        """检查项是否过期"""
        return (datetime.now() - item.created_at).total_seconds() > self.ttl_seconds
    
    def _cleanup_expired(self):
        """清理过期项"""
        expired_keys = []
        for key, item in self._memory.items():
            if self._is_expired(item):
                expired_keys.append(key)
        
        for key in expired_keys:
            item = self._memory.pop(key)
            self._current_size_bytes -= item.size_bytes
        
        if expired_keys:
            self.logger.debug(f"Cleaned up {len(expired_keys)} expired items")
    
    def _ensure_size_limit(self):
        """确保大小不超过限制"""
        while self._current_size_bytes > self.max_size_bytes and self._memory:
            # 移除最旧的项（LRU）
            key, item = self._memory.popitem(last=False)
            self._current_size_bytes -= item.size_bytes
            self._stats["evictions"] += 1
            
            self.logger.debug(f"Evicted item {key} due to size limit")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            stats = self._stats.copy()
            stats.update({
                "current_size_bytes": self._current_size_bytes,
                "current_size_mb": self._current_size_bytes / (1024 * 1024),
                "max_size_bytes": self.max_size_bytes,
                "max_size_mb": self.max_size_bytes / (1024 * 1024),
                "utilization_percent": (self._current_size_bytes / self.max_size_bytes) * 100,
                "hit_rate": (self._stats["hits"] / max(1, self._stats["total_accesses"])) * 100
            })
            return stats
    
    def get_items_by_tag(self, tag: str) -> List[Tuple[str, Any]]:
        """按标签获取项"""
        with self._lock:
            items = []
            for key, item in self._memory.items():
                if tag in item.tags:
                    items.append((key, item.value))
            return items
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用详情"""
        with self._lock:
            usage = {
                "total_items": len(self._memory),
                "total_size_bytes": self._current_size_bytes,
                "oldest_item": None,
                "newest_item": None,
                "most_accessed": None
            }
            
            if self._memory:
                # 最旧项
                oldest_key = next(iter(self._memory))
                oldest_item = self._memory[oldest_key]
                usage["oldest_item"] = {
                    "key": oldest_key,
                    "created_at": oldest_item.created_at.isoformat(),
                    "access_count": oldest_item.access_count
                }
                
                # 最新项
                newest_key = next(reversed(self._memory))
                newest_item = self._memory[newest_key]
                usage["newest_item"] = {
                    "key": newest_key,
                    "created_at": newest_item.created_at.isoformat(),
                    "access_count": newest_item.access_count
                }
                
                # 最常访问项
                most_accessed_item = max(self._memory.values(), key=lambda x: x.access_count)
                usage["most_accessed"] = {
                    "key": most_accessed_item.key,
                    "access_count": most_accessed_item.access_count,
                    "created_at": most_accessed_item.created_at.isoformat()
                }
            
            return usage


class ContextManager:
    """上下文管理器 - 管理对话上下文"""
    
    def __init__(self, max_context_length: int = 8000, max_history: int = 10):
        self.max_context_length = max_context_length
        self.max_history = max_history
        
        self._contexts: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = threading.RLock()
        
        self.logger = logging.getLogger(__name__)
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Dict[str, Any] = None):
        """添加消息到上下文"""
        with self._lock:
            if session_id not in self._contexts:
                self._contexts[session_id] = []
            
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            self._contexts[session_id].append(message)
            
            # 修剪上下文
            self._trim_context(session_id)
    
    def get_context(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话上下文"""
        with self._lock:
            return self._contexts.get(session_id, []).copy()
    
    def clear_context(self, session_id: str):
        """清空会话上下文"""
        with self._lock:
            if session_id in self._contexts:
                del self._contexts[session_id]
    
    def _trim_context(self, session_id: str):
        """修剪上下文以符合长度限制"""
        context = self._contexts[session_id]
        
        # 按历史数量限制
        while len(context) > self.max_history:
            removed = context.pop(0)
            self.logger.debug(f"Removed old message from session {session_id}")
        
        # 按字符长度限制
        total_length = sum(len(msg.get("content", "")) for msg in context)
        
        while total_length > self.max_context_length and len(context) > 1:
            # 保留最新的消息，移除最旧的
            removed = context.pop(0)
            total_length -= len(removed.get("content", ""))
            self.logger.debug(f"Trimmed message from session {session_id} due to length limit")
    
    def get_context_stats(self) -> Dict[str, Any]:
        """获取上下文统计"""
        with self._lock:
            stats = {
                "total_sessions": len(self._contexts),
                "total_messages": sum(len(ctx) for ctx in self._contexts.values()),
                "average_messages_per_session": 0,
                "max_context_length": self.max_context_length,
                "max_history": self.max_history
            }
            
            if self._contexts:
                stats["average_messages_per_session"] = stats["total_messages"] / len(self._contexts)
            
            return stats


# 全局内存管理器实例
_global_memory = None
_global_context_manager = None


def get_memory_manager(max_size_mb: int = 100, ttl_days: int = 30) -> LRUMemory:
    """获取全局内存管理器实例"""
    global _global_memory
    if _global_memory is None:
        _global_memory = LRUMemory(max_size_mb, ttl_days)
    return _global_memory


def get_context_manager(max_context_length: int = 8000, max_history: int = 10) -> ContextManager:
    """获取全局上下文管理器实例"""
    global _global_context_manager
    if _global_context_manager is None:
        _global_context_manager = ContextManager(max_context_length, max_history)
    return _global_context_manager