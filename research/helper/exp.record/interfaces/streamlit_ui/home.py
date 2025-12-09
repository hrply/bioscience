"""
首页界面 - 展示系统概览和快速入口
"""

import streamlit as st
import logging
from datetime import datetime
from pathlib import Path

from config.settings import Settings
from storage.template_manager import TemplateManager
from storage.experiment_store import ExperimentStore
from storage.backup_manager import BackupManager


def render_home():
    """渲染首页"""
    st.title("🔬 实验记录智能助手")
    st.markdown("---")
    
    # 系统简介
    st.markdown("""
    ## 🎯 系统简介
    
    这是一个基于**严格模板驱动**的实验记录智能助手，具备**三重防幻觉保障**机制：
    
    - **模板约束**：所有修订基于预定义protocol模板
    - **验证层**：自动检查修改是否超出模板范围  
    - **用户确认**：高亮显示修改，强制用户确认后保存
    
    ### 🚀 核心特性
    - ✅ 严格模板驱动，杜绝AI自由发挥
    - ✅ 完整修订追踪，记录每次修改依据
    - ✅ 智能差异对比，可视化修改内容
    - ✅ 本地数据存储，保护实验隐私
    """)
    
    # 系统状态概览
    st.markdown("## 📊 系统状态")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        try:
            template_manager = TemplateManager()
            template_count = len(template_manager.list_templates())
            st.metric("可用模板", template_count)
        except Exception as e:
            st.error(f"模板加载失败: {e}")
    
    with col2:
        try:
            experiment_store = ExperimentStore()
            stats = experiment_store.get_statistics()
            st.metric("实验记录", stats.get("total_experiments", 0))
        except Exception as e:
            st.error(f"实验数据加载失败: {e}")
    
    with col3:
        try:
            settings = Settings()
            api_status = "✅ 已配置" if settings.is_api_configured() else "❌ 未配置"
            st.metric("API状态", api_status)
        except Exception as e:
            st.error(f"配置检查失败: {e}")
    
    with col4:
        try:
            backup_manager = BackupManager()
            backup_stats = backup_manager.get_backup_statistics()
            st.metric("备份数量", backup_stats.get("total_backups", 0))
        except Exception as e:
            st.error(f"备份检查失败: {e}")
    
    # 快速操作
    st.markdown("## ⚡ 快速操作")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📝 创建新实验", type="primary", use_container_width=True):
            st.session_state.current_page = "experiments"
            st.rerun()
    
    with col2:
        if st.button("📋 管理模板", use_container_width=True):
            st.session_state.current_page = "templates"
            st.rerun()
    
    with col3:
        if st.button("📂 备份数据", use_container_width=True):
            # 显示备份选项
            with st.expander("备份选项", expanded=True):
                try:
                    backup_manager = BackupManager()
                    
                    # 创建备份
                    if st.button("创建立即备份"):
                        with st.spinner("正在创建备份..."):
                            try:
                                backup_id = backup_manager.create_backup(
                                    description="手动备份",
                                    include_templates=True,
                                    include_experiments=True,
                                    include_config=False
                                )
                                st.success(f"备份创建成功: {backup_id}")
                            except Exception as e:
                                st.error(f"备份创建失败: {e}")
                    
                    # 显示备份列表
                    backups = backup_manager.list_backups()
                    if backups:
                        st.write("最近备份:")
                        for backup in backups[:3]:  # 只显示最近3个
                            st.write(f"- {backup['backup_id']} ({backup['created_at']})")
                    
                except Exception as e:
                    st.error(f"备份功能不可用: {e}")
    
    # 最近活动
    st.markdown("## 🕒 最近活动")
    
    try:
        experiment_store = ExperimentStore()
        recent_experiments = experiment_store.list_experiments(limit=5)
        
        if recent_experiments:
            for exp in recent_experiments:
                with st.expander(f"🧪 {exp['title']} - {exp['created_at'][:10]}"):
                    st.write(f"模板ID: {exp['template_id']}")
                    st.write(f"创建时间: {exp['created_at']}")
                    
                    # 查看详情按钮
                    if st.button(f"查看详情", key=f"view_{exp['id']}"):
                        st.session_state.selected_experiment = exp['id']
                        st.session_state.current_page = "experiments"
                        st.rerun()
        else:
            st.info("暂无实验记录")
            
    except Exception as e:
        st.error(f"无法加载最近活动: {e}")
    
    # 使用指南
    with st.expander("📖 使用指南"):
        st.markdown("""
        ### 基本使用流程
        
        1. **选择模板**：在模板管理页面选择或上传基础protocol模板
        2. **描述修改**：在实验记录页面输入自然语言描述的修改需求
        3. **查看修订**：系统生成修订版本，高亮显示修改部分
        4. **确认保存**：检查验证结果，确认无误后保存为实验方案
        
        ### 防幻觉机制说明
        
        - **严格模式**：AI只能基于模板和用户明确指令进行修改
        - **验证层**：自动检查是否添加了模板不存在的章节或修改了不可修改部分
        - **保守模式**：当验证失败时，仅应用最明确、最安全的修改
        
        ### 配置API
        
        请确保已配置通义千问API密钥：
        ```bash
        export QWEN_API_KEY=your_api_key_here
        ```
        """)
    
    # 系统信息
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
        实验记录智能助手 v1.0.0 | 防幻觉版 | 
        当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
    """, unsafe_allow_html=True)