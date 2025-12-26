"""
文献深度挖掘页面模块
"""

import streamlit as st
import sys
import json
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import pandas as pd

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import settings


def mining_page():
    """文献深度挖掘页面内容"""
    st.title("⛏️ 文献深度挖掘")
    
    # 检查是否选择了数据集
    if not st.session_state.get('current_dataset'):
        st.error("请先在文献库页面选择一个数据集")
        return
    
    # 挖掘配置
    st.markdown("## ⚙️ 挖掘配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        research_topic = st.text_input(
            "研究主题",
            placeholder="例如：肿瘤免疫治疗、CRISPR基因编辑、蛋白质折叠预测",
            help="输入您感兴趣的研究主题，系统将围绕此主题进行深度分析"
        )
        
        analysis_scope = st.selectbox(
            "分析范围",
            ["全面分析", "快速分析", "趋势分析", "知识空白分析"],
            index=0,
            help="选择分析的深度和范围"
        )
    
    with col2:
        max_docs = st.slider(
            "最大文档数量",
            min_value=10,
            max_value=100,
            value=50,
            step=10,
            help="用于分析的最大文档数量，数量越多分析越全面但耗时越长"
        )
        
        similarity_threshold = st.slider(
            "相似度阈值",
            min_value=0.5,
            max_value=0.9,
            value=0.6,
            step=0.05,
            help="筛选相关文档的相似度阈值"
        )
    
    # 开始挖掘按钮
    if st.button("🚀 开始挖掘", key="start_mining", type="primary"):
        if not research_topic:
            st.error("请输入研究主题")
        else:
            perform_mining(research_topic, analysis_scope, max_docs, similarity_threshold)
    
    # 显示历史挖掘结果
    if 'mining_results' in st.session_state and st.session_state.mining_results:
        st.markdown("---")
        st.markdown("## 📊 最新挖掘结果")
        display_mining_results(st.session_state.mining_results)


