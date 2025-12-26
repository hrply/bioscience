"""
智能搜索页面模块
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import settings


def search_page():
    """智能搜索页面内容"""
    st.title("🔍 智能搜索")
    
    # 检查是否选择了数据集
    if not st.session_state.get('current_dataset'):
        st.error("请先在文献库页面选择一个数据集")
        return
    
    # 搜索配置
    st.markdown("## ⚙️ 搜索配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        search_type = st.selectbox(
            "搜索类型",
            ["语义搜索", "关键词搜索", "对话式搜索", "比较搜索"],
            index=0,
            help="选择搜索方式：语义搜索基于内容相似度，关键词搜索基于精确匹配"
        )
        
        top_k = st.slider(
            "返回结果数量",
            min_value=1,
            max_value=20,
            value=5,
            help="返回的搜索结果数量"
        )
    
    with col2:
        similarity_threshold = st.slider(
            "相似度阈值",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.05,
            help="筛选相关文档的相似度阈值，越高越严格"
        )
        
        include_metadata = st.checkbox(
            "包含元数据",
            value=True,
            help="是否在搜索结果中显示文档元数据"
        )
    
    # 根据搜索类型显示不同的搜索界面
    if search_type == "语义搜索":
        semantic_search_ui(top_k, similarity_threshold, include_metadata)
    elif search_type == "关键词搜索":
        keyword_search_ui(top_k, include_metadata)
    elif search_type == "对话式搜索":
        conversational_search_ui()
    elif search_type == "比较搜索":
        comparative_search_ui()


def semantic_search_ui(top_k, similarity_threshold, include_metadata):
    """语义搜索界面"""
    st.markdown("### 🔍 语义搜索")
    
    query = st.text_input(
        "搜索查询",
        placeholder="输入您的问题或搜索内容，例如：CRISPR技术在癌症治疗中的应用",
        help="使用自然语言描述您的搜索需求"
    )
    
    if st.button("🔍 搜索", key="semantic_search"):
        if not query:
            st.error("请输入搜索查询")
        else:
            perform_semantic_search(query, top_k, similarity_threshold, include_metadata)


def perform_semantic_search(query, top_k, similarity_threshold, include_metadata):
    """执行语义搜索"""
    with st.spinner("正在搜索相关文献..."):
        try:
            results = st.session_state.ragflow_client.search(
                dataset_id=st.session_state.current_dataset,
                query=query,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )
            
            if results:
                st.success(f"找到 {len(results)} 个相关文档")
                display_search_results(results, include_metadata)
            else:
                st.info("未找到相关文档，请尝试调整搜索词或降低相似度阈值")
                
        except Exception as e:
            st.error(f"搜索失败: {e}")


def keyword_search_ui(top_k, include_metadata):
    """关键词搜索界面"""
    st.markdown("### 🔍 关键词搜索")
    
    col1, col2 = st.columns(2)
    
    with col1:
        keywords = st.text_input(
            "关键词",
            placeholder="输入关键词，用逗号分隔，例如：免疫治疗,PD-1,肿瘤",
            help="输入要搜索的关键词，多个关键词用逗号分隔"
        )
        
        match_type = st.selectbox(
            "匹配类型",
            ["任意关键词", "所有关键词", "精确短语"],
            index=0,
            help="选择关键词匹配方式"
        )
    
    with col2:
        case_sensitive = st.checkbox(
            "区分大小写",
            value=False,
            help="是否区分大小写"
        )
        
        whole_word = st.checkbox(
            "全词匹配",
            value=True,
            help="是否只匹配完整的单词"
        )
    
    if st.button("🔍 搜索", key="keyword_search"):
        if not keywords:
            st.error("请输入关键词")
        else:
            perform_keyword_search(keywords, match_type, top_k, case_sensitive, whole_word, include_metadata)


def perform_keyword_search(keywords, match_type, top_k, case_sensitive, whole_word, include_metadata):
    """执行关键词搜索"""
    with st.spinner("正在搜索相关文献..."):
        try:
            # 构建查询字符串
            keyword_list = [k.strip() for k in keywords.split(',')]
            
            if match_type == "任意关键词":
                query = " OR ".join(keyword_list)
            elif match_type == "所有关键词":
                query = " AND ".join(keyword_list)
            else:  # 精确短语
                query = f'"{keywords}"'
            
            results = st.session_state.ragflow_client.search(
                dataset_id=st.session_state.current_dataset,
                query=query,
                top_k=top_k,
                similarity_threshold=0.3  # 关键词搜索使用较低的阈值
            )
            
            if results:
                st.success(f"找到 {len(results)} 个相关文档")
                display_search_results(results, include_metadata)
            else:
                st.info("未找到相关文档，请尝试调整关键词")
                
        except Exception as e:
            st.error(f"搜索失败: {e}")


def conversational_search_ui():
    """对话式搜索界面"""
    st.markdown("### 💬 对话式搜索")
    
    # 初始化对话历史
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    # 显示对话历史
    if st.session_state.conversation_history:
        st.markdown("#### 📜 对话历史")
        
        for i, (question, answer) in enumerate(st.session_state.conversation_history):
            with st.expander(f"💬 Q{i+1}: {question[:50]}..."):
                st.markdown(f"**问题**: {question}")
                st.markdown(f"**回答**: {answer}")
    
    # 新问题输入
    st.markdown("#### ❓ 提出新问题")
    question = st.text_input(
        "您的问题",
        placeholder="例如：请解释一下CAR-T细胞疗法的原理和应用",
        help="用自然语言提出您的问题，系统会基于文献库回答"
    )
    
    if st.button("💬 提问", key="ask_question"):
        if not question:
            st.error("请输入问题")
        else:
            perform_conversational_search(question)
    
    # 清除历史按钮
    if st.button("🗑️ 清除对话历史", key="clear_history"):
        st.session_state.conversation_history = []
        st.success("对话历史已清除")


def perform_conversational_search(question):
    """执行对话式搜索"""
    with st.spinner("正在基于文献回答您的问题..."):
        try:
            # 调用RAGFlow的对话API
            response = st.session_state.ragflow_client.chat_with_dataset(
                dataset_id=st.session_state.current_dataset,
                question=question,
                conversation_history=st.session_state.conversation_history
            )
            
            if 'error' not in response:
                answer = response.get('answer', '抱歉，无法回答这个问题')
                
                # 添加到对话历史
                st.session_state.conversation_history.append((question, answer))
                
                # 显示回答
                st.markdown("### 💡 回答")
                st.write(answer)
                
                # 显示参考文档
                if 'references' in response and response['references']:
                    st.markdown("### 📚 参考文档")
                    for ref in response['references']:
                        st.markdown(f"- {ref}")
            else:
                st.error(f"回答失败: {response['error']}")
                
        except Exception as e:
            st.error(f"对话失败: {e}")


def comparative_search_ui():
    """比较搜索界面"""
    st.markdown("### 🔍 比较搜索")
    
    col1, col2 = st.columns(2)
    
    with col1:
        topic1 = st.text_input(
            "研究主题1",
            placeholder="例如：PD-1抑制剂",
            help="输入第一个研究主题"
        )
    
    with col2:
        topic2 = st.text_input(
            "研究主题2",
            placeholder="例如：CTLA-4抑制剂",
            help="输入第二个研究主题"
        )
    
    if st.button("🔍 比较分析", key="compare_search"):
        if not topic1 or not topic2:
            st.error("请输入两个研究主题")
        else:
            perform_comparative_search(topic1, topic2)


def perform_comparative_search(topic1, topic2):
    """执行比较搜索"""
    with st.spinner(f"正在比较分析 '{topic1}' 和 '{topic2}'..."):
        try:
            # 调用文献挖掘器的比较功能
            miner = st.session_state.literature_miner
            comparison = miner.compare_literature_sets(
                dataset_id=st.session_state.current_dataset,
                topic1=topic1,
                topic2=topic2
            )
            
            if 'error' not in comparison:
                display_comparison_results(comparison)
            else:
                st.error(f"比较分析失败: {comparison['error']}")
                
        except Exception as e:
            st.error(f"比较分析失败: {e}")


def display_search_results(results, include_metadata):
    """显示搜索结果"""
    for i, result in enumerate(results, 1):
        with st.expander(f"📄 结果 {i}: {result.document_name} (相似度: {result.score:.3f})"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**文档ID**: {result.document_id}")
                st.markdown(f"**相似度**: {result.score:.3f}")
                
                # 内容预览
                preview_length = 500
                content_preview = result.content[:preview_length]
                if len(result.content) > preview_length:
                    content_preview += "..."
                
                st.markdown("**内容预览**:")
                st.text_area("", content_preview, height=150, disabled=True, key=f"preview_{i}")
            
            with col2:
                # 操作按钮
                if st.button("📖 查看全文", key=f"view_full_{i}"):
                    st.session_state[f'show_full_content_{i}'] = True
                
                if st.button("💾 收藏", key=f"favorite_{i}"):
                    st.success("已收藏到收藏夹")
            
            # 显示全文（如果点击了查看全文）
            if st.session_state.get(f'show_full_content_{i}', False):
                st.markdown("**完整内容**:")
                st.text_area("", result.content, height=300, disabled=True, key=f"full_content_{i}")
            
            # 显示元数据
            if include_metadata and result.metadata:
                st.markdown("**元数据**:")
                st.json(result.metadata)


def display_comparison_results(comparison):
    """显示比较结果"""
    topic1 = comparison['topic1']
    topic2 = comparison['topic2']
    doc_count1 = comparison['topic1_doc_count']
    doc_count2 = comparison['topic2_doc_count']
    comparison_text = comparison['comparison']
    
    # 比较统计
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(f"{topic1} 文档数", doc_count1)
    
    with col2:
        st.metric(f"{topic2} 文档数", doc_count2)
    
    with col3:
        ratio = doc_count1 / doc_count2 if doc_count2 > 0 else float('inf')
        st.metric("数量比", f"{ratio:.2f}")
    
    # 比较分析
    st.markdown("### 📊 比较分析")
    st.write(comparison_text)
    
    # 文档数量对比图
    import plotly.express as px
    import plotly.graph_objects as go
    
    df = pd.DataFrame({
        '研究主题': [topic1, topic2],
        '文档数量': [doc_count1, doc_count2]
    })
    
    fig = px.bar(df, x='研究主题', y='文档数量', title="文档数量对比")
    st.plotly_chart(fig, use_container_width=True)