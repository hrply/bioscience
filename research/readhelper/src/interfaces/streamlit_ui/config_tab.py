"""
配置页面模块
"""

import streamlit as st
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import settings
from src.core.ragflow_client import get_ragflow_client, RAGFlowConfig
from src.core.llm_client import get_llm_client, LLMConfig


def config_page():
    """配置页面内容"""
    st.title("⚙️ 系统配置")
    
    # 配置标签页
    tab1, tab2, tab3, tab4 = st.tabs(["RAGFlow配置", "大模型配置", "系统配置", "连接测试"])
    
    with tab1:
        ragflow_config_ui()
    
    with tab2:
        llm_config_ui()
    
    with tab3:
        system_config_ui()
    
    with tab4:
        connection_test_ui()


def ragflow_config_ui():
    """RAGFlow配置界面"""
    st.markdown("## 🔗 RAGFlow配置")
    
    st.markdown("### 📋 连接设置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        ragflow_base_url = st.text_input(
            "RAGFlow服务器地址",
            value=settings.ragflow_base_url,
            placeholder="http://localhost:9380",
            help="RAGFlow服务器的URL地址"
        )
        
        ragflow_api_key = st.text_input(
            "RAGFlow API密钥",
            value=settings.ragflow_api_key,
            type="password",
            placeholder="输入您的RAGFlow API密钥",
            help="用于访问RAGFlow API的密钥"
        )
    
    with col2:
        ragflow_timeout = st.number_input(
            "请求超时时间(秒)",
            min_value=5,
            max_value=300,
            value=settings.ragflow_timeout,
            help="API请求的超时时间"
        )
        
        ragflow_max_retries = st.number_input(
            "最大重试次数",
            min_value=0,
            max_value=10,
            value=settings.ragflow_max_retries,
            help="API请求失败时的最大重试次数"
        )
    
    # 保存RAGFlow配置
    if st.button("💾 保存RAGFlow配置", key="save_ragflow"):
        save_ragflow_config(ragflow_base_url, ragflow_api_key, ragflow_timeout, ragflow_max_retries)
    
    # RAGFlow使用说明
    with st.expander("📖 RAGFlow配置说明"):
        st.markdown("""
        ### RAGFlow是什么？
        RAGFlow是一个开源的RAG（检索增强生成）引擎，专为文献检索和问答设计。
        
        ### 如何获取API密钥？
        1. 启动RAGFlow服务
        2. 访问RAGFlow Web界面
        3. 在设置或API页面生成API密钥
        4. 将密钥复制到上方输入框
        
        ### 默认配置
        - 本地RAGFlow默认地址：http://localhost:9380
        - 如果使用Docker部署，请确保端口映射正确
        - 如果使用远程服务，请输入完整的URL地址
        
        ### 常见问题
        - **连接失败**：检查RAGFlow服务是否正常运行
        - **认证失败**：确认API密钥是否正确
        - **超时错误**：增加超时时间或检查网络连接
        """)


