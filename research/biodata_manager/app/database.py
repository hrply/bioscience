#!/usr/bin/env python3
"""
SQLite数据库操作模块
用于生物信息学数据管理系统的数据存储
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

class BioDataDB:
    """生物信息学数据数据库操作类"""
    
    def __init__(self, db_path: str = None):
        """初始化数据库连接"""
        if db_path is None:
            # 使用相对路径
            db_path = "data/biodata.db"
        
        self.db_path = Path(db_path)
        # 如果是相对路径，相对于脚本所在目录
        if not self.db_path.is_absolute():
            self.db_path = Path(__file__).parent / self.db_path
        
        self.conn = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """建立数据库连接"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)
        self.conn.row_factory = sqlite3.Row  # 使查询结果可以按列名访问
        # 启用外键约束
        self.conn.execute("PRAGMA foreign_keys = ON")
    
    def _create_tables(self):
        """创建数据库表"""
        cursor = self.conn.cursor()
        
        # 项目表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                doi TEXT,
                db_id TEXT,
                db_link TEXT,
                data_type TEXT DEFAULT 'other',
                organism TEXT DEFAULT 'human',
                authors TEXT,
                journal TEXT,
                description TEXT,
                created_date TEXT,
                path TEXT,
                indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 文件表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                path TEXT NOT NULL,
                size TEXT,
                size_bytes INTEGER,
                type TEXT,
                modified TEXT,
                indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)
        
        # 标签表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                tag TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_data_type ON projects(data_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_organism ON projects(organism)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_created_date ON projects(created_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_project_id ON files(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_project_id ON tags(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag)")
        
        # 处理数据表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_data (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                title TEXT NOT NULL,
                description TEXT,
                analysis_type TEXT DEFAULT 'other',
                software TEXT,
                parameters TEXT,
                created_date TEXT,
                path TEXT,
                indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)
        
        # 处理数据文件表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                processed_data_id TEXT NOT NULL,
                name TEXT NOT NULL,
                path TEXT NOT NULL,
                size TEXT,
                size_bytes INTEGER,
                type TEXT,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (processed_data_id) REFERENCES processed_data(id) ON DELETE CASCADE
            )
        """)
        
        # 创建全文搜索虚拟表（用于项目搜索）
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS projects_fts USING fts5(
                id, title, authors, journal, description, 
                content='projects', content_rowid='rowid'
            )
        """)
        
        # 创建触发器，自动更新全文搜索索引
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS projects_fts_insert AFTER INSERT ON projects
            BEGIN
                INSERT INTO projects_fts(id, title, authors, journal, description)
                VALUES (new.id, new.title, new.authors, new.journal, new.description);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS projects_fts_delete AFTER DELETE ON projects
            BEGIN
                DELETE FROM projects_fts WHERE id = old.id;
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS projects_fts_update AFTER UPDATE ON projects
            BEGIN
                DELETE FROM projects_fts WHERE id = old.id;
                INSERT INTO projects_fts(id, title, authors, journal, description)
                VALUES (new.id, new.title, new.authors, new.journal, new.description);
            END
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_processed_data_project_id ON processed_data(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_processed_data_analysis_type ON processed_data(analysis_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_processed_files_processed_data_id ON processed_files(processed_data_id)")
        
        # 缩写表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_type_abbreviations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL UNIQUE,
                abbreviation TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS organism_abbreviations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL UNIQUE,
                abbreviation TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sample_type_abbreviations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL UNIQUE,
                abbreviation TEXT NOT NULL
            )
        """)
        
        self.conn.commit()
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    # ==================== 项目操作 ====================
    
    def insert_project(self, project: Dict) -> str:
        """插入新项目"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO projects (
                id, title, doi, db_id, db_link, data_type, organism,
                authors, journal, description, created_date, path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project['id'],
            project['title'],
            project.get('doi', ''),
            project.get('dbId', ''),
            project.get('dbLink', ''),
            project.get('dataType', 'other'),
            project.get('organism', 'human'),
            project.get('authors', ''),
            project.get('journal', ''),
            project.get('description', ''),
            project.get('createdDate', datetime.now().strftime('%Y-%m-%d')),
            project.get('path', '')
        ))
        self.conn.commit()
        return project['id']
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """获取单个项目"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()

        if not row:
            return None

        project = dict(row)
        # 转换字段名为驼峰格式（与前端兼容）
        project['dbId'] = project.pop('db_id', '')
        project['dbLink'] = project.pop('db_link', '')
        project['createdDate'] = project.pop('created_date', '')

        # 获取项目标签
        project['tags'] = self.get_project_tags(project_id)
        # 获取项目文件
        project['files'] = self.get_project_files(project_id)

        return project
    
    def get_all_projects(self, limit: int = None, offset: int = None) -> List[Dict]:
        """获取所有项目"""
        cursor = self.conn.cursor()
        query = "SELECT * FROM projects ORDER BY created_date DESC"
        params = []

        if limit:
            query += " LIMIT ?"
            params.append(limit)
        if offset:
            query += " OFFSET ?"
            params.append(offset)

        cursor.execute(query, params)
        projects = []

        for row in cursor.fetchall():
            project = dict(row)
            # 转换字段名为驼峰格式（与前端兼容）
            project['dbId'] = project.pop('db_id', '')
            project['dbLink'] = project.pop('db_link', '')
            project['createdDate'] = project.pop('created_date', '')
            project['dataType'] = project.pop('data_type', '其他')

            project['tags'] = self.get_project_tags(project['id'])
            project['files'] = self.get_project_files(project['id'])
            projects.append(project)

        return projects
    
    def update_project(self, project_id: str, project_data: Dict) -> bool:
        """更新项目信息（只更新提供的字段）"""
        cursor = self.conn.cursor()

        # 字段映射（驼峰到下划线）
        field_map = {
            'title': 'title',
            'name': 'title',  # 别名：name也映射到title
            'doi': 'doi',
            'dbId': 'db_id',
            'db_link': 'db_link',  # 修正映射
            'dbLink': 'db_link',
            'dataType': 'data_type',
            'data_type': 'data_type',  # 别名：支持下划线格式
            'organism': 'organism',
            'authors': 'authors',
            'journal': 'journal',
            'description': 'description',
            'createdDate': 'created_date',
            'created_date': 'created_date',
            'path': 'path'
        }

        # 构建动态UPDATE语句
        updates = []
        params = []
        for key, db_field in field_map.items():
            if key in project_data:
                # 对数据进行基本验证和清理，防止SQL注入和特殊字符问题
                value = project_data[key]
                if value is not None and isinstance(value, (str, int, float)):
                    # 对字符串进行基本清理
                    if isinstance(value, str):
                        # 限制字符串长度，防止过长的输入
                        value = value[:500]  # 限制为500字符
                    updates.append(f"{db_field} = ?")
                    params.append(value)
                else:
                    # 跳过无效值
                    continue

        if not updates:
            return False  # 没有字段需要更新

        params.append(project_id)
        sql = f"UPDATE projects SET {', '.join(updates)} WHERE id = ?"
        try:
            cursor.execute(sql, params)
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"数据库更新错误: {e}")
            self.conn.rollback()
            return False
    
    def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def search_projects(self, query: str = None, data_type: str = None, 
                       organism: str = None, tags: List[str] = None) -> List[Dict]:
        """搜索项目"""
        cursor = self.conn.cursor()
        
        # 基础查询
        sql = "SELECT DISTINCT p.* FROM projects p"
        params = []
        conditions = []
        
        # 如果有文本搜索查询，使用全文搜索
        if query:
            sql += " JOIN projects_fts fts ON p.id = fts.id"
            conditions.append("projects_fts MATCH ?")
            params.append(query)
        
        # 数据类型筛选
        if data_type:
            conditions.append("p.data_type = ?")
            params.append(data_type)
        
        # 物种筛选
        if organism:
            conditions.append("p.organism = ?")
            params.append(organism)
        
        # 标签筛选
        if tags:
            sql += " JOIN tags t ON p.id = t.project_id"
            placeholders = ",".join(["?"] * len(tags))
            conditions.append(f"t.tag IN ({placeholders})")
            params.extend(tags)
        
        # 添加WHERE条件
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        sql += " ORDER BY p.created_date DESC"
        
        cursor.execute(sql, params)
        projects = []
        
        for row in cursor.fetchall():
            project = dict(row)
            # 转换字段名为驼峰格式（与前端兼容）
            project['dbId'] = project.pop('db_id', '')
            project['dbLink'] = project.pop('db_link', '')
            
            # 转换数据类型为中文格式（与元数据配置匹配）
            # 包含英文到元数据配置格式和中文到元数据配置格式的映射
            data_type_mapping = {
                'transcriptomics': '转录组 (RNA-seq)',  # 英文转为元数据配置格式
                'scrna-seq': '单细胞转录组',  # 英文转为元数据配置格式
                'spatial': '空间转录组',  # 英文转为元数据配置格式
                'proteomics': '蛋白组',  # 英文转为元数据配置格式
                'phosphoproteomics': '磷酸化组',  # 英文转为元数据配置格式
                'cytof': '质谱流式',  # 英文转为元数据配置格式
                'multiomics': '多组学',  # 英文转为元数据配置格式
                'other': '其他',  # 英文转为元数据配置格式
                # 已经是简短中文格式的值，映射到元数据配置格式
                '转录组': '转录组 (RNA-seq)',
                '单细胞转录组': '单细胞转录组',
                '空间转录组': '空间转录组',
                '蛋白组': '蛋白组',
                '磷酸化组': '磷酸化组',
                '质谱流式': '质谱流式',
                '多组学': '多组学',
                '其他': '其他'
            }
            original_data_type = project.pop('data_type', 'other')
            project['dataType'] = data_type_mapping.get(original_data_type, original_data_type)
            
            project['tags'] = self.get_project_tags(project['id'])
            project['files'] = self.get_project_files(project['id'])
            projects.append(project)
        
        return projects
    
    def get_project_count(self) -> int:
        """获取项目总数"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM projects")
        return cursor.fetchone()[0]
    
    def get_projects_by_type(self) -> Dict[str, int]:
        """按数据类型统计项目数量"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT data_type, COUNT(*) as count 
            FROM projects 
            GROUP BY data_type
        """)
        return {row['data_type']: row['count'] for row in cursor.fetchall()}
    
    def get_projects_by_organism(self) -> Dict[str, int]:
        """按物种统计项目数量"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT organism, COUNT(*) as count 
            FROM projects 
            GROUP BY organism
        """)
        return {row['organism']: row['count'] for row in cursor.fetchall()}
    
    # ==================== 文件操作 ====================
    
    def insert_file(self, project_id: str, file_data: Dict) -> int:
        """插入文件记录"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO files (
                project_id, name, path, size, size_bytes, type, modified
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            file_data['name'],
            file_data['path'],
            file_data.get('size', ''),
            file_data.get('sizeBytes', 0),
            file_data.get('type', ''),
            file_data.get('modified', '')
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_project_files(self, project_id: str) -> List[Dict]:
        """获取项目文件列表"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM files WHERE project_id = ? ORDER BY name", (project_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def delete_project_files(self, project_id: str) -> bool:
        """删除项目的所有文件记录"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM files WHERE project_id = ?", (project_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    # ==================== 标签操作 ====================

    def update_project_tags(self, project_id: str, tags: List[str]) -> bool:
        """更新项目标签（删除旧的，添加新的）"""
        cursor = self.conn.cursor()
        try:
            # 删除项目的所有旧标签
            cursor.execute("DELETE FROM tags WHERE project_id = ?", (project_id,))
            # 添加新标签
            for tag in tags:
                if tag.strip():  # 跳过空标签
                    cursor.execute("INSERT INTO tags (project_id, tag) VALUES (?, ?)", (project_id, tag.strip()))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"更新项目标签失败: {e}")
            self.conn.rollback()
            return False

    def add_project_tag(self, project_id: str, tag: str) -> bool:
        """为项目添加标签"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO tags (project_id, tag) VALUES (?, ?)
            """, (project_id, tag))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False
    
    def get_project_tags(self, project_id: str) -> List[str]:
        """获取项目标签"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT tag FROM tags WHERE project_id = ? ORDER BY tag", (project_id,))
        return [row['tag'] for row in cursor.fetchall()]
    
    def remove_project_tag(self, project_id: str, tag: str) -> bool:
        """删除项目标签"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tags WHERE project_id = ? AND tag = ?", (project_id, tag))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_all_tags(self) -> List[str]:
        """获取所有标签"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT tag FROM tags ORDER BY tag")
        return [row['tag'] for row in cursor.fetchall()]
    
    # ==================== 数据迁移 ====================
    
    def migrate_from_json(self, json_file_path: str) -> Tuple[int, int]:
        """从JSON文件迁移数据"""
        if not Path(json_file_path).exists():
            return 0, 0
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            projects_data = json.load(f)
        
        projects_migrated = 0
        files_migrated = 0
        
        for project_data in projects_data:
            try:
                # 插入项目
                self.insert_project(project_data)
                projects_migrated += 1
                
                # 插入文件
                project_id = project_data['id']
                for file_data in project_data.get('files', []):
                    self.insert_file(project_id, file_data)
                    files_migrated += 1
                
                # 插入标签
                for tag in project_data.get('tags', []):
                    self.add_project_tag(project_id, tag)
                    
            except Exception as e:
                print(f"迁移项目失败 {project_data.get('id', 'unknown')}: {e}")
                continue
        
        return projects_migrated, files_migrated
    
    def export_to_json(self, json_file_path: str) -> bool:
        """导出数据到JSON文件"""
        try:
            projects = self.get_all_projects()
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(projects, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出到JSON失败: {e}")
            return False
    
    # ==================== 处理数据操作 ====================
    
    def insert_processed_data(self, processed_data: Dict) -> str:
        """插入新的处理数据"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO processed_data (
                id, project_id, title, description, analysis_type, software,
                parameters, created_date, path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            processed_data['id'],
            processed_data['project_id'],
            processed_data['title'],
            processed_data.get('description', ''),
            processed_data.get('analysis_type', 'other'),
            processed_data.get('software', ''),
            processed_data.get('parameters', ''),
            processed_data.get('created_date', datetime.now().strftime('%Y-%m-%d')),
            processed_data.get('path', '')
        ))
        self.conn.commit()
        return processed_data['id']
    
    def get_processed_data(self, processed_data_id: str) -> Optional[Dict]:
        """获取单个处理数据"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM processed_data WHERE id = ?", (processed_data_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        processed_data = dict(row)
        # 获取处理数据文件
        processed_data['files'] = self.get_processed_files(processed_data_id)
        
        return processed_data
    
    def get_all_processed_data(self, project_id: str = None) -> List[Dict]:
        """获取所有处理数据"""
        cursor = self.conn.cursor()
        
        if project_id:
            cursor.execute("SELECT * FROM processed_data WHERE project_id = ? ORDER BY created_date DESC", (project_id,))
        else:
            cursor.execute("SELECT * FROM processed_data ORDER BY created_date DESC")
        
        processed_data_list = []
        
        for row in cursor.fetchall():
            processed_data = dict(row)
            processed_data['files'] = self.get_processed_files(processed_data['id'])
            processed_data_list.append(processed_data)
        
        return processed_data_list
    
    def update_processed_data(self, processed_data_id: str, processed_data: Dict) -> bool:
        """更新处理数据信息"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE processed_data SET
                title = ?, description = ?, analysis_type = ?, software = ?,
                parameters = ?, path = ?
            WHERE id = ?
        """, (
            processed_data.get('title', ''),
            processed_data.get('description', ''),
            processed_data.get('analysis_type', 'other'),
            processed_data.get('software', ''),
            processed_data.get('parameters', ''),
            processed_data.get('path', ''),
            processed_data_id
        ))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_processed_data(self, processed_data_id: str) -> bool:
        """删除处理数据"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM processed_data WHERE id = ?", (processed_data_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def insert_processed_file(self, processed_data_id: str, file_data: Dict) -> int:
        """插入处理数据文件记录"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO processed_files (
                processed_data_id, name, path, size, size_bytes, type, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            processed_data_id,
            file_data['name'],
            file_data['path'],
            file_data.get('size', ''),
            file_data.get('size_bytes', 0),
            file_data.get('type', ''),
            file_data.get('description', '')
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_processed_files(self, processed_data_id: str) -> List[Dict]:
        """获取处理数据文件列表"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM processed_files WHERE processed_data_id = ? ORDER BY name", (processed_data_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def delete_processed_files(self, processed_data_id: str) -> bool:
        """删除处理数据的所有文件记录"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM processed_files WHERE processed_data_id = ?", (processed_data_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_processed_data_count(self) -> int:
        """获取处理数据总数"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM processed_data")
        return cursor.fetchone()[0]
    
    def get_processed_data_by_type(self) -> Dict[str, int]:
        """按分析类型统计处理数据数量"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT analysis_type, COUNT(*) as count 
            FROM processed_data 
            GROUP BY analysis_type
        """)
        return {row['analysis_type']: row['count'] for row in cursor.fetchall()}
    
    # ==================== 缩写查询操作 ====================
    
    def get_data_type_abbreviation(self, full_name: str) -> Optional[str]:
        """根据完整名称获取数据类型缩写"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT abbreviation FROM data_type_abbreviations WHERE full_name = ?
        """, (full_name,))
        row = cursor.fetchone()
        return row['abbreviation'] if row else None
    
    def get_organism_abbreviation(self, full_name: str) -> Optional[str]:
        """根据完整名称获取物种缩写"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT abbreviation FROM organism_abbreviations WHERE full_name = ?
        """, (full_name,))
        row = cursor.fetchone()
        return row['abbreviation'] if row else None
    
    def get_sample_type_abbreviation(self, full_name: str) -> Optional[str]:
        """根据完整名称获取样本类型缩写"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT abbreviation FROM sample_type_abbreviations WHERE full_name = ?
        """, (full_name,))
        row = cursor.fetchone()
        return row['abbreviation'] if row else None
    
    # ==================== 缩写查询操作 ====================
    
    def get_data_type_abbreviation(self, full_name: str) -> Optional[str]:
        """获取数据类型的缩写"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT abbreviation FROM data_type_abbreviations WHERE full_name = ?", (full_name,))
        row = cursor.fetchone()
        return row['abbreviation'] if row else None
    
    def get_organism_abbreviation(self, full_name: str) -> Optional[str]:
        """获取物种的缩写"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT abbreviation FROM organism_abbreviations WHERE full_name = ?", (full_name,))
        row = cursor.fetchone()
        return row['abbreviation'] if row else None
    
    def get_sample_type_abbreviation(self, full_name: str) -> Optional[str]:
        """获取样本类型的缩写"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT abbreviation FROM sample_type_abbreviations WHERE full_name = ?", (full_name,))
        row = cursor.fetchone()
        return row['abbreviation'] if row else None