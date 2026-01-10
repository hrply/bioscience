"""
配置管理页面 - 优化版
支持API格式分类和自定义提供商
移除了后端逻辑，提升前端性能
"""

import streamlit as st
import json
import sys
from typing import Dict, List, Any


def run():
    st.title("🎛️ 配置管理")

    # 标签页
    tab1, tab2, tab3 = st.tabs(["API密钥管理", "模型配置", "系统配置"])

    with tab1:
        st.subheader("🔑 API密钥和端点管理")

        try:
            from ai_researcher.secrets_manager import get_secrets_manager

            # 内置常用提供商
            COMMON_PROVIDERS = {
                "openai": {
                    "name": "OpenAI 兼容格式",
                    "default_url": "https://api.openai.com/v1",
                    "description": "OpenAI、DeepSeek、智谱清言、月之暗面、零一万物等"
                },
                "anthropic": {
                    "name": "Anthropic 兼容格式",
                    "default_url": "https://api.anthropic.com",
                    "description": "Anthropic Claude等"
                },
                "gemini": {
                    "name": "Gemini 原生格式",
                    "default_url": "https://generativelanguage.googleapis.com/v1",
                    "description": "Google Gemini等"
                },
                "dashscope": {
                    "name": "阿里巴巴 DASHSCOPE",
                    "default_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    "description": "通义千问、阿里巴巴云等"
                },
                "zai": {
                    "name": "BIGMODEL ZAI",
                    "default_url": "https://open.bigmodel.cn/api/paas/v4",
                    "description": "智谱GLM、BIGMODEL等"
                },
                "custom": {
                    "name": "自定义",
                    "default_url": "",
                    "description": "自定义API格式"
                }
            }

            # ==================== 添加API密钥和端点组合 ====================
            st.markdown("#### 添加API密钥")

            # 使用session_state存储临时数据
            if 'temp_api_config' not in st.session_state:
                st.session_state['temp_api_config'] = {
                    'provider_name': 'openai',
                    'custom_provider': '',
                    'tag': '',
                    'test_model_name': '',
                    'api_key': '',
                    'base_url': ''
                }

            # 表单提交标志
            form_submitted = False

            # 创建表单包装所有输入框
            with st.form("add_api_secret_form"):
                # 第一行：3个输入框（25%, 25%, 50%）
                row1_col1, row1_col2, row1_col3 = st.columns([1, 1, 2])

                # 第一行第一个框：供应商名称输入框
                with row1_col1:
                    st.markdown("**供应商名称**")
                    provider_name = st.selectbox(
                        "",
                        options=list(COMMON_PROVIDERS.keys()),
                        format_func=lambda x: COMMON_PROVIDERS[x]["name"],
                        help="选择或输入供应商名称",
                        key="provider_name",
                        index=list(COMMON_PROVIDERS.keys()).index(st.session_state['temp_api_config']['provider_name']) if st.session_state['temp_api_config']['provider_name'] in COMMON_PROVIDERS else 0
                    )
                    custom_provider = ""
                    if provider_name == "custom":
                        custom_provider = st.text_input(
                            "",
                            placeholder="自定义供应商名称",
                            help="输入自定义供应商名称",
                            key="custom_provider",
                            value=st.session_state['temp_api_config']['custom_provider']
                        )

                # 第一行第二个框：API-KEY输入框
                with row1_col2:
                    st.markdown("**API-KEY**")
                    api_key = st.text_input(
                        "",
                        type="password",
                        placeholder="输入您的API密钥...",
                        help="API密钥将以加密方式安全存储",
                        key="api_key",
                        value=st.session_state['temp_api_config']['api_key']
                    )

                # 第一行第三个框：端点URL输入框
                with row1_col3:
                    st.markdown("**端点URL**")
                    # 如果session_state中有值，使用该值；否则使用默认值
                    if st.session_state['temp_api_config']['base_url']:
                        default_value = st.session_state['temp_api_config']['base_url']
                    else:
                        default_value = COMMON_PROVIDERS.get(provider_name, {}).get("default_url", "")

                    base_url = st.text_input(
                        "",
                        value=default_value,
                        placeholder="https://api.example.com",
                        help="API服务器地址",
                        key="base_url"
                    )

                # 第二行：3个框（25%, 25%, 50%）
                row2_col1, row2_col2, row2_col3 = st.columns([1, 1, 2])

                # 第二行第一个框：标签输入框
                with row2_col1:
                    st.markdown("**标签**")
                    tag = st.text_input(
                        label="",
                        placeholder="例如：生产环境, 测试环境, 开发环境...",
                        label_visibility="collapsed",
                        help="用于标记此组合的用途，便于区分",
                        key="tag",
                        value=st.session_state['temp_api_config']['tag']
                    )

                # 第二行第二个框：API-KEY连通测试框
                with row2_col2:
                    st.markdown("**API-KEY连通测试**")

                    # 初始化session_state
                    if 'test_model_name' not in st.session_state:
                        st.session_state['test_model_name'] = st.session_state['temp_api_config']['test_model_name']

                    # 输入框
                    test_model_name = st.text_input(
                        label="",
                        placeholder="测试模型名称",
                        label_visibility="collapsed",
                        key="test_model_name",
                        value=st.session_state['temp_api_config']['test_model_name'],
                        help="输入要用于测试的模型名称"
                    )

                    # 测试按钮 - 紧挨着输入框
                    st.markdown("""
                    <div style="margin-top: 4px; text-align: right;">
                        <button onclick="
                            var buttons = document.querySelectorAll('button[key=\\'test_connection_btn\\']');
                            if(buttons.length > 0) buttons[0].click();
                        " style="
                            background-color: #4CAF50;
                            color: white;
                            border: none;
                            padding: 4px 12px;
                            border-radius: 4px;
                            cursor: pointer;
                            font-size: 14px;
                            height: 32px;
                            line-height: 32px;
                        ">测试</button>
                    </div>
                    """, unsafe_allow_html=True)

                    # 隐藏disabled按钮
                    st.markdown("""
                    <style>
                    [data-testid="stButton"] button[disabled] {
                        display: none !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)

                    # 隐藏的Streamlit按钮
                    test_connection_btn = st.button(
                        "测试",
                        key="test_connection_btn",
                        help="测试当前API密钥和端点的连通性",
                        disabled=True
                    )

                # 第二行第三个框：完整URL显示框
                with row2_col3:
                    st.markdown("**完整URL**")

                    # 计算完整URL
                    full_url_preview = ""
                    if api_key and test_model_name and base_url:
                        # 这里可以根据提供商类型生成完整URL的预览
                        actual_provider = custom_provider if custom_provider else provider_name
                        provider_lower = actual_provider.lower()

                        if provider_lower in ["anthropic"] or "claude" in provider_lower:
                            full_url_preview = f"{base_url.rstrip('/')}/messages"
                        elif provider_lower in ["gemini"] or "gemini" in provider_lower:
                            full_url_preview = f"{base_url.rstrip('/')}/models/{test_model_name}:generateContent"
                        elif "openai" in provider_lower or "dashscope" in provider_lower or "zai" in provider_lower:
                            full_url_preview = f"{base_url.rstrip('/')}/chat/completions"
                        else:
                            full_url_preview = f"{base_url.rstrip('/')}/chat/completions"

                    # 显示蓝色框
                    st.markdown(f"""
                    <div style="
                        background-color: #E3F2FD;
                        border: 1px solid #90CAF9;
                        border-radius: 0.25rem;
                        padding: 0.5rem 0.75rem;
                        height: 38px;
                        display: flex;
                        align-items: center;
                        font-family: monospace;
                        font-size: 0.9rem;
                        color: #0D47A1;
                        word-break: break-all;
                    ">
                        {full_url_preview if full_url_preview else "完整URL将根据供应商类型自动生成"}
                    </div>
                    """, unsafe_allow_html=True)

                # 使用说明和提交按钮（都在表单内部）
                st.markdown("**使用说明**")
                st.markdown(
                    "- 一个提供商可添加多个组合\n"
                    "- 通过标签区分不同组合的用途\n"
                    "- 支持自定义提供商名称",
                    help="使用说明"
                )

                # 提交按钮（在表单内部）
                col_save1, col_save2, col_save3 = st.columns([1, 1, 2])

                with col_save2:
                    submitted = st.form_submit_button(
                        "💾 保存API密钥组合",
                        type="primary",
                        use_container_width=True
                    )

                # 表单结束 - 提交处理（在表单内部）
                if submitted:
                    actual_provider = custom_provider if custom_provider else provider_name
                    if not actual_provider:
                        st.error("❌ 提供商名称不能为空")
                    elif not api_key:
                        st.error("❌ API密钥不能为空")
                    elif not base_url:
                        st.error("❌ API端点不能为空")
                    else:
                        try:
                            secrets_manager = get_secrets_manager()
                            secret_id = secrets_manager.add_api_secret(
                                provider=actual_provider.strip(),
                                api_key=api_key.strip(),
                                base_url=base_url.strip(),
                                tag=tag.strip() if tag else ""
                            )
                            st.success(
                                f"✅ 已添加API密钥组合！\n"
                                f"ID: {secret_id} | TAG: {tag if tag else '(无标签)'}"
                            )
                            # 清空临时数据
                            st.session_state['temp_api_config'] = {
                                'provider_name': 'openai',
                                'custom_provider': '',
                                'tag': '',
                                'test_model_name': '',
                                'api_key': '',
                                'base_url': ''
                            }
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ 保存失败: {e}")

            # 保存临时数据到session_state（在表单外部）
            st.session_state['temp_api_config']['provider_name'] = provider_name
            st.session_state['temp_api_config']['custom_provider'] = custom_provider
            st.session_state['temp_api_config']['tag'] = tag
            st.session_state['temp_api_config']['test_model_name'] = test_model_name
            st.session_state['temp_api_config']['api_key'] = api_key
            st.session_state['temp_api_config']['base_url'] = base_url

            # 处理API-KEY连通性测试（在表单外部，不影响表单提交）
            if test_connection_btn:
                # 验证输入
                validation_passed = True
                test_error_messages = []

                actual_provider = custom_provider if custom_provider else provider_name

                if not actual_provider:
                    test_error_messages.append("❌ 提供商名称不能为空")
                    validation_passed = False

                if not api_key:
                    test_error_messages.append("❌ API密钥不能为空")
                    validation_passed = False

                if not base_url:
                    test_error_messages.append("❌ API端点不能为空")
                    validation_passed = False

                if not test_model_name:
                    test_error_messages.append("❌ 请输入测试模型名称")
                    validation_passed = False

                if not validation_passed:
                    for msg in test_error_messages:
                        st.error(msg)
                else:
                    # 进行连通性测试
                    with st.spinner("正在测试API-KEY连通性..."):
                        try:
                            secrets_manager = get_secrets_manager()
                            test_result = secrets_manager.test_api_connection(
                                provider=actual_provider.strip(),
                                api_key=api_key.strip(),
                                base_url=base_url.strip(),
                                test_model=test_model_name.strip()
                            )

                            # 显示测试结果
                            if test_result["success"]:
                                st.success(test_result["message"])
                                if "response_preview" in test_result:
                                    st.info(f"响应预览: {test_result['response_preview'][:100]}...")
                            else:
                                st.error(test_result["message"])
                                if "error" in test_result:
                                    st.error(f"错误详情: {test_result['error']}")
                        except Exception as e:
                            st.error(f"❌ 测试连接失败: {str(e)}")

            # 第一行第一个框：供应商名称输入框
            with row1_col1:
                st.markdown("**供应商名称**")
                provider_name = st.selectbox(
                    "",
                    options=list(COMMON_PROVIDERS.keys()),
                    format_func=lambda x: COMMON_PROVIDERS[x]["name"],
                    help="选择或输入供应商名称",
                    key="provider_name",
                    index=list(COMMON_PROVIDERS.keys()).index(st.session_state['temp_api_config']['provider_name']) if st.session_state['temp_api_config']['provider_name'] in COMMON_PROVIDERS else 0
                )
                custom_provider = ""
                if provider_name == "custom":
                    custom_provider = st.text_input(
                        "",
                        placeholder="自定义供应商名称",
                        help="输入自定义供应商名称",
                        key="custom_provider",
                        value=st.session_state['temp_api_config']['custom_provider']
                    )

            # 第一行第二个框：API-KEY输入框
            with row1_col2:
                st.markdown("**API-KEY**")
                api_key = st.text_input(
                    "",
                    type="password",
                    placeholder="输入您的API密钥...",
                    help="API密钥将以加密方式安全存储",
                    key="api_key",
                    value=st.session_state['temp_api_config']['api_key']
                )

            # 第一行第三个框：端点URL输入框
            with row1_col3:
                st.markdown("**端点URL**")
                # 如果session_state中有值，使用该值；否则使用默认值
                if st.session_state['temp_api_config']['base_url']:
                    default_value = st.session_state['temp_api_config']['base_url']
                else:
                    default_value = COMMON_PROVIDERS.get(provider_name, {}).get("default_url", "")

                base_url = st.text_input(
                    "",
                    value=default_value,
                    placeholder="https://api.example.com",
                    help="API服务器地址",
                    key="base_url"
                )

            # 第二行：3个框（25%, 25%, 50%）
            row2_col1, row2_col2, row2_col3 = st.columns([1, 1, 2])

            # 第二行第一个框：标签输入框
            with row2_col1:
                st.markdown("**标签**")
                tag = st.text_input(
                    label="",
                    placeholder="例如：生产环境, 测试环境, 开发环境...",
                    label_visibility="collapsed",
                    help="用于标记此组合的用途，便于区分",
                    key="tag",
                    value=st.session_state['temp_api_config']['tag']
                )

            # 第二行第二个框：API-KEY连通测试框
            with row2_col2:
                st.markdown("**API-KEY连通测试**")

                # 初始化session_state
                if 'test_model_name' not in st.session_state:
                    st.session_state['test_model_name'] = st.session_state['temp_api_config']['test_model_name']

                # 输入框
                test_model_name = st.text_input(
                    label="",
                    placeholder="测试模型名称",
                    label_visibility="collapsed",
                    key="test_model_name",
                    value=st.session_state['temp_api_config']['test_model_name'],
                    help="输入要用于测试的模型名称"
                )

                # 测试按钮 - 紧挨着输入框
                st.markdown("""
                <div style="margin-top: 4px; text-align: right;">
                    <button onclick="
                        var buttons = document.querySelectorAll('button[key=\\'test_connection_btn\\']');
                        if(buttons.length > 0) buttons[0].click();
                    " style="
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        padding: 4px 12px;
                        border-radius: 4px;
                        cursor: pointer;
                        font-size: 14px;
                        height: 32px;
                        line-height: 32px;
                    ">测试</button>
                </div>
                """, unsafe_allow_html=True)

                # 隐藏disabled按钮
                st.markdown("""
                <style>
                [data-testid="stButton"] button[disabled] {
                    display: none !important;
                }
                </style>
                """, unsafe_allow_html=True)

                # 隐藏的Streamlit按钮
                test_connection_btn = st.button(
                    "测试",
                    key="test_connection_btn",
                    help="测试当前API密钥和端点的连通性",
                    disabled=True
                )

            # 第二行第三个框：完整URL显示框
            with row2_col3:
                st.markdown("**完整URL**")

                # 计算完整URL
                full_url_preview = ""
                if api_key and test_model_name and base_url:
                    # 这里可以根据提供商类型生成完整URL的预览
                    actual_provider = custom_provider if custom_provider else provider_name
                    provider_lower = actual_provider.lower()

                    if provider_lower in ["anthropic"] or "claude" in provider_lower:
                        full_url_preview = f"{base_url.rstrip('/')}/messages"
                    elif provider_lower in ["gemini"] or "gemini" in provider_lower:
                        full_url_preview = f"{base_url.rstrip('/')}/models/{test_model_name}:generateContent"
                    elif "openai" in provider_lower or "dashscope" in provider_lower or "zai" in provider_lower:
                        full_url_preview = f"{base_url.rstrip('/')}/chat/completions"
                    else:
                        full_url_preview = f"{base_url.rstrip('/')}/chat/completions"

                # 显示蓝色框
                st.markdown(f"""
                <div style="
                    background-color: #E3F2FD;
                    border: 1px solid #90CAF9;
                    border-radius: 0.25rem;
                    padding: 0.5rem 0.75rem;
                    height: 38px;
                    display: flex;
                    align-items: center;
                    font-family: monospace;
                    font-size: 0.9rem;
                    color: #0D47A1;
                    word-break: break-all;
                ">
                    {full_url_preview if full_url_preview else "完整URL将根据供应商类型自动生成"}
                </div>
                """, unsafe_allow_html=True)

            # 使用说明和提交按钮（都在表单内部）
            st.markdown("**使用说明**")
            st.markdown(
                "- 一个提供商可添加多个组合\n"
                "- 通过标签区分不同组合的用途\n"
                "- 支持自定义提供商名称",
                help="使用说明"
            )

            # 提交按钮（在表单内部）
            col_save1, col_save2, col_save3 = st.columns([1, 1, 2])

            with col_save2:
                submitted = st.form_submit_button(
                    "💾 保存API密钥组合",
                    type="primary",
                    use_container_width=True
                )

            # 表单结束 - 提交处理（在表单内部）
            if submitted:
                actual_provider = custom_provider if custom_provider else provider_name
                if not actual_provider:
                    st.error("❌ 提供商名称不能为空")
                elif not api_key:
                    st.error("❌ API密钥不能为空")
                elif not base_url:
                    st.error("❌ API端点不能为空")
                else:
                    try:
                        secrets_manager = get_secrets_manager()
                        secret_id = secrets_manager.add_api_secret(
                            provider=actual_provider.strip(),
                            api_key=api_key.strip(),
                            base_url=base_url.strip(),
                            tag=tag.strip() if tag else ""
                        )
                        st.success(
                            f"✅ 已添加API密钥组合！\n"
                            f"ID: {secret_id} | TAG: {tag if tag else '(无标签)'}"
                        )
                        # 清空临时数据
                        st.session_state['temp_api_config'] = {
                            'provider_name': 'openai',
                            'custom_provider': '',
                            'tag': '',
                            'test_model_name': '',
                            'api_key': '',
                            'base_url': ''
                        }
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 保存失败: {e}")

            # 表单结束

        # 保存临时数据到session_state（在表单外部）
        st.session_state['temp_api_config']['provider_name'] = provider_name
        st.session_state['temp_api_config']['custom_provider'] = custom_provider
        st.session_state['temp_api_config']['tag'] = tag
        st.session_state['temp_api_config']['test_model_name'] = test_model_name
        st.session_state['temp_api_config']['api_key'] = api_key
        st.session_state['temp_api_config']['base_url'] = base_url

        # 处理API-KEY连通性测试（在表单外部，不影响表单提交）
        if test_connection_btn:
            # 验证输入
            validation_passed = True
            test_error_messages = []

            actual_provider = custom_provider if custom_provider else provider_name

            if not actual_provider:
                test_error_messages.append("❌ 提供商名称不能为空")
                validation_passed = False

            if not api_key:
                test_error_messages.append("❌ API密钥不能为空")
                validation_passed = False

            if not base_url:
                test_error_messages.append("❌ API端点不能为空")
                validation_passed = False

            if not test_model_name:
                test_error_messages.append("❌ 请输入测试模型名称")
                validation_passed = False

            if not validation_passed:
                for msg in test_error_messages:
                    st.error(msg)
            else:
                # 进行连通性测试
                with st.spinner("正在测试API-KEY连通性..."):
                    try:
                        secrets_manager = get_secrets_manager()
                        test_result = secrets_manager.test_api_connection(
                            provider=actual_provider.strip(),
                            api_key=api_key.strip(),
                            base_url=base_url.strip(),
                            test_model=test_model_name.strip()
                        )

                        # 显示测试结果
                        if test_result["success"]:
                            st.success(test_result["message"])
                            if "response_preview" in test_result:
                                st.info(f"响应预览: {test_result['response_preview'][:100]}...")
                        else:
                            st.error(test_result["message"])
                            if "error" in test_result:
                                st.error(f"错误详情: {test_result['error']}")
                    except Exception as e:
                        st.error(f"❌ 测试连接失败: {str(e)}")

        st.markdown("---")

        # ==================== 当前配置列表 ====================
        st.markdown("#### 📋 当前配置")

        secrets_manager = get_secrets_manager()

        # 获取所有API密钥和端点组合
        all_secrets = secrets_manager.get_api_secrets()

        if not all_secrets:
            st.info("📭 暂无配置，请添加API密钥组合")
        else:
            # 按提供商分组显示
            providers = {}
            for secret in all_secrets:
                provider = secret['provider']
                if provider not in providers:
                    providers[provider] = []
                providers[provider].append(secret)

            for provider, secrets in sorted(providers.items()):
                st.markdown(f"##### {provider}")
                with st.container():
                    for secret in secrets:
                        tag = secret['tag'] if secret['tag'] else "(无标签)"
                        key_preview = secret['api_key'][:10] + "..." if len(secret['api_key']) > 10 else secret['api_key']
                        endpoint = secret['base_url'] if secret['base_url'] else "(无端点)"

                        st.markdown(
                            f"**ID:** `{secret['id']}` | **TAG:** {tag} | **KEY:** {key_preview} | **ENDPOINT:** {endpoint}"
                        )
                    st.markdown("---")

        st.markdown("---")

        # ==================== 删除功能 ====================
        st.markdown("#### 🗑️ 删除API密钥组合")

        with st.expander("删除API密钥组合"):
            if not all_secrets:
                st.info("暂无配置可删除")
            else:
                # 创建删除选项
                secret_options = {}
                for secret in all_secrets:
                    tag_display = secret['tag'] if secret['tag'] else "(无标签)"
                    key_display = f"{secret['api_key'][:10]}..."
                    endpoint_display = secret['base_url'] if secret['base_url'] else "(无端点)"
                    option_text = (
                        f"[{secret['provider']}] "
                        f"ID:{secret['id']} | TAG:{tag_display} | "
                        f"KEY:{key_display} | ENDPOINT:{endpoint_display}"
                    )
                    secret_options[option_text] = secret['id']

                if secret_options:
                    selected_option = st.selectbox(
                        "选择要删除的组合",
                        options=list(secret_options.keys()),
                        help="选择一个API密钥和端点组合进行删除"
                    )

                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col2:
                        if st.button("❌ 删除组合", type="secondary"):
                            selected_id = secret_options[selected_option]
                            st.session_state['secret_to_delete'] = {
                                'id': selected_id,
                                'option': selected_option
                            }

                    # 确认删除对话框
                    if 'secret_to_delete' in st.session_state:
                        secret_info = st.session_state['secret_to_delete']
                        st.warning(
                            f"⚠️ 确认要删除组合吗？\n\n{secret_info['option']}\n\n"
                            f"此操作不可撤销！"
                        )

                        col4, col5 = st.columns(2)
                        with col4:
                            if st.button("✅ 确认删除", type="primary"):
                                try:
                                    success = secrets_manager.delete_api_secret_by_id(
                                        secret_info['id']
                                    )
                                    if success:
                                        st.success("✅ API密钥组合已删除！")
                                        del st.session_state['secret_to_delete']
                                        st.rerun()
                                    else:
                                        st.error("❌ 删除失败，组合可能已被删除")
                                        del st.session_state['secret_to_delete']
                                except Exception as e:
                                    st.error(f"❌ 删除失败: {e}")
                                    del st.session_state['secret_to_delete']

                        with col5:
                            if st.button("❌ 取消"):
                                del st.session_state['secret_to_delete']
                                st.rerun()
                else:
                    st.info("暂无配置可删除")

    except Exception as e:
        st.error(f"加载API密钥状态失败: {e}")

    with tab2:
        st.subheader("🤖 模型配置")

        try:
            from ai_researcher.models.config_manager import ModelConfigManager
            from ai_researcher.secrets_manager import get_secrets_manager

            manager = ModelConfigManager()
            secrets_manager = get_secrets_manager()

            # 获取所有提供商和端点
            providers = secrets_manager.get_all_providers()
            base_urls = secrets_manager.get_all_base_urls()

            # ==================== 添加模型配置 ====================
            st.markdown("➕ 添加模型配置")

            with st.form("add_model_config"):
                # 基本配置
                st.markdown("**基本配置**")
                col1, col2 = st.columns(2)

                with col1:
                    config_name = st.text_input("配置名称", placeholder="例如：My-GPT4")
                    provider = st.selectbox(
                        "提供商",
                        options=sorted(providers) if providers else ["无可用提供商"],
                        help="选择已在API密钥管理中配置的提供商"
                    )

                with col2:
                    model_name = st.text_input("模型名称", placeholder="例如：gpt-4, claude-3, gemini-pro")
                    api_type = st.selectbox(
                        "API类型",
                        options=[
                            "chat",
                            "messages",
                            "generateContent",
                            "response",
                            "reasoning",
                            "new_api"
                        ],
                        index=0,
                        format_func=lambda x: {
                            "chat": "Chat Completions (OpenAI兼容)",
                            "messages": "Messages (Anthropic兼容)",
                            "generateContent": "GenerateContent (Gemini原生)",
                            "response": "Response (通用)",
                            "reasoning": "Reasoning (推理模型)",
                            "new_api": "NEW-API (API代理，兼容三种格式)"
                        }.get(x, x),
                        help="""根据API格式选择类型：
• chat: 补全路径 → /v1/chat/completions
• messages: 补全路径 → /v1/messages
• generateContent: 补全路径 → /v1/generateContent
• response: 不补全路径（通用格式）
• reasoning: 不补全路径（推理模型）
• new_api: 根据模型名自动选择：
  - 含gpt/openai → /v1/chat/completions
  - 含claude/anthropic → /v1/messages
  - 含gemini/google → /v1/generateContent"""
                    )

                # 端点配置
                st.markdown("**端点配置**")
                if api_type == "new_api":
                    st.info("💡 NEW-API 说明", icon="ℹ️")
                    st.write("NEW-API 是一个API代理，通过基础URL兼容三种格式：")
                    st.write("• 含gpt/openai → 补全 → https://xxx.com/v1/chat/completions")
                    st.write("• 含claude/anthropic → 补全 → https://xxx.com/v1/messages")
                    st.write("• 含gemini/google → 补全 → https://xxx.com/v1/generateContent")
                    st.write("只需输入基础URL，如：https://api.example.com")

                if providers and base_urls:
                    selected_endpoint = st.selectbox(
                        "选择已配置的端点",
                        options=sorted(base_urls.keys()) if base_urls else ["无可用端点"],
                        help="选择已在API端点管理中配置的端点" if api_type != "new_api" else "选择NEW-API代理的基础URL"
                    )

                    if selected_endpoint and selected_endpoint != "无可用端点":
                        base_url_value = base_urls[selected_endpoint]
                        # 如果是NEW-API类型，显示完整的URL预览
                        if api_type == "new_api":
                            from ai_researcher.models.api_client import UnifiedAPIClient
                            full_url = UnifiedAPIClient.get_full_url_preview(base_url_value, api_type, model_name)
                            st.caption(f"💡 完整URL将自动生成为: {full_url}")
                            if not model_name:
                                st.caption("⚠️ 请先填写模型名称以获得准确预览")
                        else:
                            st.caption(f"端点URL: {base_url_value}")
                else:
                    selected_endpoint = st.text_input(
                        "或直接输入端点URL",
                        placeholder="https://api.example.com" if api_type == "new_api" else "https://...",
                        help="NEW-API请输入基础URL，如：https://api.example.com"
                    )

                # API密钥选择
                st.markdown("**API密钥选择**")
                # 获取所有API密钥和端点组合
                all_secrets = secrets_manager.get_api_secrets()

                # 根据选中的提供商过滤组合
                available_secrets = [s for s in all_secrets if s['provider'] == provider] if provider != "无可用提供商" else []

                if available_secrets:
                    # 创建下拉选项：显示 TAG | API-KEY | 端点
                    secret_options = {}
                    for secret in available_secrets:
                        tag = secret['tag'] if secret['tag'] else "(无标签)"
                        key_preview = f"{secret['api_key'][:8]}...{secret['api_key'][-4:]}"
                        endpoint = secret['base_url'] if secret['base_url'] else "(无端点)"
                        option_text = f"{tag} | {key_preview} | {endpoint}"
                        secret_options[option_text] = secret['id']

                    selected_secret = st.selectbox(
                        "选择API密钥和端点组合",
                        options=list(secret_options.keys()),
                        help="选择一个API密钥和端点组合（TAG | API-KEY | 端点）",
                        key="api_secret_selector"
                    )
                    selected_secret_id = secret_options[selected_secret]
                else:
                    st.warning(f"⚠️ 未找到 '{provider}' 的API密钥组合，请先在API密钥管理中添加")
                    selected_secret_id = None

                # 代理设置
                st.markdown("**网络设置**")
                col_proxy1, col_proxy2 = st.columns([3, 1])

                with col_proxy1:
                    use_proxy = st.checkbox(
                        "通过HTTP代理访问",
                        value=False,
                        help="启用后，将通过HTTP_PROXY环境变量设置的代理访问API"
                    )

                with col_proxy2:
                    st.info("💡 提示", icon="ℹ️")
                    st.write("适用于Gemini等需要代理访问的API")

                if use_proxy:
                    import os
                    proxy_url = os.environ.get('HTTP_PROXY', '')
                    if proxy_url:
                        st.success(f"✅ 代理已配置: {proxy_url}")
                    else:
                        st.warning("⚠️ HTTP_PROXY环境变量未设置，请确保在docker-compose.yml中配置")

                # 参数设置
                st.markdown("**参数设置**")
                col1, col2 = st.columns(2)
                with col1:
                    temperature = st.slider("温度参数", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
                with col2:
                    max_tokens = st.number_input("最大Token数", min_value=100, max_value=32000, value=4000, step=100)

                # 激活选项
                is_active = st.checkbox("立即激活此配置", value=True)

                # 模型连接测试和添加配置按钮
                col_test, col_submit = st.columns([1, 2])

                with col_test:
                    # 模型连接测试按钮
                    test_model_btn = st.button(
                        "🧪 测试模型连接",
                        type="secondary",
                        use_container_width=True,
                        help="点击测试当前配置的模型是否可以正常连接"
                    )

                with col_submit:
                    submitted = st.form_submit_button("💾 添加配置", type="primary")

                # 处理模型连接测试
                if test_model_btn:
                    # 验证输入
                    validation_passed = True
                    test_error_messages = []

                    if not config_name.strip():
                        test_error_messages.append("❌ 配置名称不能为空")
                        validation_passed = False

                    if not model_name.strip():
                        test_error_messages.append("❌ 模型名称不能为空")
                        validation_passed = False

                    if not provider or provider == "无可用提供商":
                        test_error_messages.append("❌ 请选择提供商")
                        validation_passed = False

                    if not api_key.strip():
                        test_error_messages.append("❌ API密钥不能为空")
                        validation_passed = False

                    if not selected_endpoint or selected_endpoint == "无可用端点":
                        test_error_messages.append("❌ 请选择或输入端点URL")
                        validation_passed = False

                    if not validation_passed:
                        for msg in test_error_messages:
                            st.error(msg)
                        st.stop()

                    # 进行连接测试
                    with st.spinner("正在测试模型连接..."):
                        try:
                            # 获取端点URL
                            if selected_endpoint and selected_endpoint != "无可用端点" and selected_endpoint in base_urls:
                                test_endpoint = base_urls[selected_endpoint]
                            else:
                                test_endpoint = selected_endpoint

                            # 如果是NEW-API类型，生成完整URL预览
                            if api_type == "new_api":
                                from ai_researcher.models.api_client import UnifiedAPIClient
                                full_url = UnifiedAPIClient.get_full_url_preview(test_endpoint, api_type, model_name)
                                test_endpoint_for_api = full_url
                            else:
                                test_endpoint_for_api = test_endpoint

                            # 调用测试连接
                            secrets_manager = get_secrets_manager()
                            test_result = secrets_manager.test_api_connection(
                                provider=provider,
                                api_key=api_key.strip(),
                                base_url=test_endpoint_for_api,
                                test_model=model_name.strip()
                            )

                            # 显示测试结果
                            if test_result["success"]:
                                st.success(test_result["message"])
                                if "response_preview" in test_result:
                                    st.info(f"响应预览: {test_result['response_preview'][:100]}...")
                            else:
                                st.error(test_result["message"])
                                if "error" in test_result:
                                    st.error(f"错误详情: {test_result['error']}")
                        except Exception as e:
                            st.error(f"❌ 测试连接失败: {str(e)}")

                if submitted:
                    # 验证输入
                    validation_passed = True

                    if not config_name.strip():
                        st.error("❌ 配置名称不能为空")
                        validation_passed = False

                    if not model_name.strip():
                        st.error("❌ 模型名称不能为空")
                        validation_passed = False

                    # 检查是否选择了API密钥组合
                    if not selected_secret_id:
                        st.error("❌ 请先选择API密钥和端点组合")
                        validation_passed = False

                    if not validation_passed:
                        st.stop()

                    try:
                        # 使用选择的API密钥组合ID
                        api_secret_id_value = selected_secret_id

                        # 获取完整的API密钥组合信息
                        secret_info = secrets_manager.get_api_secret_by_id(selected_secret_id)
                        if not secret_info:
                            st.error("❌ 无法获取API密钥组合信息")
                            st.stop()

                        # 如果是NEW-API类型，显示完整URL预览
                        if api_type == "new_api":
                            from ai_researcher.models.api_client import UnifiedAPIClient
                            full_url = UnifiedAPIClient.get_full_url_preview(
                                secret_info['base_url'], api_type, model_name
                            )
                            st.success(f"✅ NEW-API完整URL: {full_url}", icon="✅")

                        success = manager.add_model_config(
                            name=config_name,
                            provider=provider,
                            endpoint=secret_info['base_url'],
                            api_type=api_type,
                            api_key=secret_info['api_key'],
                            api_secret_id=api_secret_id_value,
                            model_name=model_name,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            use_proxy=use_proxy,
                            is_active=is_active
                        )

                        if success:
                            st.session_state['config_saved'] = True
                            st.session_state['config_name'] = config_name
                        else:
                            st.error("❌ 添加配置失败，请检查配置是否已存在")
                    except Exception as e:
                        st.error(f"❌ 添加配置失败: {e}")

            # 显示保存成功的提示
            if st.session_state.get('config_saved', False):
                st.success(f"✅ 配置 '{st.session_state.get('config_name', '')}' 添加成功！")
                # 清除状态
                del st.session_state['config_saved']
                if 'config_name' in st.session_state:
                    del st.session_state['config_name']

            st.markdown("---")

            # ==================== 配置列表 ====================
            st.markdown("📋 当前配置")

            configs = manager.list_model_configs()

            if not configs:
                st.info("📭 暂无模型配置")
            else:
                for config in configs:
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                        with col1:
                            status = "✅ 激活" if config.get('is_active') else "○ 未激活"
                            st.markdown(f"**{config['name']}** {status}")
                            st.caption(f"{config['provider']} - {config['model_name']}")

                        with col2:
                            if st.button("👁️ 查看", key=f"view_{config['name']}"):
                                st.session_state[f'view_config_{config["name"]}'] = True

                        with col3:
                            if st.button("🧪 测试", key=f"test_{config['name']}"):
                                st.session_state[f'test_config_{config["name"]}'] = True

                        with col4:
                            if st.button("🗑️ 删除", key=f"delete_{config['name']}"):
                                st.session_state[f'delete_config_{config["name"]}'] = True

                        # 查看详情
                        if st.session_state.get(f'view_config_{config["name"]}', False):
                            st.markdown("---")
                            st.json(config)
                            if st.button("✅ 关闭", key=f"close_view_{config['name']}"):
                                st.session_state[f'view_config_{config["name"]}'] = False
                                st.rerun()

                        # 测试连接
                        if st.session_state.get(f'test_config_{config["name"]}', False):
                            st.markdown("---")
                            with st.spinner("正在测试连接..."):
                                try:
                                    result = manager.test_connection(config['name'])
                                    if result['success']:
                                        st.success("✅ 连接测试成功")
                                    else:
                                        st.error(f"❌ 连接测试失败: {result.get('error', '未知错误')}")
                                except Exception as e:
                                    st.error(f"测试连接失败: {e}")

                            if st.button("✅ 关闭", key=f'close_test_{config["name"]}'):
                                st.session_state[f'test_config_{config["name"]}'] = False
                                st.rerun()

                        # 删除确认
                        if st.session_state.get(f'delete_config_{config["name"]}', False):
                            st.warning(f"⚠️ 确定要删除配置 '{config['name']}' 吗？")
                            col_a, col_b = st.columns(2)

                            with col_a:
                                if st.button("✅ 确认删除", key=f"confirm_delete_{config['name']}"):
                                    try:
                                        success = manager.delete_model_config(config['name'])
                                        if success:
                                            st.session_state['config_deleted'] = True
                                            st.session_state['config_deleted_name'] = config['name']
                                            st.session_state[f'delete_config_{config["name"]}'] = False
                                            st.rerun()
                                        else:
                                            st.error("❌ 删除失败")
                                    except Exception as e:
                                        st.error(f"❌ 删除配置失败: {e}")

                            with col_b:
                                if st.button("❌ 取消", key=f"cancel_delete_{config['name']}"):
                                    st.session_state[f'delete_config_{config["name"]}'] = False
                                    st.rerun()

            # 显示删除成功的提示
            if st.session_state.get('config_deleted', False):
                config_name = st.session_state.get('config_deleted_name', '')
                st.success(f"✅ 配置 '{config_name}' 已删除！")
                del st.session_state['config_deleted']
                del st.session_state['config_deleted_name']

            st.markdown("---")

        except Exception as e:
            st.error(f"加载模型配置失败: {e}")

    with tab3:
        st.subheader("⚙️ 系统配置")

        # RAGFlow配置
        st.markdown("### 📚 RAGFlow知识库配置")

        try:
            from ai_researcher.config import load_config, save_config
            from ai_researcher.core.ragflow import RAGFlowClient, RAGFlowError
            config = load_config()

            # 当前配置
            current_config = config.get('ragflow', {})
            current_endpoint = current_config.get('endpoint', 'http://192.168.3.147:20334')
            current_api_key = current_config.get('api_key', '')
            current_ports = current_config.get('ports', {})

            # 端口配置字典
            port_defaults = {
                'SVR_WEB_HTTP_PORT': 20334,
                'SVR_WEB_HTTPS_PORT': 443,
                'SVR_HTTP_PORT': 20335,
                'ADMIN_SVR_HTTP_PORT': 20336,
                'SVR_MCP_PORT': 20337,
            }

            st.info("ℹ️ RAGFlow Docker端口映射配置", icon="ℹ️")
            st.caption("⚠️ 端口需与RAGFlow docker-compose.yml一致")

            with st.form("ragflow_config_form"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    endpoint = st.text_input(
                        "RAGFlow服务端点",
                        value=current_endpoint,
                        help="用于检索知识库文献，例如：http://192.168.3.147:20334"
                    )

                with col2:
                    api_key = st.text_input(
                        "RAGFlow API密钥",
                        value=current_api_key,
                        type="password",
                        help="RAGFlow的访问密钥（可选）"
                    )

                st.markdown("**端口映射配置**")
                ports_cols = st.columns(3)
                ports_data = {}

                port_items = list(port_defaults.items())
                for idx, (port_name, default_val) in enumerate(port_items):
                    col = ports_cols[idx % 3]
                    with col:
                        ports_data[port_name] = st.number_input(
                            port_name,
                            value=current_ports.get(port_name, default_val),
                            min_value=1,
                            max_value=65535,
                            help=f"{port_name}端口配置"
                        )

                submitted = st.form_submit_button(
                    "💾 保存配置",
                    type="primary",
                    use_container_width=True
                )

                if submitted:
                    try:
                        config['ragflow'] = {
                            'endpoint': endpoint.strip(),
                            'api_key': api_key.strip(),
                            'ports': {k: int(v) for k, v in ports_data.items()}
                        }

                        if save_config(config):
                            st.success("✅ RAGFlow配置已保存")
                            st.rerun()
                        else:
                            st.error("❌ 保存失败")
                    except Exception as e:
                        st.error(f"❌ 保存失败: {e}")

            # 快速操作
            col1, col2 = st.columns(2)

            with col1:
                if st.button("🔍 测试连接", use_container_width=True):
                    try:
                        client = RAGFlowClient(
                            endpoint=current_endpoint,
                            api_key=current_api_key,
                            ports=current_ports
                        )
                        health = client.health_check()
                        if health:
                            st.success("✅ RAGFlow连接成功")
                        else:
                            st.warning("⚠️ RAGFlow服务未响应")
                    except Exception as e:
                        st.error(f"❌ 连接失败: {str(e)[:100]}")

            with col2:
                if st.button("🔄 重置为默认", use_container_width=True):
                    try:
                        config['ragflow'] = {
                            'endpoint': 'http://192.168.3.147:20334',
                            'api_key': '',
                            'ports': port_defaults
                        }
                        if save_config(config):
                            st.success("✅ 已重置为默认配置")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ 重置失败: {e}")

            # 显示当前配置状态
            st.markdown("---")
            st.markdown("**当前配置**")
            if current_endpoint:
                st.caption(f"端点: {current_endpoint}")
            if current_api_key:
                st.caption("API密钥: ✅ 已配置")
            else:
                st.caption("API密钥: ❌ 未配置")

            st.markdown("**端口配置**")
            for port_name, port_value in (current_ports or port_defaults).items():
                st.caption(f"{port_name}: {port_value}")

        except Exception as e:
            st.error(f"加载配置失败: {e}")

        # 数据库配置
        st.markdown("---")
        st.markdown("### 💾 数据库配置")

        try:
            import os
            db_path = os.environ.get('DATABASE_PATH', '/app/data/experiments/experiments.db')

            st.info(f"当前数据库路径: {db_path}")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("📊 查看数据库状态"):
                    try:
                        from ai_researcher.experiments.manager import ExperimentManager
                        exp_manager = ExperimentManager(db_path)
                        experiments = exp_manager.list_experiments()
                        st.success(f"✅ 数据库正常，共 {len(experiments)} 个实验")
                    except Exception as e:
                        st.error(f"❌ 数据库异常: {e}")

            with col2:
                if st.button("🗃️ 初始化数据库"):
                    try:
                        from ai_researcher.experiments.manager import ExperimentManager
                        exp_manager = ExperimentManager(db_path)
                        st.success("✅ 数据库初始化成功")
                    except Exception as e:
                        st.error(f"❌ 初始化失败: {e}")

        except Exception as e:
            st.error(f"数据库操作失败: {e}")

        # 系统信息
        st.markdown("---")
        st.markdown("### ℹ️ 系统信息")

        sys_info = {
            "Python版本": sys.version.split()[0],
            "Streamlit版本": st.__version__,
        }

        for key, value in sys_info.items():
            st.write(f"**{key}**: {value}")


if __name__ == "__main__":
    run()
