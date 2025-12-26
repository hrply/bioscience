# Cytoflow Panel Design 项目

## 项目概述

这是生物科学实验项目中的细胞流式细胞术（Cytoflow）面板设计模块。该项目专注于流式细胞术实验中抗体面板的设计和优化。

## 项目结构

当前目录 `/home/hrply/software/bioscience/experiment/cytoflow/panel_design` 是一个新创建的模块，专门用于细胞流式细胞术面板设计工作。

## 相关项目

该项目是更大的生物科学项目的一部分，位于 `/home/hrply/software/bioscience/` 目录下。相关实验模块包括：

- `experiment/grouping_tool/`: 分组工具，包含Python Flask应用程序，用于实验数据的分组和分析
- `experiment/cytoflow/`: 细胞流式细胞术相关模块

## 技术栈

基于相关项目推断，可能使用的技术栈：
- Python (用于数据处理和分析)
- Flask (Web应用框架)
- SQLite (数据存储)
- Docker (容器化部署)

## 开发环境设置

由于这是一个新创建的模块，开发环境设置步骤待定。建议参考相关模块 `grouping_tool` 的设置方式：

```bash
# 安装依赖 (待创建requirements.txt)
pip install -r requirements.txt

# 运行应用 (待创建主应用文件)
python app.py
```

## 项目用途

该模块主要用于：
1. 流式细胞术抗体面板的设计
2. 抗体组合优化
3. 实验方案规划
4. 数据分析结果可视化

## 当前状态

- 目录已创建
- 基础文档框架已建立
- 核心功能模块待开发

## 下一步开发计划

1. 创建项目基础结构
2. 实现面板设计算法
3. 添加数据输入/输出功能
4. 集成可视化组件
5. 添加测试用例