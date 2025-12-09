"""
修订审核界面 - 高亮显示修改部分，强制用户确认
"""

import streamlit as st
import logging
from datetime import datetime
from typing import Dict, Any, List
import difflib
from pathlib import Path

from config.settings import Settings
from storage.experiment_store import ExperimentStore
from storage.template_manager import TemplateManager
from utils.diff_utils import highlight_modifications, generate_side_by_side_diff


def render_revision_review():
    """渲染修订审核标签页"""
    st.title("✅ 修订审核")
    st.markdown("---")
    
    # 初始化会话状态
    if "review_mode" not in st.session_state:
        st.session_state.review_mode = "list"
    if "reviewing_experiment" not in st.session_state:
        st.session_state.reviewing_experiment = None
    
    # 侧边栏操作
    with st.sidebar:
        st.markdown("### 🔍 审核操作")
        
        if st.button("📋 待审核列表", key="review_list"):
            st.session_state.review_mode = "list"
            st.session_state.reviewing_experiment = None
            st.rerun()
        
        if st.button("📊 审核统计", key="review_stats"):
            st.session_state.review_mode = "stats"
            st.session_state.reviewing_experiment = None
            st.rerun()
        
        # 筛选选项
        st.markdown("---")
        st.markdown("### 📂 筛选选项")
        
        status_filter = st.selectbox(
            "状态筛选:",
            ["全部", "待审核", "已通过", "需修改"],
            key="status_filter"
        )
        
        date_filter = st.selectbox(
            "时间筛选:",
            ["全部", "今天", "本周", "本月"],
            key="date_filter"
        )
    
    # 渲染主要内容
    if st.session_state.review_mode == "list":
        _render_review_list(status_filter, date_filter)
    elif st.session_state.review_mode == "detail":
        _render_review_detail()
    elif st.session_state.review_mode == "stats":
        _render_review_statistics()


def _render_review_list(status_filter: str, date_filter: str):
    """渲染审核列表"""
    st.markdown("## 📋 待审核实验列表")
    
    try:
        experiment_store = ExperimentStore()
        experiments = experiment_store.list_experiments(limit=50)
        
        # 应用筛选
        filtered_experiments = _apply_filters(experiments, status_filter, date_filter)
        
        if not filtered_experiments:
            st.info("没有找到符合条件的实验记录")
            return
        
        # 显示实验卡片
        for exp in filtered_experiments:
            with st.expander(f"🧪 {exp['title']} ({exp['created_at'][:10]})"):
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    # 获取完整的实验数据以显示验证状态
                    full_exp = experiment_store.get_experiment(exp['id'])
                    if full_exp:
                        validation_result = full_exp.get('validation_result', {})
                        confidence = validation_result.get('confidence', 0)
                        is_valid = validation_result.get('is_valid', False)
                        
                        # 状态指示
                        if is_valid and confidence >= 0.8:
                            status_color = "🟢"
                            status_text = "验证通过"
                        elif is_valid and confidence >= 0.6:
                            status_color = "🟡"
                            status_text = "基本通过"
                        else:
                            status_color = "🔴"
                            status_text = "需审核"
                        
                        st.markdown(f"**状态**: {status_color} {status_text}")
                        st.markdown(f"**置信度**: {confidence:.2f}")
                        st.markdown(f"**模板**: {exp['template_id']}")
                        
                        # 显示问题摘要
                        if validation_result.get('issues'):
                            st.error("问题:")
                            for issue in validation_result['issues'][:2]:  # 只显示前2个
                                st.write(f"- {issue}")
                
                with col2:
                    if st.button("👁️ 详情", key=f"detail_{exp['id']}"):
                        st.session_state.reviewing_experiment = exp['id']
                        st.session_state.review_mode = "detail"
                        st.rerun()
                
                with col3:
                    if st.button("✅ 批准", key=f"approve_{exp['id']}"):
                        _approve_experiment(exp['id'])
                    
                    if st.button("❌ 拒绝", key=f"reject_{exp['id']}"):
                        _reject_experiment(exp['id'])
    
    except Exception as e:
        st.error(f"加载实验列表失败: {e}")


