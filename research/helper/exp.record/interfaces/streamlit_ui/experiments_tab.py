"""
实验记录界面 - 核心修订工作流实现
"""

import streamlit as st
import logging
from datetime import datetime
from typing import Dict, Any

from config.settings import Settings
from storage.template_manager import TemplateManager
from storage.experiment_store import ExperimentStore
from agents.experiment_agent import ExperimentAgent
from core.agent_coordinator import AgentCoordinator
from utils.diff_utils import highlight_modifications


def render_experiments_tab():
    """渲染实验记录标签页"""
    st.title("📝 实验记录")
    st.markdown("---")
    
    # 初始化会话状态
    if "experiment_step" not in st.session_state:
        st.session_state.experiment_step = "select_template"
    if "current_experiment" not in st.session_state:
        st.session_state.current_experiment = {}
    
    # 步骤指示器
    steps = [
        "选择模板", "描述修改", "查看修订", "确认保存"
    ]
    current_step_index = ["select_template", "describe_modifications", "review_revision", "confirm_save"].index(
        st.session_state.experiment_step
    )
    
    # 渲染步骤指示器
    cols = st.columns(len(steps))
    for i, (col, step) in enumerate(zip(cols, steps)):
        with col:
            if i <= current_step_index:
                st.success(step)
            else:
                st.info(step)
    
    st.markdown("---")
    
    # 渲染当前步骤
    if st.session_state.experiment_step == "select_template":
        _render_template_selection()
    elif st.session_state.experiment_step == "describe_modifications":
        _render_modification_description()
    elif st.session_state.experiment_step == "review_revision":
        _render_revision_review()
    elif st.session_state.experiment_step == "confirm_save":
        _render_final_confirmation()


def _render_template_selection():
    """渲染模板选择步骤"""
    st.markdown("## 📋 步骤1: 选择基础模板")
    
    try:
        template_manager = TemplateManager()
        templates = template_manager.list_templates()
        
        if not templates:
            st.warning("没有可用的模板，请先在模板管理页面创建或上传模板。")
            if st.button("前往模板管理"):
                st.session_state.current_page = "templates"
                st.rerun()
            return
        
        # 模板选择
        template_options = {f"{t['name']} ({t['category']})": t['id'] for t in templates}
        selected_template_name = st.selectbox("选择实验模板:", list(template_options.keys()))
        
        if selected_template_name:
            selected_template_id = template_options[selected_template_name]
            template = template_manager.get_template(selected_template_id)
            
            # 显示模板预览
            st.markdown("### 模板预览")
            st.markdown(f"**名称**: {template['name']}")
            st.markdown(f"**版本**: {template['version']}")
            st.markdown(f"**分类**: {template['category']}")
            st.markdown(f"**描述**: {template['description']}")
            
            with st.expander("查看模板内容"):
                st.markdown(template['content'])
            
            # 不可修改章节提示
            if template.get('immutable_sections'):
                st.warning(f"⚠️ 以下章节不可修改: {', '.join(template['immutable_sections'])}")
            
            # 确认选择
            if st.button("使用此模板", type="primary"):
                st.session_state.current_experiment = {
                    "template_id": selected_template_id,
                    "template_data": template
                }
                st.session_state.experiment_step = "describe_modifications"
                st.rerun()
    
    except Exception as e:
        st.error(f"加载模板失败: {e}")


