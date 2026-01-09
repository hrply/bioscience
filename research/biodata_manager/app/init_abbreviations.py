"""
初始化缩写映射数据
从short.md文件读取并导入到数据库
"""

import sqlite3
from pathlib import Path


def init_abbreviations():
    """初始化缩写映射数据"""
    
    # 读取short.md文件
    short_md_path = Path(__file__).parent.parent / 'short.md'
    
    if not short_md_path.exists():
        print(f"警告: 找不到short.md文件: {short_md_path}")
        return
    
    with open(short_md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析数据类型缩写
    data_type_full = []
    data_type_abbr = []
    
    in_data_type_section = False
    in_data_type_abbr_section = False
    
    for line in content.split('\n'):
        if '# 数据类型' in line and '缩写' not in line:
            in_data_type_section = True
            continue
        if '# 数据类型缩写' in line:
            in_data_type_section = False
            in_data_type_abbr_section = True
            continue
        if '# 物种' in line:
            in_data_type_abbr_section = False
            break
        
        if line.strip() and not line.startswith('#'):
            if in_data_type_section:
                data_type_full.extend([item.strip() for item in line.split(',')])
            elif in_data_type_abbr_section:
                data_type_abbr.extend([item.strip() for item in line.split(',')])
    
    # 解析物种缩写
    organism_full = []
    organism_abbr = []
    
    in_organism_section = False
    in_organism_abbr_section = False
    
    for line in content.split('\n'):
        if '# 物种' in line and '缩写' not in line:
            in_organism_section = True
            continue
        if '# 物种缩写' in line:
            in_organism_section = False
            in_organism_abbr_section = True
            continue
        if '# 样本来源' in line:
            in_organism_abbr_section = False
            break
        
        if line.strip() and not line.startswith('#'):
            if in_organism_section:
                organism_full.extend([item.strip() for item in line.split(',')])
            elif in_organism_abbr_section:
                # 使用中文逗号和英文逗号分割
                organism_abbr.extend([item.strip() for item in line.replace('，', ',').split(',')])
    
    # 解析样本类型缩写
    sample_type_full = []
    sample_type_abbr = []
    
    in_sample_type_section = False
    in_sample_type_abbr_section = False
    
    for line in content.split('\n'):
        if '# 样本来源' in line and '缩写' not in line:
            in_sample_type_section = True
            continue
        if '# 样本来源缩写' in line:
            in_sample_type_section = False
            in_sample_type_abbr_section = True
            continue
        
        if line.strip() and not line.startswith('#'):
            if in_sample_type_section:
                sample_type_full.extend([item.strip() for item in line.split(',')])
            elif in_sample_type_abbr_section:
                sample_type_abbr.extend([item.strip() for item in line.split(',')])
    
    # 连接数据库 - 支持环境变量配置
    import os
    db_path_from_env = os.environ.get('BIODATA_DB_PATH')
    if db_path_from_env:
        db_path = Path(db_path_from_env)
    else:
        db_path = Path(__file__).parent / 'data' / 'biodata.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 插入数据类型缩写
    for full, abbr in zip(data_type_full, data_type_abbr):
        cursor.execute("""
            INSERT OR REPLACE INTO data_type_abbreviations (full_name, abbreviation)
            VALUES (?, ?)
        """, (full, abbr))
    
    # 插入物种缩写
    for full, abbr in zip(organism_full, organism_abbr):
        cursor.execute("""
            INSERT OR REPLACE INTO organism_abbreviations (full_name, abbreviation)
            VALUES (?, ?)
        """, (full, abbr))
    
    # 插入样本类型缩写
    for full, abbr in zip(sample_type_full, sample_type_abbr):
        cursor.execute("""
            INSERT OR REPLACE INTO sample_type_abbreviations (full_name, abbreviation)
            VALUES (?, ?)
        """, (full, abbr))
    
    conn.commit()
    conn.close()
    
    print(f"已导入 {len(data_type_full)} 个数据类型缩写")
    print(f"已导入 {len(organism_full)} 个物种缩写")
    print(f"已导入 {len(sample_type_full)} 个样本类型缩写")


if __name__ == '__main__':
    init_abbreviations()
