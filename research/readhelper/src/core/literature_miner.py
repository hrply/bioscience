"""
文献深度挖掘模块
"""

import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import logging

# 导入自定义模块
from .ragflow_client import RAGFlowClient, SearchResult, get_ragflow_client
from .llm_client import LLMClient, Message, get_llm_client, LLMResponse
from ..config.prompts import PromptTemplates

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ResearchTrend:
    """研究趋势"""
    topic: str
    trend: str  # increasing, decreasing, stable
    confidence: float
    evidence: List[str]
    time_period: str


@dataclass
class KnowledgeGap:
    """知识空白"""
    description: str
    importance: float
    research_opportunities: List[str]
    related_papers: List[str]


@dataclass
class ResearchNetwork:
    """研究网络"""
    authors: Dict[str, List[str]]  # 作者及其合作者
    institutions: Dict[str, List[str]]  # 机构及其合作机构
    topics: Dict[str, List[str]]  # 主题及其相关主题
    citations: Dict[str, List[str]]  # 论文及其引用的论文


@dataclass
class ConceptEvolution:
    """概念演化"""
    concept: str
    evolution_timeline: List[Tuple[str, str]]  # (时间, 描述)
    key_papers: List[str]
    related_concepts: List[str]


@dataclass
class LiteratureInsight:
    """文献洞察"""
    summary: str
    key_findings: List[str]
    research_trends: List[ResearchTrend]
    knowledge_gaps: List[KnowledgeGap]
    research_network: ResearchNetwork
    concept_evolutions: List[ConceptEvolution]
    recommendations: List[str]


