"""
向量数据库管理 - 使用ChromaDB实现语义搜索
"""

import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


class VectorDB:
    """向量数据库管理器"""
    
    def __init__(self, db_path: str = None, settings=None):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        if not CHROMADB_AVAILABLE:
            self.logger.warning("ChromaDB not available, vector search disabled")
            self.client = None
            return
        
        # 设置数据库路径
        if db_path is None:
            if settings:
                db_path = settings.vector_db_path
            else:
                db_path = Path.home() / ".lab_notebook_agent" / "vector_db"
        
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化ChromaDB客户端
        try:
            self.client = chromadb.PersistentClient(
                path=str(self.db_path),
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            self.logger.info(f"VectorDB initialized at {self.db_path}")
        except Exception as e:
            self.logger.error(f"Failed to initialize ChromaDB: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """检查向量数据库是否可用"""
        return self.client is not None
    
    def create_collection(self, name: str, metadata: Dict[str, Any] = None) -> bool:
        """创建集合"""
        if not self.is_available():
            return False
        
        try:
            # 检查集合是否已存在
            existing_collections = self.client.list_collections()
            if any(col.name == name for col in existing_collections):
                self.logger.info(f"Collection {name} already exists")
                return True
            
            # 创建新集合
            collection = self.client.create_collection(
                name=name,
                metadata=metadata or {}
            )
            self.logger.info(f"Created collection: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating collection {name}: {e}")
            return False
    
    def add_documents(self, collection_name: str, documents: List[str], 
                     metadatas: List[Dict[str, Any]] = None, 
                     ids: List[str] = None) -> bool:
        """添加文档到集合"""
        if not self.is_available():
            return False
        
        try:
            # 获取或创建集合
            collection = self._get_collection(collection_name)
            if not collection:
                return False
            
            # 生成ID（如果未提供）
            if ids is None:
                ids = [f"{collection_name}_{datetime.now().timestamp()}_{i}" 
                       for i in range(len(documents))]
            
            # 添加文档
            collection.add(
                documents=documents,
                metadatas=metadatas or [{}] * len(documents),
                ids=ids
            )
            
            self.logger.info(f"Added {len(documents)} documents to {collection_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding documents to {collection_name}: {e}")
            return False
    
    def search(self, collection_name: str, query: str, 
               n_results: int = 5, where: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """搜索相似文档"""
        if not self.is_available():
            return []
        
        try:
            collection = self._get_collection(collection_name)
            if not collection:
                return []
            
            # 执行搜索
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where
            )
            
            # 格式化结果
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        "document": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {},
                        "id": results['ids'][0][i] if results['ids'] and results['ids'][0] else "",
                        "distance": results['distances'][0][i] if results['distances'] and results['distances'][0] else 0.0
                    })
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error searching in {collection_name}: {e}")
            return []
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """获取集合统计信息"""
        if not self.is_available():
            return {}
        
        try:
            collection = self._get_collection(collection_name)
            if not collection:
                return {}
            
            count = collection.count()
            
            return {
                "name": collection_name,
                "document_count": count,
                "available": True
            }
            
        except Exception as e:
            self.logger.error(f"Error getting stats for {collection_name}: {e}")
            return {"name": collection_name, "available": False}
    
    def list_collections(self) -> List[str]:
        """列出所有集合"""
        if not self.is_available():
            return []
        
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            self.logger.error(f"Error listing collections: {e}")
            return []
    
    def delete_collection(self, collection_name: str) -> bool:
        """删除集合"""
        if not self.is_available():
            return False
        
        try:
            self.client.delete_collection(name=collection_name)
            self.logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting collection {collection_name}: {e}")
            return False
    
    def _get_collection(self, name: str):
        """获取集合"""
        if not self.is_available():
            return None
        
        try:
            return self.client.get_collection(name)
        except Exception:
            # 集合不存在，尝试创建
            if self.create_collection(name):
                return self.client.get_collection(name)
            return None
    
    def reset_database(self) -> bool:
        """重置数据库"""
        if not self.is_available():
            return False
        
        try:
            self.client.reset()
            self.logger.info("Vector database reset successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error resetting database: {e}")
            return False


# 全局向量数据库实例
_global_vector_db = None


def get_vector_db(db_path: str = None, settings=None) -> VectorDB:
    """获取全局向量数据库实例"""
    global _global_vector_db
    if _global_vector_db is None:
        _global_vector_db = VectorDB(db_path, settings)
    return _global_vector_db