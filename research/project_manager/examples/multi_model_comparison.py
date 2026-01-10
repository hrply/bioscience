"""
多模型对比示例
演示如何在AI科研助手中使用不同的模型提供商
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_researcher import ResearchAgent


def compare_models():
    """对比不同模型生成的实验方案"""

    experiment_objective = """
    设计一个实验来验证microRNA-21对肿瘤细胞迁移的影响。
    包括实验设计、细胞培养、transwell迁移实验、
    数据收集和统计分析方法。
    """

    # 定义要测试的模型
    models = [
        {"provider": "openai", "name": "gpt-4", "description": "OpenAI GPT-4"},
        {"provider": "gemini", "name": "gemini-pro", "description": "Google Gemini Pro"},
    ]

    results = {}

    for model_config in models:
        provider = model_config["provider"]
        name = model_config["name"]
        description = model_config["description"]

        print(f"\n{'=' * 60}")
        print(f"测试模型: {description}")
        print(f"{'=' * 60}")

        try:
            # 初始化助手
            agent = ResearchAgent(
                model_provider=provider,
                model_name=name
            )

            # 生成实验方案
            print("\n生成实验方案中...")
            plan = agent.generate_experiment_plan(
                objective=experiment_objective,
                search_top_k=3
            )

            results[provider] = {
                "success": True,
                "plan": plan,
                "plan_length": len(plan.get('plan', {})),
                "has_procedure": bool(plan.get('procedure'))
            }

            print(f"\n✓ {description} 生成成功")
            print(f"  实验ID: {plan.get('id')}")
            print(f"  标题: {plan.get('title', '')[:50]}...")

        except Exception as e:
            print(f"\n✗ {description} 生成失败: {e}")
            results[provider] = {
                "success": False,
                "error": str(e)
            }

    # 对比结果
    print(f"\n{'=' * 60}")
    print("模型对比结果")
    print(f"{'=' * 60}\n")

    for provider, result in results.items():
        print(f"{provider.upper()}:")
        if result["success"]:
            print(f"  ✓ 成功")
            print(f"  方案详情长度: {result['plan_length']}")
            print(f"  包含实验步骤: {'是' if result['has_procedure'] else '否'}")
        else:
            print(f"  ✗ 失败: {result.get('error')}")
        print()

    return results


def main():
    print("=" * 60)
    print("AI科研助手 - 多模型对比示例")
    print("=" * 60)
    print("\n注意: 此示例需要配置相应的API密钥")
    print("支持的模型:")
    print("  - OpenAI GPT-4")
    print("  - Google Gemini Pro")
    print("  - Anthropic Claude (需要额外配置)")

    results = compare_models()

    print("=" * 60)
    print("对比完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