def perform_mining(research_topic, analysis_scope, max_docs, similarity_threshold):
    """执行文献挖掘"""
    with st.spinner(f"正在对'{research_topic}'进行深度挖掘，请稍候..."):
        try:
            # 调用文献挖掘器
            miner = st.session_state.literature_miner
            
            # 根据分析范围调整参数
            if analysis_scope == "快速分析":
                max_docs = min(max_docs, 20)
            elif analysis_scope == "趋势分析":
                max_docs = min(max_docs, 40)
            elif analysis_scope == "知识空白分析":
                max_docs = min(max_docs, 30)
            
            # 执行挖掘
            results = miner.mine_literature(
                dataset_id=st.session_state.current_dataset,
                research_topic=research_topic,
                analysis_scope=analysis_scope.lower()
            )
            
            # 保存结果到会话状态
            st.session_state.mining_results = {
                'topic': research_topic,
                'scope': analysis_scope,
                'results': results,
                'timestamp': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            st.success("文献挖掘完成！")
            
        except Exception as e:
            st.error(f"文献挖掘失败: {e}")
            return
    
    # 显示结果
    display_mining_results(st.session_state.mining_results)


def display_mining_results(mining_data):
    """显示挖掘结果"""
    if not mining_data:
        return
    
    topic = mining_data['topic']
    scope = mining_data['scope']
    results = mining_data['results']
    timestamp = mining_data['timestamp']
    
    st.markdown(f"### 📋 分析主题: {topic}")
    st.markdown(f"**分析范围**: {scope}")
    st.markdown(f"**分析时间**: {timestamp}")
    
    # 总体摘要
    if results.summary:
        st.markdown("---")
        st.markdown("## 📝 总体摘要")
        st.info(results.summary)
    
    # 关键发现
    if results.key_findings:
        st.markdown("---")
        st.markdown("## 🔍 关键发现")
        
        for i, finding in enumerate(results.key_findings, 1):
            st.markdown(f"{i}. {finding}")
    
    # 研究趋势
    if results.research_trends:
        st.markdown("---")
        st.markdown("## 📈 研究趋势")
        
        # 创建趋势可视化
        trend_data = []
        for trend in results.research_trends:
            trend_data.append({
                '主题': trend.topic,
                '趋势': trend.trend,
                '置信度': trend.confidence,
                '时间周期': trend.time_period
            })
        
        if trend_data:
            df_trends = pd.DataFrame(trend_data)
            
            # 趋势条形图
            fig = px.bar(
                df_trends,
                x='主题',
                y='置信度',
                color='趋势',
                title="研究趋势分析",
                color_discrete_map={
                    'increasing': 'green',
                    'decreasing': 'red',
                    'stable': 'blue'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 趋势详情
            for i, trend in enumerate(results.research_trends):
                with st.expander(f"📊 {trend.topic} ({trend.trend})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("趋势方向", trend.trend)
                        st.metric("置信度", f"{trend.confidence:.2f}")
                    
                    with col2:
                        st.metric("时间周期", trend.time_period)
                        st.metric("证据数量", len(trend.evidence))
                    
                    if trend.evidence:
                        st.markdown("**支持证据**:")
                        for evidence in trend.evidence:
                            st.markdown(f"- {evidence}")
    
    # 知识空白
    if results.knowledge_gaps:
        st.markdown("---")
        st.markdown("## 🕳️ 知识空白")
        
        # 创建重要性排序
        gap_data = []
        for gap in results.knowledge_gaps:
            gap_data.append({
                '描述': gap.description[:50] + "..." if len(gap.description) > 50 else gap.description,
                '重要性': gap.importance,
                '机会数量': len(gap.research_opportunities)
            })
        
        if gap_data:
            df_gaps = pd.DataFrame(gap_data)
            
            # 重要性散点图
            fig = px.scatter(
                df_gaps,
                x='描述',
                y='重要性',
                size='机会数量',
                title="知识空白分析 (气泡大小表示研究机会数量)",
                hover_data=['机会数量']
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            # 知识空白详情
            for i, gap in enumerate(results.knowledge_gaps):
                with st.expander(f"🕳️ {gap.description[:50]}..."):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("重要性", f"{gap.importance:.2f}")
                        st.metric("研究机会", len(gap.research_opportunities))
                    
                    with col2:
                        st.metric("相关论文", len(gap.related_papers))
                    
                    if gap.research_opportunities:
                        st.markdown("**研究机会**:")
                        for opportunity in gap.research_opportunities:
                            st.markdown(f"- {opportunity}")
    
    # 研究网络
    if results.research_network:
        st.markdown("---")
        st.markdown("## 🌐 研究网络")
        
        network = results.research_network
        
        # 网络统计
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("作者数量", len(network.authors))
        
        with col2:
            st.metric("机构数量", len(network.institutions))
        
        with col3:
            st.metric("主题数量", len(network.topics))
        
        with col4:
            st.metric("引用关系", len(network.citations))
        
        # 网络详情标签页
        tab1, tab2, tab3 = st.tabs(["作者网络", "机构网络", "主题网络"])
        
        with tab1:
            if network.authors:
                st.markdown("### 👥 作者合作网络")
                
                # 显示合作最多的作者
                author_collaborations = {author: len(collaborators) for author, collaborators in network.authors.items()}
                top_authors = sorted(author_collaborations.items(), key=lambda x: x[1], reverse=True)[:10]
                
                if top_authors:
                    df_authors = pd.DataFrame(top_authors, columns=['作者', '合作者数量'])
                    fig = px.bar(df_authors, x='作者', y='合作者数量', title="合作最多的作者")
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                
                # 作者合作详情
                selected_author = st.selectbox("选择作者查看合作网络", options=list(network.authors.keys()))
                
                if selected_author and network.authors[selected_author]:
                    st.markdown(f"**{selected_author} 的合作者**:")
                    collaborators = network.authors[selected_author]
                    for collaborator in collaborators:
                        st.markdown(f"- {collaborator}")
        
        with tab2:
            if network.institutions:
                st.markdown("### 🏢 机构合作网络")
                
                # 显示合作最多的机构
                institution_collaborations = {inst: len(collaborators) for inst, collaborators in network.institutions.items()}
                top_institutions = sorted(institution_collaborations.items(), key=lambda x: x[1], reverse=True)[:10]
                
                if top_institutions:
                    df_institutions = pd.DataFrame(top_institutions, columns=['机构', '合作机构数量'])
                    fig = px.bar(df_institutions, x='机构', y='合作机构数量', title="合作最多的机构")
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                
                # 机构合作详情
                selected_institution = st.selectbox("选择机构查看合作网络", options=list(network.institutions.keys()))
                
                if selected_institution and network.institutions[selected_institution]:
                    st.markdown(f"**{selected_institution} 的合作机构**:")
                    collaborators = network.institutions[selected_institution]
                    for collaborator in collaborators:
                        st.markdown(f"- {collaborator}")
        
        with tab3:
            if network.topics:
                st.markdown("### 🏷️ 主题关联网络")
                
                # 显示关联最多的主题
                topic_connections = {topic: len(connections) for topic, connections in network.topics.items()}
                top_topics = sorted(topic_connections.items(), key=lambda x: x[1], reverse=True)[:10]
                
                if top_topics:
                    df_topics = pd.DataFrame(top_topics, columns=['主题', '相关主题数量'])
                    fig = px.bar(df_topics, x='主题', y='相关主题数量', title="关联最多的主题")
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                
                # 主题关联详情
                selected_topic = st.selectbox("选择主题查看关联网络", options=list(network.topics.keys()))
                
                if selected_topic and network.topics[selected_topic]:
                    st.markdown(f"**{selected_topic} 的相关主题**:")
                    related_topics = network.topics[selected_topic]
                    for topic in related_topics:
                        st.markdown(f"- {topic}")
    
    # 概念演化
    if results.concept_evolutions:
        st.markdown("---")
        st.markdown("## 🔄 概念演化")
        
        for i, evolution in enumerate(results.concept_evolutions):
            with st.expander(f"🔄 {evolution.concept}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("关键论文数量", len(evolution.key_papers))
                    st.metric("相关概念数量", len(evolution.related_concepts))
                
                with col2:
                    if evolution.evolution_timeline:
                        st.metric("时间跨度", 
                                f"{evolution.evolution_timeline[0][0]} - {evolution.evolution_timeline[-1][0]}")
                
                # 演化时间线
                if evolution.evolution_timeline:
                    st.markdown("**演化时间线**:")
                    timeline_data = []
                    for time_point, description in evolution.evolution_timeline:
                        timeline_data.append({
                            '时间': time_point,
                            '事件': description[:50] + "..." if len(description) > 50 else description
                        })
                    
                    df_timeline = pd.DataFrame(timeline_data)
                    st.dataframe(df_timeline, use_container_width=True)
                
                # 关键论文
                if evolution.key_papers:
                    st.markdown("**关键论文**:")
                    for paper in evolution.key_papers:
                        st.markdown(f"- {paper}")
                
                # 相关概念
                if evolution.related_concepts:
                    st.markdown("**相关概念**:")
                    for concept in evolution.related_concepts:
                        st.markdown(f"- {concept}")
    
    # 研究建议
    if results.recommendations:
        st.markdown("---")
        st.markdown("## 💡 研究建议")
        
        for i, recommendation in enumerate(results.recommendations, 1):
            st.markdown(f"{i}. {recommendation}")
    
    # 导出结果
    st.markdown("---")
    st.markdown("## 📤 导出结果")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("导出为JSON", key="export_json"):
            export_data = {
                'topic': topic,
                'scope': scope,
                'timestamp': timestamp,
                'summary': results.summary,
                'key_findings': results.key_findings,
                'recommendations': results.recommendations
            }
            
            json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
            st.download_button(
                label="下载JSON文件",
                data=json_str,
                file_name=f"literature_mining_{topic.replace(' ', '_')}_{timestamp.replace(':', '-')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("导出为报告", key="export_report"):
            # 生成文本报告
            report = generate_text_report(mining_data)
            st.download_button(
                label="下载文本报告",
                data=report,
                file_name=f"literature_mining_report_{topic.replace(' ', '_')}_{timestamp.replace(':', '-')}.txt",
                mime="text/plain"
            )


def generate_text_report(mining_data):
    """生成文本报告"""
    topic = mining_data['topic']
    scope = mining_data['scope']
    results = mining_data['results']
    timestamp = mining_data['timestamp']
    
    report = f"""
文献深度挖掘报告
================

分析主题: {topic}
分析范围: {scope}
生成时间: {timestamp}

1. 总体摘要
-----------
{results.summary}

2. 关键发现
-----------
"""
    
    for i, finding in enumerate(results.key_findings, 1):
        report += f"{i}. {finding}\n"
    
    if results.research_trends:
        report += "\n3. 研究趋势\n-----------\n"
        for i, trend in enumerate(results.research_trends, 1):
            report += f"{i}. {trend.topic}\n"
            report += f"   趋势: {trend.trend}\n"
            report += f"   置信度: {trend.confidence:.2f}\n"
            report += f"   时间周期: {trend.time_period}\n"
            if trend.evidence:
                report += "   支持证据:\n"
                for evidence in trend.evidence:
                    report += f"   - {evidence}\n"
            report += "\n"
    
    if results.knowledge_gaps:
        report += "4. 知识空白\n-----------\n"
        for i, gap in enumerate(results.knowledge_gaps, 1):
            report += f"{i}. {gap.description}\n"
            report += f"   重要性: {gap.importance:.2f}\n"
            if gap.research_opportunities:
                report += "   研究机会:\n"
                for opportunity in gap.research_opportunities:
                    report += f"   - {opportunity}\n"
            report += "\n"
    
    if results.recommendations:
        report += "5. 研究建议\n-----------\n"
        for i, recommendation in enumerate(results.recommendations, 1):
            report += f"{i}. {recommendation}\n"
    
    report += "\n报告结束\n"
    
    return report