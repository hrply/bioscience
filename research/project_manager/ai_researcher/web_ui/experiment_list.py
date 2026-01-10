"""
实验列表页面
"""

import streamlit as st
import pandas as pd
from datetime import datetime


def run():
    st.title("📋 实验列表")

    # 筛选器
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search_term = st.text_input("🔍 搜索实验：", placeholder="输入实验ID或标题...")

    with col2:
        status_filter = st.selectbox(
            "状态筛选：",
            options=["全部", "planned", "in_progress", "completed", "failed"],
            index=0,
            format_func=lambda x: {
                "全部": "全部状态",
                "planned": "计划中",
                "in_progress": "进行中",
                "completed": "已完成",
                "failed": "失败"
            }.get(x, x)
        )

    with col3:
        sort_by = st.selectbox(
            "排序方式：",
            options=["created_at", "updated_at", "status"],
            format_func=lambda x: {
                "created_at": "创建时间",
                "updated_at": "更新时间",
                "status": "状态"
            }.get(x, x)
        )

    # 获取实验数据
    try:
        from ai_researcher.experiments.manager import ExperimentManager
        import os

        db_path = os.environ.get('DATABASE_PATH', '/app/data/experiments/experiments.db')
        exp_manager = ExperimentManager(db_path)
        experiments = exp_manager.list_experiments()

        # 应用筛选
        if status_filter != "全部":
            experiments = [e for e in experiments if e.get('status') == status_filter]

        if search_term:
            experiments = [
                e for e in experiments
                if search_term.lower() in e.get('id', '').lower()
                or search_term.lower() in e.get('title', '').lower()
            ]

        # 排序
        experiments = sorted(experiments, key=lambda x: x.get(sort_by, ''), reverse=True)

        if not experiments:
            st.info("📭 暂无实验记录")
            if st.button("➕ 创建第一个实验", type="primary"):
                st.session_state['selected_page'] = '🔬 创建实验'
                st.rerun()
            return

        # 显示统计信息
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总数", len(experiments))
        with col2:
            planned = len([e for e in experiments if e.get('status') == 'planned'])
            st.metric("计划中", planned)
        with col3:
            in_progress = len([e for e in experiments if e.get('status') == 'in_progress'])
            st.metric("进行中", in_progress)
        with col4:
            completed = len([e for e in experiments if e.get('status') == 'completed'])
            st.metric("已完成", completed)

        st.markdown("---")

        # 实验卡片
        for exp in experiments:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                with col1:
                    status_color = {
                        "planned": "🟡",
                        "in_progress": "🔵",
                        "completed": "🟢",
                        "failed": "🔴"
                    }.get(exp.get('status', 'planned'), "⚪")

                    st.markdown(f"### {status_color} {exp.get('title', 'N/A')}")
                    st.caption(f"ID: {exp.get('id', 'N/A')}")
                    st.caption(f"目标: {exp.get('objective', 'N/A')[:100]}...")

                with col2:
                    st.markdown("**创建时间**")
                    created_at = exp.get('created_at', '')
                    if created_at:
                        st.caption(created_at[:19])

                with col3:
                    st.markdown("**更新时间**")
                    updated_at = exp.get('updated_at', '')
                    if updated_at:
                        st.caption(updated_at[:19])

                with col4:
                    st.markdown("**操作**")
                    col_a, col_b = st.columns(2)

                    with col_a:
                        if st.button("👁️ 查看", key=f"view_{exp.get('id')}"):
                            st.session_state[f'view_experiment_{exp.get("id")}'] = True

                    with col_b:
                        if st.button("✏️ 更新", key=f"update_{exp.get('id')}"):
                            st.session_state[f'update_experiment_{exp.get("id")}'] = True

                # 实验详情（可展开）
                if st.session_state.get(f'view_experiment_{exp.get("id")}', False):
                    st.markdown("---")
                    st.subheader("📄 实验详情")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.json(exp)

                    with col2:
                        st.markdown("**进度历史**")
                        try:
                            progress_history = exp_manager.get_progress_history(exp.get('id'))
                            if progress_history:
                                for p in progress_history:
                                    st.info(f"📅 {p['timestamp'][:19]}: {p['status']}")
                                    if p.get('notes'):
                                        st.caption(f"  {p['notes']}")
                            else:
                                st.caption("暂无进度记录")
                        except Exception as e:
                            st.error(f"加载进度历史失败: {e}")

                    if st.button("✅ 关闭详情", key=f"close_view_{exp.get('id')}"):
                        st.session_state[f'view_experiment_{exp.get("id")}'] = False
                        st.rerun()

                # 更新状态
                if st.session_state.get(f'update_experiment_{exp.get("id")}', False):
                    st.markdown("---")
                    st.subheader("✏️ 更新实验状态")

                    new_status = st.selectbox(
                        "选择新状态：",
                        options=["planned", "in_progress", "completed", "failed"],
                        index=["planned", "in_progress", "completed", "failed"].index(exp.get('status', 'planned')) + 1
                        if exp.get('status') in ["planned", "in_progress", "completed", "failed"] else 0,
                        format_func=lambda x: {
                            "planned": "计划中",
                            "in_progress": "进行中",
                            "completed": "已完成",
                            "failed": "失败"
                        }.get(x, x)
                    )

                    notes = st.text_area("备注 (可选)：", placeholder="记录实验进度或注意事项...")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💾 保存更新", key=f"save_{exp.get('id')}"):
                            try:
                                exp_manager.update_progress(
                                    experiment_id=exp.get('id'),
                                    status=new_status,
                                    notes=notes
                                )
                                st.success("✅ 状态更新成功！")
                                st.session_state[f'update_experiment_{exp.get("id")}'] = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"更新失败: {e}")

                    with col2:
                        if st.button("❌ 取消", key=f"cancel_{exp.get('id')}"):
                            st.session_state[f'update_experiment_{exp.get("id")}'] = False
                            st.rerun()

                st.markdown("---")

        # 批量操作
        st.subheader("🔧 批量操作")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🗑️ 删除选中实验", type="secondary", use_container_width=True):
                st.warning("功能开发中...")

        with col2:
            if st.button("📊 导出实验数据", type="secondary", use_container_width=True):
                if experiments:
                    df = pd.DataFrame(experiments)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="💾 下载CSV",
                        data=csv,
                        file_name=f"experiments_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

    except Exception as e:
        st.error(f"加载实验列表失败: {e}")
        st.info("请确保数据库已初始化，可以尝试运行：")
        st.code("python -m ai_researcher.cli init")


if __name__ == "__main__":
    run()
