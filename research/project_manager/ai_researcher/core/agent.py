"""
AI科研助手核心Agent类
支持多模型提供商的统一接口
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import yaml

from .models.openai_model import OpenAIModel
from .models.gemini_model import GeminiModel
from .models.anthropic_model import AnthropicModel
from .models.iflow_model import IFlowModel
from .models.base import BaseModel
from .ragflow import RAGFlowClient
from ..templates.manager import TemplateManager
from ..experiments.manager import ExperimentManager
from ..results.analyzer import ResultAnalyzer
from ..config import load_config
from ..secrets_manager import get_secrets_manager
from ..cli_tools.manager import CLIManager


logger = logging.getLogger(__name__)


class ResearchAgent:
    """
    AI科研助手主类

    整合了模型、知识库、模板和实验管理功能的统一接口。
    支持多种AI模型提供商（OpenAI、Gemini、Anthropic、iFlow），
    提供实验方案生成、进度管理、结果分析等核心功能。

    主要功能:
    - 多模型支持：通过统一的模型接口支持多种AI模型
    - 实验管理：创建、更新、跟踪实验进度
    - 知识库集成：与RAGFlow知识库无缝集成
    - 模板系统：支持自定义实验模板
    - 结果分析：AI驱动的实验结果分析
    - CLI工具：统一管理各种CLI工具

    支持的模型提供商:
    - openai: OpenAI的GPT系列模型
    - gemini: Google的Gemini系列模型
    - anthropic: Anthropic的Claude系列模型
    - iflow: iFlow CLI工具（支持工具执行和任务规划）

    使用示例:
        agent = ResearchAgent(
            model_provider="openai",
            model_name="gpt-4"
        )
        plan = agent.generate_experiment_plan(
            objective="研究CRISPR技术"
        )
    """

    def __init__(
        self,
        model_provider: str = "openai",
        model_name: str = "gpt-4",
        ragflow_endpoint: Optional[str] = None,
        config_path: Optional[str] = None,
        **kwargs
    ):
        """
        初始化AI科研助手

        Args:
            model_provider: 模型提供商 ("openai", "gemini", "anthropic", "iflow")
            model_name: 模型名称
            ragflow_endpoint: RAGFlow服务地址
            config_path: 配置文件路径
            **kwargs: 其他模型参数
        """
        # 加载配置
        self.config = load_config(config_path)

        # 初始化模型接口
        self.model = self._init_model(model_provider, model_name, **kwargs)

        # 初始化RAGFlow客户端
        ragflow_config = self.config.get("ragflow", {})
        self.ragflow = RAGFlowClient(
            endpoint=ragflow_endpoint or ragflow_config.get("endpoint"),
            api_key=ragflow_config.get("api_key"),
            ports=ragflow_config.get("ports")
        )

        # 初始化管理器
        self.templates = TemplateManager(
            template_dir=self.config.get("templates", {}).get("dir", "templates")
        )
        self.experiments = ExperimentManager(
            db_path=self.config.get("database", {}).get("path", "experiments.db")
        )
        self.analyzer = ResultAnalyzer(model=self.model)

        # 初始化CLI管理器
        self.cli_manager = CLIManager(self.config.get("cli", {}))

        logger.info(f"AI科研助手初始化完成，使用模型: {model_provider}/{model_name}")

    def _init_model(self, provider: str, name: str, **kwargs) -> BaseModel:
        """初始化模型接口"""
        # 优先从secrets_manager获取API密钥
        secrets_manager = get_secrets_manager()

        if provider == "openai":
            # 优先从secrets_manager获取，其次从kwargs，最后从配置文件
            api_key = (
                kwargs.get("api_key")
                or secrets_manager.get_api_key("openai")
                or self.config.get("openai", {}).get("api_key")
            )
            base_url = kwargs.get("base_url") or self.config.get("openai", {}).get("base_url")

            if not api_key:
                raise ValueError(
                    "未找到OpenAI API密钥。请使用以下命令配置:\n"
                    "  python -m ai_researcher.cli config keys setup\n"
                    "或:\n"
                    "  python -m ai_researcher.cli config keys set openai"
                )

            return OpenAIModel(api_key=api_key, base_url=base_url, model_name=name)

        elif provider == "gemini":
            # 优先从secrets_manager获取，其次从kwargs，最后从配置文件
            api_key = (
                kwargs.get("api_key")
                or secrets_manager.get_api_key("gemini")
                or self.config.get("gemini", {}).get("api_key")
            )

            if not api_key:
                raise ValueError(
                    "未找到Gemini API密钥。请使用以下命令配置:\n"
                    "  python -m ai_researcher.cli config keys setup\n"
                    "或:\n"
                    "  python -m ai_researcher.cli config keys set gemini"
                )

            return GeminiModel(api_key=api_key, model_name=name)

        elif provider == "anthropic":
            # 优先从secrets_manager获取，其次从kwargs，最后从配置文件
            api_key = (
                kwargs.get("api_key")
                or secrets_manager.get_api_key("anthropic")
                or self.config.get("anthropic", {}).get("api_key")
            )

            if not api_key:
                raise ValueError(
                    "未找到Anthropic API密钥。请使用以下命令配置:\n"
                    "  python -m ai_researcher.cli config keys setup\n"
                    "或:\n"
                    "  python -m ai_researcher.cli config keys set anthropic"
                )

            from .models.anthropic_model import AnthropicModel
            return AnthropicModel(api_key=api_key, model_name=name)

        elif provider == "iflow":
            # 优先从secrets_manager获取，其次从kwargs，最后从配置文件
            api_key = (
                kwargs.get("api_key")
                or secrets_manager.get_api_key("iflow")
                or self.config.get("iflow", {}).get("api_key")
            )
            base_url = (
                kwargs.get("base_url")
                or self.config.get("iflow", {}).get("base_url")
            )

            if not api_key:
                raise ValueError(
                    "未找到iFlow API密钥。请使用以下命令配置:\n"
                    "  python -m ai_researcher.cli config keys setup\n"
                    "或:\n"
                    "  python -m ai_researcher.cli config keys set iflow\n"
                    "或设置环境变量: IFLOW_API_KEY"
                )

            return IFlowModel(
                api_key=api_key,
                base_url=base_url,
                model_name=name
            )

        else:
            raise ValueError(f"不支持的模型提供商: {provider}")

    def generate_experiment_plan(
        self,
        objective: str,
        template: Optional[str] = None,
        search_top_k: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        根据实验目标生成详细的实验方案

        Args:
            objective: 实验目标描述
            template: 使用的模板名称
            search_top_k: 知识库检索返回结果数量
            **kwargs: 其他参数

        Returns:
            包含实验方案的字典
        """
        logger.info(f"开始生成实验方案，目标: {objective}")

        # 1. 检索相关文献和方法
        try:
            relevant_docs = self.ragflow.search(
                query=objective,
                top_k=search_top_k
            )
        except Exception as e:
            logger.warning(f"RAGFlow检索失败: {e}")
            relevant_docs = []

        # 2. 获取实验模板
        template_content = self.templates.get_template(template) if template else None

        # 3. 构建提示词
        prompt = self._build_plan_prompt(objective, relevant_docs, template_content)

        # 4. 调用模型生成方案
        response = self.model.generate(
            prompt=prompt,
            system_message=self._get_system_message(),
            **kwargs
        )

        # 5. 解析和结构化结果
        experiment_plan = self._parse_experiment_plan(response)

        # 6. 保存到数据库
        experiment_id = self.experiments.create_experiment(
            objective=objective,
            plan=experiment_plan,
            relevant_docs=relevant_docs
        )
        experiment_plan["id"] = experiment_id

        logger.info(f"实验方案生成完成，ID: {experiment_id}")
        return experiment_plan

    def update_progress(
        self,
        experiment_id: str,
        status: str,
        notes: Optional[str] = None,
        data: Optional[Dict] = None
    ) -> bool:
        """
        更新实验进度

        Args:
            experiment_id: 实验ID
            status: 实验状态 ("planned", "in_progress", "completed", "failed")
            notes: 进度备注
            data: 额外数据

        Returns:
            是否更新成功
        """
        return self.experiments.update_progress(
            experiment_id=experiment_id,
            status=status,
            notes=notes,
            data=data
        )

    def analyze_results(
        self,
        experiment_id: str,
        data_file: Optional[str] = None,
        data_dict: Optional[Dict] = None,
        analysis_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        分析实验结果

        Args:
            experiment_id: 实验ID
            data_file: 结果数据文件路径
            data_dict: 结果数据字典
            analysis_type: 分析类型 ("auto", "statistical", "biological")

        Returns:
            分析结果
        """
        logger.info(f"开始分析实验结果，ID: {experiment_id}")

        # 获取实验信息
        experiment = self.experiments.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"实验不存在: {experiment_id}")

        # 加载数据
        if data_file:
            data = self.analyzer.load_data(data_file)
        elif data_dict:
            data = data_dict
        else:
            raise ValueError("必须提供数据文件或数据字典")

        # 执行分析
        analysis_result = self.analyzer.analyze(
            data=data,
            experiment=experiment,
            analysis_type=analysis_type
        )

        # 保存结果
        self.experiments.save_results(
            experiment_id=experiment_id,
            results=analysis_result
        )

        logger.info(f"实验结果分析完成")
        return analysis_result

    def get_experiment_status(self, experiment_id: str) -> Dict[str, Any]:
        """获取实验状态"""
        return self.experiments.get_experiment(experiment_id)

    def list_experiments(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出实验"""
        return self.experiments.list_experiments(status=status)

    def _build_plan_prompt(
        self,
        objective: str,
        relevant_docs: List[Dict],
        template: Optional[str]
    ) -> str:
        """构建实验方案生成提示词"""
        docs_text = "\n\n".join([
            f"文献{i+1}: {doc.get('content', '')}"
            for i, doc in enumerate(relevant_docs[:3])
        ])

        prompt = f"""
作为一个专业的生物医学研究员，请根据以下信息设计详细的实验方案：

## 实验目标
{objective}

## 相关文献和方法
{docs_text}

## 实验模板
{template if template else "无特定模板"}

请生成一个详细的实验方案，包括：
1. 实验设计原理
2. 实验材料和试剂
3. 实验步骤（详细到每天的操作）
4. 预期结果
5. 注意事项
6. 质量控制要点
7. 数据收集和分析计划

请以JSON格式输出，包含以下字段：
- title: 实验标题
- objective: 详细目标
- design_rationale: 设计原理
- materials: 材料清单
- procedure: 详细步骤（数组）
- expected_results: 预期结果
- precautions: 注意事项
- quality_control: 质量控制
- timeline: 时间安排
        """

        return prompt

    def _get_system_message(self) -> str:
        """获取系统消息"""
        return """你是一位经验丰富的生物医学研究员，擅长设计严谨的实验方案。
请始终遵循科学严谨性，确保实验方案的可操作性和可重复性。
输出的实验方案应该结构清晰、内容详细、逻辑严密。"""

    def _parse_experiment_plan(self, response: str) -> Dict[str, Any]:
        """解析实验方案响应"""
        try:
            # 尝试解析JSON
            plan = json.loads(response)
            return plan
        except json.JSONDecodeError:
            # 如果不是JSON，则使用模型提取结构化信息
            return self.model.extract_structured_data(
                text=response,
                schema={
                    "title": "string",
                    "objective": "string",
                    "design_rationale": "string",
                    "materials": "array",
                    "procedure": "array",
                    "expected_results": "string",
                    "precautions": "array",
                    "quality_control": "array",
                    "timeline": "array"
                }
            )

    def export_experiment(self, experiment_id: str, format: str = "json") -> str:
        """导出实验方案"""
        return self.experiments.export_experiment(experiment_id, format)

    def batch_analyze(self, experiment_ids: List[str]) -> Dict[str, Any]:
        """批量分析多个实验的结果"""
        results = {}
        for exp_id in experiment_ids:
            try:
                results[exp_id] = self.analyze_results(exp_id)
            except Exception as e:
                logger.error(f"分析实验 {exp_id} 时出错: {e}")
                results[exp_id] = {"error": str(e)}
        return results

    # ==================== iFlow特色功能 ====================

    async def iflow_execute_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        使用iFlow执行工具调用（仅当模型提供商为iFlow时可用）

        Args:
            tool_name: 工具名称
            tool_args: 工具参数
            **kwargs: 其他参数

        Returns:
            工具执行结果

        Raises:
            ValueError: 如果当前模型不是iFlow
        """
        if not isinstance(self.model, IFlowModel):
            raise ValueError(
                "工具调用功能仅在使用iFlow模型时可用。"
                f"当前模型类型: {type(self.model).__name__}"
            )

        return await self.model.execute_tool_call(
            tool_name=tool_name,
            tool_args=tool_args,
            **kwargs
        )

    async def iflow_get_task_plan(
        self,
        objective: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        使用iFlow获取智能任务计划（仅当模型提供商为iFlow时可用）

        Args:
            objective: 任务目标
            **kwargs: 其他参数

        Returns:
            任务计划信息

        Raises:
            ValueError: 如果当前模型不是iFlow
        """
        if not isinstance(self.model, IFlowModel):
            raise ValueError(
                "任务规划功能仅在使用iFlow模型时可用。"
                f"当前模型类型: {type(self.model).__name__}"
            )

        return await self.model.get_task_plan(objective=objective, **kwargs)

    def iflow_generate_async(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        使用iFlow异步生成文本（当前模型为iFlow时的便捷方法）

        Args:
            prompt: 用户提示词
            system_message: 系统消息
            **kwargs: 其他参数

        Returns:
            模型生成的文本

        Raises:
            ValueError: 如果当前模型不是iFlow
        """
        if not isinstance(self.model, IFlowModel):
            raise ValueError(
                "此方法仅在使用iFlow模型时可用。"
                f"当前模型类型: {type(self.model).__name__}"
            )

        return self.model.generate(
            prompt=prompt,
            system_message=system_message,
            use_async=True,
            **kwargs
        )

    def iflow_generate_sync(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        使用iFlow同步生成文本（当前模型为iFlow时的便捷方法）

        Args:
            prompt: 用户提示词
            system_message: 系统消息
            **kwargs: 其他参数

        Returns:
            模型生成的文本

        Raises:
            ValueError: 如果当前模型不是iFlow
        """
        if not isinstance(self.model, IFlowModel):
            raise ValueError(
                "此方法仅在使用iFlow模型时可用。"
                f"当前模型类型: {type(self.model).__name__}"
            )

        return self.model.generate(
            prompt=prompt,
            system_message=system_message,
            use_async=False,
            **kwargs
        )

    # ==================== CLI工具支持 ====================

    def get_cli_manager(self) -> CLIManager:
        """
        获取CLI管理器实例

        Returns:
            CLI管理器
        """
        return self.cli_manager

    def execute_cli_command(
        self,
        tool_name: str,
        command: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行CLI命令

        Args:
            tool_name: CLI工具名称 (claude, codex, gemini, opencode, iflow)
            command: 要执行的命令
            **kwargs: 其他参数

        Returns:
            命令执行结果
        """
        return self.cli_manager.execute(tool_name, command, **kwargs)

    def get_cli_status(self) -> Dict[str, Any]:
        """
        获取所有CLI工具的状态

        Returns:
            CLI状态信息
        """
        return self.cli_manager.get_all_status()

    def check_cli_installation(self) -> Dict[str, bool]:
        """
        检查CLI工具安装状态

        Returns:
            安装状态字典
        """
        return self.cli_manager.check_installation()

    # 便捷CLI方法

    def cli_claude(self, command: str, **kwargs) -> Dict[str, Any]:
        """使用Claude CLI"""
        return self.cli_manager.claude(command, **kwargs)

    def cli_codex(self, command: str, **kwargs) -> Dict[str, Any]:
        """使用Codex CLI"""
        return self.cli_manager.codex(command, **kwargs)

    def cli_gemini(self, command: str, **kwargs) -> Dict[str, Any]:
        """使用Gemini CLI"""
        return self.cli_manager.gemini(command, **kwargs)

    def cli_opencode(self, command: str, **kwargs) -> Dict[str, Any]:
        """使用OpenCode CLI"""
        return self.cli_manager.opencode(command, **kwargs)

    def cli_iflow(self, command: str, **kwargs) -> Dict[str, Any]:
        """使用iFlow CLI"""
        return self.cli_manager.iflow(command, **kwargs)
