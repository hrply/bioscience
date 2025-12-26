#!/usr/bin/env python3
"""
IBD患者肠道DRAK2(STK17B)表达水平ROC曲线分析
分析DRAK2高表达与IBD患病的相关性
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc, roc_auc_score
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体（可选）
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

class IBDROCanalysis:
    def __init__(self, data_path=None):
        """
        初始化ROC分析类
        
        参数:
        data_path: 数据文件路径，如果为None则需要手动加载数据
        """
        self.data_path = data_path
        self.data = None
        self.draK2_col = 'STK17B'  # DRAK2基因符号
        self.status_col = 'IBD_status'  # IBD状态列
        
    def load_data(self, file_path, file_type='csv'):
        """
        加载数据
        
        参数:
        file_path: 文件路径
        file_type: 文件类型 ('csv', 'excel', 'tsv')
        """
        try:
            if file_type == 'csv':
                self.data = pd.read_csv(file_path)
            elif file_type == 'excel':
                self.data = pd.read_excel(file_path)
            elif file_type == 'tsv':
                self.data = pd.read_csv(file_path, sep='\t')
            else:
                raise ValueError("不支持的文件类型")
                
            print(f"数据加载成功，共{len(self.data)}个样本")
            print(f"数据列: {list(self.data.columns)}")
            return True
        except Exception as e:
            print(f"数据加载失败: {e}")
            return False
    
    def preprocess_data(self):
        """
        数据预处理
        """
        if self.data is None:
            raise ValueError("请先加载数据")
            
        # 检查必要的列是否存在
        if self.draK2_col not in self.data.columns:
            raise ValueError(f"数据中未找到{self.draK2_col}列")
            
        if self.status_col not in self.data.columns:
            raise ValueError(f"数据中未找到{self.status_col}列")
            
        # 处理缺失值
        self.data = self.data.dropna(subset=[self.draK2_col, self.status_col])
        
        # 确保IBD状态为二分类 (0=健康, 1=IBD)
        unique_status = self.data[self.status_col].unique()
        print(f"IBD状态分布: {dict(zip(*np.unique(self.data[self.status_col], return_counts=True)))}")
        
        return self.data
    
    def calculate_roc_curve(self):
        """
        计算ROC曲线
        """
        if self.data is None:
            raise ValueError("请先加载数据")
            
        # 提取特征和标签
        y_true = self.data[self.status_col].values
        y_scores = self.data[self.draK2_col].values
        
        # 计算ROC曲线
        fpr, tpr, thresholds = roc_curve(y_true, y_scores)
        roc_auc = auc(fpr, tpr)
        
        # 找到最佳阈值 (Youden指数)
        youden_index = tpr - fpr
        optimal_threshold_idx = np.argmax(youden_index)
        optimal_threshold = thresholds[optimal_threshold_idx]
        
        return {
            'fpr': fpr,
            'tpr': tpr,
            'thresholds': thresholds,
            'roc_auc': roc_auc,
            'optimal_threshold': optimal_threshold,
            'optimal_sensitivity': tpr[optimal_threshold_idx],
            'optimal_specificity': 1 - fpr[optimal_threshold_idx]
        }
    
    def plot_roc_curve(self, roc_data, save_path=None):
        """
        绘制ROC曲线
        
        参数:
        roc_data: ROC曲线数据
        save_path: 保存路径，如果为None则不保存
        """
        plt.figure(figsize=(10, 8))
        
        # 绘制ROC曲线
        plt.plot(roc_data['fpr'], roc_data['tpr'], 
                color='darkorange', lw=2, 
                label=f'ROC曲线 (AUC = {roc_data["roc_auc"]:.3f})')
        
        # 绘制对角线
        plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', 
                label='随机分类器')
        
        # 标记最佳阈值点
        optimal_idx = np.argmax(roc_data['tpr'] - roc_data['fpr'])
        plt.plot(roc_data['fpr'][optimal_idx], roc_data['tpr'][optimal_idx], 
                'ro', markersize=8, 
                label=f'最佳阈值 = {roc_data["optimal_threshold"]:.3f}')
        
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('假阳性率 (1 - 特异性)', fontsize=12)
        plt.ylabel('真阳性率 (敏感性)', fontsize=12)
        plt.title('DRAK2表达水平诊断IBD的ROC曲线分析', fontsize=14, fontweight='bold')
        plt.legend(loc="lower right", fontsize=10)
        plt.grid(True, alpha=0.3)
        
        # 添加统计信息
        stats_text = (f'AUC: {roc_data["roc_auc"]:.3f} (95% CI: 需要计算)\n'
                     f'最佳阈值: {roc_data["optimal_threshold"]:.3f}\n'
                     f'敏感性: {roc_data["optimal_sensitivity"]:.3f}\n'
                     f'特异性: {roc_data["optimal_specificity"]:.3f}')
        
        plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, 
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"ROC曲线已保存至: {save_path}")
        
        plt.show()
    
    def plot_expression_distribution(self, save_path=None):
        """
        绘制DRAK2表达分布图
        """
        if self.data is None:
            raise ValueError("请先加载数据")
            
        plt.figure(figsize=(12, 5))
        
        # 箱线图
        plt.subplot(1, 2, 1)
        sns.boxplot(x=self.status_col, y=self.draK2_col, data=self.data)
        plt.title('DRAK2表达水平分布', fontsize=12, fontweight='bold')
        plt.xlabel('IBD状态 (0=健康, 1=IBD)', fontsize=10)
        plt.ylabel('DRAK2表达水平', fontsize=10)
        
        # 小提琴图
        plt.subplot(1, 2, 2)
        sns.violinplot(x=self.status_col, y=self.draK2_col, data=self.data)
        plt.title('DRAK2表达密度分布', fontsize=12, fontweight='bold')
        plt.xlabel('IBD状态 (0=健康, 1=IBD)', fontsize=10)
        plt.ylabel('DRAK2表达水平', fontsize=10)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"表达分布图已保存至: {save_path}")
        
        plt.show()
    
    def perform_statistical_analysis(self):
        """
        执行统计分析
        """
        if self.data is None:
            raise ValueError("请先加载数据")
            
        from scipy import stats
        
        # 分离健康组和IBD组
        healthy_group = self.data[self.data[self.status_col] == 0][self.draK2_col]
        ibd_group = self.data[self.data[self.status_col] == 1][self.draK2_col]
        
        # 执行t检验
        t_stat, p_value = stats.ttest_ind(healthy_group, ibd_group)
        
        # 计算效应大小 (Cohen's d)
        pooled_std = np.sqrt(((len(healthy_group) - 1) * healthy_group.var() + 
                             (len(ibd_group) - 1) * ibd_group.var()) / 
                            (len(healthy_group) + len(ibd_group) - 2))
        cohens_d = (ibd_group.mean() - healthy_group.mean()) / pooled_std
        
        # 计算描述性统计
        stats_results = {
            'healthy_mean': healthy_group.mean(),
            'healthy_std': healthy_group.std(),
            'healthy_n': len(healthy_group),
            'ibd_mean': ibd_group.mean(),
            'ibd_std': ibd_group.std(),
            'ibd_n': len(ibd_group),
            't_statistic': t_stat,
            'p_value': p_value,
            'cohens_d': cohens_d,
            'effect_size_interpretation': self._interpret_effect_size(cohens_d)
        }
        
        return stats_results
    
    def _interpret_effect_size(self, cohens_d):
        """
        解释效应大小
        """
        abs_d = abs(cohens_d)
        if abs_d < 0.2:
            return "小效应"
        elif abs_d < 0.5:
            return "中等效应"
        elif abs_d < 0.8:
            return "大效应"
        else:
            return "极大效应"
    
    def generate_report(self, roc_data, stats_results, save_path=None):
        """
        生成分析报告
        """
        report = f"""
