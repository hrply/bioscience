"""
防幻觉验证模块 - 核心防幻觉保障机制
实现三重约束验证：语法分析、语义分析和依据追踪
"""

import re
import logging
from typing import Dict, List, Any, Tuple, Optional, Set
from dataclasses import dataclass
from difflib import SequenceMatcher
import yaml
from pathlib import Path


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    confidence: float  # 0.0-1.0
    issues: List[str]
    warnings: List[str]
    modifications: List[Dict[str, Any]]  # 修改详情
    conservative_suggestions: List[str]  # 保守模式建议


@dataclass
class ModificationDetail:
    """修改详情"""
    section: str
    original_text: str
    modified_text: str
    justification: str  # 来自用户提示的依据
    confidence: float


class SectionValidator:
    """章节完整性验证器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def check_section_integrity(self, original_template: str, revised_content: str) -> ValidationResult:
        """
        检查是否添加了模板不存在的章节
        """
        issues = []
        warnings = []
        modifications = []
        
        # 提取原始模板的章节结构
        original_sections = self._extract_sections(original_template)
        revised_sections = self._extract_sections(revised_content)
        
        # 检查新增章节
        new_sections = set(revised_sections.keys()) - set(original_sections.keys())
        if new_sections:
            issues.extend([
                f"检测到新增章节: {section}"
                for section in new_sections
            ])
        
        # 检查删除章节
        removed_sections = set(original_sections.keys()) - set(revised_sections.keys())
        if removed_sections:
            issues.extend([
                f"检测到删除章节: {section}"
                for section in removed_sections
            ])
        
        # 检查章节顺序变化
        if len(original_sections) > 1 and len(revised_sections) > 1:
            original_order = list(original_sections.keys())
            revised_order = list(revised_sections.keys())
            
            # 过滤掉新增和删除的章节
            common_sections = [s for s in original_order if s in revised_sections]
            revised_common = [s for s in revised_order if s in original_sections]
            
            if common_sections != revised_common:
                warnings.append("章节顺序发生变化")
        
        # 计算置信度
        total_issues = len(issues)
        confidence = max(0.0, 1.0 - (total_issues * 0.3))
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            confidence=confidence,
            issues=issues,
            warnings=warnings,
            modifications=modifications,
            conservative_suggestions=[]
        )
    
    def _extract_sections(self, content: str) -> Dict[str, str]:
        """提取文档章节"""
        sections = {}
        
        # 匹配Markdown标题
        header_pattern = r'^(#{1,6})\s+(.+)$'
        current_section = "引言"
        current_content = []
        
        for line in content.split('\n'):
            header_match = re.match(header_pattern, line, re.MULTILINE)
            if header_match:
                # 保存当前章节
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # 开始新章节
                current_section = header_match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)
        
        # 保存最后一个章节
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections


class ImmutableSectionValidator:
    """不可修改章节验证器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def check_immutable_sections(self, original_template: str, revised_content: str) -> ValidationResult:
        """
        检查标记为不可修改的部分是否被篡改
        """
        issues = []
        warnings = []
        modifications = []
        
        # 提取不可修改章节
        immutable_sections = self._extract_immutable_sections(original_template)
        
        if not immutable_sections:
            return ValidationResult(
                is_valid=True,
                confidence=1.0,
                issues=[],
                warnings=[],
                modifications=[],
                conservative_suggestions=[]
            )
        
        # 检查不可修改章节是否被修改
        revised_sections = self._extract_sections(revised_content)
        
        for section_name in immutable_sections:
            if section_name in revised_sections:
                original_content = immutable_sections[section_name]
                revised_content_section = revised_sections[section_name]
                
                # 计算相似度
                similarity = SequenceMatcher(None, original_content, revised_content_section).ratio()
                
                if similarity < 0.95:  # 允许微小的格式差异
                    issues.append(f"不可修改章节 '{section_name}' 被篡改 (相似度: {similarity:.2f})")
                    
                    # 记录修改详情
                    modifications.append({
                        "section": section_name,
                        "type": "immutable_modified",
                        "similarity": similarity
                    })
        
        confidence = max(0.0, 1.0 - (len(issues) * 0.4))
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            confidence=confidence,
            issues=issues,
            warnings=warnings,
            modifications=modifications,
            conservative_suggestions=[]
        )
    
    def _extract_immutable_sections(self, content: str) -> Dict[str, str]:
        """提取标记为不可修改的章节"""
        immutable_sections = {}
        sections = self._extract_sections_with_markers(content)
        
        for section_name, section_content in sections.items():
            if self._is_immutable_section(section_name, section_content):
                immutable_sections[section_name] = section_content
        
        return immutable_sections
    
    def _extract_sections_with_markers(self, content: str) -> Dict[str, str]:
        """提取带标记的章节"""
        sections = {}
        
        # 匹配带标记的标题
        header_pattern = r'^(#{1,6})\s*(\[不可修改\])?\s*(.+)$'
        current_section = "引言"
        current_content = []
        current_immutable = False
        
        for line in content.split('\n'):
            header_match = re.match(header_pattern, line, re.MULTILINE)
            if header_match:
                # 保存当前章节
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # 开始新章节
                current_immutable = bool(header_match.group(2))
                current_section = header_match.group(3).strip()
                current_content = []
            else:
                current_content.append(line)
        
        # 保存最后一个章节
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _is_immutable_section(self, section_name: str, section_content: str) -> bool:
        """判断章节是否为不可修改"""
        # 检查章节标题标记
        if "[不可修改]" in section_name:
            return True
        
        # 检查内容标记
        if "[不可修改]" in section_content:
            return True
        
        # 检查YAML前置元数据
        yaml_match = re.search(r'^---\n(.*?)\n---', section_content, re.DOTALL)
        if yaml_match:
            try:
                yaml_data = yaml.safe_load(yaml_match.group(1))
                if isinstance(yaml_data, dict) and "immutable_sections" in yaml_data:
                    immutable_sections = yaml_data["immutable_sections"]
                    if isinstance(immutable_sections, list) and section_name in immutable_sections:
                        return True
            except yaml.YAMLError:
                pass
        
        return False


