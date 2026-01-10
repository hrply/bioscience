"""
RAGFlow知识库集成模块
用于检索相关文献和方法
对接本地RAGFlow服务

基于 RAGFlow SDK API 文档实现
https://github.com/infiniflow/ragflow
"""

import requests
import logging
from typing import List, Dict, Optional, Any, Union
from urllib.parse import urljoin
import json
import re
import os


logger = logging.getLogger(__name__)


class RAGFlowError(Exception):
    """RAGFlow API异常"""
    pass


class RAGFlowClient:
    """RAGFlow客户端 - 对接RAGFlow服务"""

    # API错误码
    ERROR_CODES = {
        400: "Bad Request - Invalid request parameters",
        401: "Unauthorized - Unauthorized access",
        403: "Forbidden - Access denied",
        404: "Not Found - Resource not found",
        500: "Internal Server Error - Server internal error",
        1001: "Invalid Chunk ID",
        1002: "Chunk Update Failed",
    }

    # 端口映射变量名到内部标识符的映射
    PORT_MAPPING = {
        'SVR_WEB_HTTP_PORT': 'web_http',
        'SVR_WEB_HTTPS_PORT': 'web_https',
        'SVR_HTTP_PORT': 'api',
        'ADMIN_SVR_HTTP_PORT': 'admin',
        'SVR_MCP_PORT': 'mcp',
    }

    def __init__(self, endpoint: Optional[str] = None, api_key: Optional[str] = None, ports: Optional[Dict[str, int]] = None):
        """
        初始化RAGFlow客户端

        Args:
            endpoint: RAGFlow服务地址，如 http://192.168.3.147:20334
            api_key: RAGFlow API密钥（可选）
            ports: Docker端口映射配置，格式：{
                'SVR_WEB_HTTP_PORT': 80,
                'SVR_WEB_HTTPS_PORT': 443,
                'SVR_HTTP_PORT': 9380,
                'ADMIN_SVR_HTTP_PORT': 9381,
                'SVR_MCP_PORT': 9382
            }
        """
        # 解析endpoint获取主机和端口信息
        if endpoint:
            self._parse_endpoint(endpoint)
        else:
            # 使用默认配置
            self.host = "localhost"
            self.port = 20334
            self.scheme = "http"

        self.api_key = api_key
        self.session = requests.Session()

        # 设置请求头
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.session.headers.update(headers)

        # 构建endpoint
        self.endpoint = f"{self.scheme}://{self.host}:{self.port}"

        # 加载端口配置（优先级：参数 > 环境变量 > 默认值）
        self.ports = self._load_port_config(ports)

    def _load_port_config(self, ports: Optional[Dict[str, int]]) -> Dict[str, int]:
        """
        从环境变量加载端口配置

        Args:
            ports: 传入的端口配置（优先级最高）

        Returns:
            端口配置字典
        """
        # 如果直接传入端口配置，使用传入的配置
        if ports:
            return ports

        # 从环境变量加载
        env_ports = {}
        port_vars = [
            'SVR_WEB_HTTP_PORT',
            'SVR_WEB_HTTPS_PORT',
            'SVR_HTTP_PORT',
            'ADMIN_SVR_HTTP_PORT',
            'SVR_MCP_PORT'
        ]

        for port_var in port_vars:
            env_value = os.environ.get(port_var)
            if env_value:
                # 处理形如 "127.0.0.1:20334" 的值
                if ':' in env_value:
                    try:
                        port_num = int(env_value.split(':')[-1])
                        env_ports[port_var] = port_num
                    except ValueError:
                        logger.warning(f"无法解析环境变量 {port_var} 的值: {env_value}")
                else:
                    # 纯端口号
                    try:
                        env_ports[port_var] = int(env_value)
                    except ValueError:
                        logger.warning(f"无法解析环境变量 {port_var} 的值: {env_value}")
            else:
                # 使用默认值（根据.env文件中的值）
                default_ports = {
                    'SVR_WEB_HTTP_PORT': 20334,
                    'SVR_WEB_HTTPS_PORT': 443,
                    'SVR_HTTP_PORT': 20335,
                    'ADMIN_SVR_HTTP_PORT': 20336,
                    'SVR_MCP_PORT': 20337,
                }
                env_ports[port_var] = default_ports.get(port_var, 9380)

        logger.info(f"已加载RAGFlow端口配置: {env_ports}")
        return env_ports

    def _parse_endpoint(self, endpoint: str):
        """
        解析endpoint字符串，提取主机、端口和协议

        Args:
            endpoint: 形如 http://192.168.3.147:20334 的端点地址
        """
        # 匹配协议、主机和端口
        pattern = r'^(https?)://([^:]+):(\d+)$'
        match = re.match(pattern, endpoint)

        if match:
            self.scheme = match.group(1)
            self.host = match.group(2)
            self.port = int(match.group(3))
        else:
            # 如果解析失败，尝试仅匹配主机
            pattern = r'^(https?)://(.+)$'
            match = re.match(pattern, endpoint)
            if match:
                self.scheme = match.group(1)
                self.host = match.group(2)
                # 默认端口
                self.port = 9380 if self.scheme == "http" else 443
            else:
                # 纯主机名，无协议
                self.host = endpoint
                self.scheme = "http"
                self.port = 9380

    def get_port(self, port_variable: str) -> Optional[int]:
        """
        获取指定端口变量对应的端口号

        Args:
            port_variable: 端口变量名，如 'SVR_HTTP_PORT'

        Returns:
            端口号，如果未配置则返回None
        """
        return self.ports.get(port_variable)

    def get_url(self, port_variable: str, path: str = "") -> str:
        """
        根据端口变量构建完整的URL

        Args:
            port_variable: 端口变量名，如 'SVR_HTTP_PORT'
            path: API路径，如 '/api/v1/datasets'

        Returns:
            完整的URL字符串
        """
        port = self.get_port(port_variable)
        if port:
            return f"{self.scheme}://{self.host}:{port}{path}"
        else:
            # 如果未配置端口，使用默认endpoint
            return f"{self.endpoint}{path}"

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        处理API响应

        Args:
            response: requests响应对象

        Returns:
            响应数据

        Raises:
            RAGFlowError: API返回错误
        """
        try:
            result = response.json()
        except json.JSONDecodeError:
            raise RAGFlowError(f"Invalid JSON response: {response.text}")

        # 检查业务错误码
        if "code" in result and result["code"] != 0:
            error_msg = result.get("message", "Unknown error")
            error_code = result.get("code")
            logger.error(f"RAGFlow API error {error_code}: {error_msg}")
            raise RAGFlowError(f"API error {error_code}: {error_msg}")

        # 检查HTTP状态码
        if response.status_code >= 400:
            error_msg = self.ERROR_CODES.get(
                response.status_code,
                f"HTTP {response.status_code}"
            )
            logger.error(f"RAGFlow HTTP error: {error_msg}")
            raise RAGFlowError(f"{error_msg}: {response.text}")

        return result

    def search(
        self,
        query: str,
        dataset_ids: Optional[List[str]] = None,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.2,
        vector_similarity_weight: float = 0.3,
        page: int = 1,
        page_size: int = 30,
        use_kg: bool = False,
        keyword: bool = False,
        highlight: bool = False,
        cross_languages: Optional[List[str]] = None,
        metadata_condition: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        检索知识库

        Args:
            query: 搜索查询（必需）
            dataset_ids: 数据集ID列表（与document_ids二选一）
            document_ids: 文档ID列表（与dataset_ids二选一）
            top_k: 参与向量相似度计算的数量，默认1024
            similarity_threshold: 最小相似度阈值，默认0.2
            vector_similarity_weight: 向量余弦相似度权重，默认0.3
            page: 页码，默认1
            page_size: 每页最大块数，默认30
            use_kg: 是否包含知识图谱相关文本块，默认False
            keyword: 是否启用关键词匹配，默认False
            highlight: 是否高亮匹配项，默认False
            cross_languages: 跨语言翻译列表
            metadata_condition: 元数据过滤条件

        Returns:
            搜索结果列表

        Raises:
            RAGFlowError: API调用失败
        """
        payload = {
            "question": query,
            "top_k": top_k,
            "similarity_threshold": similarity_threshold,
            "vector_similarity_weight": vector_similarity_weight,
            "page": page,
            "page_size": page_size,
            "use_kg": use_kg,
            "keyword": keyword,
            "highlight": highlight,
        }

        # 设置数据集或文档ID
        if dataset_ids:
            payload["dataset_ids"] = dataset_ids
        elif document_ids:
            payload["document_ids"] = document_ids
        else:
            logger.warning("No dataset_ids or document_ids specified for search")

        if cross_languages:
            payload["cross_languages"] = cross_languages

        if metadata_condition:
            payload["metadata_condition"] = metadata_condition

        try:
            url = self.get_url('SVR_HTTP_PORT', "/api/v1/retrieval")
            response = self.session.post(url, json=payload, timeout=30)

            result = self._handle_response(response)
            data = result.get("data", [])

            logger.info(f"RAGFlow检索成功，返回 {len(data)} 条结果")

            return data

        except RAGFlowError:
            raise
        except requests.RequestException as e:
            logger.error(f"RAGFlow检索失败: {e}")
            raise RAGFlowError(f"Request failed: {e}")

    def list_datasets(self) -> List[Dict[str, Any]]:
        """
        列出所有数据集

        Returns:
            数据集列表

        Raises:
            RAGFlowError: API调用失败
        """
        try:
            # 使用配置的API端口
            url = self.get_url('SVR_HTTP_PORT', "/api/v1/datasets")
            response = self.session.get(url, timeout=10)

            result = self._handle_response(response)
            datasets = result.get("data", [])

            # 如果data是False（API错误），返回空列表
            if isinstance(datasets, bool):
                datasets = []

            logger.info(f"获取到 {len(datasets)} 个数据集")
            return datasets

        except RAGFlowError:
            raise
        except requests.RequestException as e:
            logger.error(f"获取数据集列表失败: {e}")
            raise RAGFlowError(f"Request failed: {e}")

    def create_dataset(
        self,
        name: str,
        description: Optional[str] = None,
        embedding_model: Optional[str] = None,
        permission: str = "me",
        chunk_method: str = "naive",
        parser_config: Optional[Dict[str, Any]] = None,
        avatar: Optional[str] = None,
    ) -> str:
        """
        创建数据集

        Args:
            name: 数据集名称（必需，唯一，最大128字符）
            description: 数据集描述（可选）
            embedding_model: 嵌入模型名称（可选，如 "BAAI/bge-large-zh-v1.5@BAAI"）
            permission: 访问权限，"me"（仅自己）或 "team"（团队），默认"me"
            chunk_method: 分块方法，默认"naive"，可选："book", "email", "laws",
                        "manual", "one", "paper", "picture", "presentation", "qa", "table", "tag"
            parser_config: 解析器配置（可选）
            avatar: 头像的Base64编码（可选）

        Returns:
            数据集ID

        Raises:
            RAGFlowError: API调用失败
        """
        payload = {
            "name": name,
            "permission": permission,
            "chunk_method": chunk_method,
        }

        if description:
            payload["description"] = description

        if embedding_model:
            payload["embedding_model"] = embedding_model

        if parser_config:
            payload["parser_config"] = parser_config

        if avatar:
            payload["avatar"] = avatar

        try:
            url = self.get_url('SVR_HTTP_PORT', "/api/v1/datasets")
            response = self.session.post(url, json=payload, timeout=30)

            result = self._handle_response(response)
            dataset_id = result.get("data", {}).get("dataset_id")
            logger.info(f"创建数据集成功: {dataset_id}")
            return dataset_id

        except RAGFlowError:
            raise
        except requests.RequestException as e:
            logger.error(f"创建数据集失败: {e}")
            raise RAGFlowError(f"Request failed: {e}")

    def get_dataset_info(self, dataset_id: str) -> Dict[str, Any]:
        """
        获取数据集信息

        Args:
            dataset_id: 数据集ID

        Returns:
            数据集信息

        Raises:
            RAGFlowError: API调用失败
        """
        try:
            url = self.get_url('SVR_HTTP_PORT', f"/api/v1/datasets/{dataset_id}")
            response = self.session.get(url, timeout=10)

            result = self._handle_response(response)
            dataset_info = result.get("data", {})
            return dataset_info

        except RAGFlowError:
            raise
        except requests.RequestException as e:
            logger.error(f"获取数据集信息失败: {e}")
            raise RAGFlowError(f"Request failed: {e}")

    def upload_document(
        self,
        dataset_id: str,
        document_path: str,
        chunk_method: Optional[str] = None,
        parser_config: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        上传文档到数据集

        Args:
            dataset_id: 数据集ID
            document_path: 文档路径
            chunk_method: 分块方法（可选）
            parser_config: 解析器配置（可选）

        Returns:
            上传的文档信息列表

        Raises:
            RAGFlowError: API调用失败
        """
        try:
            with open(document_path, 'rb') as f:
                files = {'file': (document_path.split('/')[-1], f)}
                data = {
                    "dataset_id": dataset_id,
                }
                if chunk_method:
                    data["chunk_method"] = chunk_method
                if parser_config:
                    data["parser_config"] = parser_config

                # 创建新的session用于multipart/form-data
                temp_session = requests.Session()
                headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
                temp_session.headers.update(headers)

                url = self.get_url('SVR_HTTP_PORT', f"/api/v1/datasets/{dataset_id}/documents")
                response = temp_session.post(url, files=files, data=data, timeout=60)

                result = self._handle_response(response)
                documents = result.get("data", [])
                logger.info(f"上传文档成功，共 {len(documents)} 个")
                return documents

        except RAGFlowError:
            raise
        except Exception as e:
            logger.error(f"上传文档失败: {e}")
            raise RAGFlowError(f"Request failed: {e}")

    def list_documents(self, dataset_id: str) -> List[Dict[str, Any]]:
        """
        列出数据集中的文档

        Args:
            dataset_id: 数据集ID

        Returns:
            文档列表

        Raises:
            RAGFlowError: API调用失败
        """
        try:
            url = self.get_url('SVR_HTTP_PORT', f"/api/v1/datasets/{dataset_id}/documents")
            response = self.session.get(url, timeout=10)

            result = self._handle_response(response)
            documents = result.get("data", {})
            return documents if isinstance(documents, list) else documents.get("documents", [])

        except RAGFlowError:
            raise
        except requests.RequestException as e:
            logger.error(f"获取文档列表失败: {e}")
            raise RAGFlowError(f"Request failed: {e}")

    def delete_dataset(self, dataset_id: str) -> bool:
        """
        删除数据集

        Args:
            dataset_id: 数据集ID

        Returns:
            是否成功

        Raises:
            RAGFlowError: API调用失败
        """
        try:
            url = self.get_url('SVR_HTTP_PORT', f"/api/v1/datasets/{dataset_id}")
            response = self.session.delete(url, timeout=30)

            self._handle_response(response)
            logger.info(f"删除数据集成功: {dataset_id}")
            return True

        except RAGFlowError:
            raise
        except requests.RequestException as e:
            logger.error(f"删除数据集失败: {e}")
            raise RAGFlowError(f"Request failed: {e}")

    def parse_documents(self, dataset_id: str, document_ids: List[str]) -> bool:
        """
        解析文档

        Args:
            dataset_id: 数据集ID
            document_ids: 文档ID列表

        Returns:
            是否成功

        Raises:
            RAGFlowError: API调用失败
        """
        try:
            payload = {
                "dataset_id": dataset_id,
                "document_ids": document_ids
            }

            url = self.get_url('SVR_HTTP_PORT', f"/api/v1/datasets/{dataset_id}/chunks")
            response = self.session.post(url, json=payload, timeout=120)

            self._handle_response(response)
            logger.info(f"解析文档成功")
            return True

        except RAGFlowError:
            raise
        except requests.RequestException as e:
            logger.error(f"解析文档失败: {e}")
            raise RAGFlowError(f"Request failed: {e}")

    def chat(
        self,
        query: str,
        dataset_ids: Optional[List[str]] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.2,
        vector_similarity_weight: float = 0.3,
        use_kg: bool = False,
    ) -> Dict[str, Any]:
        """
        对话检索

        Args:
            query: 查询问题（必需）
            dataset_ids: 数据集ID列表（可选）
            top_k: 参与向量相似度计算的数量，默认1024
            similarity_threshold: 最小相似度阈值，默认0.2
            vector_similarity_weight: 向量余弦相似度权重，默认0.3
            use_kg: 是否包含知识图谱相关文本块，默认False

        Returns:
            对话结果字典，包含answer和citations

        Raises:
            RAGFlowError: API调用失败
        """
        payload = {
            "question": query,
            "top_k": top_k,
            "similarity_threshold": similarity_threshold,
            "vector_similarity_weight": vector_similarity_weight,
            "use_kg": use_kg,
        }

        if dataset_ids:
            payload["dataset_ids"] = dataset_ids

        try:
            url = self.get_url('SVR_HTTP_PORT', "/api/v1/chats")
            response = self.session.post(url, json=payload, timeout=30)

            result = self._handle_response(response)
            chat_data = result.get("data", {})
            logger.info(f"对话检索成功")

            return chat_data

        except RAGFlowError:
            raise
        except requests.RequestException as e:
            logger.error(f"对话检索失败: {e}")
            raise RAGFlowError(f"Request failed: {e}")

    def chat_completion(
        self,
        chat_id: str,
        messages: List[Dict[str, str]],
        model: str = "default",
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        创建聊天完成（类似OpenAI的Chat Completions）

        Args:
            chat_id: 聊天会话ID
            messages: 消息列表，格式为[{"role": "user", "content": "..."}]
            model: 模型名称
            stream: 是否流式返回，默认False

        Returns:
            聊天完成响应

        Raises:
            RAGFlowError: API调用失败
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

        try:
            url = self.get_url('SVR_HTTP_PORT', f"/api/v1/chats/{chat_id}/completions")
            response = self.session.post(url, json=payload, timeout=30)

            result = self._handle_response(response)
            logger.info(f"聊天完成成功")

            return result

        except RAGFlowError:
            raise
        except requests.RequestException as e:
            logger.error(f"聊天完成失败: {e}")
            raise RAGFlowError(f"Request failed: {e}")

    def create_chat_session(
        self,
        chat_id: str,
        dataset_ids: Optional[List[str]] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.2,
    ) -> str:
        """
        创建聊天会话

        Args:
            chat_id: 聊天ID
            dataset_ids: 关联的数据集ID列表
            top_k: 检索数量
            similarity_threshold: 相似度阈值

        Returns:
            会话ID

        Raises:
            RAGFlowError: API调用失败
        """
        payload = {
            "dataset_ids": dataset_ids or [],
            "top_k": top_k,
            "similarity_threshold": similarity_threshold,
        }

        try:
            url = self.get_url('SVR_HTTP_PORT', f"/api/v1/chats/{chat_id}/sessions")
            response = self.session.post(url, json=payload, timeout=30)

            result = self._handle_response(response)
            session_id = result.get("data", {}).get("session_id")
            logger.info(f"创建聊天会话成功: {session_id}")
            return session_id

        except RAGFlowError:
            raise
        except requests.RequestException as e:
            logger.error(f"创建聊天会话失败: {e}")
            raise RAGFlowError(f"Request failed: {e}")

    def health_check(self) -> bool:
        """
        健康检查

        Returns:
            服务是否可用

        Raises:
            RAGFlowError: API调用失败
        """
        try:
            url = self.get_url('SVR_HTTP_PORT', "/api/v1/datasets")
            response = self.session.get(url, timeout=5)
            # 尝试解析响应，但不抛出异常
            try:
                result = response.json()
                # 检查是否是成功的响应
                return isinstance(result, dict)
            except:
                return False
        except Exception:
            return False
