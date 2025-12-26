#!/usr/bin/env python3
"""
个人实验记录智能助手 - 主入口
防幻觉版本的实验记录管理系统
"""

import os
import sys
import streamlit as st
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from interfaces.streamlit_ui.home import render_home
from interfaces.streamlit_ui.experiments_tab import render_experiments_tab
from interfaces.streamlit_ui.templates_tab import render_templates_tab
from interfaces.streamlit_ui.revision_review import render_revision_review

def main():
    """主应用程序入口"""
    st.set_page_config(
        page_title="实验记录智能助手",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 初始化会话状态
    if "settings" not in st.session_state:
        st.session_state.settings = Settings()
    
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"
    
    # 渲染侧边栏导航
    with st.sidebar:
        st.title("🔬 实验助手")
        st.markdown("---")
        
        page = st.selectbox(
            "选择功能页面",
            ["首页", "实验记录", "模板管理", "修订审核"],
            index=["home", "experiments", "templates", "review"].index(
                st.session_state.get("current_page", "home")
            ),
            format_func=lambda x: {
                "home": "🏠 首页",
                "experiments": "📝 实验记录", 
                "templates": "📋 模板管理",
                "review": "✅ 修订审核"
            }[x],
            key="page_selector"
        )
        
        st.session_state.current_page = page
        
        # 显示系统状态
        st.markdown("---")
        st.markdown("### 系统状态")
        
        # 检查API配置
        api_status = "✅ 已配置" if st.session_state.settings.QWEN_API_KEY else "❌ 未配置"
        st.write(f"通义千问API: {api_status}")
        
        # 检查模板数量
        from storage.template_manager import TemplateManager
        template_mgr = TemplateManager()
        template_count = len(template_mgr.list_templates())
        st.write(f"可用模板: {template_count}个")
        
        # 检查实验记录数量
        from storage.experiment_store import ExperimentStore
        exp_store = ExperimentStore()
        exp_count = len(exp_store.list_experiments())
        st.write(f"实验记录: {exp_count}个")
    
    # 渲染主页面内容
    if st.session_state.current_page == "home":
        render_home()
    elif st.session_state.current_page == "experiments":
        render_experiments_tab()
    elif st.session_state.current_page == "templates":
        render_templates_tab()
    elif st.session_state.current_page == "review":
        render_revision_review()

if __name__ == "__main__":
    main()