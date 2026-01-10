#!/usr/bin/env python3
"""
数据迁移脚本
用于从旧的目录结构迁移到新的卷结构

旧的目录结构：
- ./data/experiments/
- ./data/results/
- ./data/uploads/
- ./data/chroma/
- ./config/
- ./templates/

新的卷结构：
- ai_researcher_data 卷：/app/data/
  - /app/data/experiments/
  - /app/data/results/
  - /app/data/uploads/
  - /app/data/config/
  - /app/data/templates/
- ai_researcher_chroma 卷：/app/chroma/
- ai_researcher_uploads 卷：/app/uploads/
"""

import os
import shutil
from pathlib import Path


def migrate_data():
    """执行数据迁移"""
    print("🔄 开始数据迁移...")

    # 创建新目录结构
    directories = [
        "/app/data/experiments",
        "/app/data/results",
        "/app/data/config",
        "/app/data/templates",
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ 创建目录: {directory}")

    # 迁移实验数据
    old_experiments = "./data/experiments"
    if os.path.exists(old_experiments):
        shutil.copytree(old_experiments, "/app/data/experiments", dirs_exist_ok=True)
        print(f"✅ 迁移实验数据: {old_experiments} -> /app/data/experiments")

    # 迁移结果数据
    old_results = "./data/results"
    if os.path.exists(old_results):
        shutil.copytree(old_results, "/app/data/results", dirs_exist_ok=True)
        print(f"✅ 迁移结果数据: {old_results} -> /app/data/results")

    # 迁移配置文件
    old_config = "./config"
    if os.path.exists(old_config):
        shutil.copytree(old_config, "/app/data/config", dirs_exist_ok=True)
        print(f"✅ 迁移配置文件: {old_config} -> /app/data/config")

    # 迁移模板文件
    old_templates = "./templates"
    if os.path.exists(old_templates):
        shutil.copytree(old_templates, "/app/data/templates", dirs_exist_ok=True)
        print(f"✅ 迁移模板文件: {old_templates} -> /app/data/templates")

    # 迁移ChromaDB
    old_chroma = "./data/chroma"
    if os.path.exists(old_chroma):
        shutil.copytree(old_chroma, "/app/chroma", dirs_exist_ok=True)
        print(f"✅ 迁移ChromaDB: {old_chroma} -> /app/chroma")

    # 迁移上传文件
    old_uploads = "./data/uploads"
    if os.path.exists(old_uploads):
        shutil.copytree(old_uploads, "/app/uploads", dirs_exist_ok=True)
        print(f"✅ 迁移上传文件: {old_uploads} -> /app/uploads")

    print("\n🎉 数据迁移完成！")
    print("\n📝 注意事项：")
    print("1. 旧的目录结构已保留，但新数据将写入新的卷结构")
    print("2. 如需清理旧目录，请在确认迁移成功后手动删除")
    print("3. 建议创建备份以防万一")


if __name__ == "__main__":
    migrate_data()
