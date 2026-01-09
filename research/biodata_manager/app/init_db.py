#!/usr/bin/env python3
"""
系统启动时初始化数据库
"""

import os
import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def initialize_database():
    """初始化数据库"""
    try:
        from database import BioDataDB
        
        print("初始化SQLite数据库...")
        
        # 初始化数据库
        db = BioDataDB()
        print(f"✓ 数据库已创建: {db.db_path}")
        
        # 显示数据库信息
        project_count = db.get_project_count()
        print(f"✓ 数据库初始化完成，当前项目数: {project_count}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = initialize_database()
    sys.exit(0 if success else 1)