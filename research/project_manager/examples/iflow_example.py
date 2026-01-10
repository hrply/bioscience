"""
iFlow集成使用示例
展示如何在ai_researcher项目中使用iFlow的功能
"""

import asyncio
import os
from pathlib import Path

# 添加项目根目录到Python路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_researcher import ResearchAgent


async def basic_iflow_example():
    """iFlow基本使用示例"""
    print("=" * 60)
    print("iFlow基本使用示例")
    print("=" * 60)

    # 初始化iFlow模型
    # 注意：需要先配置IFLOW_API_KEY环境变量或配置文件
    agent = ResearchAgent(
        model_provider="iflow",
        model_name="Qwen3-Coder"
    )

    # 使用iFlow生成文本
    response = agent.model.generate(
        prompt="请解释一下什么是基因编辑技术，以及它的应用场景。",
        system_message="你是一个专业的生物医学研究员"
    )

    print("\n=== iFlow生成结果 ===")
    print(response)
    print()

    return response


async def experiment_plan_with_iflow():
    """使用iFlow生成实验方案"""
    print("=" * 60)
    print("使用iFlow生成实验方案")
    print("=" * 60)

    # 初始化iFlow模型
    agent = ResearchAgent(
        model_provider="iflow",
        model_name="Qwen3-Coder"
    )

    # 生成实验方案
    plan = agent.generate_experiment_plan(
        objective="研究CRISPR-Cas9技术在肺癌细胞系A549中的基因编辑效率",
        template="cell_culture"
    )

    print("\n=== 实验方案 ===")
    print(f"实验ID: {plan.get('id')}")
    print(f"实验标题: {plan.get('title')}")
    print(f"目标: {plan.get('objective')}")
    print()

    return plan


async def iflow_tool_execution_example():
    """iFlow工具执行示例"""
    print("=" * 60)
    print("iFlow工具执行示例")
    print("=" * 60)

    # 初始化iFlow模型
    agent = ResearchAgent(
        model_provider="iflow",
        model_name="Qwen3-Coder"
    )

    # 使用iFlow执行工具调用
    try:
        # 注意：这需要iFlow CLI已安装并配置
        result = await agent.iflow_execute_tool(
            tool_name="read_file",
            tool_args={"path": "/home/hrply/software/bioscience/research/project_manager/README.md"}
        )

        print("\n=== 工具执行结果 ===")
        print(result)
        print()

        return result
    except Exception as e:
        print(f"\n注意：工具执行需要iFlow CLI支持，当前示例可能失败")
        print(f"错误信息: {e}")
        print()


async def iflow_task_planning_example():
    """iFlow任务规划示例"""
    print("=" * 60)
    print("iFlow任务规划示例")
    print("=" * 60)

    # 初始化iFlow模型
    agent = ResearchAgent(
        model_provider="iflow",
        model_name="Qwen3-Coder"
    )

    # 获取任务计划
    try:
        plan = await agent.iflow_get_task_plan(
            objective="设计一个完整的蛋白质表达和纯化实验流程"
        )

        print("\n=== 任务计划 ===")
        print(f"任务目标: {plan.get('objective')}")
        print(f"计划步骤数: {plan.get('total_steps')}")

        if 'plan' in plan:
            print("\n详细计划:")
            for i, step in enumerate(plan['plan'], 1):
                print(f"  {i}. [{step.get('priority')}] {step.get('content')} - {step.get('status')}")
        print()

        return plan
    except Exception as e:
        print(f"\n注意：任务规划需要iFlow CLI支持，当前示例可能失败")
        print(f"错误信息: {e}")
        print()


def sync_iflow_example():
    """iFlow同步调用示例"""
    print("=" * 60)
    print("iFlow同步调用示例")
    print("=" * 60)

    # 初始化iFlow模型
    agent = ResearchAgent(
        model_provider="iflow",
        model_name="Qwen3-Coder"
    )

    # 同步调用
    response = agent.iflow_generate_sync(
        prompt="列举三种常用的细胞培养基，并说明它们各自的特点。",
        system_message="你是一个专业的细胞生物学研究员"
    )

    print("\n=== iFlow同步生成结果 ===")
    print(response)
    print()

    return response


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("ai_researcher - iFlow集成示例")
    print("=" * 60 + "\n")

    # 检查环境变量
    if not os.getenv('IFLOW_API_KEY'):
        print("警告：未检测到IFLOW_API_KEY环境变量")
        print("请设置您的iFlow API密钥：")
        print("  export IFLOW_API_KEY=your_api_key_here")
        print("或者在.env文件中添加IFLOW_API_KEY配置")
        print()

    # 运行示例
    try:
        # 1. 基本使用
        asyncio.run(basic_iflow_example())

        # 2. 同步调用
        sync_iflow_example()

        # 3. 实验方案生成
        asyncio.run(experiment_plan_with_iflow())

        # 4. 任务规划（需要iFlow CLI）
        asyncio.run(iflow_task_planning_example())

        # 5. 工具执行（需要iFlow CLI）
        asyncio.run(iflow_tool_execution_example())

        print("\n" + "=" * 60)
        print("所有示例执行完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n执行过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
