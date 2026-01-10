"""
实验结果分析示例
演示如何使用AI科研助手分析实验数据
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_researcher import ResearchAgent


def generate_sample_data():
    """生成示例实验数据"""
    np.random.seed(42)

    # 创建示例数据：细胞活力实验结果
    concentrations = [0, 10, 20, 40, 80]  # μM
    time_points = [24, 48]  # 小时

    data = []
    for time in time_points:
        for conc in concentrations:
            # 模拟细胞活力数据
            # 浓度越高，活力越低
            base_viability = 100 - conc * 0.8 + np.random.normal(0, 5)
            viability = max(0, min(100, base_viability))

            data.append({
                'concentration': conc,
                'time_hours': time,
                'viability_percent': viability,
                'absorbance_570nm': viability / 100 * 2.5 + np.random.normal(0, 0.1)
            })

    return pd.DataFrame(data)


def main():
    print("=" * 60)
    print("AI科研助手 - 实验结果分析示例")
    print("=" * 60)

    # 1. 生成示例数据
    print("\n1. 生成示例实验数据...")
    data = generate_sample_data()
    print(f"✓ 生成了 {len(data)} 条数据记录")
    print("\n数据预览:")
    print(data.head(10))

    # 2. 保存数据到文件
    data_file = Path("sample_results.xlsx")
    data.to_excel(data_file, index=False)
    print(f"\n✓ 数据已保存到 {data_file}")

    # 3. 初始化助手
    print("\n2. 初始化AI科研助手...")
    agent = ResearchAgent(
        model_provider="openai",
        model_name="gpt-4"
    )
    print("✓ 助手初始化完成")

    # 4. 创建实验记录
    print("\n3. 创建实验记录...")
    experiment_objective = """
    研究化合物A对肺癌细胞A549的增殖抑制作用
    """
    plan = agent.generate_experiment_plan(
        objective=experiment_objective,
        template="cell_culture"
    )
    experiment_id = plan.get('id')
    print(f"✓ 创建实验: {experiment_id}")

    # 5. 分析实验结果
    print("\n4. 分析实验结果...")
    print("正在调用AI分析实验数据...")

    analysis = agent.analyze_results(
        experiment_id=experiment_id,
        data_file=str(data_file)
    )

    print("\n✓ 分析完成！")

    # 6. 显示分析结果
    print("\n5. 分析结果摘要:")
    print("-" * 60)

    # 数据概览
    if 'data_summary' in analysis:
        summary = analysis['data_summary']
        print(f"数据形状: {summary.get('shape')}")
        print(f"数值列: {summary.get('columns')}")

    # 统计分析
    if 'statistical_analysis' in analysis:
        stats = analysis['statistical_analysis']
        if 'numeric_columns' in stats:
            print("\n数值列统计:")
            for col, stat in stats['numeric_columns'].items():
                print(f"  {col}:")
                print(f"    均值: {stat['mean']:.2f}")
                print(f"    标准差: {stat['std']:.2f}")

    # AI解读
    if 'ai_interpretation' in analysis:
        print("\nAI解读:")
        print("-" * 60)
        interpretation = analysis['ai_interpretation']
        if 'text' in interpretation:
            print(interpretation['text'])

    # 可视化图表
    if 'visualizations' in analysis and analysis['visualizations']:
        print("\n6. 生成的图表:")
        print("-" * 60)
        for chart in analysis['visualizations']:
            print(f"  • {chart}")

    # 7. 保存分析结果
    print("\n7. 保存分析结果...")
    results_file = Path(f"analysis_{experiment_id}.json")
    import json
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    print(f"✓ 分析结果已保存到 {results_file}")

    print("\n" + "=" * 60)
    print("分析示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