class ModificationJustificationValidator:
    """修改依据验证器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def verify_modification_justification(self, user_prompt: str, modifications_made: List[Dict[str, Any]]) -> ValidationResult:
        """
        验证每个修改是否在用户提示中有明确依据
        """
        issues = []
        warnings = []
        modifications = []
        conservative_suggestions = []
        
        # 提取用户意图关键词
        user_intents = self._extract_user_intents(user_prompt)
        
        for modification in modifications_made:
            section = modification.get("section", "")
            change_type = modification.get("type", "")
            modified_content = modification.get("modified_text", "")
            
            # 验证修改依据
            justification = self._find_justification(user_prompt, user_intents, modification)
            
            if not justification:
                issues.append(f"章节 '{section}' 的修改缺乏用户提示依据")
                
                # 保守模式建议
                conservative_suggestions.append(
                    f"建议撤销或重新确认对章节 '{section}' 的修改"
                )
            else:
                # 记录有效的修改
                modifications.append({
                    "section": section,
                    "type": change_type,
                    "justification": justification,
                    "confidence": self._calculate_justification_confidence(justification, user_prompt)
                })
        
        # 计算总体置信度
        if modifications_made:
            justified_count = len(modifications)
            total_count = len(modifications_made)
            confidence = justified_count / total_count
        else:
            confidence = 1.0
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            confidence=confidence,
            issues=issues,
            warnings=warnings,
            modifications=modifications,
            conservative_suggestions=conservative_suggestions
        )
    
    def _extract_user_intents(self, user_prompt: str) -> List[str]:
        """提取用户意图关键词"""
        intents = []
        
        # 常见的修改意图关键词
        intent_patterns = {
            "修改": ["修改", "更改", "调整", "变更", "改动"],
            "添加": ["添加", "增加", "补充", "加入"],
            "删除": ["删除", "移除", "去掉", "去除"],
            "替换": ["替换", "换成", "改为"],
            "数值": ["浓度", "温度", "时间", "体积", "重量", "比例"],
            "试剂": ["培养基", "血清", "抗体", "酶", "缓冲液"],
            "设备": ["培养箱", "显微镜", "离心机", "PCR仪"]
        }
        
        for intent, keywords in intent_patterns.items():
            for keyword in keywords:
                if keyword in user_prompt:
                    intents.append(intent)
                    break
        
        return list(set(intents))  # 去重
    
    def _find_justification(self, user_prompt: str, user_intents: List[str], modification: Dict[str, Any]) -> Optional[str]:
        """查找修改的依据"""
        section = modification.get("section", "")
        modified_text = modification.get("modified_text", "")
        
        # 简单的关键词匹配
        for intent in user_intents:
            if intent.lower() in section.lower() or intent.lower() in modified_text.lower():
                return f"用户提示中包含{intent}意图"
        
        # 检查具体内容匹配
        user_words = set(user_prompt.lower().split())
        mod_words = set(modified_text.lower().split())
        
        common_words = user_words & mod_words
        if len(common_words) >= 2:  # 至少有2个共同词汇
            return f"与用户提示中的词汇匹配: {', '.join(common_words)}"
        
        return None
    
    def _calculate_justification_confidence(self, justification: str, user_prompt: str) -> float:
        """计算依据置信度"""
        if not justification:
            return 0.0
        
        # 基于依据类型计算置信度
        if "意图" in justification:
            return 0.8
        elif "词汇匹配" in justification:
            word_count = len(justification.split(":")[-1].split(","))
            return min(1.0, 0.3 + (word_count * 0.1))
        else:
            return 0.5


class AntiHallucinationValidator:
    """防幻觉验证器 - 主验证器"""
    
    def __init__(self, settings=None):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # 子验证器
        self.section_validator = SectionValidator()
        self.immutable_validator = ImmutableSectionValidator()
        self.justification_validator = ModificationJustificationValidator()
    
    def validate_revision(self, original_template: str, user_prompt: str, ai_output: str) -> ValidationResult:
        """
        验证AI输出是否超出模板范围
        """
        self.logger.info("开始防幻觉验证")
        
        # 1. 章节完整性检查
        section_result = self.section_validator.check_section_integrity(original_template, ai_output)
        
        # 2. 不可修改章节检查
        immutable_result = self.immutable_validator.check_immutable_sections(original_template, ai_output)
        
        # 3. 修改依据检查
        modifications_made = self._extract_modifications(original_template, ai_output)
        justification_result = self.justification_validator.verify_modification_justification(
            user_prompt, modifications_made
        )
        
        # 合并结果
        combined_result = self._combine_validation_results([
            section_result, immutable_result, justification_result
        ])
        
        self.logger.info(f"验证完成，置信度: {combined_result.confidence:.2f}")
        
        return combined_result
    
    def _extract_modifications(self, original: str, revised: str) -> List[Dict[str, Any]]:
        """提取修改详情"""
        modifications = []
        
        # 使用difflib找出差异
        original_lines = original.splitlines()
        revised_lines = revised.splitlines()
        
        differ = SequenceMatcher(None, original_lines, revised_lines)
        
        for tag, i1, i2, j1, j2 in differ.get_opcodes():
            if tag == 'replace':
                modifications.append({
                    "type": "replace",
                    "section": f"行 {i1+1}-{i2}",
                    "original_text": '\n'.join(original_lines[i1:i2]),
                    "modified_text": '\n'.join(revised_lines[j1:j2])
                })
            elif tag == 'delete':
                modifications.append({
                    "type": "delete",
                    "section": f"行 {i1+1}-{i2}",
                    "original_text": '\n'.join(original_lines[i1:i2]),
                    "modified_text": ""
                })
            elif tag == 'insert':
                modifications.append({
                    "type": "insert",
                    "section": f"行 {j1+1}-{j2}",
                    "original_text": "",
                    "modified_text": '\n'.join(revised_lines[j1:j2])
                })
        
        return modifications
    
    def _combine_validation_results(self, results: List[ValidationResult]) -> ValidationResult:
        """合并多个验证结果"""
        all_issues = []
        all_warnings = []
        all_modifications = []
        all_conservative_suggestions = []
        
        total_confidence = 0.0
        valid_count = 0
        
        for result in results:
            all_issues.extend(result.issues)
            all_warnings.extend(result.warnings)
            all_modifications.extend(result.modifications)
            all_conservative_suggestions.extend(result.conservative_suggestions)
            
            total_confidence += result.confidence
            valid_count += 1
        
        # 计算平均置信度
        average_confidence = total_confidence / valid_count if valid_count > 0 else 0.0
        
        # 如果有任何严重问题，整体验证失败
        is_valid = len(all_issues) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=average_confidence,
            issues=all_issues,
            warnings=all_warnings,
            modifications=all_modifications,
            conservative_suggestions=all_conservative_suggestions
        )


# 全局验证器实例
_global_validator = None


def get_validator(settings=None) -> AntiHallucinationValidator:
    """获取全局验证器实例"""
    global _global_validator
    if _global_validator is None:
        _global_validator = AntiHallucinationValidator(settings)
    return _global_validator