"""
结果分析页面 - 优化版
移除了不必要的import，提升加载性能
"""

import streamlit as st


def run():
    st.title("📊 结果分析")

    # 选择实验
    st.subheader("1️⃣ 选择实验")
    try:
        # 按需导入（移入函数内）
        from ai_researcher.experiments.manager import ExperimentManager
        import os

        db_path = os.environ.get('DATABASE_PATH', '/app/data/experiments/experiments.db')
        exp_manager = ExperimentManager(db_path)
        experiments = exp_manager.list_experiments()

        if not experiments:
            st.info("📭 暂无实验记录，请先创建实验")
            return

        # 过滤已完成的实验
        completed_experiments = [
            e for e in experiments
            if e.get('status') in ['completed', 'in_progress']
        ]

        if not completed_experiments:
            st.warning("⚠️ 没有可分析的实验（需要已完成或进行中的实验）")
            return

        exp_options = {
            f"{e.get('id')} - {e.get('title', 'N/A')}": e
            for e in completed_experiments
        }

        selected_exp = st.selectbox(
            "选择要分析的实验：",
            options=list(exp_options.keys())
        )

        experiment = exp_options[selected_exp]
        exp_id = experiment.get('id')

    except Exception as e:
        st.error(f"加载实验列表失败: {e}")
        return

    st.markdown("---")

    # 数据上传
    st.subheader("2️⃣ 上传数据文件")
    st.info("支持格式：CSV, Excel (.xlsx), JSON")

    uploaded_file = st.file_uploader(
        "选择数据文件：",
        type=["csv", "xlsx", "json"],
        help="上传包含实验结果的数据文件"
    )

    if uploaded_file:
        # 读取数据
        try:
            with st.spinner("正在加载数据..."):
                file_extension = Path(uploaded_file.name).suffix.lower()

                if file_extension == ".csv":
                    data = pd.read_csv(uploaded_file)
                elif file_extension == ".xlsx":
                    data = pd.read_excel(uploaded_file)
                elif file_extension == ".json":
                    json_data = json.load(uploaded_file)
                    data = pd.DataFrame(json_data)
                else:
                    st.error("不支持的文件格式")
                    return

            # 显示数据概览
            st.success(f"✅ 数据加载成功！共 {data.shape[0]} 行 × {data.shape[1]} 列")
            col1, col2 = st.columns(2)

            with col1:
                st.metric("数据行数", data.shape[0])
                st.metric("数据列数", data.shape[1])

            with col2:
                st.metric("数值列数", len(data.select_dtypes(include=['number']).columns))
                st.metric("文本列数", len(data.select_dtypes(include=['object']).columns))

            st.markdown("---")

            # 数据预览
            with st.expander("👀 查看数据前5行", expanded=True):
                st.dataframe(data.head(), use_container_width=True)

            # 数据统计
            st.markdown("---")
            st.subheader("3️⃣ 基础统计分析")

            with st.expander("📈 描述性统计", expanded=True):
                numeric_data = data.select_dtypes(include=['number'])
                if not numeric_data.empty:
                    st.dataframe(numeric_data.describe(), use_container_width=True)
                else:
                    st.warning("数据中没有数值列")

            with st.expander("📋 数据类型", expanded=False):
                st.write(data.dtypes)

            # AI分析
            st.markdown("---")
            st.subheader("4️⃣ AI智能分析")

            col1, col2 = st.columns([3, 1])

            with col1:
                st.text_area(
                    "添加分析说明 (可选)：",
                    placeholder="例如：请重点分析组间差异、显著性检验结果等...",
                    key="analysis_notes"
                )

            with col2:
                st.markdown("<br/>", unsafe_allow_html=True)
                if st.button("🤖 开始AI分析", type="primary", use_container_width=True):
                    with st.spinner("正在进行AI分析，请稍候..."):
                        try:
                            from ai_researcher.core.agent import ResearchAgent
                            from ai_researcher.core.models.base import BaseModel

                            # 获取模型配置
                            agent = ResearchAgent()
                            model = agent.model

                            # 准备分析数据
                            data_summary = {
                                "shape": data.shape,
                                "columns": list(data.columns),
                                "dtypes": data.dtypes.to_dict(),
                                "numeric_cols": list(data.select_dtypes(include=['number']).columns),
                                "description": data.describe().to_dict() if not data.select_dtypes(include=['number']).empty else {}
                            }

                            # 构建提示词
                            prompt = f"""
                            请对以下实验数据进行智能分析：

                            实验信息：
                            - 实验ID: {exp_id}
                            - 实验标题: {experiment.get('title', 'N/A')}
                            - 实验目标: {experiment.get('objective', 'N/A')}

                            数据概览：
                            {json.dumps(data_summary, indent=2, default=str, ensure_ascii=False)}

                            额外说明：
                            {st.session_state.get('analysis_notes', '无')}

                            请提供：
                            1. 数据质量评估
                            2. 主要发现和趋势
                            3. 统计显著性分析
                            4. 实验结果解读
                            5. 后续实验建议
                            """

                            # 调用AI分析
                            if hasattr(model, 'generate_response'):
                                response = model.generate_response(prompt)
                                st.markdown("### 🤖 AI分析结果")
                                st.markdown(response)
                            else:
                                st.error("当前模型不支持AI分析功能")

                        except Exception as e:
                            st.error(f"AI分析失败: {e}")
                            st.info("请检查：1) API密钥配置 2) 模型连接 3) 数据格式")

            # 数据可视化
            st.markdown("---")
            st.subheader("5️⃣ 数据可视化")

            if not data.select_dtypes(include=['number']).empty:
                col1, col2 = st.columns(2)

                with col1:
                    chart_type = st.selectbox(
                        "选择图表类型：",
                        options=["分布图", "相关性热图", "箱线图", "散点图", "条形图"]
                    )

                with col2:
                    numeric_columns = data.select_dtypes(include=['number']).columns.tolist()
                    if len(numeric_columns) >= 2:
                        x_col = st.selectbox("X轴 (数值列):", numeric_columns)
                        y_col = st.selectbox("Y轴 (数值列):", [c for c in numeric_columns if c != x_col])
                    else:
                        x_col = None
                        y_col = None

                # 生成图表
                if chart_type:
                    with st.spinner("正在生成图表..."):
                        try:
                            import matplotlib.pyplot as plt
                            import seaborn as sns
                            import io
                            import base64

                            fig, ax = plt.subplots(figsize=(10, 6))

                            if chart_type == "分布图":
                                data[x_col].hist(bins=30, ax=ax)
                                ax.set_title(f"{x_col} 分布图")
                                ax.set_xlabel(x_col)
                                ax.set_ylabel("频次")

                            elif chart_type == "相关性热图":
                                corr_data = data.select_dtypes(include=['number']).corr()
                                sns.heatmap(corr_data, annot=True, cmap='coolwarm', center=0, ax=ax)
                                ax.set_title("相关性热图")

                            elif chart_type == "箱线图" and x_col and y_col:
                                # 需要一个分类列
                                cat_columns = data.select_dtypes(include=['object']).columns
                                if len(cat_columns) > 0:
                                    cat_col = st.selectbox("分组列 (分类):", cat_columns, key="boxplot_group")
                                    data.boxplot(column=y_col, by=cat_col, ax=ax)
                                    ax.set_title(f"{y_col} 按 {cat_col} 分组")
                                else:
                                    data.boxplot(column=numeric_columns[0], ax=ax)
                                    ax.set_title(f"{numeric_columns[0]} 箱线图")

                            elif chart_type == "散点图" and x_col and y_col:
                                ax.scatter(data[x_col], data[y_col])
                                ax.set_xlabel(x_col)
                                ax.set_ylabel(y_col)
                                ax.set_title(f"{x_col} vs {y_col}")

                            elif chart_type == "条形图":
                                # 需要分类列
                                cat_columns = data.select_dtypes(include=['object']).columns
                                if len(cat_columns) > 0:
                                    cat_col = st.selectbox("分组列 (分类):", cat_columns, key="barplot_group")
                                    value_col = st.selectbox("数值列:", numeric_columns, key="barplot_value")
                                    data.groupby(cat_col)[value_col].mean().plot(kind='bar', ax=ax)
                                    ax.set_title(f"按 {cat_col} 分组的 {value_col} 平均值")
                                    plt.xticks(rotation=45)
                                else:
                                    st.warning("需要至少一个分类列来生成条形图")

                            plt.tight_layout()
                            st.pyplot(fig)
                            plt.close()

                            # 保存图表
                            img_buffer = io.BytesIO()
                            fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                            img_buffer.seek(0)
                            st.download_button(
                                label="💾 下载图表",
                                data=img_buffer,
                                file_name=f"analysis_{exp_id}_{chart_type}.png",
                                mime="image/png"
                            )

                        except Exception as e:
                            st.error(f"生成图表失败: {e}")
            else:
                st.warning("数据中没有数值列，无法生成图表")

        except Exception as e:
            st.error(f"处理文件失败: {e}")

    # 分析历史
    st.markdown("---")
    st.subheader("📚 分析历史")

    try:
        # 显示分析记录
        st.info("功能开发中... 将显示历史分析记录")
    except Exception as e:
        st.error(f"加载分析历史失败: {e}")


if __name__ == "__main__":
    run()
