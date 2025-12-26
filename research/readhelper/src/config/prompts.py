"""
AI提示词模板
"""

from typing import Dict, Any


class PromptTemplates:
    """AI提示词模板类"""
    
    # 文献摘要模板
    SUMMARY_TEMPLATE = """
    请为以下生物科学文献生成一个简洁准确的摘要，突出研究目的、方法、主要发现和结论。

    文献标题：{title}
    作者：{authors}
    发表年份：{year}
    期刊：{journal}

    文献内容：
    {content}

    请生成一个{length}长度的摘要（中文），包含以下要素：
    1. 研究背景和目的
    2. 主要研究方法
    3. 关键发现和结果
    4. 研究结论和意义

    摘要：
    """
    
    # 关键词提取模板
    KEYWORDS_TEMPLATE = """
    请从以下生物科学文献中提取{max_count}个最重要的关键词或术语。

    文献标题：{title}
    摘要：{summary}
    正文内容（节选）：
    {content}

    请提取最能代表该文献研究主题和内容的关键词，按重要性排序。
    关键词应该是生物科学领域的专业术语，可以是：
    - 研究对象（如细胞类型、蛋白质、基因等）
    - 研究方法（如实验技术、分析方法等）
    - 研究领域（如疾病名称、生物过程等）
    - 重要概念或理论

    关键词（每行一个，按重要性排序）：
    """
    
    # 实体识别模板
    ENTITY_EXTRACTION_TEMPLATE = """
    请从以下生物科学文献中识别并提取重要的实体信息。

    文献内容：
    {content}

    请识别以下类型的实体，并按类别整理：
    1. 基因和蛋白质名称
    2. 细胞类型和组织
    3. 疾病名称
    4. 药物和化合物
    5. 实验技术和方法
    6. 生物过程和通路

    请以JSON格式返回结果：
    {{
        "genes_proteins": ["实体1", "实体2"],
        "cells_tissues": ["实体1", "实体2"],
        "diseases": ["实体1", "实体2"],
        "drugs_compounds": ["实体1", "实体2"],
        "techniques": ["实体1", "实体2"],
        "processes": ["实体1", "实体2"]
    }}
    """
    
    # 文献分类模板
    CLASSIFICATION_TEMPLATE = """
    请对以下生物科学文献进行分类。

    文献标题：{title}
    摘要：{summary}
    关键词：{keywords}

    请从以下维度对文献进行分类：

    1. 研究领域（如：分子生物学、细胞生物学、免疫学、神经科学、遗传学等）
    2. 研究类型（如：基础研究、应用研究、临床研究、综述等）
    3. 研究方法（如：实验研究、计算模拟、数据分析、文献综述等）
    4. 生物层级（如：分子、细胞、组织、器官、系统、群体等）

    请以JSON格式返回分类结果：
    {{
        "research_field": "主要研究领域",
        "research_type": "研究类型",
        "research_method": "主要研究方法",
        "biological_level": "生物层级",
        "confidence": 0.95
    }}
    """
    
    # 文献比较模板
    COMPARISON_TEMPLATE = """
    请比较以下两篇生物科学文献的相似性和差异性。

    文献1：
    标题：{title1}
    摘要：{summary1}
    关键词：{keywords1}

    文献2：
    标题：{title2}
    摘要：{summary2}
    关键词：{keywords2}

    请从以下方面进行比较分析：
    1. 研究主题的相似性
    2. 研究方法的异同
    3. 主要结论的一致性或差异性
    4. 两篇文献的关联性（是否相互引用、是否属于同一研究系列等）

    请提供一个0-1的相似度评分，并详细说明比较结果。
    """
    
    # 问答模板
    QA_TEMPLATE = """
    基于以下生物科学文献内容，请回答用户的问题。

    文献标题：{title}
    作者：{authors}
    发表年份：{year}
    期刊：{journal}

    文献内容：
    {content}

    用户问题：{question}

    请基于文献内容准确回答问题，如果文献中没有相关信息，请明确说明。
    回答应该：
    1. 准确反映文献内容
    2. 引用相关的具体内容或数据
    3. 如果需要，可以适当扩展背景知识
    4. 用中文回答

    回答：
    """
    
    # 推荐理由模板
    RECOMMENDATION_TEMPLATE = """
    基于用户的阅读历史和当前文献，请生成推荐理由。

    用户阅读历史关键词：{user_keywords}
    用户感兴趣领域：{user_interests}

    当前推荐文献：
    标题：{title}
    摘要：{summary}
    关键词：{keywords}

    请生成一个简洁的推荐理由，说明为什么这篇文献可能对用户有价值。
    推荐理由应该：
    1. 突出文献与用户兴趣的关联性
    2. 说明文献的新颖性或重要性
    3. 简洁明了，不超过100字

    推荐理由：
    """
    
    @classmethod
    def get_template(cls, template_name: str) -> str:
        """获取指定的提示词模板"""
        templates = {
            "summary": cls.SUMMARY_TEMPLATE,
            "keywords": cls.KEYWORDS_TEMPLATE,
            "entity_extraction": cls.ENTITY_EXTRACTION_TEMPLATE,
            "classification": cls.CLASSIFICATION_TEMPLATE,
            "comparison": cls.COMPARISON_TEMPLATE,
            "qa": cls.QA_TEMPLATE,
            "recommendation": cls.RECOMMENDATION_TEMPLATE
        }
        return templates.get(template_name, "")
    
    @classmethod
    def format_template(cls, template_name: str, **kwargs) -> str:
        """格式化指定的提示词模板"""
        template = cls.get_template(template_name)
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"模板参数缺失: {e}")