# DRAK2(STK17B)表达水平与IBD患病相关性分析报告

## 1. 数据概览
- 总样本数: {len(self.data)}
- 健康对照组: {stats_results['healthy_n']} 例
- IBD患者组: {stats_results['ibd_n']} 例

## 2. 描述性统计
### DRAK2表达水平
- 健康对照组: {stats_results['healthy_mean']:.3f} ± {stats_results['healthy_std']:.3f}
- IBD患者组: {stats_results['ibd_mean']:.3f} ± {stats_results['ibd_std']:.3f}

## 3. 统计检验结果
- t统计量: {stats_results['t_statistic']:.3f}
- p值: {stats_results['p_value']:.6f}
- Cohen's d: {stats_results['cohens_d']:.3f} ({stats_results['effect_size_interpretation']})

## 4. ROC曲线分析
- AUC值: {roc_data['roc_auc']:.3f}
- 最佳阈值: {roc_data['optimal_threshold']:.3f}
- 敏感性: {roc_data['optimal_sensitivity']:.3f}
- 特异性: {roc_data['optimal_specificity']:.3f}

## 5. 结论
"""
        
        if stats_results['p_value'] < 0.05:
            if stats_results['ibd_mean'] > stats_results['healthy_mean']:
                report += "DRAK2在IBD患者中显著高表达，支持DRAK2高表达与IBD患病正相关的假设。"
            else:
                report += "DRAK2在IBD患者中显著低表达，与预期假设不符。"
        else:
            report += "DRAK2表达水平在IBD患者和健康对照组之间无显著差异。"
        
        report += f"\n\nROC曲线AUC值为{roc_data['roc_auc']:.3f}，"
        
        if roc_data['roc_auc'] > 0.7:
            report += "表明DRAK2表达水平对IBD具有较好的诊断价值。"
        elif roc_data['roc_auc'] > 0.5:
            report += "表明DRAK2表达水平对IBD具有一定的诊断价值。"
        else:
            report += "表明DRAK2表达水平对IBD的诊断价值有限。"
        
        print(report)
        
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"分析报告已保存至: {save_path}")
        
        return report


def main():
    """
    主函数示例
    """
    # 创建分析实例
    analyzer = IBDROCanalysis()
    
    # 示例数据生成（实际使用时应从文件加载）
    print("生成示例数据...")
    np.random.seed(42)
    n_healthy = 100
    n_ibd = 100
    
    # 健康对照组DRAK2表达 (正态分布)
    healthy_draK2 = np.random.normal(5.0, 1.5, n_healthy)
    
    # IBD患者组DRAK2表达 (高表达，均值更高)
    ibd_draK2 = np.random.normal(7.5, 2.0, n_ibd)
    
    # 创建数据框
    sample_data = pd.DataFrame({
        'STK17B': np.concatenate([healthy_draK2, ibd_draK2]),
        'IBD_status': np.concatenate([np.zeros(n_healthy), np.ones(n_ibd)])
    })
    
    analyzer.data = sample_data
    
    try:
        # 数据预处理
        analyzer.preprocess_data()
        
        # 计算ROC曲线
        print("\n计算ROC曲线...")
        roc_data = analyzer.calculate_roc_curve()
        
        # 绘制ROC曲线
        print("绘制ROC曲线...")
        analyzer.plot_roc_curve(roc_data, save_path='DRAK2_ROC_Curve.png')
        
        # 绘制表达分布
        print("绘制表达分布图...")
        analyzer.plot_expression_distribution(save_path='DRAK2_Expression_Distribution.png')
        
        # 统计分析
        print("\n执行统计分析...")
        stats_results = analyzer.perform_statistical_analysis()
        
        # 生成报告
        print("\n生成分析报告...")
        analyzer.generate_report(roc_data, stats_results, save_path='DRAK2_IBD_Analysis_Report.md')
        
    except Exception as e:
        print(f"分析过程中出现错误: {e}")


if __name__ == "__main__":
    main()