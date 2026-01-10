"""
AI科研助手基本使用示例
演示如何使用AI科研助手生成实验方案和管理实验
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_researcher import ResearchAgent


def main():
    print("=" * 60)
    print("AI科研助手 - 基本使用示例")
    print("=" * 60)

    # 1. 初始化助手（使用OpenAI模型）
    print("\n1. 初始化AI科研助手...")
    agent = ResearchAgent(
        model_provider="openai",
        model_name="gpt-4"
    )
    print("✓ 助手初始化完成")

    # 2. 生成实验方案
    print("\n2. 生成实验方案...")
    experiment_objective = """
    研究化合物A对人类肺癌细胞系A549的增殖抑制作用。
    需要设置不同浓度梯度（0, 10, 20, 40, 80 μM），
    处理时间分别为24小时和48小时，
    使用MTT法检测细胞活力。
    """

    plan = agent.generate_experiment_plan(
        objective=experiment_objective,
        template="cell_culture",
        search_top_k=5
    )

    print(f"\n✓ 实验方案生成完成")
    print(f"  实验ID: {plan.get('id')}")
    print(f"  实验标题: {plan.get('title')}")
    print(f"  状态: {plan.get('status', 'planned')}")

    # 3. 查看实验方案详情
    print("\n3. 实验方案详情:")
    print("-" * 60)
    print(f"目标: {plan.get('objective', '')}")
    print("\n设计原理:")
    print(plan.get('design_rationale', ''))

    # 4. 更新实验进度
    print("\n4. 更新实验进度...")
    experiment_id = plan.get('id')

    # 标记为进行中
    agent.update_progress(
        experiment_id=experiment_id,
        status="in_progress",
        notes="细胞培养完成，准备进行药物处理"
    )
    print("✓ 进度已更新: in_progress")

    # 模拟实验过程
    import time
    time.sleep(1)

    # 标记为完成
    agent.update_progress(
        experiment_id=experiment_id,
        status="completed",
        notes="实验已完成，收集数据进行后续分析"
    )
    print("✓ 进度已更新: completed")

    # 5. 查看实验状态
    print("\n5. 查看实验最终状态...")
    status = agent.get_experiment_status(experiment_id)
    print(f"  状态: {status.get('status')}")
    print(f"  创建时间: {status.get('created_at')}")
    print(f"  更新时间: {status.get('updated_at')}")

    # 6. 获取进度历史
    print("\n6. 实验进度历史:")
    history = agent.experiments.get_progress_history(experiment_id)
    for i, entry in enumerate(history, 1):
        print(f"  {i}. {entry['timestamp'][:19]} - {entry['status']}")
        if entry.get('notes'):
            print(f"     {entry['notes']}")

    print("\n" + "=" * 60)
    print("示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