def llm_config_ui():
    """大模型配置界面"""
    st.markdown("## 🤖 大模型配置")
    
    st.markdown("### 📋 模型选择")
    
    col1, col2 = st.columns(2)
    
    with col1:
        llm_provider = st.selectbox(
            "大模型提供商",
            ["openai", "qwen", "claude", "local"],
            index=["openai", "qwen", "claude", "local"].index(settings.llm_provider),
            help="选择您要使用的大模型提供商"
        )
        
        llm_api_key = st.text_input(
            "API密钥",
            value=settings.llm_api_key,
            type="password",
            placeholder="输入您的API密钥",
            help=f"{llm_provider.upper()}的API密钥"
        )
    
    with col2:
        llm_base_url = st.text_input(
            "API基础URL",
            value=settings.llm_base_url,
            placeholder="自动根据提供商设置",
            help="API的基础URL，留空则使用默认地址"
        )
        
        llm_model = st.text_input(
            "模型名称",
            value=settings.llm_model,
            placeholder="自动根据提供商设置",
            help="要使用的具体模型名称"
        )
    
    st.markdown("### ⚙️ 模型参数")
    
    col3, col4 = st.columns(2)
    
    with col3:
        llm_temperature = st.slider(
            "温度参数",
            min_value=0.0,
            max_value=2.0,
            value=settings.llm_temperature,
            step=0.1,
            help="控制生成文本的随机性，越高越随机"
        )
        
        llm_max_tokens = st.number_input(
            "最大Token数",
            min_value=100,
            max_value=8192,
            value=settings.llm_max_tokens,
            step=100,
            help="生成文本的最大长度"
        )
    
    with col4:
        llm_timeout = st.number_input(
            "请求超时时间(秒)",
            min_value=10,
            max_value=600,
            value=settings.llm_timeout,
            help="API请求的超时时间"
        )
        
        llm_max_retries = st.number_input(
            "最大重试次数",
            min_value=0,
            max_value=10,
            value=settings.llm_max_retries,
            help="API请求失败时的最大重试次数"
        )
    
    # 保存大模型配置
    if st.button("💾 保存大模型配置", key="save_llm"):
        save_llm_config(llm_provider, llm_api_key, llm_base_url, llm_model, 
                      llm_temperature, llm_max_tokens, llm_timeout, llm_max_retries)
    
    # 模型提供商说明
    with st.expander("📖 大模型提供商说明"):
        st.markdown("""
        ### OpenAI
        - **模型**: gpt-3.5-turbo, gpt-4, gpt-4-turbo
        - **API密钥**: 从OpenAI官网获取
        - **适用场景**: 通用问答、文本生成
        
        ### 通义千问
        - **模型**: qwen-turbo, qwen-plus, qwen-max
        - **API密钥**: 从阿里云DashScope获取
        - **适用场景**: 中文处理、专业领域
        
        ### Claude
        - **模型**: claude-3-sonnet, claude-3-opus, claude-3-haiku
        - **API密钥**: 从Anthropic官网获取
        - **适用场景**: 长文本处理、复杂推理
        
        ### 本地模型
        - **模型**: 通过Ollama部署的模型
        - **API密钥**: 通常不需要
        - **适用场景**: 离线使用、数据隐私
        
        ### 推荐配置
        - **文献摘要**: 温度0.3-0.5，最大Token 1000-1500
        - **关键词提取**: 温度0.1-0.3，最大Token 500-800
        - **趋势分析**: 温度0.5-0.7，最大Token 1500-2000
        """)


