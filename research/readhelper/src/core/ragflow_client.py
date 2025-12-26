"""
RAGFlow API客户端模块
"""

import json
import requests
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from urllib.parse import urljoin
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RAGFlowConfig:
    """RAGFlow配置"""
    base_url: str = "http://localhost:9380"
    api_key: str = ""
    timeout: int = 30
    max_retries: int = 3


@dataclass
class Document:
    """文档对象"""
    id: str
    name: str
    content: str
    metadata: Dict[str, Any] = None
    chunk_size: int = 512
    chunk_overlap: int = 50
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Dataset:
    """数据集对象"""
    id: str
    name: str
    description: str = ""
    document_count: int = 0
    created_at: str = ""
    updated_at: str = ""


@dataclass
class SearchResult:
    """搜索结果"""
    content: str
    document_id: str
    document_name: str
    score: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class RAGFlowClient:
    """RAGFlow API客户端"""
    
    def __init__(self, config: RAGFlowConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        })
        
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                      params: Optional[Dict] = None) -> Dict[str, Any]:
        """发送HTTP请求"""
        url = urljoin(self.config.base_url, endpoint)
        
        for attempt in range(self.config.max_retries):
            try:
                if method.upper() == "GET":
                    response = self.session.get(url, params=params, timeout=self.config.timeout)
                elif method.upper() == "POST":
                    response = self.session.post(url, json=data, params=params, timeout=self.config.timeout)
                elif method.upper() == "PUT":
                    response = self.session.put(url, json=data, params=params, timeout=self.config.timeout)
                elif method.upper() == "DELETE":
                    response = self.session.delete(url, params=params, timeout=self.config.timeout)
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{self.config.max_retries}): {e}")
                if attempt == self.config.max_retries - 1:
                    raise
                continue
        
        raise Exception("请求失败，已达到最大重试次数")
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            response = self._make_request("GET", "/api/v1/health")
            return response
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    def list_datasets(self) -> List[Dataset]:
        """列出所有数据集"""
        try:
            response = self._make_request("GET", "/api/v1/datasets")
            datasets = []
            for item in response.get("data", []):
                dataset = Dataset(
                    id=item.get("id", ""),
                    name=item.get("name", ""),
                    description=item.get("description", ""),
                    document_count=item.get("document_count", 0),
                    created_at=item.get("created_at", ""),
                    updated_at=item.get("updated_at", "")
                )
                datasets.append(dataset)
            return datasets
        except Exception as e:
            logger.error(f"获取数据集列表失败: {e}")
            return []
    
    def get_dataset(self, dataset_id: str) -> Optional[Dataset]:
        """获取特定数据集"""
        try:
            response = self._make_request("GET", f"/api/v1/datasets/{dataset_id}")
            item = response.get("data", {})
            return Dataset(
                id=item.get("id", ""),
                name=item.get("name", ""),
                description=item.get("description", ""),
                document_count=item.get("document_count", 0),
                created_at=item.get("created_at", ""),
                updated_at=item.get("updated_at", "")
            )
        except Exception as e:
            logger.error(f"获取数据集失败: {e}")
            return None
    
    def create_dataset(self, name: str, description: str = "") -> Optional[Dataset]:
        """创建数据集"""
        try:
            data = {
                "name": name,
                "description": description
            }
            response = self._make_request("POST", "/api/v1/datasets", data=data)
            item = response.get("data", {})
            return Dataset(
                id=item.get("id", ""),
                name=item.get("name", ""),
                description=item.get("description", ""),
                document_count=item.get("document_count", 0),
                created_at=item.get("created_at", ""),
                updated_at=item.get("updated_at", "")
            )
        except Exception as e:
            logger.error(f"创建数据集失败: {e}")
            return None
    
    def delete_dataset(self, dataset_id: str) -> bool:
        """删除数据集"""
        try:
            self._make_request("DELETE", f"/api/v1/datasets/{dataset_id}")
            return True
        except Exception as e:
            logger.error(f"删除数据集失败: {e}")
            return False
    
    def list_documents(self, dataset_id: str) -> List[Document]:
        """列出数据集中的所有文档"""
        try:
            response = self._make_request("GET", f"/api/v1/datasets/{dataset_id}/documents")
            documents = []
            for item in response.get("data", []):
                document = Document(
                    id=item.get("id", ""),
                    name=item.get("name", ""),
                    content=item.get("content", ""),
                    metadata=item.get("metadata", {})
                )
                documents.append(document)
            return documents
        except Exception as e:
            logger.error(f"获取文档列表失败: {e}")
            return []
    
    def get_document(self, dataset_id: str, document_id: str) -> Optional[Document]:
        """获取特定文档"""
        try:
            response = self._make_request("GET", f"/api/v1/datasets/{dataset_id}/documents/{document_id}")
            item = response.get("data", {})
            return Document(
                id=item.get("id", ""),
                name=item.get("name", ""),
                content=item.get("content", ""),
                metadata=item.get("metadata", {})
            )
        except Exception as e:
            logger.error(f"获取文档失败: {e}")
            return None
    
    def upload_document(self, dataset_id: str, document: Document) -> Optional[str]:
        """上传文档到数据集"""
        try:
            data = {
                "name": document.name,
                "content": document.content,
                "metadata": document.metadata,
                "chunk_size": document.chunk_size,
                "chunk_overlap": document.chunk_overlap
            }
            response = self._make_request("POST", f"/api/v1/datasets/{dataset_id}/documents", data=data)
            return response.get("data", {}).get("id")
        except Exception as e:
            logger.error(f"上传文档失败: {e}")
            return None
    
    def delete_document(self, dataset_id: str, document_id: str) -> bool:
        """删除文档"""
        try:
            self._make_request("DELETE", f"/api/v1/datasets/{dataset_id}/documents/{document_id}")
            return True
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    def search(self, dataset_id: str, query: str, top_k: int = 5, 
              similarity_threshold: float = 0.7) -> List[SearchResult]:
        """在数据集中搜索"""
        try:
            data = {
                "query": query,
                "top_k": top_k,
                "similarity_threshold": similarity_threshold
            }
            response = self._make_request("POST", f"/api/v1/datasets/{dataset_id}/search", data=data)
            
            results = []
            for item in response.get("data", []):
                result = SearchResult(
                    content=item.get("content", ""),
                    document_id=item.get("document_id", ""),
                    document_name=item.get("document_name", ""),
                    score=item.get("score", 0.0),
                    metadata=item.get("metadata", {})
                )
                results.append(result)
            return results
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    def chat_with_dataset(self, dataset_id: str, question: str, 
                         conversation_history: Optional[List[Dict]] = None,
                         search_kwargs: Optional[Dict] = None) -> Dict[str, Any]:
        """与数据集对话"""
        try:
            data = {
                "question": question,
                "conversation_history": conversation_history or [],
                "search_kwargs": search_kwargs or {}
            }
            response = self._make_request("POST", f"/api/v1/datasets/{dataset_id}/chat", data=data)
            return response.get("data", {})
        except Exception as e:
            logger.error(f"对话失败: {e}")
            return {"error": str(e)}
    
    def get_retrieval_results(self, dataset_id: str, query: str, 
                             retrieval_config: Optional[Dict] = None) -> List[SearchResult]:
        """获取检索结果（不经过LLM）"""
        try:
            data = {
                "query": query,
                "retrieval_config": retrieval_config or {}
            }
            response = self._make_request("POST", f"/api/v1/datasets/{dataset_id}/retrieval", data=data)
            
            results = []
            for item in response.get("data", []):
                result = SearchResult(
                    content=item.get("content", ""),
                    document_id=item.get("document_id", ""),
                    document_name=item.get("document_name", ""),
                    score=item.get("score", 0.0),
                    metadata=item.get("metadata", {})
                )
                results.append(result)
            return results
        except Exception as e:
            logger.error(f"检索失败: {e}")
            return []
    
    def analyze_documents(self, dataset_id: str, analysis_type: str, 
                         analysis_config: Optional[Dict] = None) -> Dict[str, Any]:
        """分析文档集合"""
        try:
            data = {
                "analysis_type": analysis_type,
                "analysis_config": analysis_config or {}
            }
            response = self._make_request("POST", f"/api/v1/datasets/{dataset_id}/analyze", data=data)
            return response.get("data", {})
        except Exception as e:
            logger.error(f"文档分析失败: {e}")
            return {"error": str(e)}
    
    def get_document_insights(self, dataset_id: str, document_id: str) -> Dict[str, Any]:
        """获取文档洞察"""
        try:
            response = self._make_request("GET", f"/api/v1/datasets/{dataset_id}/documents/{document_id}/insights")
            return response.get("data", {})
        except Exception as e:
            logger.error(f"获取文档洞察失败: {e}")
            return {"error": str(e)}
    
    def batch_upload_documents(self, dataset_id: str, documents: List[Document]) -> List[str]:
        """批量上传文档"""
        successful_uploads = []
        for document in documents:
            doc_id = self.upload_document(dataset_id, document)
            if doc_id:
                successful_uploads.append(doc_id)
        return successful_uploads
    
    def update_document(self, dataset_id: str, document_id: str, 
                       updates: Dict[str, Any]) -> bool:
        """更新文档"""
        try:
            self._make_request("PUT", f"/api/v1/datasets/{dataset_id}/documents/{document_id}", data=updates)
            return True
        except Exception as e:
            logger.error(f"更新文档失败: {e}")
            return False


# 全局RAGFlow客户端实例
ragflow_client = None


def get_ragflow_client(config: Optional[RAGFlowConfig] = None) -> RAGFlowClient:
    """获取RAGFlow客户端实例"""
    global ragflow_client
    if ragflow_client is None or config is not None:
        ragflow_client = RAGFlowClient(config or RAGFlowConfig())
    return ragflow_client