def _render_review_detail():
    """渲染详细审核界面"""
    if not st.session_state.reviewing_experiment:
        st.session_state.review_mode = "list"
        st.rerun()
    
    try:
        experiment_store = ExperimentStore()
        template_manager = TemplateManager()
        
        experiment = experiment_store.get_experiment(st.session_state.reviewing_experiment)
        if not experiment:
            st.error("实验记录不存在")
            return
        
        template = template_manager.get_template(experiment['template_id'])
        if not template:
            st.error("关联模板不存在")
            return
        
        st.markdown(f"## 🔍 详细审核: {experiment['title']}")
        
        # 基本信息
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("模板", template['name'])
        
        with col2:
            validation_result = experiment.get('validation_result', {})
            st.metric("置信度", f"{validation_result.get('confidence', 0):.2f}")
        
        with col3:
            is_valid = validation_result.get('is_valid', False)
            st.metric("验证状态", "通过" if is_valid else "失败")
        
        with col4:
            st.metric("创建时间", experiment['created_at'][:10])
        
        # 用户修改描述
        st.markdown("### 📝 用户修改需求")
        st.text_area("", experiment['user_modifications'], height=100, disabled=True)
        
        # 验证结果详情
        validation_result = experiment.get('validation_result', {})
        _render_validation_details(validation_result)
        
        # 差异对比
        st.markdown("### 🔍 修订内容对比")
        
        tab1, tab2, tab3 = st.tabs(["并排对比", "高亮修改", "完整版本"])
        
        with tab1:
            # 并排对比
            side_by_side = generate_side_by_side_diff(
                experiment['original_template'],
                experiment['revised_content']
            )
            st.markdown(side_by_side, unsafe_allow_html=True)
        
        with tab2:
            # 高亮修改
            highlighted = highlight_modifications(
                experiment['original_template'],
                experiment['revised_content']
            )
            st.markdown(highlighted, unsafe_allow_html=True)
        
        with tab3:
            # 完整修订版本
            st.text_area(
                "修订后完整版本:",
                experiment['revised_content'],
                height=400,
                disabled=True
            )
        
        # 修订历史
        revision_history = experiment_store.get_revision_history(experiment['id'])
        if revision_history:
            st.markdown("### 📚 修订历史")
            
            for revision in revision_history:
                with st.expander(f"修订 {revision['revision_number']}: {revision['change_description']}"):
                    st.write(f"时间: {revision['created_at']}")
                    st.write(f"类型: {revision['change_type']}")
                    
                    if revision.get('user_prompt'):
                        st.text_area("用户提示:", revision['user_prompt'], height=80, disabled=True)
        
        # 审核操作
        st.markdown("---")
        st.markdown("### 🎯 审核决定")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("返回列表"):
                st.session_state.review_mode = "list"
                st.session_state.reviewing_experiment = None
                st.rerun()
        
        with col2:
            if st.button("✅ 批准", type="primary"):
                _approve_experiment(experiment['id'])
        
        with col3:
            if st.button("❌ 拒绝"):
                _reject_experiment(experiment['id'])
        
        with col4:
            if st.button("🔄 要求重审"):
                _request_rereview(experiment['id'])
    
    except Exception as e:
        st.error(f"加载实验详情失败: {e}")
        logging.error(f"Review detail error: {e}")


