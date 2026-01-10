"""
实验结果分析模块
支持统计分析、图表生成和智能解读
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional
import json
import logging
from pathlib import Path

# 可选依赖
try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False
    sns = None


logger = logging.getLogger(__name__)

# 如果seaborn未安装，记录警告
if not HAS_SEABORN:
    logger.warning("seaborn未安装，部分可视化功能将不可用")


class ResultAnalyzer:
    """实验结果分析器"""

    def __init__(self, model=None):
        """
        初始化结果分析器

        Args:
            model: 大模型实例，用于智能解读
        """
        self.model = model
        self.charts_dir = Path("results/charts")
        self.charts_dir.mkdir(parents=True, exist_ok=True)

    def load_data(self, file_path: str) -> pd.DataFrame:
        """
        加载实验数据

        Args:
            file_path: 数据文件路径

        Returns:
            数据DataFrame
        """
        file_path = Path(file_path)

        if file_path.suffix.lower() == ".csv":
            return pd.read_csv(file_path)
        elif file_path.suffix.lower() in [".xlsx", ".xls"]:
            return pd.read_excel(file_path)
        elif file_path.suffix.lower() == ".json":
            return pd.read_json(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_path.suffix}")

    def analyze(
        self,
        data: pd.DataFrame,
        experiment: Dict[str, Any],
        analysis_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        分析实验数据

        Args:
            data: 实验数据
            experiment: 实验信息
            analysis_type: 分析类型 ("auto", "statistical", "biological")

        Returns:
            分析结果
        """
        results = {
            "data_summary": self._summarize_data(data),
            "statistical_analysis": self._statistical_analysis(data),
            "visualizations": self._create_visualizations(data, experiment),
        }

        # 智能解读
        if self.model:
            results["ai_interpretation"] = self._ai_interpret(data, experiment)

        return results

    def _summarize_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """数据概览"""
        summary = {
            "shape": data.shape,
            "columns": list(data.columns),
            "dtypes": data.dtypes.to_dict(),
            "missing_values": data.isnull().sum().to_dict(),
            "numeric_summary": data.describe().to_dict() if not data.empty else {},
        }
        return summary

    def _statistical_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """统计分析"""
        analysis = {}

        # 数值列分析
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            analysis["numeric_columns"] = {}
            for col in numeric_cols:
                analysis["numeric_columns"][col] = {
                    "mean": float(data[col].mean()),
                    "std": float(data[col].std()),
                    "min": float(data[col].min()),
                    "max": float(data[col].max()),
                    "median": float(data[col].median()),
                }

        # 相关性分析
        if len(numeric_cols) > 1:
            correlation = data[numeric_cols].corr()
            analysis["correlation"] = correlation.to_dict()

        # 分组分析
        categorical_cols = data.select_dtypes(include=["object"]).columns
        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            analysis["group_statistics"] = {}
            for cat_col in categorical_cols[:3]:  # 限制前3个分类列
                for num_col in numeric_cols[:5]:  # 限制前5个数值列
                    try:
                        grouped = data.groupby(cat_col)[num_col].agg([
                            "mean", "std", "count"
                        ]).to_dict()
                        analysis["group_statistics"][f"{cat_col}_{num_col}"] = grouped
                    except Exception as e:
                        logger.warning(f"分组统计失败: {e}")

        return analysis

    def _create_visualizations(
        self,
        data: pd.DataFrame,
        experiment: Dict[str, Any]
    ) -> List[str]:
        """创建可视化图表"""
        chart_files = []
        experiment_id = experiment.get("id", "unknown")

        # 设置中文字体
        plt.rcParams["font.sans-serif"] = ["SimHei", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False

        numeric_cols = data.select_dtypes(include=[np.number]).columns

        try:
            # 1. 数值分布图
            if len(numeric_cols) > 0:
                fig, axes = plt.subplots(min(3, len(numeric_cols)), 1, figsize=(10, 12))
                if len(numeric_cols) == 1:
                    axes = [axes]
                for i, col in enumerate(numeric_cols[:3]):
                    data[col].hist(bins=20, ax=axes[i])
                    axes[i].set_title(f"{col} 分布")
                    axes[i].set_xlabel(col)
                    axes[i].set_ylabel("频数")

                plt.tight_layout()
                chart_file = self.charts_dir / f"{experiment_id}_distribution.png"
                plt.savefig(chart_file)
                plt.close()
                chart_files.append(str(chart_file))

            # 2. 相关性热图
            if len(numeric_cols) > 1 and HAS_SEABORN:
                plt.figure(figsize=(10, 8))
                corr = data[numeric_cols].corr()
                sns.heatmap(corr, annot=True, cmap="coolwarm", center=0)
                plt.title("变量相关性热图")
                plt.tight_layout()
                chart_file = self.charts_dir / f"{experiment_id}_correlation.png"
                plt.savefig(chart_file)
                plt.close()
                chart_files.append(str(chart_file))

            # 3. 分组箱线图
            categorical_cols = data.select_dtypes(include=["object"]).columns
            if len(categorical_cols) > 0 and len(numeric_cols) > 0:
                fig, axes = plt.subplots(min(2, len(numeric_cols)), 1, figsize=(12, 10))
                if len(numeric_cols) == 1:
                    axes = [axes]
                for i, col in enumerate(numeric_cols[:2]):
                    cat_col = categorical_cols[0]
                    data.boxplot(column=col, by=cat_col, ax=axes[i])
                    axes[i].set_title(f"{col} 按 {cat_col} 分组")
                    plt.suptitle("")

                plt.tight_layout()
                chart_file = self.charts_dir / f"{experiment_id}_boxplot.png"
                plt.savefig(chart_file)
                plt.close()
                chart_files.append(str(chart_file))

        except Exception as e:
            logger.error(f"创建可视化图表失败: {e}")

        return chart_files

    def _ai_interpret(
        self,
        data: pd.DataFrame,
        experiment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用AI解读实验结果"""
        if not self.model:
            return {"error": "未配置模型，无法进行AI解读"}

        try:
            # 准备解读提示
            prompt = self._build_interpretation_prompt(data, experiment)

            # 调用模型
            interpretation = self.model.generate(
                prompt=prompt,
                system_message="你是一位专业的生物医学研究员，擅长解读实验数据和结果。",
                temperature=0.3
            )

            # 尝试解析结构化信息
            structured = self.model.extract_structured_data(
                text=interpretation,
                schema={
                    "conclusion": "string",
                    "key_findings": "array",
                    "statistical_significance": "string",
                    "biological_significance": "string",
                    "limitations": "array",
                    "future_directions": "array"
                }
            )

            return {
                "text": interpretation,
                "structured": structured
            }

        except Exception as e:
            logger.error(f"AI解读失败: {e}")
            return {"error": str(e)}

    def _build_interpretation_prompt(
        self,
        data: pd.DataFrame,
        experiment: Dict[str, Any]
    ) -> str:
        """构建解读提示词"""
        # 数据摘要
        data_summary = {
            "shape": data.shape,
            "columns": list(data.columns),
            "numeric_summary": data.describe().to_dict()
        }

        prompt = f"""
请解读以下实验结果：

## 实验信息
实验目标: {experiment.get('objective', '')}
实验方案: {json.dumps(experiment.get('plan', {}), ensure_ascii=False, indent=2)}

## 数据概览
{json.dumps(data_summary, ensure_ascii=False, indent=2)}

## 数据样本
{data.head().to_string()}

请从以下角度进行分析：
1. 实验结果的总体结论
2. 关键发现和统计显著性
3. 生物学意义解读
4. 实验局限性
5. 后续研究方向建议

请提供专业、客观的解读。
        """

        return prompt

    def compare_experiments(
        self,
        experiment_ids: List[str],
        data_files: List[str]
    ) -> Dict[str, Any]:
        """比较多个实验的结果"""
        datasets = []
        for exp_id, file_path in zip(experiment_ids, data_files):
            data = self.load_data(file_path)
            data["experiment_id"] = exp_id
            datasets.append(data)

        # 合并数据
        combined_data = pd.concat(datasets, ignore_index=True)

        comparison = {
            "combined_summary": self._summarize_data(combined_data),
            "experiment_comparison": {},
            "visualizations": []
        }

        # 比较分析
        numeric_cols = combined_data.select_dtypes(include=[np.number]).columns
        categorical_cols = combined_data.select_dtypes(include=["object"]).columns

        if len(numeric_cols) > 0 and "experiment_id" in combined_data.columns:
            # 按实验分组统计
            for col in numeric_cols[:5]:
                grouped = combined_data.groupby("experiment_id")[col].agg([
                    "mean", "std", "count"
                ]).to_dict()
                comparison["experiment_comparison"][col] = grouped

            # 创建比较图表
            fig, axes = plt.subplots(min(3, len(numeric_cols)), 1, figsize=(12, 15))
            if len(numeric_cols) == 1:
                axes = [axes]
            for i, col in enumerate(numeric_cols[:3]):
                combined_data.boxplot(column=col, by="experiment_id", ax=axes[i])
                axes[i].set_title(f"{col} 实验间比较")
                plt.suptitle("")

            plt.tight_layout()
            chart_file = self.charts_dir / "experiment_comparison.png"
            plt.savefig(chart_file)
            plt.close()
            comparison["visualizations"].append(str(chart_file))

        return comparison
