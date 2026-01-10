"""
创建实验页面
"""

import streamlit as st
import json
from pathlib import Path


def run():
    st.title("🔬 创建新实验")

    # 实验目标输入
    st.subheader("1️⃣ 输入实验目标")
    objective = st.text_area(
        "请描述您的实验目标：",
        height=150,
        placeholder="例如：研究药物X对肺癌细胞A549的增殖抑制作用"
    )

    # 选择模板
    st.subheader("2️⃣ 选择实验模板")
    try:
        from ai_researcher.templates.manager import TemplateManager
        template_manager = TemplateManager()
        templates = template_manager.list_templates()

        if templates:
            selected_template = st.selectbox(
                "选择实验模板：",
                options=list(templates.keys()),
                format_func=lambda x: f"{x} - {templates[x]}"
            )
        else:
            st.warning("未找到模板，使用默认模板")
            selected_template = None
    except Exception as e:
        st.error(f"加载模板失败: {e}")
        selected_template = None

    # 选择模型
    st.subheader("3️⃣ 选择AI模型")
    col1, col2 = st.columns(2)

    with col1:
        model_provider = st.selectbox(
            "模型提供商：",
            options=["openai", "gemini", "anthropic"],
            format_func=lambda x: {
                "openai": "OpenAI (GPT-4, GPT-3.5)",
                "gemini": "Google Gemini",
                "anthropic": "Anthropic Claude"
            }.get(x, x)
        )

    with col2:
        model_names = {
            "openai": ["gpt-4", "gpt-3.5-turbo"],
            "gemini": ["gemini-pro"],
            "anthropic": ["claude-3-opus", "claude-3-sonnet"]
        }
        model_name = st.selectbox(
            "模型名称：",
            options=model_names.get(model_provider, ["default"]),
            index=0
        )

    # RAGFlow配置
    st.subheader("4️⃣ 知识库配置")
    ragflow_endpoint = st.text_input(
        "RAGFlow服务端点：",
        value="http://192.168.3.147:20334",
        help="用于检索相关文献和知识库"
    )

    # 生成方案按钮
    if st.button("🚀 生成实验方案", type="primary", use_container_width=True):
        if not objective:
            st.error("请输入实验目标")
        else:
            with st.spinner("正在生成实验方案..."):
                try:
                    # 导入ResearchAgent
                    from ai_researcher.core.agent import ResearchAgent

                    # 初始化Agent
                    agent = ResearchAgent(
                        model_provider=model_provider,
                        model_name=model_name,
                        ragflow_endpoint=ragflow_endpoint
                    )

                    # 生成实验方案
                    plan = agent.generate_experiment_plan(
                        objective=objective,
                        template=selected_template
                    )

                    # 显示结果
                    st.success("✅ 实验方案生成成功！")

                    st.markdown("---")
                    st.subheader("📋 实验方案详情")

                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**实验ID:** {plan.get('id', 'N/A')}")
                        st.markdown(f"**实验标题:** {plan.get('title', 'N/A')}")
                        st.markdown(f"**状态:** {plan.get('status', 'N/A')}")

                    with col2:
                        st.metric("进度", "0%")

                    st.markdown("---")
                    st.subheader("📄 完整方案")
                    st.json(plan)

                    # 提供后续操作
                    st.markdown("---")
                    st.subheader("🎯 后续操作")
                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("📋 查看实验列表", use_container_width=True):
                            st.session_state['selected_page'] = '📋 实验列表'
                            st.rerun()

                    with col2:
                        if st.button("🚀 开始实验", use_container_width=True):
                            from ai_researcher.core.agent import ResearchAgent
                            agent = ResearchAgent(
                                model_provider=model_provider,
                                model_name=model_name,
                                ragflow_endpoint=ragflow_endpoint
                            )
                            agent.update_progress(plan['id'], "in_progress")
                            st.success("实验已开始！")
                            st.rerun()

                except Exception as e:
                    st.error(f"生成实验方案失败: {e}")
                    st.info("请检查：1) API密钥是否配置 2) RAGFlow服务是否可用 3) 网络连接")

    # 使用说明
    st.markdown("---")
    with st.expander("💡 使用说明", expanded=False):
        st.markdown("""
        ### 如何使用？

        1. **输入实验目标**：清晰描述您要进行的实验，包括：
           - 实验对象（如：细胞、动物、样本类型）
           - 实验目的（如：药物效果、基因功能、蛋白表达）
           - 检测指标（如：增殖、凋亡、表达水平）

        2. **选择模板**：根据实验类型选择合适的模板：
           - 细胞培养：细胞培养和传代实验
           - PCR：基因扩增和定量分析
           - Western Blot：蛋白质表达检测
           - 流式细胞术：细胞表型和功能分析
           - 等等...

        3. **选择AI模型**：
           - GPT-4：推荐用于复杂实验设计
           - Gemini Pro：平衡性能和成本
           - Claude：擅长长文本分析

        4. **配置RAGFlow**：连接您的知识库，AI将检索相关文献支持

        ### 💡 提示
        - 实验目标越详细，生成的方案越精准
        - 选择合适的模板可提高方案质量
        - 知识库连接后可以基于文献生成更可靠的方案
        """)


if __name__ == "__main__":
    run()