def system_config_ui():
    """系统配置界面"""
    st.markdown("## 🖥️ 系统配置")
    
    st.markdown("### 📄 文档处理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_pdf_size = st.number_input(
            "最大PDF文件大小(MB)",
            min_value=1,
            max_value=100,
            value=settings.max_pdf_size // (1024*1024),
            help="允许上传的PDF文件最大大小"
        )
        
        auto_extract_metadata = st.checkbox(
            "自动提取元数据",
            value=settings.auto_extract_metadata,
            help="是否自动从文档中提取元数据"
        )
    
    with col2:
        summary_max_length = st.number_input(
            "摘要最大长度",
            min_value=100,
            max_value=2000,
            value=settings.summary_max_length,
            step=50,
            help="生成摘要的最大字符数"
        )
        
        keywords_max_count = st.number_input(
            "关键词最大数量",
            min_value=5,
            max_value=20,
            value=settings.keywords_max_count,
            help="提取关键词的最大数量"
        )
    
    st.markdown("### 🔍 搜索设置")
    
    col3, col4 = st.columns(2)
    
    with col3:
        search_results_limit = st.number_input(
            "搜索结果限制",
            min_value=5,
            max_value=50,
            value=settings.search_results_limit,
            help="默认返回的搜索结果数量"
        )
        
        similarity_threshold = st.slider(
            "相似度阈值",
            min_value=0.0,
            max_value=1.0,
            value=settings.similarity_threshold,
            step=0.05,
            help="筛选相关文档的相似度阈值"
        )
    
    with col4:
        semantic_search_enabled = st.checkbox(
            "启用语义搜索",
            value=settings.semantic_search_enabled,
            help="是否启用基于语义的搜索功能"
        )
        
        cache_enabled = st.checkbox(
            "启用缓存",
            value=settings.cache_enabled,
            help="是否启用结果缓存以提高性能"
        )
    
    st.markdown("### ⛏️ 文献挖掘")
    
    col5, col6 = st.columns(2)
    
    with col5:
        mining_max_docs = st.number_input(
            "挖掘最大文档数",
            min_value=10,
            max_value=100,
            value=settings.mining_max_docs,
            step=10,
            help="文献挖掘时使用的最大文档数量"
        )
        
        mining_similarity_threshold = st.slider(
            "挖掘相似度阈值",
            min_value=0.5,
            max_value=0.9,
            value=settings.mining_similarity_threshold,
            step=0.05,
            help="文献挖掘时筛选文档的相似度阈值"
        )
    
    with col6:
        mining_summary_length = st.selectbox(
            "摘要长度",
            ["简短", "中等长度", "详细"],
            index=["简短", "中等长度", "详细"].index(settings.mining_summary_length),
            help="文献挖掘时生成摘要的长度"
        )
        
        page_size = st.number_input(
            "页面大小",
            min_value=5,
            max_value=50,
            value=settings.page_size,
            help="分页显示时每页的项目数量"
        )
    
    # 保存系统配置
    if st.button("💾 保存系统配置", key="save_system"):
        save_system_config(
            max_pdf_size, auto_extract_metadata, summary_max_length, keywords_max_count,
            search_results_limit, similarity_threshold, semantic_search_enabled, cache_enabled,
            mining_max_docs, mining_similarity_threshold, mining_summary_length, page_size
        )
    
    # 配置说明
    with st.expander("📖 系统配置说明"):
        st.markdown("""
        ### 文档处理设置
        - **PDF大小限制**: 防止上传过大文件导致系统问题
        - **元数据提取**: 自动从文档中提取标题、作者等信息
        - **摘要长度**: 控制生成摘要的详细程度
        - **关键词数量**: 提取的关键词数量，影响分析精度
        
        ### 搜索设置
        - **结果限制**: 控制返回的搜索结果数量，影响响应速度
        - **相似度阈值**: 筛选相关文档的严格程度
        - **语义搜索**: 基于内容理解而非关键词匹配
        - **缓存**: 缓存搜索结果以提高响应速度
        
        ### 文献挖掘设置
        - **文档数量**: 挖掘分析的文档数量，影响分析深度和速度
        - **相似度阈值**: 筛选相关文档的阈值
        - **摘要长度**: 挖掘分析时生成摘要的详细程度
        - **页面大小**: 界面分页显示的项目数量
        """)


def connection_test_ui():
    """连接测试界面"""
    st.markdown("## 🔧 连接测试")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔗 RAGFlow连接测试")
        
        if st.button("🔍 测试RAGFlow连接", key="test_ragflow"):
            test_ragflow_connection()
    
    with col2:
        st.markdown("### 🤖 大模型连接测试")
        
        if st.button("🔍 测试大模型连接", key="test_llm"):
            test_llm_connection()
    
    st.markdown("---")
    st.markdown("### 📊 配置状态")
    
    # 显示当前配置状态
    config_validation = settings.validate_config()
    
    if config_validation['valid']:
        st.success("✅ 配置验证通过")
    else:
        st.error("❌ 配置存在问题")
    
    # RAGFlow配置状态
    ragflow_configured = settings.is_ragflow_configured()
    if ragflow_configured:
        st.success("✅ RAGFlow配置完整")
    else:
        st.error("❌ RAGFlow配置不完整")
    
    # 大模型配置状态
    llm_configured = settings.is_llm_configured()
    if llm_configured:
        st.success("✅ 大模型配置完整")
    else:
        st.error("❌ 大模型配置不完整")
    
    # 显示配置问题
    if config_validation['issues']:
        st.markdown("#### ⚠️ 配置问题")
        for issue in config_validation['issues']:
            st.error(f"- {issue}")
    
    if config_validation['warnings']:
        st.markdown("#### ⚠️ 配置警告")
        for warning in config_validation['warnings']:
            st.warning(f"- {warning}")


