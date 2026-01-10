"""
模板管理页面
"""

import streamlit as st
import yaml
import json
from pathlib import Path


def run():
    st.title("📋 模板管理")

    # 标签页
    tab1, tab2, tab3 = st.tabs(["查看模板", "添加模板", "模板详情"])

    with tab1:
        st.subheader("📚 可用模板")

        try:
            from ai_researcher.templates.manager import TemplateManager
            template_manager = TemplateManager()
            templates = template_manager.list_templates()

            if not templates:
                st.info("📭 暂无模板，请先添加模板")
            else:
                # 模板卡片
                for template_name, description in templates.items():
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])

                        with col1:
                            st.markdown(f"### 📄 {template_name}")
                            st.caption(description)

                        with col2:
                            st.markdown("<br/>", unsafe_allow_html=True)
                            if st.button("👁️ 查看", key=f"view_{template_name}"):
                                st.session_state[f'view_template_{template_name}'] = True

                        with col3:
                            st.markdown("<br/>", unsafe_allow_html=True)
                            if st.button("🗑️ 删除", key=f"delete_{template_name}"):
                                st.session_state[f'delete_template_{template_name}'] = True

                        # 查看模板详情
                        if st.session_state.get(f'view_template_{template_name}', False):
                            st.markdown("---")
                            st.subheader(f"📄 模板详情: {template_name}")

                            try:
                                template_content = template_manager.get_template(template_name)
                                st.json(template_content)
                            except Exception as e:
                                st.error(f"加载模板失败: {e}")

                            if st.button("✅ 关闭", key=f"close_view_{template_name}"):
                                st.session_state[f'view_template_{template_name}'] = False
                                st.rerun()

                        # 删除确认
                        if st.session_state.get(f'delete_template_{template_name}', False):
                            st.warning(f"⚠️ 确定要删除模板 '{template_name}' 吗？")
                            col_a, col_b = st.columns(2)

                            with col_a:
                                if st.button("✅ 确认删除", key=f"confirm_delete_{template_name}"):
                                    try:
                                        template_manager.delete_template(template_name)
                                        st.success(f"✅ 模板 '{template_name}' 已删除")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"删除模板失败: {e}")

                            with col_b:
                                if st.button("❌ 取消", key=f"cancel_delete_{template_name}"):
                                    st.session_state[f'delete_template_{template_name}'] = False
                                    st.rerun()

                        st.markdown("---")

        except Exception as e:
            st.error(f"加载模板列表失败: {e}")

    with tab2:
        st.subheader("➕ 添加新模板")

        template_name = st.text_input("模板名称：", placeholder="例如：细胞培养实验")
        template_description = st.text_area("模板描述：", placeholder="简要描述这个模板的用途...")

        # 模板内容输入方式
        input_method = st.radio(
            "选择输入方式：",
            options=["JSON编辑器", "YAML编辑器", "文件上传"],
            horizontal=True
        )

        template_content = None

        if input_method == "JSON编辑器":
            template_json = st.text_area(
                "模板内容 (JSON格式)：",
                height=400,
                placeholder='{\n  "name": "模板名称",\n  "description": "描述",\n  "steps": [\n    {\n      "name": "步骤1",\n      "description": "步骤描述",\n      "details": "详细说明"\n    }\n  ]\n}'
            )
            if template_json:
                try:
                    template_content = json.loads(template_json)
                    st.success("✅ JSON格式验证通过")
                except json.JSONDecodeError:
                    st.error("❌ JSON格式错误")

        elif input_method == "YAML编辑器":
            template_yaml = st.text_area(
                "模板内容 (YAML格式)：",
                height=400,
                placeholder='name: 模板名称\ndescription: 描述\nsteps:\n  - name: 步骤1\n    description: 步骤描述\n    details: 详细说明'
            )
            if template_yaml:
                try:
                    template_content = yaml.safe_load(template_yaml)
                    st.success("✅ YAML格式验证通过")
                except yaml.YAMLError:
                    st.error("❌ YAML格式错误")

        else:  # 文件上传
            uploaded_file = st.file_uploader(
                "上传模板文件：",
                type=["yaml", "yml", "json"],
                help="支持 .yaml, .yml, .json 格式"
            )

            if uploaded_file:
                try:
                    file_extension = Path(uploaded_file.name).suffix.lower()
                    if file_extension in [".yaml", ".yml"]:
                        template_content = yaml.safe_load(uploaded_file)
                    else:  # .json
                        template_content = json.load(uploaded_file)
                    st.success("✅ 文件加载成功")
                    template_name = uploaded_file.name.split('.')[0]
                except Exception as e:
                    st.error(f"加载文件失败: {e}")

        # 保存按钮
        if st.button("💾 保存模板", type="primary", disabled=template_content is None):
            try:
                from ai_researcher.templates.manager import TemplateManager
                template_manager = TemplateManager()

                if not template_name:
                    st.error("请输入模板名称")
                else:
                    template_manager.add_template(
                        name=template_name,
                        description=template_description,
                        content=template_content
                    )
                    st.success(f"✅ 模板 '{template_name}' 添加成功！")
                    st.rerun()
            except Exception as e:
                st.error(f"添加模板失败: {e}")

        # 模板示例
        with st.expander("💡 查看模板格式示例", expanded=False):
            st.markdown("""
            ### JSON格式示例
            ```json
            {
              "name": "细胞培养实验",
              "description": "用于细胞培养的标准操作流程",
              "category": "细胞生物学",
              "steps": [
                {
                  "name": "准备培养基",
                  "description": "准备新鲜的细胞培养基",
                  "details": "DMEM培养基 + 10% FBS + 1% P/S",
                  "duration": "10分钟",
                  "notes": "所有试剂需预热至37°C"
                },
                {
                  "name": "细胞复苏",
                  "description": "从液氮中取出细胞并复苏",
                  "details": "37°C水浴快速解冻，缓慢加入培养基",
                  "duration": "5分钟",
                  "notes": "避免长时间室温暴露"
                }
              ],
              "materials": [
                "DMEM培养基",
                "胎牛血清",
                "青霉素-链霉素",
                "胰蛋白酶"
              ]
            }
            ```

            ### YAML格式示例
            ```yaml
            name: 细胞培养实验
            description: 用于细胞培养的标准操作流程
            category: 细胞生物学
            steps:
              - name: 准备培养基
                description: 准备新鲜的细胞培养基
                details: DMEM培养基 + 10% FBS + 1% P/S
                duration: 10分钟
                notes: 所有试剂需预热至37°C
              - name: 细胞复苏
                description: 从液氮中取出细胞并复苏
                details: 37°C水浴快速解冻，缓慢加入培养基
                duration: 5分钟
                notes: 避免长时间室温暴露
            materials:
              - DMEM培养基
              - 胎牛血清
              - 青霉素-链霉素
              - 胰蛋白酶
            ```
            """)

    with tab3:
        st.subheader("🔍 模板详情")

        try:
            from ai_researcher.templates.manager import TemplateManager
            template_manager = TemplateManager()
            templates = template_manager.list_templates()

            if templates:
                selected_template = st.selectbox(
                    "选择模板：",
                    options=list(templates.keys())
                )

                if selected_template:
                    try:
                        template_content = template_manager.get_template(selected_template)

                        col1, col2 = st.columns([3, 1])

                        with col1:
                            st.markdown(f"### 📄 {selected_template}")
                            st.caption(templates[selected_template])

                        with col2:
                            st.download_button(
                                label="💾 导出模板",
                                data=json.dumps(template_content, indent=2, ensure_ascii=False),
                                file_name=f"{selected_template}.json",
                                mime="application/json",
                                use_container_width=True
                            )

                        st.markdown("---")
                        st.json(template_content)

                        # 步骤详情
                        if 'steps' in template_content:
                            st.markdown("### 📋 实验步骤")
                            for i, step in enumerate(template_content['steps'], 1):
                                with st.container():
                                    st.markdown(f"#### 步骤 {i}: {step.get('name', '')}")
                                    st.markdown(f"**描述**: {step.get('description', '')}")
                                    if 'details' in step:
                                        st.markdown(f"**详细说明**: {step['details']}")
                                    if 'duration' in step:
                                        st.markdown(f"**预计时长**: {step['duration']}")
                                    if 'notes' in step:
                                        st.markdown(f"**注意事项**: {step['notes']}")
                                    st.markdown("---")

                    except Exception as e:
                        st.error(f"加载模板失败: {e}")
            else:
                st.info("暂无模板")

        except Exception as e:
            st.error(f"加载模板列表失败: {e}")


if __name__ == "__main__":
    run()
