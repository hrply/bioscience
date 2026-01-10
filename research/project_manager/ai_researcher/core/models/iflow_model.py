"""
iFlow模型接口实现
支持iFlow CLI的Python SDK，集成工具执行和任务规划能力
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from .base import BaseModel


class IFlowModel(BaseModel):
    """
    iFlow模型接口实现

    基于iFlow CLI SDK的模型接口，提供以下特色功能：
    - 标准文本生成和对话能力
    - 工具执行功能
    - 智能任务规划
    - 异步和同步调用支持

    iFlow是一个强大的AI CLI工具，支持工具调用和任务规划。
    通过此接口可以将iFlow集成到ai_researcher项目中。

    注意事项:
    - 嵌入功能当前不支持，会抛出NotImplementedError
    - 需要iFlow CLI已安装并配置
    - 支持异步和同步两种调用方式
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "Qwen3-Coder",
        base_url: Optional[str] = None,
        config_manager=None,
        config_name: Optional[str] = None,
        **kwargs
    ):
        """
        初始化iFlow模型

        Args:
            api_key: API密钥
            model_name: 模型名称
            base_url: API基础URL
            config_manager: 模型配置管理器
            config_name: 配置名称（从配置管理器加载）
            **kwargs: 其他参数
        """
        super().__init__(model_name, **kwargs)

        # 如果提供了配置管理器，从管理器加载配置
        if config_manager and config_name:
            config = config_manager.get_model_config(config_name)
            if config:
                api_key = config.get('api_key') or api_key
                base_url = config.get('endpoint') or base_url
                model_name = config.get('model_name') or model_name
                self.temperature = config.get('temperature', 0.7)
                self.max_tokens = config.get('max_tokens', 4000)
                self.extra_params = config.get('extra_params', {})
            else:
                raise ValueError(f"配置不存在: {config_name}")
        else:
            self.temperature = kwargs.get('temperature', 0.7)
            self.max_tokens = kwargs.get('max_tokens', 4000)
            self.extra_params = {}

        # 初始化参数
        self.api_key = api_key
        self.base_url = base_url or "https://apis.iflow.cn/v1"

        # 检查iflow SDK是否可用
        try:
            import iflow_sdk
        except ImportError:
            raise ImportError(
                "请安装iFlow SDK: pip install iflow-cli-sdk\n"
                "或参考: https://platform.iflow.cn/cli/sdk/sdk-python"
            )

    async def _send_message(self, prompt: str, **kwargs) -> str:
        """
        异步发送消息到iFlow

        Args:
            prompt: 用户提示词
            **kwargs: 其他参数

        Returns:
            iFlow响应的文本
        """
        try:
            from iflow_sdk import IFlowClient, AssistantMessage, TaskFinishMessage

            # 构建配置
            auth_method_info = {
                "api_key": self.api_key,
                "base_url": self.base_url,
                "model_name": self.model_name
            }

            async with IFlowClient() as client:
                await client.send_message(prompt)

                response_text = ""
                async for message in client.receive_messages():
                    if isinstance(message, AssistantMessage):
                        response_text += message.chunk.text
                    elif isinstance(message, TaskFinishMessage):
                        break

                return response_text

        except Exception as e:
            raise RuntimeError(f"iFlow调用失败: {e}")

    def _send_message_sync(self, prompt: str, **kwargs) -> str:
        """
        同步发送消息到iFlow

        Args:
            prompt: 用户提示词
            **kwargs: 其他参数

        Returns:
            iFlow响应的文本
        """
        try:
            from iflow_sdk import query_sync, IFlowOptions

            options = IFlowOptions(
                timeout=kwargs.get('timeout', 30.0)
            )

            response = query_sync(prompt, options=options)
            return response

        except Exception as e:
            raise RuntimeError(f"iFlow同步调用失败: {e}")

    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_async: bool = True,
        **kwargs
    ) -> str:
        """
        生成文本响应

        Args:
            prompt: 用户提示词
            system_message: 系统消息
            temperature: 温度参数
            max_tokens: 最大令牌数
            use_async: 是否使用异步调用
            **kwargs: 其他参数

        Returns:
            模型生成的文本
        """
        # 构建完整提示词
        full_prompt = prompt
        if system_message:
            full_prompt = f"{system_message}\n\n{prompt}"

        # 使用配置或默认值
        temperature = temperature if temperature is not None else getattr(self, 'temperature', 0.7)
        max_tokens = max_tokens if max_tokens is not None else getattr(self, 'max_tokens', 4000)

        # 合并额外参数
        all_params = {
            'temperature': temperature,
            'max_tokens': max_tokens,
            **getattr(self, 'extra_params', {}),
            **kwargs
        }

        if use_async:
            try:
                # 尝试异步调用
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果事件循环正在运行，在新线程中执行
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            self._send_message(full_prompt, **all_params)
                        )
                        return future.result()
                else:
                    # 如果没有运行中的事件循环，直接使用
                    return asyncio.run(self._send_message(full_prompt, **all_params))
            except Exception:
                # 如果异步失败，回退到同步调用
                return self._send_message_sync(full_prompt, **all_params)
        else:
            return self._send_message_sync(full_prompt, **all_params)

    def extract_structured_data(
        self,
        text: str,
        schema: Dict[str, str],
        temperature: float = 0.1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        从文本中提取结构化数据

        Args:
            text: 输入文本
            schema: 数据结构定义
            temperature: 温度参数
            **kwargs: 其他参数

        Returns:
            结构化数据字典
        """
        prompt = f"""
请从以下文本中提取结构化数据，并以JSON格式返回：

文本内容：
{text}

数据结构要求：
{json.dumps(schema, indent=2)}

请只返回JSON数据，不要其他解释。
        """

        response = self.generate(
            prompt,
            temperature=temperature,
            use_async=False,
            **kwargs
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "raw_text": text,
                "error": "JSON解析失败",
                "partial_data": response
            }

    def embed(self, text: str) -> List[float]:
        """
        生成文本嵌入向量

        注意：iFlow当前可能不直接支持嵌入功能

        Args:
            text: 输入文本

        Returns:
            嵌入向量（模拟返回）
        """
        # iFlow可能不直接支持嵌入，这里返回空列表
        # 或者可以尝试使用其他方式获取嵌入
        raise NotImplementedError(
            "iFlow当前版本可能不支持嵌入功能。"
            "请使用其他模型提供商（如OpenAI）获取嵌入向量。"
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        对话模式

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Returns:
            响应文本
        """
        # 将消息列表转换为文本
        conversation = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in messages
        ])

        return self.generate(
            prompt=conversation,
            use_async=False,
            **kwargs
        )

    async def execute_tool_call(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行工具调用（iFlow特色功能）

        Args:
            tool_name: 工具名称
            tool_args: 工具参数
            **kwargs: 其他参数

        Returns:
            工具执行结果
        """
        try:
            from iflow_sdk import IFlowClient, ToolCallMessage, TaskFinishMessage

            prompt = f"请调用工具: {tool_name}，参数: {json.dumps(tool_args)}"

            async with IFlowClient() as client:
                await client.send_message(prompt)

                result = None
                async for message in client.receive_messages():
                    if isinstance(message, ToolCallMessage):
                        result = {
                            "tool_name": message.tool_name,
                            "status": str(message.status),
                            "label": getattr(message, 'label', None),
                            "content": getattr(message, 'content', None)
                        }
                    elif isinstance(message, TaskFinishMessage):
                        break

                return result or {"error": "未收到工具调用结果"}

        except Exception as e:
            raise RuntimeError(f"iFlow工具调用失败: {e}")

    async def get_task_plan(
        self,
        objective: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        获取任务计划（iFlow特色功能）

        Args:
            objective: 任务目标
            **kwargs: 其他参数

        Returns:
            任务计划
        """
        try:
            from iflow_sdk import IFlowClient, PlanMessage, TaskFinishMessage

            prompt = f"请为以下目标制定详细计划: {objective}"

            async with IFlowClient() as client:
                await client.send_message(prompt)

                plan_entries = []
                async for message in client.receive_messages():
                    if isinstance(message, PlanMessage):
                        plan_entries = [
                            {
                                "content": entry.content,
                                "priority": entry.priority,
                                "status": entry.status
                            }
                            for entry in message.entries
                        ]
                    elif isinstance(message, TaskFinishMessage):
                        break

                return {
                    "objective": objective,
                    "plan": plan_entries,
                    "total_steps": len(plan_entries)
                }

        except Exception as e:
            raise RuntimeError(f"iFlow获取任务计划失败: {e}")