def save_ragflow_config(base_url, api_key, timeout, max_retries):
    """保存RAGFlow配置"""
    try:
        # 更新设置
        settings.ragflow_base_url = base_url
        settings.ragflow_api_key = api_key
        settings.ragflow_timeout = timeout
        settings.ragflow_max_retries = max_retries
        
        # 重新创建客户端
        ragflow_config = RAGFlowConfig(**settings.get_ragflow_config())
        st.session_state.ragflow_client = get_ragflow_client(ragflow_config)
        
        st.success("RAGFlow配置已保存")
    except Exception as e:
        st.error(f"保存RAGFlow配置失败: {e}")


def save_llm_config(provider, api_key, base_url, model, temperature, max_tokens, timeout, max_retries):
    """保存大模型配置"""
    try:
        # 更新设置
        settings.llm_provider = provider
        settings.llm_api_key = api_key
        settings.llm_base_url = base_url
        settings.llm_model = model
        settings.llm_temperature = temperature
        settings.llm_max_tokens = max_tokens
        settings.llm_timeout = timeout
        settings.llm_max_retries = max_retries
        
        # 重新创建客户端
        llm_config = LLMConfig(**settings.get_llm_config())
        st.session_state.llm_client = get_llm_client(llm_config)
        
        st.success("大模型配置已保存")
    except Exception as e:
        st.error(f"保存大模型配置失败: {e}")


def save_system_config(max_pdf_size, auto_extract_metadata, summary_max_length, keywords_max_count,
                     search_results_limit, similarity_threshold, semantic_search_enabled, cache_enabled,
                     mining_max_docs, mining_similarity_threshold, mining_summary_length, page_size):
    """保存系统配置"""
    try:
        # 更新设置
        settings.max_pdf_size = max_pdf_size * 1024 * 1024  # 转换为字节
        settings.auto_extract_metadata = auto_extract_metadata
        settings.summary_max_length = summary_max_length
        settings.keywords_max_count = keywords_max_count
        settings.search_results_limit = search_results_limit
        settings.similarity_threshold = similarity_threshold
        settings.semantic_search_enabled = semantic_search_enabled
        settings.cache_enabled = cache_enabled
        settings.mining_max_docs = mining_max_docs
        settings.mining_similarity_threshold = mining_similarity_threshold
        settings.mining_summary_length = mining_summary_length
        settings.page_size = page_size
        
        st.success("系统配置已保存")
    except Exception as e:
        st.error(f"保存系统配置失败: {e}")


def test_ragflow_connection():
    """测试RAGFlow连接"""
    with st.spinner("正在测试RAGFlow连接..."):
        try:
            health = st.session_state.ragflow_client.health_check()
            
            if health.get("status") == "healthy":
                st.success("✅ RAGFlow连接成功")
                st.json(health)
            else:
                st.error("❌ RAGFlow连接失败")
                if "error" in health:
                    st.error(f"错误信息: {health['error']}")
        except Exception as e:
            st.error(f"❌ RAGFlow连接测试失败: {e}")


def test_llm_connection():
    """测试大模型连接"""
    with st.spinner("正在测试大模型连接..."):
        try:
            from src.core.llm_client import Message
            
            # 发送测试消息
            messages = [
                Message(role="system", content="你是一个测试助手"),
                Message(role="user", content="请回复'连接成功'")
            ]
            
            response = st.session_state.llm_client.chat(messages)
            
            if response.content and "连接成功" in response.content:
                st.success("✅ 大模型连接成功")
                st.text_area("模型回复", response.content, height=100, disabled=True)
            else:
                st.warning("⚠️ 大模型连接异常")
                st.text_area("模型回复", response.content, height=100, disabled=True)
        except Exception as e:
            st.error(f"❌ 大模型连接测试失败: {e}")