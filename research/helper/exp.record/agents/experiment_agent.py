"""
实验记录Agent - 核心防幻觉修订功能
严格基于模板和用户指令进行实验记录修订
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import re

from agents.base_agent import BaseAgent, AgentCapabilityError
from core.validation import get_validator, ValidationResult
from storage.template_manager import TemplateManager
from storage.experiment_store import ExperimentStore
from utils.ai_helpers import AIHelper


class ExperimentAgent(BaseAgent):
    """实验记录Agent - 实现防幻觉修订流程"""
    
    CAPABILITIES = ["experiment_revision", "template_based_editing", "protocol_modification"]
    
    # 三重约束系统提示词
    SYSTEM_PROMPT = """你是一个严谨的实验记录助手，必须严格遵守以下规则：

1. 仅基于用户提供的基础protocol模板和明确修改指令进行修订
2. 绝不添加模板中不存在的步骤、试剂或设备
3. 当用户描述不明确时，必须列出具体问题请求澄清，而不是猜测
4. 所有修改必须在最终输出中标注修订痕迹
5. 修改后的内容必须保持模板原有的结构和格式

<template>
{template_content}
</template>

<user_instructions>
{user_modifications}
</template>

请基于以上模板和用户指令进行修订，并返回修订后的完整内容。"""

    def __init__(self, settings=None, tool_registry=None, template_manager=None, validator=None, ai_helper=None):
        super().__init__(settings, tool_registry)
        
        # 依赖注入
        self.template_manager = template_manager or TemplateManager()
        self.validator = validator or get_validator(settings)
        self.ai_helper = ai_helper or AIHelper(settings)
        
        # 数据存储
        self.experiment_store = ExperimentStore()
        
        self.logger.info("ExperimentAgent initialized with anti-hallucination features")
    
    async def process(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理实验修订请求的完整流程：
        1. 获取关联的基础模板
        2. 应用三重约束提示词
        3. 生成修订版本
        4. 运行防幻觉验证
        5. 返回带修订标记的结果
        """
        try:
            # 解析请求数据
            template_id = request_data.get("template_id")
            user_modifications = request_data.get("user_modifications", "")
            experiment_title = request_data.get("experiment_title", "")
            strict_mode = request_data.get("strict_mode", self.settings.strict_mode if self.settings else True)
            conservative_mode = request_data.get("conservative_mode", self.settings.conservative_mode if self.settings else False)
            
            if not template_id:
                raise ValueError("缺少模板ID")
            
            if not user_modifications:
                raise ValueError("缺少用户修改指令")
            
            self.logger.info(f"Processing experiment revision for template {template_id}")
            
            # 步骤1: 获取基础模板
            template_data = await self._get_template(template_id)
            original_template = template_data["content"]
            
            # 步骤2: 应用三重约束提示词
            constrained_prompt = self._apply_revision_constraints(original_template, user_modifications)
            
            # 步骤3: 生成修订版本
            ai_revision = await self._generate_revision(constrained_prompt)
            
            # 步骤4: 运行防幻觉验证
            validation_result = await self._run_validation(original_template, user_modifications, ai_revision)
            
            # 步骤5: 处理验证结果
            if not validation_result.is_valid:
                if conservative_mode or (strict_mode and validation_result.confidence < 0.7):
                    # 保守模式或严格模式下置信度不足，应用保守策略
                    final_revision = await self._apply_conervative_revision(original_template, user_modifications, validation_result)
                    validation_result = await self._run_validation(original_template, user_modifications, final_revision)
                else:
                    # 记录问题但继续
                    self.logger.warning(f"Validation failed with confidence {validation_result.confidence:.2f}")
                    final_revision = ai_revision
            else:
                final_revision = ai_revision
            
            # 步骤6: 生成修订标记和差异对比
            revision_markers = self._generate_revision_markers(original_template, final_revision)
            diff_comparison = self._generate_diff_comparison(original_template, final_revision)
            
            # 步骤7: 准备响应数据
            result = {
                "success": True,
                "template_id": template_id,
                "experiment_title": experiment_title or f"实验记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "original_template": original_template,
                "user_modifications": user_modifications,
                "revised_content": final_revision,
                "validation_result": {
                    "is_valid": validation_result.is_valid,
                    "confidence": validation_result.confidence,
                    "issues": validation_result.issues,
                    "warnings": validation_result.warnings,
                    "conservative_suggestions": validation_result.conservative_suggestions
                },
                "revision_markers": revision_markers,
                "diff_comparison": diff_comparison,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "strict_mode": strict_mode,
                    "conservative_mode": conservative_mode,
                    "template_name": template_data.get("name", ""),
                    "template_version": template_data.get("version", "1.0")
                }
            }
            
            self.logger.info(f"Experiment revision completed with confidence {validation_result.confidence:.2f}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in experiment revision: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def _get_template(self, template_id: str) -> Dict[str, Any]:
        """获取模板数据"""
        template = self.template_manager.get_template(template_id)
        if not template:
            raise ValueError(f"模板 {template_id} 不存在")
        
        return template
    
    def _apply_revision_constraints(self, template: str, user_modifications: str) -> str:
        """应用三重约束提示词"""
        constrained_prompt = self.SYSTEM_PROMPT.format(
            template_content=template,
            user_modifications=user_modifications
        )
        
        # 添加额外的约束指令
        if self.settings and self.settings.strict_mode:
            constrained_prompt += "\n\n额外约束：请以最高精度执行，任何不确定的地方都要明确询问。"
        
        if self.settings and self.settings.conservative_mode:
            constrained_prompt += "\n\n保守模式：只进行最明确、最安全的修改，避免任何推测性内容。"
        
        return constrained_prompt
    
    async def _generate_revision(self, constrained_prompt: str) -> str:
        """生成修订版本"""
        try:
            response = await self.ai_helper.generate_response(constrained_prompt)
            return response.strip()
        except Exception as e:
            self.logger.error(f"Error generating AI revision: {e}")
            raise Exception(f"AI修订生成失败: {str(e)}")
    
    async def _run_validation(self, original_template: str, user_modifications: str, ai_revision: str) -> ValidationResult:
        """运行防幻觉验证"""
        try:
            validation_result = self.validator.validate_revision(original_template, user_modifications, ai_revision)
            
            self.logger.info(f"Validation completed: valid={validation_result.is_valid}, confidence={validation_result.confidence:.2f}")
            
            if validation_result.issues:
                self.logger.warning(f"Validation issues: {validation_result.issues}")
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Error during validation: {e}")
            # 返回失败的验证结果
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                issues=[f"验证过程出错: {str(e)}"],
                warnings=[],
                modifications=[],
                conservative_suggestions=[]
            )
    
    async def _apply_conervative_revision(self, original_template: str, user_modifications: str, validation_result: ValidationResult) -> str:
        """应用保守修订策略"""
        self.logger.info("Applying conservative revision strategy")
        
        # 基于验证建议应用保守修改
        conservative_prompt = f"""基于以下验证结果，请应用最保守的修订策略：

原始模板：
{original_template}

用户修改指令：
{user_modifications}

验证问题：
{chr(10).join(validation_result.issues)}

保守建议：
{chr(10).join(validation_result.conservative_suggestions)}

请仅应用最明确、最安全的修改，对于任何不确定的内容保持原文不变。"""

        try:
            conservative_revision = await self.ai_helper.generate_response(conservative_prompt)
            return conservative_revision.strip()
        except Exception as e:
            self.logger.error(f"Error in conservative revision: {e}")
            # 如果保守修订失败，返回原始模板
            return original_template
    
    def _generate_revision_markers(self, original: str, revised: str) -> List[Dict[str, Any]]:
        """生成修订标记"""
        markers = []
        
        # 使用简单的行对比
        original_lines = original.splitlines()
        revised_lines = revised.splitlines()
        
        from difflib import SequenceMatcher
        differ = SequenceMatcher(None, original_lines, revised_lines)
        
        for tag, i1, i2, j1, j2 in differ.get_opcodes():
            if tag == 'replace':
                markers.append({
                    "type": "replace",
                    "line_number": i1 + 1,
                    "original": '\n'.join(original_lines[i1:i2]),
                    "revised": '\n'.join(revised_lines[j1:j2]),
                    "description": f"替换了第{i1+1}-{i2}行内容"
                })
            elif tag == 'delete':
                markers.append({
                    "type": "delete",
                    "line_number": i1 + 1,
                    "original": '\n'.join(original_lines[i1:i2]),
                    "revised": "",
                    "description": f"删除了第{i1+1}-{i2}行内容"
                })
            elif tag == 'insert':
                markers.append({
                    "type": "insert",
                    "line_number": i1 + 1,
                    "original": "",
                    "revised": '\n'.join(revised_lines[j1:j2]),
                    "description": f"在第{i1+1}行后插入了新内容"
                })
        
        return markers
    
    def _generate_diff_comparison(self, original: str, revised: str) -> Dict[str, Any]:
        """生成差异对比"""
        import difflib
        
        original_lines = original.splitlines(keepends=True)
        revised_lines = revised.splitlines(keepends=True)
        
        # 生成统一差异格式
        unified_diff = list(difflib.unified_diff(
            original_lines, 
            revised_lines,
            fromfile="原始模板",
            tofile="修订版本",
            lineterm=""
        ))
        
        # 生成HTML差异（用于显示）
        html_diff = difflib.HtmlDiff().make_file(
            original_lines,
            revised_lines,
            fromdesc="原始模板",
            todesc="修订版本"
        )
        
        # 计算统计信息
        stats = {
            "original_lines": len(original_lines),
            "revised_lines": len(revised_lines),
            "changes_added": len([line for line in unified_diff if line.startswith('+') and not line.startswith('+++')]),
            "changes_removed": len([line for line in unified_diff if line.startswith('-') and not line.startswith('---')]),
            "unchanged_lines": len(original_lines) - len([line for line in unified_diff if line.startswith('-') and not line.startswith('---')])
        }
        
        return {
            "unified_diff": '\n'.join(unified_diff),
            "html_diff": html_diff,
            "statistics": stats
        }
    
    # 扩展功能：保存实验记录
    async def save_experiment(self, experiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """保存实验记录"""
        try:
            experiment_id = self.experiment_store.save_experiment(experiment_data)
            
            return {
                "success": True,
                "experiment_id": experiment_id,
                "message": "实验记录保存成功"
            }
            
        except Exception as e:
            self.logger.error(f"Error saving experiment: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # 扩展功能：获取实验历史
    async def get_experiment_history(self, template_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """获取实验历史记录"""
        try:
            experiments = self.experiment_store.list_experiments(template_id, limit)
            return experiments
        except Exception as e:
            self.logger.error(f"Error getting experiment history: {e}")
            return []
    
    # EXTENSION_POINT: 未来可扩展更多实验相关功能
    async def analyze_experiment_patterns(self, template_id: str) -> Dict[str, Any]:
        """分析实验模式（未来扩展）"""
        # 可以分析常见修改模式、用户偏好等
        pass