def _render_modification_description():
    """渲染修改描述步骤"""
    st.markdown("## ✏️ 步骤2: 描述修改需求")
    
    if not st.session_state.current_experiment.get("template_id"):
        st.error("请先选择模板")
        return
    
    template = st.session_state.current_experiment["template_data"]
    
    # 显示模板信息
    st.info(f"当前模板: {template['name']} v{template['version']}")
    
    # 实验标题
    experiment_title = st.text_input(
        "实验标题:",
        value=f"{template['name']}_修订_{datetime.now().strftime('%Y%m%d')}",
        help="为本次实验记录起一个描述性的标题"
    )
    
    # 修改描述
    st.markdown("### 修改需求描述")
    st.markdown("""
    请详细描述您希望对模板进行的修改，例如：
    - 将培养基更换为DMEM+10%FBS
    - 细胞密度调整为5000 cells/cm²
    - 培养时间延长至48小时
    """)
    
    user_modifications = st.text_area(
        "修改描述:",
        height=150,
        placeholder="请描述您希望进行的修改...",
        help="请尽可能详细和具体，避免模糊描述"
    )
    
    # 高级选项
    with st.expander("高级选项"):
        strict_mode = st.checkbox(
            "严格模式",
            value=True,
            help="启用更严格的验证，任何不确定的修改都会被拒绝"
        )
        
        conservative_mode = st.checkbox(
            "保守模式",
            value=False,
            help="仅应用最明确、最安全的修改"
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("返回选择模板"):
            st.session_state.experiment_step = "select_template"
            st.rerun()
    
    with col2:
        if st.button("生成修订", type="primary", disabled=not user_modifications.strip()):
            # 保存用户输入
            st.session_state.current_experiment.update({
                "title": experiment_title,
                "user_modifications": user_modifications,
                "strict_mode": strict_mode,
                "conservative_mode": conservative_mode
            })
            
            # 生成修订
            _generate_revision()


def _generate_revision():
    """生成修订版本"""
    with st.spinner("正在生成修订版本..."):
        try:
            # 初始化Agent
            settings = Settings()
            coordinator = AgentCoordinator(settings)
            
            # 注册实验Agent
            from agents.experiment_agent import ExperimentAgent
            experiment_agent = ExperimentAgent(settings)
            coordinator.register_agent(ExperimentAgent, "experiment_agent", "实验记录修订Agent")
            
            # 准备请求数据
            request_data = {
                "template_id": st.session_state.current_experiment["template_id"],
                "user_modifications": st.session_state.current_experiment["user_modifications"],
                "experiment_title": st.session_state.current_experiment["title"],
                "strict_mode": st.session_state.current_experiment.get("strict_mode", True),
                "conservative_mode": st.session_state.current_experiment.get("conservative_mode", False)
            }
            
            # 处理请求
            result = await coordinator.route_request({
                "agent": "experiment_agent",
                "type": "experiment_revision",
                "data": request_data
            })
            
            if result["success"]:
                st.session_state.current_experiment.update(result["result"])
                st.session_state.experiment_step = "review_revision"
                st.success("修订版本生成成功！")
            else:
                st.error(f"修订生成失败: {result.get('error', '未知错误')}")
                
        except Exception as e:
            st.error(f"生成修订时出错: {e}")
            logging.error(f"Revision generation error: {e}")
    
    st.rerun()


def _render_revision_review():
    """渲染修订审核步骤"""
    st.markdown("## 🔍 步骤3: 审核修订版本")
    
    experiment_data = st.session_state.current_experiment
    
    # 显示基本信息
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("模板", experiment_data["template_data"]["name"])
    
    with col2:
        st.metric("验证置信度", f"{experiment_data['validation_result']['confidence']:.2f}")
    
    with col3:
        validation_status = "✅ 通过" if experiment_data['validation_result']['is_valid'] else "⚠️ 有问题"
        st.metric("验证状态", validation_status)
    
    # 验证结果
    validation_result = experiment_data['validation_result']
    
    if not validation_result['is_valid'] or validation_result['issues']:
        st.error("### ⚠️ 验证问题")
        for issue in validation_result['issues']:
            st.write(f"- {issue}")
    
    if validation_result['warnings']:
        st.warning("### ⚠️ 警告信息")
        for warning in validation_result['warnings']:
            st.write(f"- {warning}")
    
    if validation_result['conservative_suggestions']:
        st.info("### 💡 保守模式建议")
        for suggestion in validation_result['conservative_suggestions']:
            st.write(f"- {suggestion}")
    
    # 修订内容对比
    st.markdown("### 📝 修订内容对比")
    
    tab1, tab2, tab3 = st.tabs(["差异对比", "修订标记", "完整版本"])
    
    with tab1:
        # 显示差异对比
        diff_comparison = experiment_data['diff_comparison']
        st.markdown(f"**统计信息**:")
        st.write(f"- 原始行数: {diff_comparison['statistics']['original_lines']}")
        st.write(f"- 修订行数: {diff_comparison['statistics']['revised_lines']}")
        st.write(f"- 新增内容: {diff_comparison['statistics']['changes_added']} 行")
        st.write(f"- 删除内容: {diff_comparison['statistics']['changes_removed']} 行")
        
        # 显示HTML差异
        st.markdown(diff_comparison['html_diff'], unsafe_allow_html=True)
    
    with tab2:
        # 显示修订标记
        revision_markers = experiment_data['revision_markers']
        
        if revision_markers:
            for i, marker in enumerate(revision_markers, 1):
                st.markdown(f"**修订 {i}: {marker['description']}**")
                
                if marker['type'] == 'replace':
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_area("原始内容:", marker['original'], height=100, disabled=True, key=f"orig_{i}")
                    with col2:
                        st.text_area("修订内容:", marker['revised'], height=100, disabled=True, key=f"rev_{i}")
                else:
                    st.text_area("内容:", marker.get('revised', marker.get('original', '')), height=100, disabled=True, key=f"content_{i}")
                
                st.markdown("---")
        else:
            st.info("没有检测到修改内容")
    
    with tab3:
        # 显示完整修订版本
        st.text_area(
            "完整修订版本:",
            experiment_data['revised_content'],
            height=400,
            disabled=True
        )
    
    # 操作按钮
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("返回修改"):
            st.session_state.experiment_step = "describe_modifications"
            st.rerun()
    
    with col2:
        if st.button("重新生成"):
            _generate_revision()
    
    with col3:
        can_proceed = validation_result['is_valid'] or st.session_state.current_experiment.get('conservative_mode', False)
        if st.button("确认保存", type="primary", disabled=not can_proceed):
            if not can_proceed:
                st.warning("验证未通过，无法保存。请启用保守模式或修改描述后重试。")
            else:
                st.session_state.experiment_step = "confirm_save"
                st.rerun()


def _render_final_confirmation():
    """渲染最终确认步骤"""
    st.markdown("## ✅ 步骤4: 最终确认")
    
    experiment_data = st.session_state.current_experiment
    
    # 最终确认信息
    st.success("### 📋 实验记录信息确认")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**实验标题**: {experiment_data['title']}")
        st.write(f"**基础模板**: {experiment_data['template_data']['name']}")
        st.write(f"**模板版本**: {experiment_data['template_data']['version']}")
    
    with col2:
        st.write(f"**创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"**验证置信度**: {experiment_data['validation_result']['confidence']:.2f}")
        validation_status = "通过" if experiment_data['validation_result']['is_valid'] else "有保留"
        st.write(f"**验证状态**: {validation_status}")
    
    # 用户修改描述
    st.markdown("### 📝 修改需求")
    st.text_area("", experiment_data['user_modifications'], height=100, disabled=True)
    
    # 最终确认
    st.markdown("---")
    st.warning("⚠️ 请仔细确认以上信息，保存后将无法修改本次修订的依据。")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("返回审核"):
            st.session_state.experiment_step = "review_revision"
            st.rerun()
    
    with col2:
        if st.button("确认保存", type="primary"):
            _save_experiment()


def _save_experiment():
    """保存实验记录"""
    with st.spinner("正在保存实验记录..."):
        try:
            # 初始化存储
            experiment_store = ExperimentStore()
            
            # 准备保存数据
            save_data = {
                "experiment_title": st.session_state.current_experiment["title"],
                "template_id": st.session_state.current_experiment["template_id"],
                "user_modifications": st.session_state.current_experiment["user_modifications"],
                "original_template": st.session_state.current_experiment["original_template"],
                "revised_content": st.session_state.current_experiment["revised_content"],
                "validation_result": st.session_state.current_experiment["validation_result"],
                "revision_markers": st.session_state.current_experiment["revision_markers"],
                "diff_comparison": st.session_state.current_experiment["diff_comparison"],
                "metadata": st.session_state.current_experiment["metadata"]
            }
            
            # 保存实验
            experiment_id = experiment_store.save_experiment(save_data)
            
            st.success(f"✅ 实验记录保存成功！实验ID: {experiment_id}")
            
            # 清理会话状态
            st.session_state.experiment_step = "select_template"
            st.session_state.current_experiment = {}
            
            # 显示成功信息
            st.balloons()
            
            # 询问是否继续
            if st.button("创建新实验", type="primary"):
                st.rerun()
            
        except Exception as e:
            st.error(f"保存失败: {e}")
            logging.error(f"Save experiment error: {e}")


# 历史记录侧边栏
def _render_experiment_history():
    """渲染实验历史记录侧边栏"""
    st.markdown("### 📚 历史记录")
    
    try:
        experiment_store = ExperimentStore()
        experiments = experiment_store.list_experiments(limit=10)
        
        if experiments:
            for exp in experiments:
                with st.expander(f"🧪 {exp['title']} ({exp['created_at'][:10]})"):
                    st.write(f"ID: {exp['id']}")
                    st.write(f"模板: {exp['template_id']}")
                    
                    if st.button(f"查看详情", key=f"hist_{exp['id']}"):
                        st.session_state.selected_experiment = exp['id']
                        # 这里可以跳转到详情页面
        else:
            st.info("暂无历史记录")
            
    except Exception as e:
        st.error(f"加载历史记录失败: {e}")


# 在主界面中添加历史记录侧边栏
if st.sidebar.checkbox("显示历史记录"):
    _render_experiment_history()