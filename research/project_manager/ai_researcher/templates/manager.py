"""
实验模板管理系统
用于管理实验方案模板
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging


logger = logging.getLogger(__name__)


class TemplateManager:
    """实验模板管理器"""

    def __init__(self, template_dir: str = "/app/data/templates"):
        """
        初始化模板管理器

        Args:
            template_dir: 模板目录路径
        """
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)

        # 预定义模板类型
        self.default_templates = {
            "cell_culture": "细胞培养",
            "pcr": "PCR扩增",
            "western_blot": "Western Blot",
            "flow_cytometry": "流式细胞术",
            "elisa": "ELISA",
            "microscopy": "显微镜观察",
            "protein_purification": "蛋白质纯化",
            "drug_screening": "药物筛选",
            "animal_experiment": "动物实验",
        }

    def get_template(self, template_name: str) -> Optional[str]:
        """
        获取模板内容

        Args:
            template_name: 模板名称

        Returns:
            模板内容字符串
        """
        # 尝试从文件加载
        template_path = self.template_dir / f"{template_name}.yaml"
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()

        # 如果没有文件，返回默认模板
        return self._get_default_template(template_name)

    def list_templates(self) -> Dict[str, str]:
        """列出所有可用模板"""
        templates = {}

        # 扫描模板目录
        for template_file in self.template_dir.glob("*.yaml"):
            name = template_file.stem
            templates[name] = name

        # 添加默认模板
        templates.update(self.default_templates)

        return templates

    def create_template(
        self,
        name: str,
        content: str,
        description: Optional[str] = None
    ) -> bool:
        """
        创建新模板

        Args:
            name: 模板名称
            content: 模板内容（YAML格式）
            description: 模板描述

        Returns:
            是否创建成功
        """
        template_path = self.template_dir / f"{name}.yaml"

        try:
            # 验证YAML格式
            yaml.safe_load(content)

            # 添加描述头
            if description:
                content = f"# {description}\n" + content

            with open(template_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"模板创建成功: {name}")
            return True

        except Exception as e:
            logger.error(f"创建模板失败: {e}")
            return False

    def update_template(
        self,
        name: str,
        content: str
    ) -> bool:
        """更新模板"""
        return self.create_template(name, content)

    def delete_template(self, name: str) -> bool:
        """
        删除模板

        Args:
            name: 模板名称

        Returns:
            是否删除成功
        """
        template_path = self.template_dir / f"{name}.yaml"

        try:
            if template_path.exists():
                template_path.unlink()
                logger.info(f"模板删除成功: {name}")
                return True
            return False

        except Exception as e:
            logger.error(f"删除模板失败: {e}")
            return False

    def _get_default_template(self, template_name: str) -> Optional[str]:
        """获取默认模板"""
        templates = {
            "cell_culture": """
# 细胞培养实验模板

## 实验目标
根据研究目的确定细胞培养的具体目标

## 实验材料
- 细胞系: [细胞名称]
- 培养基: [培养基类型]
- 血清: [血清类型和浓度]
- 培养皿/瓶: [规格]
- 试剂: [列出所需试剂]

## 实验步骤
1. **细胞复苏**
   - 从液氮中取出冻存管
   - 37℃水浴快速解冻
   - 转移到含培养基的培养皿中
   - 37℃，5% CO2培养

2. **细胞传代**
   - 观察细胞融合度
   - 达到80-90%融合时传代
   - 弃去旧培养基
   - PBS清洗
   - 加入胰蛋白酶消化
   - 加入培养基终止消化
   - 按比例接种到新培养皿

3. **细胞计数**
   - 使用血细胞计数板
   - 记录细胞密度
   - 调整至所需浓度

4. **实验处理**
   - 接种细胞至实验板
   - 贴壁后进行实验处理
   - [根据具体实验添加处理步骤]

## 注意事项
- 无菌操作
- 定期检查细胞状态
- 记录所有操作细节
- 控制传代次数

## 质量控制
- 细胞形态观察
- 细胞活力检测
- 支原体检测
- 细胞计数准确性
            """,

            "pcr": """
# PCR扩增实验模板

## 实验目标
扩增特定DNA片段

## 实验材料
- DNA模板: [来源和浓度]
- 引物: [正向和反向引物序列]
- dNTP mix: [浓度]
- DNA聚合酶: [类型和浓度]
- 缓冲液: [对应缓冲液]
- MgCl2: [浓度]
- 无菌水: [体积]

## 实验步骤
1. **反应体系配制**
   - 冰上配制反应液
   - 按照说明书配制25μl或50μl体系
   - 充分混匀，离心

2. **PCR程序设置**
   - 94℃预变性: 5分钟
   - 循环反应(30-35个循环):
     * 94℃变性: 30秒
     * 退火温度: 30秒 [根据引物Tm值确定]
     * 72℃延伸: 30秒-1分钟 [根据片段长度]
   - 72℃终末延伸: 5-10分钟

3. **产物检测**
   - 1-2%琼脂糖凝胶电泳
   - EB染色或安全染料
   - 紫外灯下观察结果

## 注意事项
- 冰上操作防止酶失活
- 准确配制反应体系
- 设置阴性对照
- 注意引物特异性

## 质量控制
- 阴性对照
- 阳性对照
- 熔解曲线分析(实时定量PCR)
- 测序验证
            """,

            "western_blot": """
# Western Blot实验模板

## 实验目标
检测特定蛋白的表达水平

## 实验材料
- 蛋白样品: [裂解液制备]
- SDS-PAGE凝胶: [浓度]
- 转膜装置: [PVDF或NC膜]
- 一抗: [抗体名称和稀释比例]
- 二抗: [抗体名称和稀释比例]
- ECL发光液: [化学发光试剂]
- 蛋白 marker: [分子量标准]

## 实验步骤
1. **样品制备**
   - 细胞裂解
   - 蛋白定量(BCA或Bradford)
   - 加入上样缓冲液
   - 95℃加热5分钟

2. **SDS-PAGE电泳**
   - 制备凝胶
   - 上样
   - 80V浓缩胶，120V分离胶
   - 直至染料到达凝胶底部

3. **转膜**
   - 湿转或半干转
   - 200mA，1-2小时
   - 或按蛋白分子量调整时间

4. **封闭**
   - 5%脱脂奶粉或BSA
   - 室温1-2小时或4℃过夜

5. **一抗孵育**
   - 4℃过夜或室温1-2小时
   - TBST洗涤3次，每次5分钟

6. **二抗孵育**
   - 室温1小时
   - TBST洗涤3次，每次5分钟

7. **显影**
   - ECL发光液孵育
   - 化学发光成像系统检测

## 注意事项
- 蛋白定量要准确
- 避免气泡影响转膜
- 抗体浓度要优化
- 内参蛋白用于标准化

## 质量控制
- 内参蛋白检测
- 重复实验
- 抗体特异性验证
- 线性范围检测
            """
        }

        return templates.get(template_name)

    def export_template(self, name: str) -> Optional[str]:
        """导出模板"""
        return self.get_template(name)

    def import_template(
        self,
        name: str,
        content: str,
        description: Optional[str] = None
    ) -> bool:
        """导入模板"""
        return self.create_template(name, content, description)
