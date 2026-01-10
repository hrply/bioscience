"""
向量数据库管理模块
固化ChromaDB数据目录路径
"""

import os
import chromadb
from pathlib import Path


# 固化ChromaDB数据目录
CHROMA_DB_PATH = "/app/chroma"


class ChromaDBManager:
    """ChromaDB管理器"""

    def __init__(self):
        """初始化ChromaDB管理器"""
        self.client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self.collection_name = "ai_researcher"

    def get_or_create_collection(self, name: str = None):
        """
        获取或创建集合

        Args:
            name: 集合名称，默认为ai_researcher

        Returns:
            ChromaDB集合对象
        """
        collection_name = name or self.collection_name
        return self.client.get_or_create_collection(name=collection_name)

    def add_documents(
        self,
        documents,
        metadatas=None,
        ids=None,
        collection_name=None
    ):
        """
        添加文档到向量数据库

        Args:
            documents: 文档内容列表
            metadatas: 元数据列表
            ids: 文档ID列表
            collection_name: 集合名称
        """
        collection = self.get_or_create_collection(collection_name)
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def query(
        self,
        query_texts,
        n_results=5,
        collection_name=None
    ):
        """
        查询向量数据库

        Args:
            query_texts: 查询文本列表
            n_results: 返回结果数量
            collection_name: 集合名称

        Returns:
            查询结果
        """
        collection = self.get_or_create_collection(collection_name)
        return collection.query(
            query_texts=query_texts,
            n_results=n_results
        )


def get_chroma_client():
    """获取ChromaDB客户端实例"""
    return ChromaDBManager()