def _render_validation_details(validation_result: Dict[str, Any]):
    """渲染验证结果详情"""
    if not validation_result:
        return
    
    # 问题列表
    if validation_result.get('issues'):
        st.error("### ❌ 验证问题")
        for i, issue in enumerate(validation_result['issues'], 1):
            st.write(f"{i}. {issue}")
    
    # 警告列表
    if validation_result.get('warnings'):
        st.warning("### ⚠️ 警告信息")
        for i, warning in enumerate(validation_result['warnings'], 1):
            st.write(f"{i}. {warning}")
    
    # 保守建议
    if validation_result.get('conservative_suggestions'):
        st.info("### 💡 保守模式建议")
        for i, suggestion in enumerate(validation_result['conservative_suggestions'], 1):
            st.write(f"{i}. {suggestion}")
    
    # 修改详情
    modifications = validation_result.get('modifications', [])
    if modifications:
        st.success("### ✅ 有效修改")
        for i, mod in enumerate(modifications, 1):
            st.write(f"{i}. **{mod.get('section', '未知章节')}**: {mod.get('justification', '无依据')}")
            st.write(f"   置信度: {mod.get('confidence', 0):.2f}")


def _render_review_statistics():
    """渲染审核统计"""
    st.markdown("## 📊 审核统计")
    
    try:
        experiment_store = ExperimentStore()
        experiments = experiment_store.list_experiments(limit=1000)  # 获取更多数据用于统计
        
        if not experiments:
            st.info("暂无数据")
            return
        
        # 统计分析
        stats = _calculate_review_stats(experiments)
        
        # 总体统计
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总实验数", stats['total_experiments'])
        
        with col2:
            st.metric("验证通过", stats['passed_validations'])
        
        with col3:
            st.metric("需审核", stats['need_review'])
        
        with col4:
            st.metric("平均置信度", f"{stats['avg_confidence']:.2f}")
        
        # 置信度分布
        st.markdown("### 📈 置信度分布")
        confidence_data = stats['confidence_distribution']
        
        if confidence_data:
            import pandas as pd
            df = pd.DataFrame(list(confidence_data.items()), columns=['置信度区间', '数量'])
            st.bar_chart(df.set_index('置信度区间'))
        
        # 问题类型统计
        st.markdown("### 🚨 常见问题类型")
        issue_types = stats['issue_types']
        
        if issue_types:
            for issue_type, count in issue_types.most_common(5):
                st.write(f"- {issue_type}: {count} 次")
        
        # 模板使用统计
        st.markdown("### 📋 模板使用统计")
        template_usage = stats['template_usage']
        
        if template_usage:
            for template_id, count in template_usage.most_common(10):
                st.write(f"- {template_id}: {count} 次使用")
    
    except Exception as e:
        st.error(f"加载统计数据失败: {e}")


def _apply_filters(experiments: List[Dict[str, Any]], status_filter: str, date_filter: str) -> List[Dict[str, Any]]:
    """应用筛选条件"""
    filtered = experiments.copy()
    
    # 状态筛选
    if status_filter != "全部":
        experiment_store = ExperimentStore()
        temp_filtered = []
        
        for exp in filtered:
            full_exp = experiment_store.get_experiment(exp['id'])
            if full_exp:
                validation_result = full_exp.get('validation_result', {})
                confidence = validation_result.get('confidence', 0)
                is_valid = validation_result.get('is_valid', False)
                
                if status_filter == "待审核" and not is_valid:
                    temp_filtered.append(exp)
                elif status_filter == "已通过" and is_valid and confidence >= 0.8:
                    temp_filtered.append(exp)
                elif status_filter == "需修改" and is_valid and confidence < 0.8:
                    temp_filtered.append(exp)
        
        filtered = temp_filtered
    
    # 时间筛选
    if date_filter != "全部":
        from datetime import datetime, timedelta
        
        now = datetime.now()
        if date_filter == "今天":
            cutoff = now - timedelta(days=1)
        elif date_filter == "本周":
            cutoff = now - timedelta(days=7)
        elif date_filter == "本月":
            cutoff = now - timedelta(days=30)
        else:
            cutoff = None
        
        if cutoff:
            temp_filtered = []
            for exp in filtered:
                exp_date = datetime.fromisoformat(exp['created_at'])
                if exp_date >= cutoff:
                    temp_filtered.append(exp)
            filtered = temp_filtered
    
    return filtered