class LiteratureMiner:
    """文献深度挖掘器"""
    
    def __init__(self, ragflow_client: Optional[RAGFlowClient] = None, 
                 llm_client: Optional[LLMClient] = None):
        self.ragflow_client = ragflow_client or get_ragflow_client()
        self.llm_client = llm_client or get_llm_client()
    
    def mine_literature(self, dataset_id: str, research_topic: str, 
                       analysis_scope: str = "comprehensive") -> LiteratureInsight:
        """深度挖掘文献"""
        logger.info(f"开始深度挖掘文献: {research_topic}")
        
        # 1. 获取相关文献
        relevant_docs = self._get_relevant_documents(dataset_id, research_topic)
        
        # 2. 生成总体摘要
        summary = self._generate_summary(relevant_docs, research_topic)
        
        # 3. 提取关键发现
        key_findings = self._extract_key_findings(relevant_docs, research_topic)
        
        # 4. 分析研究趋势
        research_trends = self._analyze_research_trends(relevant_docs, research_topic)
        
        # 5. 识别知识空白
        knowledge_gaps = self._identify_knowledge_gaps(relevant_docs, research_topic)
        
        # 6. 构建研究网络
        research_network = self._build_research_network(relevant_docs)
        
        # 7. 分析概念演化
        concept_evolutions = self._analyze_concept_evolution(relevant_docs, research_topic)
        
        # 8. 生成研究建议
        recommendations = self._generate_recommendations(
            research_trends, knowledge_gaps, research_network, research_topic
        )
        
        return LiteratureInsight(
            summary=summary,
            key_findings=key_findings,
            research_trends=research_trends,
            knowledge_gaps=knowledge_gaps,
            research_network=research_network,
            concept_evolutions=concept_evolutions,
            recommendations=recommendations
        )
    
    def _get_relevant_documents(self, dataset_id: str, research_topic: str, 
                              max_docs: int = 50) -> List[SearchResult]:
        """获取相关文献"""
        try:
            # 使用RAGFlow搜索相关文献
            search_results = self.ragflow_client.search(
                dataset_id=dataset_id,
                query=research_topic,
                top_k=max_docs,
                similarity_threshold=0.6
            )
            return search_results
        except Exception as e:
            logger.error(f"获取相关文献失败: {e}")
            return []
    
    def _generate_summary(self, documents: List[SearchResult], research_topic: str) -> str:
        """生成文献摘要"""
        if not documents:
            return "未找到相关文献"
        
        # 准备文档内容
        doc_contents = []
        for i, doc in enumerate(documents[:10]):  # 限制文档数量以避免token过多
            doc_contents.append(f"文献{i+1}: {doc.content[:1000]}...")  # 截取前1000字符
        
        context = "\n\n".join(doc_contents)
        
        # 构建提示词
        prompt = PromptTemplates.format_template(
            "summary",
            title=research_topic,
            authors="",
            year="",
            journal="",
            content=context,
            length="中等长度"
        )
        
        messages = [
            Message(role="system", content="你是一个专业的生物科学文献分析专家，擅长总结和分析科学文献。"),
            Message(role="user", content=prompt)
        ]
        
        try:
            response = self.llm_client.chat(messages)
            return response.content
        except Exception as e:
            logger.error(f"生成摘要失败: {e}")
            return "摘要生成失败"
    
    def _extract_key_findings(self, documents: List[SearchResult], research_topic: str) -> List[str]:
        """提取关键发现"""
        if not documents:
            return []
        
        # 准备文档内容
        doc_contents = []
        for i, doc in enumerate(documents[:15]):  # 限制文档数量
            doc_contents.append(f"文献{i+1}: {doc.content[:800]}...")  # 截取前800字符
        
        context = "\n\n".join(doc_contents)
        
        # 构建提示词
        prompt = f"""
        基于以下关于"{research_topic}"的文献内容，提取5-7个最重要的关键发现或结论。
        每个发现应该简洁明了，基于文献内容，具有科学价值。
        
        文献内容：
        {context}
        
        请以编号列表形式返回关键发现：
        """
        
        messages = [
            Message(role="system", content="你是一个专业的生物科学文献分析专家，擅长提取科学文献中的关键发现。"),
            Message(role="user", content=prompt)
        ]
        
        try:
            response = self.llm_client.chat(messages)
            findings_text = response.content
            
            # 解析关键发现
            findings = []
            lines = findings_text.split('\n')
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    # 移除编号和符号
                    finding = re.sub(r'^\d+\.?\s*|[-•]\s*', '', line).strip()
                    if finding and len(finding) > 10:
                        findings.append(finding)
            
            return findings[:7]  # 最多返回7个关键发现
        except Exception as e:
            logger.error(f"提取关键发现失败: {e}")
            return []
    
    def _analyze_research_trends(self, documents: List[SearchResult], research_topic: str) -> List[ResearchTrend]:
        """分析研究趋势"""
        if not documents:
            return []
        
        # 准备文档内容和元数据
        doc_contents = []
        for i, doc in enumerate(documents):
            # 尝试从文档内容中提取年份
            year_match = re.search(r'\b(19|20)\d{2}\b', doc.content)
            year = year_match.group() if year_match else "未知"
            
            doc_contents.append(f"文献{i+1} ({year}): {doc.content[:600]}...")
        
        context = "\n\n".join(doc_contents)
        
        # 构建提示词
        prompt = f"""
        基于以下关于"{research_topic}"的文献内容，分析研究趋势。
        识别3-5个主要的研究主题或方向，并分析它们的发展趋势（增长、减少、稳定）。
        为每个趋势提供证据支持，并尽可能确定时间周期。
        
        文献内容：
        {context}
        
        请以JSON格式返回结果：
        {{
            "trends": [
                {{
                    "topic": "研究主题",
                    "trend": "increasing/decreasing/stable",
                    "confidence": 0.8,
                    "evidence": ["证据1", "证据2"],
                    "time_period": "时间周期"
                }}
            ]
        }}
        """
        
        messages = [
            Message(role="system", content="你是一个专业的生物科学文献分析专家，擅长分析研究趋势。"),
            Message(role="user", content=prompt)
        ]
        
        try:
            response = self.llm_client.chat(messages)
            result_text = response.content
            
            # 尝试解析JSON
            try:
                result = json.loads(result_text)
                trends_data = result.get("trends", [])
            except json.JSONDecodeError:
                # 如果JSON解析失败，尝试文本解析
                trends_data = self._parse_trends_from_text(result_text)
            
            # 转换为ResearchTrend对象
            trends = []
            for trend_data in trends_data:
                trend = ResearchTrend(
                    topic=trend_data.get("topic", ""),
                    trend=trend_data.get("trend", "stable"),
                    confidence=trend_data.get("confidence", 0.5),
                    evidence=trend_data.get("evidence", []),
                    time_period=trend_data.get("time_period", "")
                )
                trends.append(trend)
            
            return trends
        except Exception as e:
            logger.error(f"分析研究趋势失败: {e}")
            return []
    
    def _parse_trends_from_text(self, text: str) -> List[Dict]:
        """从文本中解析趋势信息"""
        trends = []
        lines = text.split('\n')
        current_trend = {}
        
        for line in lines:
            line = line.strip()
            if "主题" in line or "topic" in line.lower():
                if current_trend:
                    trends.append(current_trend)
                current_trend = {"topic": line.split(':', 1)[-1].strip()}
            elif "趋势" in line or "trend" in line.lower():
                current_trend["trend"] = line.split(':', 1)[-1].strip()
            elif "置信度" in line or "confidence" in line.lower():
                try:
                    confidence = float(re.search(r'\d+\.?\d*', line).group())
                    current_trend["confidence"] = confidence
                except:
                    current_trend["confidence"] = 0.5
            elif "证据" in line or "evidence" in line.lower():
                evidence = line.split(':', 1)[-1].strip()
                current_trend["evidence"] = [evidence]
            elif "时间" in line or "period" in line.lower():
                current_trend["time_period"] = line.split(':', 1)[-1].strip()
        
        if current_trend:
            trends.append(current_trend)
        
        return trends
    
    def _identify_knowledge_gaps(self, documents: List[SearchResult], research_topic: str) -> List[KnowledgeGap]:
        """识别知识空白"""
        if not documents:
            return []
        
        # 准备文档内容
        doc_contents = []
        for i, doc in enumerate(documents[:12]):  # 限制文档数量
            doc_contents.append(f"文献{i+1}: {doc.content[:800]}...")
        
        context = "\n\n".join(doc_contents)
        
        # 构建提示词
        prompt = f"""
        基于以下关于"{research_topic}"的文献内容，识别3-5个知识空白或研究不足的领域。
        对于每个知识空白，描述其重要性（0-1评分），并提出可能的研究机会。
        
        文献内容：
        {context}
        
        请以JSON格式返回结果：
        {{
            "knowledge_gaps": [
                {{
                    "description": "知识空白描述",
                    "importance": 0.8,
                    "research_opportunities": ["机会1", "机会2"],
                    "related_papers": ["相关论文1", "相关论文2"]
                }}
            ]
        }}
        """
        
        messages = [
            Message(role="system", content="你是一个专业的生物科学文献分析专家，擅长识别研究中的知识空白。"),
            Message(role="user", content=prompt)
        ]
        
        try:
            response = self.llm_client.chat(messages)
            result_text = response.content
            
            # 尝试解析JSON
            try:
                result = json.loads(result_text)
                gaps_data = result.get("knowledge_gaps", [])
            except json.JSONDecodeError:
                # 如果JSON解析失败，返回空列表
                gaps_data = []
            
            # 转换为KnowledgeGap对象
            knowledge_gaps = []
            for gap_data in gaps_data:
                gap = KnowledgeGap(
                    description=gap_data.get("description", ""),
                    importance=gap_data.get("importance", 0.5),
                    research_opportunities=gap_data.get("research_opportunities", []),
                    related_papers=gap_data.get("related_papers", [])
                )
                knowledge_gaps.append(gap)
            
            return knowledge_gaps
        except Exception as e:
            logger.error(f"识别知识空白失败: {e}")
            return []
    
    def _build_research_network(self, documents: List[SearchResult]) -> ResearchNetwork:
        """构建研究网络"""
        authors_dict = defaultdict(list)
        institutions_dict = defaultdict(list)
        topics_dict = defaultdict(list)
        citations_dict = defaultdict(list)
        
        for doc in documents:
            # 提取作者信息
            authors = self._extract_authors(doc.content)
            for author in authors:
                # 查找合作者
                co_authors = [a for a in authors if a != author]
                authors_dict[author].extend(co_authors)
            
            # 提取机构信息
            institutions = self._extract_institutions(doc.content)
            for institution in institutions:
                # 查找合作机构
                co_institutions = [inst for inst in institutions if inst != institution]
                institutions_dict[institution].extend(co_institutions)
            
            # 提取主题信息
            topics = self._extract_topics(doc.content)
            for topic in topics:
                # 查找相关主题
                related_topics = [t for t in topics if t != topic]
                topics_dict[topic].extend(related_topics)
            
            # 提取引用信息
            citations = self._extract_citations(doc.content)
            citations_dict[doc.document_name] = citations
        
        # 去重
        for key in authors_dict:
            authors_dict[key] = list(set(authors_dict[key]))
        
        for key in institutions_dict:
            institutions_dict[key] = list(set(institutions_dict[key]))
        
        for key in topics_dict:
            topics_dict[key] = list(set(topics_dict[key]))
        
        return ResearchNetwork(
            authors=dict(authors_dict),
            institutions=dict(institutions_dict),
            topics=dict(topics_dict),
            citations=dict(citations_dict)
        )
    
    def _extract_authors(self, content: str) -> List[str]:
        """提取作者信息"""
        # 简单的作者提取逻辑
        authors = []
        
        # 常见作者模式
        author_patterns = [
            r'([A-Z][a-z]+ [A-Z][a-z]+)',  # 名字 姓氏
            r'([A-Z]\. [A-Z][a-z]+)',     # 首字母. 姓氏
            r'([A-Z][a-z]+, [A-Z]\.)',     # 姓氏, 首字母.
        ]
        
        for pattern in author_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if len(match.split()) >= 2 and len(match) < 30:
                    authors.append(match)
        
        # 限制作者数量
        return list(set(authors))[:10]
    
    def _extract_institutions(self, content: str) -> List[str]:
        """提取机构信息"""
        institutions = []
        
        # 常见机构关键词
        institution_keywords = [
            'University', 'Institute', 'College', 'Hospital', 'Medical Center',
            'Laboratory', 'Research Center', 'School of', 'Department of',
            '大学', '学院', '研究所', '医院', '实验室', '研究中心'
        ]
        
        lines = content.split('\n')
        for line in lines:
            for keyword in institution_keywords:
                if keyword in line:
                    # 提取包含关键词的短语
                    institution = line.strip()
                    if len(institution) < 100 and len(institution) > 10:
                        institutions.append(institution)
        
        return list(set(institutions))[:5]
    
    def _extract_topics(self, content: str) -> List[str]:
        """提取主题信息"""
        topics = []
        
        # 使用关键词提取
        prompt = f"""
        从以下文本中提取5-7个主要的研究主题或关键词：
        
        {content[:1000]}
        
        请以逗号分隔的形式返回主题：
        """
        
        messages = [
            Message(role="system", content="你是一个专业的生物科学文献分析专家，擅长提取研究主题。"),
            Message(role="user", content=prompt)
        ]
        
        try:
            response = self.llm_client.chat(messages)
            topics_text = response.content
            topics = [topic.strip() for topic in topics_text.split(',') if topic.strip()]
        except Exception as e:
            logger.error(f"提取主题失败: {e}")
        
        return topics[:7]
    
    def _extract_citations(self, content: str) -> List[str]:
        """提取引用信息"""
        citations = []
        
        # 简单的引用模式
        citation_patterns = [
            r'\[(\d+)\]',  # [1], [2], etc.
            r'\(([^)]+\d{4}[^)]*)\)',  # (Author, Year)
            r'(\d{4})',  # 年份
        ]
        
        for pattern in citation_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, str) and len(match) < 50:
                    citations.append(match)
        
        return list(set(citations))[:10]
    
    def _analyze_concept_evolution(self, documents: List[SearchResult], research_topic: str) -> List[ConceptEvolution]:
        """分析概念演化"""
        if not documents:
            return []
        
        # 准备文档内容
        doc_contents = []
        for i, doc in enumerate(documents):
            # 尝试从文档内容中提取年份
            year_match = re.search(r'\b(19|20)\d{2}\b', doc.content)
            year = year_match.group() if year_match else "未知"
            
            doc_contents.append(f"文献{i+1} ({year}): {doc.content[:600]}...")
        
        context = "\n\n".join(doc_contents)
        
        # 构建提示词
        prompt = f"""
        基于以下关于"{research_topic}"的文献内容，分析2-3个关键概念的演化过程。
        对于每个概念，识别其发展时间线、关键论文和相关概念。
        
        文献内容：
        {context}
        
        请以JSON格式返回结果：
        {{
            "concepts": [
                {{
                    "concept": "概念名称",
                    "evolution_timeline": [["时间1", "描述1"], ["时间2", "描述2"]],
                    "key_papers": ["论文1", "论文2"],
                    "related_concepts": ["相关概念1", "相关概念2"]
                }}
            ]
        }}
        """
        
        messages = [
            Message(role="system", content="你是一个专业的生物科学文献分析专家，擅长分析概念演化。"),
            Message(role="user", content=prompt)
        ]
        
        try:
            response = self.llm_client.chat(messages)
            result_text = response.content
            
            # 尝试解析JSON
            try:
                result = json.loads(result_text)
                concepts_data = result.get("concepts", [])
            except json.JSONDecodeError:
                # 如果JSON解析失败，返回空列表
                concepts_data = []
            
            # 转换为ConceptEvolution对象
            concept_evolutions = []
            for concept_data in concepts_data:
                evolution = ConceptEvolution(
                    concept=concept_data.get("concept", ""),
                    evolution_timeline=concept_data.get("evolution_timeline", []),
                    key_papers=concept_data.get("key_papers", []),
                    related_concepts=concept_data.get("related_concepts", [])
                )
                concept_evolutions.append(evolution)
            
            return concept_evolutions
        except Exception as e:
            logger.error(f"分析概念演化失败: {e}")
            return []
    
    def _generate_recommendations(self, research_trends: List[ResearchTrend], 
                                 knowledge_gaps: List[KnowledgeGap],
                                 research_network: ResearchNetwork,
                                 research_topic: str) -> List[str]:
        """生成研究建议"""
        if not research_trends and not knowledge_gaps:
            return []
        
        # 准备数据
        trends_summary = "\n".join([f"- {t.topic}: {t.trend}" for t in research_trends])
        gaps_summary = "\n".join([f"- {g.description}" for g in knowledge_gaps])
        
        # 构建提示词
        prompt = f"""
        基于以下关于"{research_topic}"的分析结果，生成5-7个具体的研究建议。
        
        研究趋势：
        {trends_summary}
        
        知识空白：
        {gaps_summary}
        
        请生成具体、可行的研究建议，每个建议应该：
        1. 基于分析结果
        2. 具有实际可行性
        3. 简洁明了
        4. 有科学价值
        
        请以编号列表形式返回建议：
        """
        
        messages = [
            Message(role="system", content="你是一个专业的生物科学文献分析专家，擅长生成研究建议。"),
            Message(role="user", content=prompt)
        ]
        
        try:
            response = self.llm_client.chat(messages)
            recommendations_text = response.content
            
            # 解析建议
            recommendations = []
            lines = recommendations_text.split('\n')
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    # 移除编号和符号
                    recommendation = re.sub(r'^\d+\.?\s*|[-•]\s*', '', line).strip()
                    if recommendation and len(recommendation) > 10:
                        recommendations.append(recommendation)
            
            return recommendations[:7]  # 最多返回7个建议
        except Exception as e:
            logger.error(f"生成研究建议失败: {e}")
            return []
    
    def compare_literature_sets(self, dataset_id: str, topic1: str, topic2: str) -> Dict[str, Any]:
        """比较两个文献集合"""
        # 获取两个主题的相关文献
        docs1 = self._get_relevant_documents(dataset_id, topic1)
        docs2 = self._get_relevant_documents(dataset_id, topic2)
        
        # 生成比较分析
        comparison_prompt = f"""
        比较以下两个研究主题的文献集合：
        
        主题1: {topic1}
        文献数量: {len(docs1)}
        
        主题2: {topic2}
        文献数量: {len(docs2)}
        
        请从以下方面进行比较：
        1. 研究方法差异
        2. 研究焦点差异
        3. 发展趋势差异
        4. 可能的交叉点
        
        请提供详细的比较分析。
        """
        
        messages = [
            Message(role="system", content="你是一个专业的生物科学文献分析专家，擅长比较不同研究领域。"),
            Message(role="user", content=comparison_prompt)
        ]
        
        try:
            response = self.llm_client.chat(messages)
            return {
                "topic1": topic1,
                "topic2": topic2,
                "topic1_doc_count": len(docs1),
                "topic2_doc_count": len(docs2),
                "comparison": response.content
            }
        except Exception as e:
            logger.error(f"文献集合比较失败: {e}")
            return {"error": str(e)}


# 全局文献挖掘器实例
literature_miner = None


def get_literature_miner(ragflow_client: Optional[RAGFlowClient] = None, 
                        llm_client: Optional[LLMClient] = None) -> LiteratureMiner:
    """获取文献挖掘器实例"""
    global literature_miner
    if literature_miner is None:
        literature_miner = LiteratureMiner(ragflow_client, llm_client)
    return literature_miner