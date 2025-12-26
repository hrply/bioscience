"""
首页模块
"""

import streamlit as st
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import settings


def home_page():
    """首页内容"""
    st.title("🏠 欢迎使用文献深度挖掘助手")
    
    # 介绍
    st.markdown("""
    ## 📖 系统介绍
    
    文献深度挖掘助手是一个基于RAGFlow和大模型技术的智能文献分析平台，
    专为生物科学研究人员设计，帮助您深度挖掘文献价值，发现研究趋势和知识空白。
    
    ### 🚀 核心功能
    
    - **📚 文献库管理**: 连接RAGFlow，管理您的文献集合
    - **🔍 智能搜索**: 基于语义的文献搜索和检索
    - **⛏️ 深度挖掘**: AI驱动的文献深度分析和洞察
    - **📊 趋势分析**: 研究趋势识别和知识图谱构建
    - **💡 智能推荐**: 基于分析结果的研究建议
    
    ### 🎯 使用场景
    
    - **文献综述**: 快速了解研究领域的现状和发展
    - **课题选择**: 识别知识空白和研究机会
    - **合作发现**: 发现潜在的研究合作伙伴
    - **趋势预测**: 把握研究领域的发展方向
    """)
    
    # 快速开始
    st.markdown("---")
    st.markdown("## 🚀 快速开始")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 1️⃣ 配置系统
        前往 **配置** 页面，设置：
        - RAGFlow连接信息
        - 大模型API密钥
        - 其他系统参数
        """)
        
        if st.button("前往配置", key="config_btn"):
            st.switch_page("app.py")
    
    with col2:
        st.markdown("""
        ### 2️⃣ 连接文献库
        在 **文献库** 页面：
        - 连接到RAGFlow数据集
        - 查看文献统计信息
        - 管理文献内容
        """)
        
        if st.button("查看文献库", key="library_btn"):
            st.switch_page("app.py")
    
    with col3:
        st.markdown("""
        ### 3️⃣ 开始挖掘
        在 **深度挖掘** 页面：
        - 输入研究主题
        - 选择分析范围
        - 获取深度洞察
        """)
        
        if st.button("开始挖掘", key="mining_btn"):
            st.switch_page("app.py")
    
    # 系统状态
    st.markdown("---")
    st.markdown("## 📊 系统状态")
    
    status_col1, status_col2, status_col3, status_col4 = st.columns(4)
    
    with status_col1:
        st.metric(
            "RAGFlow状态",
            "✅ 已连接" if settings.is_ragflow_configured() else "❌ 未配置"
        )
    
    with status_col2:
        st.metric(
            "大模型状态",
            "✅ 已配置" if settings.is_llm_configured() else "❌ 未配置"
        )
    
    with status_col3:
        try:
            datasets = st.session_state.get('datasets', [])
            st.metric("可用数据集", len(datasets))
        except:
            st.metric("可用数据集", "未知")
    
    with status_col4:
        st.metric("系统版本", settings.app_version)
    
    # 使用指南
    with st.expander("📋 使用指南"):
        st.markdown("""
        ### 详细使用步骤
        
        #### 第一步：系统配置
        1. 点击侧边栏的"配置"选项
        2. 填写RAGFlow的连接信息（URL和API密钥）
        3. 配置大模型API（选择提供商、填写API密钥和模型名称）
        4. 点击"测试连接"验证配置
        5. 保存配置
        
        #### 第二步：连接文献库
        1. 点击侧边栏的"文献库"选项
        2. 系统将自动获取RAGFlow中的数据集列表
        3. 选择要分析的数据集
        4. 查看数据集中的文献统计信息
        
        #### 第三步：深度挖掘
        1. 点击侧边栏的"深度挖掘"选项
        2. 输入您感兴趣的研究主题
        3. 选择分析范围（全面分析或快速分析）
        4. 点击"开始挖掘"
        5. 等待分析完成，查看结果
        
        #### 第四步：智能搜索
        1. 点击侧边栏的"智能搜索"选项
        2. 输入搜索问题
        3. 选择搜索策略（语义搜索或关键词搜索）
        4. 查看搜索结果和相关文献
        
        ### 常见问题
        
        **Q: RAGFlow连接失败怎么办？**
        A: 请检查RAGFlow服务是否正常运行，URL和API密钥是否正确。
        
        **Q: 大模型API调用失败？**
        A: 请检查API密钥是否有效，网络连接是否正常，模型名称是否正确。
        
        **Q: 分析结果不准确？**
        A: 可以尝试调整分析参数，如相似度阈值、文档数量等。
        
        **Q: 如何提高分析速度？**
        A: 可以减少分析的文档数量，或使用性能更好的硬件。
        """)
    
    # 更新日志
    with st.expander("📝 更新日志"):
        st.markdown("""
        ### v1.0.0 (2025-12-19)
        
        #### 新功能
        - 🎉 首次发布文献深度挖掘助手
        - 🔗 集成RAGFlow API连接
        - 🤖 支持多种大模型（OpenAI、通义千问、Claude、本地模型）
        - ⛏️ 文献深度挖掘功能
        - 🔍 智能文献搜索
        - 📊 研究趋势分析
        - 💡 知识空白识别
        - 🌐 研究网络构建
        - 📈 概念演化分析
        
        #### 技术特性
        - 基于Streamlit的Web界面
        - 模块化架构设计
        - 异步处理支持
        - 配置管理系统
        - 错误处理和日志记录
        
        #### 支持的文献格式
        - PDF文档
        - HTML网页
        - 纯文本文件
        - Markdown文档
        
        #### 支持的大模型
        - OpenAI GPT系列
        - 阿里云通义千问
        - Anthropic Claude
        - 本地Ollama模型
        """)