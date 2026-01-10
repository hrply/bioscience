"""
CLI工具集成使用示例
展示如何在ai_researcher项目中统一使用各种CLI工具
"""

import os
from pathlib import Path

# 添加项目根目录到Python路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_researcher import ResearchAgent
from ai_researcher.cli_tools.manager import CLIManager


def example_1_basic_cli_manager():
    """示例1: 使用CLI管理器"""
    print("=" * 60)
    print("示例1: 使用CLI管理器")
    print("=" * 60)

    # 创建CLI管理器
    cli_manager = CLIManager()

    # 列出所有工具
    print("\n已注册的CLI工具:")
    for tool in cli_manager.list_tools():
        print(f"  - {tool}")

    # 检查安装状态
    print("\nCLI工具安装状态:")
    status = cli_manager.check_installation()
    for tool, installed in status.items():
        icon = "✅" if installed else "❌"
        print(f"  {icon} {tool}: {'已安装' if installed else '未安装'}")

    # 获取详细状态
    print("\n详细状态信息:")
    all_status = cli_manager.get_all_status()
    for tool, info in all_status.items():
        print(f"\n{tool}:")
        print(f"  版本: {info.get('version', 'N/A')}")
        if 'available_models' in info:
            print(f"  可用模型: {info['available_models']}")

    print()


def example_2_agent_with_cli():
    """示例2: 在Agent中使用CLI工具"""
    print("=" * 60)
    print("示例2: 在Agent中使用CLI工具")
    print("=" * 60)

    # 初始化agent（不需要API密钥来使用CLI工具）
    agent = ResearchAgent(
        model_provider="openai",
        model_name="gpt-4"
    )

    # 获取CLI管理器
    cli_manager = agent.get_cli_manager()

    print("\n通过Agent访问的CLI工具:")
    for tool in cli_manager.list_tools():
        print(f"  - {tool}")

    # 检查安装状态
    print("\nCLI工具安装状态:")
    status = agent.check_cli_installation()
    for tool, installed in status.items():
        icon = "✅" if installed else "❌"
        print(f"  {icon} {tool}")

    print()


def example_3_execute_commands():
    """示例3: 执行CLI命令"""
    print("=" * 60)
    print("示例3: 执行CLI命令")
    print("=" * 60)

    cli_manager = CLIManager()

    # 示例：执行Claude CLI命令（如果已安装）
    print("\n尝试执行Claude CLI命令...")
    result = cli_manager.claude("--version")
    print(f"结果: {result}")

    # 示例：执行iFlow CLI命令（如果已安装）
    print("\n尝试执行iFlow CLI命令...")
    result = cli_manager.iflow("--version")
    print(f"结果: {result}")

    print()


def example_4_model_providers_comparison():
    """示例4: 对比不同模型提供商"""
    print("=" * 60)
    print("示例4: 不同模型提供商对比")
    print("=" * 60)

    providers = [
        ("openai", "gpt-4"),
        ("gemini", "gemini-1.5-pro"),
        ("anthropic", "claude-3-5-sonnet-20241022"),
        ("iflow", "Qwen3-Coder")
    ]

    print("\n支持的模型提供商:")
    for provider, model in providers:
        print(f"  - {provider}: {model}")

    print("\n注意：每个提供商都需要相应的API密钥配置")


def example_5_batch_operations():
    """示例5: 批量操作"""
    print("=" * 60)
    print("示例5: 批量操作")
    print("=" * 60)

    cli_manager = CLIManager()

    # 批量执行版本检查命令
    print("\n批量检查CLI工具版本...")
    commands = [
        {"tool": "claude", "command": "--version", "kwargs": {}},
        {"tool": "codex", "command": "--version", "kwargs": {}},
        {"tool": "gemini", "command": "--version", "kwargs": {}},
        {"tool": "opencode", "command": "--version", "kwargs": {}},
        {"tool": "iflow", "command": "--version", "kwargs": {}}
    ]

    results = cli_manager.batch_execute(commands)

    for i, result in enumerate(results):
        tool_name = commands[i]["tool"]
        if result["success"]:
            print(f"✅ {tool_name}: {result['output'][:50]}")
        else:
            print(f"❌ {tool_name}: {result['error'][:50]}")

    print()


def example_6_configure_cli_tools():
    """示例6: 配置CLI工具"""
    print("=" * 60)
    print("示例6: 配置CLI工具")
    print("=" * 60)

    # 创建带配置的CLI管理器
    config = {
        "claude": {
            "model": "claude-3-5-sonnet-20241022"
        },
        "gemini": {
            "model": "gemini-1.5-pro"
        },
        "iflow": {
            "model": "Qwen3-Coder",
            "base_url": "https://apis.iflow.cn/v1"
        }
    }

    cli_manager = CLIManager(config=config)

    print("\n已配置的CLI工具:")
    for tool_name in config.keys():
        tool = cli_manager.get_tool(tool_name)
        if tool:
            print(f"\n{tool_name}:")
            print(f"  配置: {tool.get_config()}")

    print()


def example_7_cli_vs_sdk():
    """示例7: CLI vs SDK对比"""
    print("=" * 60)
    print("示例7: CLI工具 vs SDK对比")
    print("=" * 60)

    print("""
CLI工具的优势:
  ✅ 独立于编程语言，可在任何环境中使用
  ✅ 简单易用，适合快速原型开发
  ✅ 可以直接与命令行交互
  ✅ 便于脚本化和自动化

SDK的优势:
  ✅ 更丰富的API接口
  ✅ 更精细的控制
  ✅ 更好的错误处理
  ✅ 更强的集成能力

推荐使用方式:
  - 开发阶段: 使用CLI工具快速测试
  - 生产环境: 使用SDK进行深度集成
  - 自动化脚本: 结合CLI和SDK
    """)


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("ai_researcher - CLI工具集成示例")
    print("=" * 60 + "\n")

    # 检查环境变量
    print("环境检查:")
    print(f"  Python路径: {sys.version}")
    print(f"  项目路径: {Path(__file__).parent.parent}")
    print()

    try:
        # 运行示例
        example_1_basic_cli_manager()
        example_2_agent_with_cli()
        example_3_execute_commands()
        example_4_model_providers_comparison()
        example_5_batch_operations()
        example_6_configure_cli_tools()
        example_7_cli_vs_sdk()

        print("=" * 60)
        print("所有示例执行完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n执行过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
