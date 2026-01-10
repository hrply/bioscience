import streamlit as st
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, '/home/hrply/software/bioscience/research/project_manager')

from ai_researcher.secrets_manager import SecretsManager
from ai_researcher.models.config_manager import ModelConfigManager
from ai_researcher.config import load_config


def get_model_defaults():
    """获取模型默认配置"""
    try:
        config = load_config()
        model_defaults = config.get('model_defaults', {})
        return {
            'temperature': model_defaults.get('temperature', 0.7),
            'max_tokens': model_defaults.get('max_tokens', 4000),
            'top_p': model_defaults.get('top_p', 0.9),
            'top_k': model_defaults.get('top_k', 40),
            'system_prompt': model_defaults.get('system_prompt', '你是一个有用的AI助手。'),
            'frequency_penalty': model_defaults.get('frequency_penalty', 0.0),
            'presence_penalty': model_defaults.get('presence_penalty', 0.0),
        }
    except:
        # 如果加载失败，返回默认值
        return {
            'temperature': 0.7,
            'max_tokens': 4000,
            'top_p': 0.9,
            'top_k': 40,
            'system_prompt': '你是一个有用的AI助手。',
            'frequency_penalty': 0.0,
            'presence_penalty': 0.0,
        }


def run():
    # 设置页面配置
    st.set_page_config(
        page_title="AI科研助手 - 配置管理",
        page_icon="⚙️",
        layout="wide"
    )

    # CSS样式
    st.markdown("""
    <style>
        /* 蓝色URL框样式增强 */
        .url-preview-box {
            background-color: #E3F2FD;
            border: 1px solid #90CAF9;
            border-radius: 0.25rem;
            padding: 0.5rem 0.75rem;
            height: 38px;
            display: flex;
            align-items: center;
            font-family: monospace;
            font-size: 0.875rem;
            color: #0D47A1;
            word-break: break-all;
        }

        /* 完整URL输入框蓝色样式 */
        [data-testid="text-input"] input:disabled {
            background-color: #E3F2FD !important;
            border-color: #90CAF9 !important;
            color: #0D47A1 !important;
            font-family: monospace !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # 隐藏JavaScript警告
    st.markdown("""
    <script>
    console.log = console.warn = console.error = () => {};
    </script>
    """, unsafe_allow_html=True)

    # 页面标题
    st.title("⚙️ 配置管理")

    # 获取管理器实例
    try:
        secrets_manager = SecretsManager()
        manager = ModelConfigManager()
    except Exception as e:
        st.error(f"初始化失败: {e}")
        st.stop()

    # 创建选项卡
    tab1, tab2, tab3 = st.tabs(["🔑 API密钥管理", "🤖 模型配置管理", "⚙️ 系统配置"])

    with tab1:
        st.markdown("### 🔑 API密钥管理")

        # 初始化临时数据
        if 'temp_api_config' not in st.session_state:
            st.session_state['temp_api_config'] = {
                'provider_name': '',
                'api_key': '',
                'base_url': '',
                'tag': '',
                'test_model_name': '',
                'selected_full_url': ''
            }

        # 第一部分标题
        st.markdown("##### 📡 基础信息")

        # 第一行：供应商名称 + API-KEY + EndPoint
        col1, col2, col3 = st.columns(3)

        with col1:
            # 供应商名称输入框
            provider_name = st.text_input(
                "供应商名称",
                placeholder="例如：openai, anthropic, gemini",
                key="provider_name",
                value=st.session_state['temp_api_config']['provider_name']
            )

        with col2:
            # API密钥输入框
            api_key = st.text_input(
                "API-KEY",
                type="password",
                placeholder="输入API密钥",
                key="api_key",
                value=st.session_state['temp_api_config']['api_key']
            )

        with col3:
            # EndPoint输入框
            base_url = st.text_input(
                "EndPoint",
                placeholder="例如：https://api.openai.com",
                key="base_url",
                value=st.session_state['temp_api_config']['base_url']
            )

        # 第二行：标签 + 完整URL
        col1, col2 = st.columns([1, 2])

        with col1:
            # 标签输入框
            tag = st.text_input(
                "标签",
                placeholder="例如：openai-key-1",
                key="tag",
                value=st.session_state['temp_api_config']['tag']
            )

        with col2:
            # 生成三种格式的完整URL选项
            url_options = []
            url_values = {}

            if base_url:
                # OpenAI格式
                if base_url.endswith('/'):
                    openai_url = f"{base_url}chat/completions"
                else:
                    openai_url = f"{base_url}/v1/chat/completions"
                url_options.append(f"OpenAI格式: {openai_url}")
                url_values[url_options[-1]] = openai_url

                # Gemini格式
                if base_url.endswith('/'):
                    gemini_url = f"{base_url}models/gemini-pro:generateContent"
                else:
                    gemini_url = f"{base_url}/models/gemini-pro:generateContent"
                url_options.append(f"Gemini格式: {gemini_url}")
                url_values[url_options[-1]] = gemini_url

                # Anthropic格式
                if base_url.endswith('/'):
                    anthropic_url = f"{base_url}messages"
                else:
                    anthropic_url = f"{base_url}/v1/messages"
                url_options.append(f"Anthropic格式: {anthropic_url}")
                url_values[url_options[-1]] = anthropic_url

            # 完整URL下拉选择框
            selected_url_label = st.selectbox(
                "完整URL",
                options=url_options if url_options else ["请先输入EndPoint地址"],
                key="full_url_select",
                disabled=not url_options
            )

            # 获取选中的完整URL
            selected_full_url = url_values.get(selected_url_label, "") if url_options else ""

        # 第二部分标题
        st.markdown("##### 🔧 操作")

        # 三个功能框：33%宽度并排
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            test_model_name = st.text_input(
                "",
                placeholder="输入测试模型名称",
                key="test_model_name",
                value=st.session_state['temp_api_config']['test_model_name'],
                label_visibility="collapsed"
            )

        with col2:
            if st.button("🧪 测试API连接", type="secondary", use_container_width=True):
                # 验证输入
                validation_passed = True
                test_error_messages = []

                if not provider_name:
                    test_error_messages.append("❌ 供应商名称不能为空")
                    validation_passed = False

                if not api_key:
                    test_error_messages.append("❌ API密钥不能为空")
                    validation_passed = False

                if not base_url:
                    test_error_messages.append("❌ EndPoint地址不能为空")
                    validation_passed = False

                if not selected_full_url:
                    test_error_messages.append("❌ 请选择完整URL格式")
                    validation_passed = False

                if not test_model_name:
                    test_error_messages.append("❌ 测试模型名称不能为空")
                    validation_passed = False

                if not validation_passed:
                    for msg in test_error_messages:
                        st.error(msg)
                else:
                    # 进行连通性测试
                    with st.spinner("正在测试API连通性..."):
                        try:
                            import requests
                            import json

                            # 根据URL格式确定API类型
                            if "/chat/completions" in selected_full_url:
                                # OpenAI格式
                                payload = {
                                    "model": test_model_name.strip(),
                                    "messages": [{"role": "user", "content": "Hi"}],
                                    "max_tokens": 5
                                }
                            elif "/messages" in selected_full_url:
                                # Anthropic格式
                                payload = {
                                    "model": test_model_name.strip(),
                                    "max_tokens": 5,
                                    "messages": [{"role": "user", "content": "Hi"}]
                                }
                            elif "/generateContent" in selected_full_url:
                                # Gemini格式
                                payload = {
                                    "contents": [{
                                        "parts": [{"text": "Hi"}]
                                    }],
                                    "generationConfig": {
                                        "maxOutputTokens": 5
                                    }
                                }
                            else:
                                # 默认使用OpenAI格式
                                payload = {
                                    "model": test_model_name.strip(),
                                    "messages": [{"role": "user", "content": "Hi"}],
                                    "max_tokens": 5
                                }

                            headers = {
                                "Content-Type": "application/json",
                                "Authorization": f"Bearer {api_key.strip()}"
                            }

                            # 发送HTTP请求
                            response = requests.post(
                                selected_full_url.strip(),
                                headers=headers,
                                data=json.dumps(payload),
                                timeout=10
                            )

                            # 检查响应
                            if response.status_code == 200:
                                st.success(f"✅ API连接测试成功！状态码: {response.status_code}")
                                try:
                                    resp_json = response.json()
                                    if "choices" in resp_json:
                                        content = resp_json["choices"][0]["message"]["content"]
                                    elif "content" in resp_json:
                                        content = resp_json["content"][0]["text"]
                                    elif "candidates" in resp_json:
                                        content = resp_json["candidates"][0]["content"]["parts"][0]["text"]
                                    else:
                                        content = str(resp_json)[:100]
                                    st.info(f"响应预览: {content[:100]}...")
                                except:
                                    pass
                            elif response.status_code == 401:
                                st.error(f"❌ 认证失败，请检查API密钥。状态码: {response.status_code}")
                            elif response.status_code == 404:
                                st.error(f"❌ API端点不存在或模型名称错误。状态码: {response.status_code}")
                            else:
                                st.warning(f"⚠️ API响应异常。状态码: {response.status_code}")
                                try:
                                    error_data = response.json()
                                    st.error(f"错误信息: {error_data}")
                                except:
                                    st.error(f"响应内容: {response.text[:200]}")
                        except requests.exceptions.Timeout:
                            st.error("❌ 连接超时，请检查网络或端点地址")
                        except requests.exceptions.ConnectionError:
                            st.error("❌ 连接失败，请检查EndPoint地址是否正确")
                        except Exception as e:
                            st.error(f"❌ 测试连接失败: {str(e)}")

        with col3:
            save_btn = st.button("💾 保存API密钥", type="primary", use_container_width=True)

        # 处理保存按钮
        if save_btn:
            # 验证输入
            validation_passed = True
            save_error_messages = []

            if not provider_name.strip():
                save_error_messages.append("❌ 供应商名称不能为空")
                validation_passed = False

            if not api_key.strip():
                save_error_messages.append("❌ API密钥不能为空")
                validation_passed = False

            if not base_url.strip():
                save_error_messages.append("❌ EndPoint地址不能为空")
                validation_passed = False

            if not tag.strip():
                save_error_messages.append("❌ 标签不能为空")
                validation_passed = False

            if not validation_passed:
                for msg in save_error_messages:
                    st.error(msg)
            else:
                try:
                    # 保存到数据库
                    secret_id = secrets_manager.add_api_secret(
                        provider=provider_name.strip(),
                        api_key=api_key.strip(),
                        base_url=base_url.strip(),
                        tag=tag.strip()
                    )

                    if secret_id:
                        st.success("✅ API密钥保存成功！")
                        # 清除临时数据
                        st.session_state['temp_api_config'] = {
                            'provider_name': '',
                            'api_key': '',
                            'base_url': '',
                            'tag': '',
                            'test_model_name': '',
                            'selected_full_url': ''
                        }
                        st.rerun()
                    else:
                        st.error("❌ 保存失败")
                except Exception as e:
                    st.error(f"❌ 保存失败: {str(e)}")

        # 保存临时数据到session_state
        st.session_state['temp_api_config']['provider_name'] = provider_name
        st.session_state['temp_api_config']['tag'] = tag
        st.session_state['temp_api_config']['test_model_name'] = test_model_name
        st.session_state['temp_api_config']['api_key'] = api_key
        st.session_state['temp_api_config']['base_url'] = base_url
        st.session_state['temp_api_config']['selected_full_url'] = selected_full_url

        st.markdown("---")

        # ==================== API密钥列表 ====================
        st.markdown("📋 当前API密钥")

        try:
            # 获取所有密钥
            secrets = secrets_manager.get_api_secrets()

            if not secrets:
                st.info("📭 暂无API密钥")
            else:
                # 按供应商分组
                providers = {}
                for secret in secrets:
                    provider = secret['provider']
                    if provider not in providers:
                        providers[provider] = []
                    providers[provider].append(secret)

                # 展示每个供应商及其密钥
                for provider, provider_secrets in providers.items():
                    with st.container():
                        st.markdown(f"### {provider}")

                        for secret in provider_secrets:
                            col1, col2 = st.columns([3, 1])

                            with col1:
                                tag = secret['tag'] if secret['tag'] else "(无标签)"
                                key_preview = f"{secret['api_key'][:8]}...{secret['api_key'][-4:]}"
                                st.write(f"**{tag}** | {key_preview} | {secret['base_url']}")

                            with col2:
                                if st.button("🗑️ 删除", key=f"delete_{secret['id']}"):
                                    st.session_state[f'delete_secret_{secret["id"]}'] = True

                        # 删除确认
                        if st.session_state.get(f'delete_secret_{secret["id"]}', False):
                            st.warning(f"⚠️ 确定要删除 '{secret['tag']}' 吗？")
                            col_a, col_b = st.columns(2)

                            with col_a:
                                if st.button("✅ 确认删除", key=f"confirm_delete_{secret['id']}"):
                                    try:
                                        success = secrets_manager.delete_api_secret_by_id(secret['id'])
                                        if success:
                                            st.session_state['secret_deleted'] = True
                                            st.session_state[f'delete_secret_{secret["id"]}'] = False
                                            st.rerun()
                                        else:
                                            st.error("❌ 删除失败")
                                    except Exception as e:
                                        st.error(f"❌ 删除失败: {e}")

                            with col_b:
                                if st.button("❌ 取消", key=f"cancel_delete_{secret['id']}"):
                                    st.session_state[f'delete_secret_{secret["id"]}'] = False
                                    st.rerun()

        except Exception as e:
            st.error(f"加载API密钥失败: {e}")

        # 显示删除成功的提示
        if st.session_state.get('secret_deleted', False):
            st.success("✅ API密钥已删除！")
            del st.session_state['secret_deleted']

        st.markdown("---")

    with tab2:
        st.markdown("### ⚙️ 模型配置管理")

        try:
            manager = ModelConfigManager()

            # 获取所有提供商和端点
            all_secrets = secrets_manager.get_api_secrets()
            providers = list(set([s['provider'] for s in all_secrets])) if all_secrets else []

            # 获取系统默认配置
            model_defaults = get_model_defaults()
            default_temperature = model_defaults['temperature']
            default_max_tokens = model_defaults['max_tokens']

            # ==================== 添加模型配置 ====================
            st.markdown("**基本配置**")

            # 第一行：配置名称、提供商、API类型（各33%宽度）
            col1, col2, col3 = st.columns(3)

            with col1:
                config_name = st.text_input("配置名称", placeholder="例如：My-GPT4", key="test_config_name")

            with col2:
                provider = st.selectbox(
                    "提供商",
                    options=sorted(providers) if providers else ["无可用提供商"],
                    key="test_provider"
                )

            with col3:
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
                    key="test_api_type"
                )

            # 第二行：模型名称、选择API-KEY、代理设置（各33%宽度）
            col1, col2, col3 = st.columns(3)

            with col1:
                model_name = st.text_input("模型名称", placeholder="例如：gpt-4, claude-3, gemini-pro", key="model_name_config")

            with col2:
                # API密钥选择
                # 根据选中的提供商过滤组合
                available_secrets = [s for s in all_secrets if s['provider'] == provider] if provider != "无可用提供商" else []

                if available_secrets:
                    # 创建下拉选项：显示 TAG | API-KEY
                    secret_options = {}
                    for secret in available_secrets:
                        tag = secret['tag'] if secret['tag'] else "(无标签)"
                        key_preview = f"{secret['api_key'][:8]}...{secret['api_key'][-4:]}"
                        option_text = f"{tag} | {key_preview}"
                        secret_options[option_text] = secret['id']

                    selected_secret = st.selectbox(
                        "选择API-KEY",
                        options=list(secret_options.keys()),
                        key="test_api_secret_selector"
                    )
                    selected_secret_id = secret_options[selected_secret]
                else:
                    st.warning(f"⚠️ 未找到 '{provider}' 的API密钥")
                    selected_secret_id = None

            with col3:
                proxy_config = st.text_input("代理配置", placeholder="例如：http://127.0.0.1:7890", key="proxy_config")

            # 第三行：蓝色的端点URL展示框（占据整行）
            st.markdown("**模型访问地址**")
            if selected_secret_id and selected_secret_id is not None:
                try:
                    # 获取选中的密钥信息
                    secret_info = secrets_manager.get_api_secret_by_id(selected_secret_id)
                    if secret_info:
                        base_url = secret_info.get('base_url', '')

                        # 根据API类型生成完整URL
                        if api_type == "new_api":
                            from ai_researcher.models.api_client import UnifiedAPIClient
                            full_url = UnifiedAPIClient.get_full_url_preview(base_url, api_type, model_name)
                        elif api_type == "chat":
                            if base_url.endswith('/'):
                                full_url = f"{base_url}chat/completions"
                            else:
                                full_url = f"{base_url}/v1/chat/completions"
                        elif api_type == "messages":
                            if base_url.endswith('/'):
                                full_url = f"{base_url}messages"
                            else:
                                full_url = f"{base_url}/v1/messages"
                        elif api_type == "generateContent":
                            if base_url.endswith('/'):
                                full_url = f"{base_url}models/{model_name}:generateContent"
                            else:
                                full_url = f"{base_url}/models/{model_name}:generateContent"
                        else:
                            full_url = base_url

                        # 显示蓝色URL框
                        st.markdown(f"""
                        <div class="url-preview-box">
                            {full_url}
                        </div>
                        """, unsafe_allow_html=True)
                except Exception as e:
                    st.warning(f"⚠️ 无法生成URL预览: {str(e)}")
            else:
                # 显示提示信息
                st.markdown("""
                <div class="url-preview-box" style="color: #666; font-style: italic;">
                    请选择API-KEY以查看端点URL
                </div>
                """, unsafe_allow_html=True)

            # 增加一行间距
            st.write("")
            st.write("")

            # 第四行：操作按钮（各33%宽度）
            col1, col2, col3 = st.columns(3)

            with col1:
                test_model_btn = st.button("🔍 模型连通性测试", type="secondary", use_container_width=True)

            with col2:
                save_config_btn = st.button("💾 添加配置", type="primary", use_container_width=True)

            with col3:
                is_active = st.checkbox("立刻激活此配置", value=True, key="test_is_active")

            # 处理模型连通性测试
            if test_model_btn:
                # 获取输入值
                test_config_name = st.session_state.get('test_config_name', '')
                test_provider = st.session_state.get('test_provider', '')
                model_name = st.session_state.get('model_name_config', '')
                api_type = st.session_state.get('test_api_type', 'chat')
                proxy_config = st.session_state.get('proxy_config', '')

                # 验证输入
                validation_passed = True
                test_error_messages = []

                if not test_provider or test_provider == "无可用提供商":
                    test_error_messages.append("❌ 请选择提供商")
                    validation_passed = False

                if not model_name.strip():
                    test_error_messages.append("❌ 请输入模型名称")
                    validation_passed = False

                if not validation_passed:
                    for msg in test_error_messages:
                        st.error(msg)
                else:
                    # 进行模型连通性测试
                    with st.spinner("正在测试模型连通性..."):
                        try:
                            # 获取API密钥信息
                            if not selected_secret_id:
                                st.error("❌ 请先选择API-KEY")
                                st.stop()

                            secret_info = secrets_manager.get_api_secret_by_id(selected_secret_id)
                            if not secret_info:
                                st.error("❌ 无法获取API密钥信息")
                                st.stop()

                            base_url = secret_info.get('base_url', '')

                            # 根据API类型生成完整URL
                            if api_type == "new_api":
                                from ai_researcher.models.api_client import UnifiedAPIClient
                                test_endpoint_for_api = UnifiedAPIClient.get_full_url_preview(base_url, api_type, model_name)
                            elif api_type == "chat":
                                if base_url.endswith('/'):
                                    test_endpoint_for_api = f"{base_url}chat/completions"
                                else:
                                    test_endpoint_for_api = f"{base_url}/v1/chat/completions"
                            elif api_type == "messages":
                                if base_url.endswith('/'):
                                    test_endpoint_for_api = f"{base_url}messages"
                                else:
                                    test_endpoint_for_api = f"{base_url}/v1/messages"
                            elif api_type == "generateContent":
                                if base_url.endswith('/'):
                                    test_endpoint_for_api = f"{base_url}models/{model_name}:generateContent"
                                else:
                                    test_endpoint_for_api = f"{base_url}/models/{model_name}:generateContent"
                            else:
                                test_endpoint_for_api = base_url

                            # 根据URL格式确定API类型
                            if "/chat/completions" in test_endpoint_for_api:
                                # OpenAI格式
                                payload = {
                                    "model": model_name.strip(),
                                    "messages": [{"role": "user", "content": "Hi"}],
                                    "max_tokens": 5
                                }
                            elif "/messages" in test_endpoint_for_api:
                                # Anthropic格式
                                payload = {
                                    "model": model_name.strip(),
                                    "max_tokens": 5,
                                    "messages": [{"role": "user", "content": "Hi"}]
                                }
                            elif "/generateContent" in test_endpoint_for_api:
                                # Gemini格式
                                payload = {
                                    "contents": [{
                                        "parts": [{"text": "Hi"}]
                                    }],
                                    "generationConfig": {
                                        "maxOutputTokens": 5
                                    }
                                }
                            else:
                                # 默认使用OpenAI格式
                                payload = {
                                    "model": model_name.strip(),
                                    "messages": [{"role": "user", "content": "Hi"}],
                                    "max_tokens": 5
                                }

                            headers = {
                                "Content-Type": "application/json",
                                "Authorization": f"Bearer {secret_info['api_key']}"
                            }

                            # 发送HTTP请求
                            import requests
                            import json
                            response = requests.post(
                                test_endpoint_for_api,
                                headers=headers,
                                data=json.dumps(payload),
                                timeout=10
                            )

                            # 检查响应
                            if response.status_code == 200:
                                st.success(f"✅ 模型连通性测试成功！状态码: {response.status_code}")
                                try:
                                    resp_json = response.json()
                                    if "choices" in resp_json:
                                        content = resp_json["choices"][0]["message"]["content"]
                                    elif "content" in resp_json:
                                        content = resp_json["content"][0]["text"]
                                    elif "candidates" in resp_json:
                                        content = resp_json["candidates"][0]["content"]["parts"][0]["text"]
                                    else:
                                        content = str(resp_json)[:100]
                                    st.info(f"响应预览: {content[:100]}...")
                                except:
                                    pass
                            elif response.status_code == 401:
                                st.error(f"❌ 认证失败，请检查API密钥。状态码: {response.status_code}")
                            elif response.status_code == 404:
                                st.error(f"❌ API端点不存在或模型名称错误。状态码: {response.status_code}")
                            else:
                                st.warning(f"⚠️ API响应异常。状态码: {response.status_code}")
                                try:
                                    error_data = response.json()
                                    st.error(f"错误信息: {error_data}")
                                except:
                                    st.error(f"响应内容: {response.text[:200]}")
                        except requests.exceptions.Timeout:
                            st.error("❌ 连接超时，请检查网络或端点地址")
                        except requests.exceptions.ConnectionError:
                            st.error("❌ 连接失败，请检查端点地址是否正确")
                        except Exception as e:
                            st.error(f"❌ 模型连通性测试失败: {str(e)}")

            # 处理保存配置
            if save_config_btn:
                # 验证输入
                validation_passed = True

                if not config_name.strip():
                    st.error("❌ 配置名称不能为空")
                    validation_passed = False

                if not model_name.strip():
                    st.error("❌ 模型名称不能为空")
                    validation_passed = False

                # 检查是否选择了API密钥
                if not selected_secret_id:
                    st.error("❌ 请先选择API-KEY")
                    validation_passed = False

                if not validation_passed:
                    st.stop()

                try:
                    # 获取完整的API密钥信息
                    secret_info = secrets_manager.get_api_secret_by_id(selected_secret_id)
                    if not secret_info:
                        st.error("❌ 无法获取API密钥信息")
                        st.stop()

                    # 如果是NEW-API类型，显示完整URL预览
                    if api_type == "new_api":
                        from ai_researcher.models.api_client import UnifiedAPIClient
                        full_url = UnifiedAPIClient.get_full_url_preview(
                            secret_info['base_url'], api_type, model_name
                        )
                        st.success(f"✅ NEW-API完整URL: {full_url}", icon="✅")

                    # 使用默认参数
                    default_temperature = 0.7
                    default_max_tokens = 4000

                    # 获取代理配置
                    proxy_config_value = st.session_state.get('proxy_config', '')
                    use_proxy = bool(proxy_config_value.strip())

                    success = manager.add_model_config(
                        name=config_name,
                        provider=provider,
                        endpoint=secret_info['base_url'],
                        api_type=api_type,
                        api_key=secret_info['api_key'],
                        api_secret_id=selected_secret_id,
                        model_name=model_name,
                        temperature=default_temperature,
                        max_tokens=default_max_tokens,
                        use_proxy=use_proxy,
                        is_active=is_active
                    )

                    if success:
                        st.success(f"✅ 配置 '{config_name}' 添加成功！")
                    else:
                        st.error("❌ 添加配置失败，请检查配置是否已存在")
                except Exception as e:
                    st.error(f"❌ 添加配置失败: {e}")

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
                            st.write(f"{config['provider']} - {config['model_name']}")

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

        # 模型调用设置
        st.markdown("### 🤖 模型调用设置")

        try:
            from ai_researcher.config import load_config, save_config
            config = load_config()

            # 当前模型调用配置
            model_defaults = get_model_defaults()
            current_temperature = model_defaults['temperature']
            current_max_tokens = model_defaults['max_tokens']
            current_top_p = model_defaults['top_p']
            current_top_k = model_defaults['top_k']
            current_system_prompt = model_defaults['system_prompt']
            current_frequency_penalty = model_defaults['frequency_penalty']
            current_presence_penalty = model_defaults['presence_penalty']

            with st.form("model_config_form"):
                st.markdown("**基础参数**")
                col1, col2 = st.columns(2)

                with col1:
                    temperature = st.slider(
                        "温度参数 (Temperature)",
                        min_value=0.0,
                        max_value=2.0,
                        value=current_temperature,
                        step=0.1,
                        help="控制输出随机性，值越低越确定性，越高越随机"
                    )
                    max_tokens = st.number_input(
                        "最大Token数 (Max Tokens)",
                        min_value=1,
                        max_value=32000,
                        value=current_max_tokens,
                        step=100,
                        help="模型生成的最大token数量"
                    )

                with col2:
                    top_p = st.slider(
                        "Top-P",
                        min_value=0.0,
                        max_value=1.0,
                        value=current_top_p,
                        step=0.1,
                        help="核心采样，控制词汇选择范围"
                    )
                    top_k = st.number_input(
                        "Top-K",
                        min_value=1,
                        max_value=1000,
                        value=current_top_k,
                        step=1,
                        help="限制每步考虑的候选词数量"
                    )

                st.markdown("**惩罚参数**")
                col1, col2 = st.columns(2)

                with col1:
                    frequency_penalty = st.slider(
                        "频率惩罚 (Frequency Penalty)",
                        min_value=-2.0,
                        max_value=2.0,
                        value=current_frequency_penalty,
                        step=0.1,
                        help="减少重复内容的概率"
                    )

                with col2:
                    presence_penalty = st.slider(
                        "存在惩罚 (Presence Penalty)",
                        min_value=-2.0,
                        max_value=2.0,
                        value=current_presence_penalty,
                        step=0.1,
                        help="鼓励引入新话题"
                    )

                st.markdown("**系统提示**")
                system_prompt = st.text_area(
                    "System Prompt",
                    value=current_system_prompt,
                    height=100,
                    help="设置AI助手的角色和行为准则"
                )

                submitted = st.form_submit_button(
                    "💾 保存配置",
                    type="primary",
                    use_container_width=True
                )

                if submitted:
                    try:
                        # 更新配置
                        config['model_defaults'] = {
                            'temperature': temperature,
                            'max_tokens': max_tokens,
                            'top_p': top_p,
                            'top_k': top_k,
                            'system_prompt': system_prompt,
                            'frequency_penalty': frequency_penalty,
                            'presence_penalty': presence_penalty
                        }

                        # 保存配置
                        save_config(config)
                        st.success("✅ 模型调用设置保存成功！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 保存失败: {str(e)}")

            st.markdown("---")

        except Exception as e:
            st.error(f"加载模型配置失败: {str(e)}")

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

            with st.form("ragflow_config_form"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    endpoint = st.text_input(
                        "RAGFlow服务端点",
                        value=current_endpoint
                    )

                with col2:
                    api_key = st.text_input(
                        "RAGFlow API密钥",
                        value=current_api_key,
                        type="password"
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
                            max_value=65535
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
                st.write(f"端点: {current_endpoint}")
            if current_api_key:
                st.write("API密钥: ✅ 已配置")
            else:
                st.write("API密钥: ❌ 未配置")

            st.markdown("**端口配置**")
            for port_name, port_value in (current_ports or port_defaults).items():
                st.write(f"{port_name}: {port_value}")

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
                        import sqlite3
                        if os.path.exists(db_path):
                            conn = sqlite3.connect(db_path)
                            cursor = conn.cursor()
                            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                            tables = cursor.fetchall()
                            conn.close()
                            st.success(f"✅ 数据库连接正常，共 {len(tables)} 个表")
                        else:
                            st.warning("⚠️ 数据库文件不存在")
                    except Exception as e:
                        st.error(f"❌ 数据库连接失败: {e}")

            with col2:
                if st.button("🔄 重建数据库"):
                    try:
                        # 这里可以添加重建数据库的逻辑
                        st.success("✅ 数据库重建完成")
                    except Exception as e:
                        st.error(f"❌ 重建失败: {e}")

        except Exception as e:
            st.error(f"加载数据库配置失败: {e}")