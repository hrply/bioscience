"""
首页 - 应用介绍和快速开始
"""

import streamlit as st
import time


def run():
    st.markdown('<h1 class="main-header">🔬 AI科研助手</h1>', unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-box">
        <h3>🎯 欢迎使用AI科研助手</h3>
        <p>基于大模型的智能科研助手，支持自动化实验方案设计、进度管理和结果分析。</p>
    </div>
    """, unsafe_allow_html=True)

    # 系统功能介绍
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔬 核心功能")
        features = [
            "✅ 智能实验方案生成",
            "📚 RAGFlow知识库集成",
            "📋 模板系统",
            "⏱️ 进度管理",
            "📊 结果记录与分析",
            "🤖 多模型支持",
            "⚙️ 应用内配置管理"
        ]
        for feature in features:
            st.markdown(feature)

    with col2:
        st.subheader("📊 快速统计")
        try:
            from ai_researcher.experiments.manager import ExperimentManager
            import os

            # 获取数据库路径
            db_path = os.environ.get('DATABASE_PATH', '/app/data/experiments/experiments.db')

            exp_manager = ExperimentManager(db_path)
            experiments = exp_manager.list_experiments()

            stats = {
                "总实验数": len(experiments),
                "进行中": len([e for e in experiments if e.get('status') == 'in_progress']),
                "已完成": len([e for e in experiments if e.get('status') == 'completed']),
                "计划中": len([e for e in experiments if e.get('status') == 'planned'])
            }

            for key, value in stats.items():
                st.metric(key, value)

        except Exception as e:
            st.info("统计信息暂时不可用")

    st.markdown("---")

    # 快速开始
    st.subheader("🚀 快速开始")

    quick_start = st.expander("点击查看快速开始指南", expanded=False)
    with quick_start:
        st.markdown("""
        ### 1️⃣ 配置API密钥
        前往"⚙️ 配置管理"页面，添加您的模型API密钥。

        ### 2️⃣ 创建实验
        点击左侧"🔬 创建实验"菜单，输入实验目标，AI将自动生成实验方案。

        ### 3️⃣ 查看进度
        在"📋 实验列表"中查看所有实验的进度和状态。

        ### 4️⃣ 分析结果
        在"📊 结果分析"页面上传数据，获取AI智能分析。

        ### 5️⃣ 管理模板
        在"📝 模板管理"中查看和使用实验模板。
        """)

    # 系统状态
    st.markdown("---")
    st.subheader("📡 系统状态")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info("**RAGFlow连接**")
        try:
            from ai_researcher.config import load_config
            import requests

            config = load_config()
            ragflow_config = config.get('ragflow', {})
            ragflow_endpoint = ragflow_config.get('endpoint', 'http://192.168.3.147:20334')
            ragflow_api_key = ragflow_config.get('api_key')

            headers = {"Content-Type": "application/json"}
            if ragflow_api_key:
                headers["Authorization"] = f"Bearer {ragflow_api_key}"

            response = requests.get(
                f"{ragflow_endpoint}/api/v1/dataset",
                headers=headers,
                timeout=2
            )
            if response.status_code == 200:
                st.success("✓ 已连接")
            else:
                st.warning("⚠️ 连接异常")
        except Exception as e:
            st.error("✗ 未连接")

    with col2:
        st.info("**数据库状态**")
        try:
            from ai_researcher.experiments.manager import ExperimentManager
            import os
            db_path = os.environ.get('DATABASE_PATH', '/app/data/experiments/experiments.db')
            if os.path.exists(db_path):
                st.success("✓ 正常")
            else:
                st.warning("⚠️ 需初始化")
        except:
            st.error("✗ 异常")

    with col3:
        st.info("**模型配置**")
        try:
            from ai_researcher.secrets_manager import check_api_keys
            api_status = check_api_keys()
            if any(api_status.values()):
                st.success("✓ 已配置")
            else:
                st.warning("⚠️ 未配置")
        except:
            st.error("✗ 异常")

    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray;'>
        <p>AI科研助手 - 智能实验方案生成和管理系统</p>
        <p>基于大模型技术，集成RAGFlow知识库</p>
    </div>
    """, unsafe_allow_html=True)
