#!/usr/bin/env python3
"""
生物科学文献阅读助手 - 主入口
"""

import os
import sys
import streamlit as st
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入自定义模块
from src.config.settings import settings
from src.core.ragflow_client import get_ragflow_client, RAGFlowConfig
from src.core.llm_client import get_llm_client, LLMConfig
from src.core.literature_miner import get_literature_miner

# 导入页面模块
from src.interfaces.streamlit_ui.home import home_page
from src.interfaces.streamlit_ui.library_tab import library_page
from src.interfaces.streamlit_ui.mining_tab import mining_page
from src.interfaces.streamlit_ui.search_tab import search_page
from src.interfaces.streamlit_ui.config_tab import config_page


def init_session_state():
    """初始化会话状态"""
    if 'ragflow_client' not in st.session_state:
        ragflow_config = RAGFlowConfig(**settings.get_ragflow_config())
        st.session_state.ragflow_client = get_ragflow_client(ragflow_config)
    
    if 'llm_client' not in st.session_state:
        llm_config = LLMConfig(**settings.get_llm_config())
        st.session_state.llm_client = get_llm_client(llm_config)
    
    if 'literature_miner' not in st.session_state:
        st.session_state.literature_miner = get_literature_miner(
            st.session_state.ragflow_client,
            st.session_state.llm_client
        )
    
    if 'current_dataset' not in st.session_state:
        st.session_state.current_dataset = None
    
    if 'datasets' not in st.session_state:
        st.session_state.datasets = []


def check_configuration():
    """检查配置"""
    config_validation = settings.validate_config()
    
    if not config_validation['valid']:
        st.error("配置存在问题，请检查配置页面")
        for issue in config_validation['issues']:
            st.error(f"- {issue}")
        return False
    
    if config_validation['warnings']:
        for warning in config_validation['warnings']:
            st.warning(f"- {warning}")
    
    return True


def main():
    """主应用程序入口"""
    st.set_page_config(
        page_title="文献深度挖掘助手",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 初始化会话状态
    init_session_state()
    
    # 侧边栏
    with st.sidebar:
        st.title("📚 文献深度挖掘助手")
        st.markdown("---")
        
        # 配置检查
        if not check_configuration():
            st.warning("请先配置RAGFlow和大模型设置")
        
        # 导航菜单
        page = st.selectbox(
            "选择功能",
            ["首页", "文献库", "深度挖掘", "智能搜索", "配置"],
            index=0
        )
        
        # 状态信息
        st.markdown("---")
        st.markdown("### 连接状态")
        
        # RAGFlow状态
        try:
            health = st.session_state.ragflow_client.health_check()
            if health.get("status") == "healthy":
                st.success("RAGFlow: ✅ 已连接")
            else:
                st.error("RAGFlow: ❌ 连接失败")
        except Exception as e:
            st.error(f"RAGFlow: ❌ {str(e)}")
        
        # 大模型状态
        if settings.is_llm_configured():
            st.success("大模型: ✅ 已配置")
        else:
            st.error("大模型: ❌ 未配置")
        
        # 当前数据集
        if st.session_state.current_dataset:
            st.markdown(f"**当前数据集**: {st.session_state.current_dataset}")
        else:
            st.markdown("**当前数据集**: 未选择")
    
    # 主页面内容
    if page == "首页":
        home_page()
    elif page == "文献库":
        library_page()
    elif page == "深度挖掘":
        mining_page()
    elif page == "智能搜索":
        search_page()
    elif page == "配置":
        config_page()
    
    # 页脚
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray; font-size: small;'>
            文献深度挖掘助手 v1.0.0 | 基于RAGFlow和大模型技术
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()