def _calculate_review_stats(experiments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """计算审核统计数据"""
    from collections import Counter
    
    experiment_store = ExperimentStore()
    
    stats = {
        'total_experiments': len(experiments),
        'passed_validations': 0,
        'need_review': 0,
        'avg_confidence': 0.0,
        'confidence_distribution': Counter(),
        'issue_types': Counter(),
        'template_usage': Counter()
    }
    
    confidences = []
    
    for exp in experiments:
        full_exp = experiment_store.get_experiment(exp['id'])
        if not full_exp:
            continue
        
        validation_result = full_exp.get('validation_result', {})
        confidence = validation_result.get('confidence', 0)
        is_valid = validation_result.get('is_valid', False)
        
        # 统计验证状态
        if is_valid and confidence >= 0.8:
            stats['passed_validations'] += 1
        elif not is_valid or confidence < 0.6:
            stats['need_review'] += 1
        
        # 置信度统计
        confidences.append(confidence)
        
        # 置信度分布
        if confidence >= 0.9:
            stats['confidence_distribution']['0.9-1.0'] += 1
        elif confidence >= 0.8:
            stats['confidence_distribution']['0.8-0.9'] += 1
        elif confidence >= 0.6:
            stats['confidence_distribution']['0.6-0.8'] += 1
        else:
            stats['confidence_distribution']['0.0-0.6'] += 1
        
        # 问题类型统计
        for issue in validation_result.get('issues', []):
            # 简单的问题分类
            if "章节" in issue:
                stats['issue_types']['章节问题'] += 1
            elif "不可修改" in issue:
                stats['issue_types']['不可修改章节问题'] += 1
            elif "依据" in issue:
                stats['issue_types']['修改依据问题'] += 1
            else:
                stats['issue_types']['其他问题'] += 1
        
        # 模板使用统计
        stats['template_usage'][exp['template_id']] += 1
    
    # 计算平均置信度
    if confidences:
        stats['avg_confidence'] = sum(confidences) / len(confidences)
    
    return stats


def _approve_experiment(experiment_id: str):
    """批准实验"""
    try:
        experiment_store = ExperimentStore()
        
        # 添加批准记录到修订历史
        experiment_store.add_revision(experiment_id, {
            "change_type": "approval",
            "change_description": "实验记录审核通过",
            "user_prompt": "管理员批准",
            "validation_result": {"approved": True}
        })
        
        st.success(f"✅ 实验 {experiment_id} 已批准")
        st.rerun()
        
    except Exception as e:
        st.error(f"批准实验失败: {e}")
        logging.error(f"Approve experiment error: {e}")


def _reject_experiment(experiment_id: str):
    """拒绝实验"""
    try:
        experiment_store = ExperimentStore()
        
        # 添加拒绝记录到修订历史
        experiment_store.add_revision(experiment_id, {
            "change_type": "rejection",
            "change_description": "实验记录审核未通过",
            "user_prompt": "管理员拒绝",
            "validation_result": {"approved": False}
        })
        
        st.success(f"❌ 实验 {experiment_id} 已拒绝")
        st.rerun()
        
    except Exception as e:
        st.error(f"拒绝实验失败: {e}")
        logging.error(f"Reject experiment error: {e}")


def _request_rereview(experiment_id: str):
    """要求重新审核"""
    try:
        experiment_store = ExperimentStore()
        
        # 添加重审记录到修订历史
        experiment_store.add_revision(experiment_id, {
            "change_type": "rerequest",
            "change_description": "要求重新审核",
            "user_prompt": "管理员要求重审",
            "validation_result": {"rereview_requested": True}
        })
        
        st.success(f"🔄 已要求重新审核实验 {experiment_id}")
        st.rerun()
        
    except Exception as e:
        st.error(f"要求重审失败: {e}")
        logging.error(f"Request rereview error: {e}")