"""
统一API变量系统使用示例
展示如何使用AI_API_KEY和AI_BASE_URL变量
"""

from ai_researcher.models.api_client import (
    UnifiedAPIClient,
    ModelConfigResolver,
    get_config_resolver,
    load_model_config,
    get_active_model_config
)


def example_1_basic_usage():
    """示例1：基本使用方式"""
    print("=== 示例1：基本使用方式 ===\n")

    # 获取配置解析器
    resolver = get_config_resolver()

    # 加载指定配置
    client = resolver.load_config("My-GPT4")

    # 获取SDK客户端
    openai_client = client.get_client()

    # 获取模型参数
    model_name = client.get_model_name()
    temperature = client.get_temperature()

    print(f"已加载配置: My-GPT4")
    print(f"模型名称: {model_name}")
    print(f"温度参数: {temperature}")
    print(f"SDK类型: {client.sdk_type.value}")
    print()


def example_2_active_config():
    """示例2：使用当前激活的配置"""
    print("=== 示例2：使用激活的配置 ===\n")

    # 获取当前激活的配置
    client = get_active_model_config()

    if client:
        # 获取SDK客户端
        sdk_client = client.get_client()

        print(f"使用激活的配置: {client.config_name}")
        print(f"模型: {client.get_model_name()}")
        print(f"SDK: {client.sdk_type.value}")
        print()
    else:
        print("❌ 没有激活的配置")
        print()


def example_3_different_providers():
    """示例3：不同提供商的自动映射"""
    print("=== 示例3：不同提供商的自动映射 ===\n")

    # 假设有以下配置
    configs = [
        "OpenAI-GPT4",
        "Anthropic-Claude",
        "Gemini-Pro",
        "DASHSCOPE-Qwen",
        "ZAI-GLM4"
    ]

    for config_name in configs:
        try:
            client = load_model_config(config_name)
            print(f"配置: {config_name}")
            print(f"  SDK类型: {client.sdk_type.value}")
            print(f"  模型: {client.get_model_name()}")
            print()
        except ValueError as e:
            print(f"配置 {config_name} 不存在: {e}")
            print()


def example_4_sdk_comparison():
    """示例4：不同SDK的调用方式"""
    print("=== 示例4：不同SDK的调用方式 ===\n")

    # OpenAI兼容格式
    try:
        client = load_model_config("OpenAI-GPT4")
        openai_client = client.get_client()

        # OpenAI调用方式
        response = openai_client.chat.completions.create(
            model=client.get_model_name(),
            messages=[
                {"role": "user", "content": "你好"}
            ]
        )
        print("✅ OpenAI兼容格式调用成功")
        print(f"响应: {response.choices[0].message.content}")
        print()
    except Exception as e:
        print(f"❌ OpenAI调用失败: {e}\n")

    # Anthropic兼容格式
    try:
        client = load_model_config("Anthropic-Claude")
        anthropic_client = client.get_client()

        # Anthropic调用方式
        response = anthropic_client.messages.create(
            model=client.get_model_name(),
            max_tokens=1000,
            messages=[
                {"role": "user", "content": "你好"}
            ]
        )
        print("✅ Anthropic兼容格式调用成功")
        print(f"响应: {response.content[0].text}")
        print()
    except Exception as e:
        print(f"❌ Anthropic调用失败: {e}\n")

    # Gemini原生格式
    try:
        client = load_model_config("Gemini-Pro")
        gemini_client = client.get_client()

        # Gemini调用方式
        response = gemini_client.generate_content(
            model=client.get_model_name(),
            contents="你好"
        )
        print("✅ Gemini原生格式调用成功")
        print(f"响应: {response.text}")
        print()
    except Exception as e:
        print(f"❌ Gemini调用失败: {e}\n")


def example_5_environment_variables():
    """示例5：环境变量映射"""
    print("=== 示例5：环境变量映射 ===\n")

    import os

    # 加载配置
    client = load_model_config("My-GPT4")

    # 检查统一变量
    print("统一变量:")
    print(f"  AI_API_KEY: {os.environ.get('AI_API_KEY', '未设置')[:20]}...")
    print(f"  AI_BASE_URL: {os.environ.get('AI_BASE_URL', '未设置')}")
    print()

    # 检查映射后的SDK变量
    print("SDK映射变量:")
    if client.sdk_type.value == "openai":
        print(f"  OPENAI_API_KEY: {os.environ.get('OPENAI_API_KEY', '未设置')[:20]}...")
        print(f"  OPENAI_BASE_URL: {os.environ.get('OPENAI_BASE_URL', '未设置')}")
    elif client.sdk_type.value == "anthropic":
        print(f"  ANTHROPIC_API_KEY: {os.environ.get('ANTHROPIC_API_KEY', '未设置')[:20]}...")
        print(f"  ANTHROPIC_BASE_URL: {os.environ.get('ANTHROPIC_BASE_URL', '未设置')}")
    elif client.sdk_type.value == "gemini":
        print(f"  GEMINI_API_KEY: {os.environ.get('GEMINI_API_KEY', '未设置')[:20]}...")
        print(f"  GEMINI_BASE_URL: {os.environ.get('GEMINI_BASE_URL', '未设置')}")
    elif client.sdk_type.value == "dashscope":
        print(f"  DASHSCOPE_API_KEY: {os.environ.get('DASHSCOPE_API_KEY', '未设置')[:20]}...")
        print(f"  DASHSCOPE_BASE_URL: {os.environ.get('DASHSCOPE_BASE_URL', '未设置')}")
    elif client.sdk_type.value == "zai":
        print(f"  ZAI_API_KEY: {os.environ.get('ZAI_API_KEY', '未设置')[:20]}...")
        print(f"  ZAI_BASE_URL: {os.environ.get('ZAI_BASE_URL', '未设置')}")
    print()


def example_6_list_configs():
    """示例6：列出所有配置"""
    print("=== 示例6：列出所有配置 ===\n")

    resolver = get_config_resolver()
    configs = resolver.list_configs()

    if not configs:
        print("❌ 暂无配置")
        return

    print(f"共 {len(configs)} 个配置:\n")

    for config in configs:
        status = "✅ 激活" if config.get('is_active') else "○ 未激活"
        print(f"[{status}] {config['name']}")
        print(f"  提供商: {config['provider']}")
        print(f"  模型: {config['model_name']}")
        print(f"  API类型: {config['api_type']}")
        print(f"  端点: {config['endpoint']}")
        print()


if __name__ == "__main__":
    print("统一API变量系统使用示例")
    print("=" * 50)
    print()

    # 运行所有示例
    example_1_basic_usage()
    example_2_active_config()
    example_3_different_providers()
    example_4_sdk_comparison()
    example_5_environment_variables()
    example_6_list_configs()

    print("=" * 50)
    print("所有示例运行完成")
