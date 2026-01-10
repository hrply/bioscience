"""
模板管理示例
演示如何创建、使用和管理自定义实验模板
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_researcher.templates import TemplateManager
from ai_researcher import ResearchAgent


def main():
    print("=" * 60)
    print("AI科研助手 - 模板管理示例")
    print("=" * 60)

    # 1. 初始化模板管理器
    print("\n1. 初始化模板管理器...")
    manager = TemplateManager()
    print("✓ 模板管理器初始化完成")

    # 2. 查看预置模板
    print("\n2. 查看预置模板:")
    templates = manager.list_templates()
    for name, desc in list(templates.items())[:5]:
        print(f"  • {name}: {desc}")

    # 3. 获取特定模板内容
    print("\n3. 获取细胞培养模板内容:")
    cell_template = manager.get_template("cell_culture")
    print(cell_template[:300] + "...")

    # 4. 创建自定义模板
    print("\n4. 创建自定义实验模板...")
    custom_template = """
# siRNA转染实验模板

## 实验目标
使用siRNA敲降目标基因表达

## 实验材料
- 细胞系: [细胞名称]
- siRNA: [序列和浓度]
- 转染试剂: [试剂名称]
- 培养基: [类型]
- OPTI-MEM: [无血清培养基]
- 6孔板: [培养板]

## 实验步骤
1. **细胞接种**
   - 转染前24小时接种细胞
   - 细胞密度达到50-70%汇合度
   - 每孔加入2ml完全培养基

2. **siRNA-转染试剂复合物制备**
   - 将siRNA稀释于OPTI-MEM中
   - 转染试剂稀释于OPTI-MEM中
   - 室温孵育5分钟
   - 混合两者，室温孵育20分钟

3. **转染**
   - 将复合物加入培养孔中
   - 轻轻摇匀
   - 37℃，5% CO2培养

4. **基因表达检测**
   - 转染后24-72小时收集细胞
   - RNA提取和qRT-PCR检测
   - Western Blot检测蛋白表达

## 注意事项
- siRNA序列需要特异性验证
- 转染效率需要预实验确定
- 设置阴性对照和阳性对照
- 避免血清和抗生素影响

## 质量控制
- 转染效率检测
- 细胞活力检测
- 目标基因敲降效率验证
- 重复实验验证
    """

    success = manager.create_template(
        name="sirna_transfection",
        content=custom_template,
        description="siRNA转染实验标准流程"
    )

    if success:
        print("✓ 自定义模板创建成功")
    else:
        print("✗ 模板创建失败")

    # 5. 使用自定义模板生成实验方案
    print("\n5. 使用自定义模板生成实验方案...")
    agent = ResearchAgent(
        model_provider="openai",
        model_name="gpt-4"
    )

    experiment_objective = """
    使用siRNA敲降HeLa细胞中的EGFR基因，
    检测对细胞增殖和迁移的影响
    """

    try:
        plan = agent.generate_experiment_plan(
            objective=experiment_objective,
            template="sirna_transfection"
        )

        print(f"✓ 实验方案生成成功")
        print(f"  实验ID: {plan.get('id')}")
        print(f"  实验标题: {plan.get('title')}")

    except Exception as e:
        print(f"✗ 生成失败: {e}")

    # 6. 更新模板
    print("\n6. 更新模板...")
    updated_template = custom_template + """

## 额外步骤
5. **功能检测**
   - 细胞增殖检测 (MTT/CCK-8)
   - 细胞迁移检测 (划痕实验)
   - 细胞凋亡检测 (Annexin V/PI)

## 预期结果
- 目标基因表达降低>70%
- 细胞增殖能力下降
- 细胞迁移能力减弱
    """

    success = manager.update_template(
        name="sirna_transfection",
        content=updated_template
    )

    if success:
        print("✓ 模板更新成功")

    # 7. 导出模板
    print("\n7. 导出模板...")
    exported = manager.export_template("sirna_transfection")
    template_file = Path("sirna_transfection_template.yaml")
    template_file.write_text(exported, encoding='utf-8')
    print(f"✓ 模板已导出到 {template_file}")

    # 8. 删除模板
    print("\n8. 删除模板...")
    if click_confirm("是否删除自定义模板?"):
        success = manager.delete_template("sirna_transfection")
        if success:
            print("✓ 模板删除成功")

    print("\n" + "=" * 60)
    print("模板管理示例完成！")
    print("=" * 60)


def click_confirm(prompt):
    """简单的确认对话框"""
    response = input(f"\n{prompt} (y/n): ").lower().strip()
    return response in ['y', 'yes']


if __name__ == "__main__":
    main()
