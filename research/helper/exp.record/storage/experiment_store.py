"""
实验存储管理 - 记录完整的实验修订历史
"""

import sqlite3
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import uuid


class ExperimentStore:
    """实验记录存储管理器"""
    
    def __init__(self, db_path: str = None, settings=None):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # 设置数据库路径
        if db_path is None:
            if settings:
                db_path = settings.db_path
            else:
                db_path = Path.home() / ".lab_notebook_agent" / "experiments.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建实验记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS experiments (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    template_id TEXT NOT NULL,
                    user_modifications TEXT NOT NULL,
                    original_template TEXT NOT NULL,
                    revised_content TEXT NOT NULL,
                    validation_result TEXT,
                    revision_markers TEXT,
                    diff_comparison TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建修订历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS revision_history (
                    id TEXT PRIMARY KEY,
                    experiment_id TEXT NOT NULL,
                    revision_number INTEGER NOT NULL,
                    change_type TEXT NOT NULL,
                    change_description TEXT,
                    previous_content TEXT,
                    new_content TEXT,
                    user_prompt TEXT,
                    validation_result TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (experiment_id) REFERENCES experiments (id) ON DELETE CASCADE
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_experiments_template_id 
                ON experiments(template_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_experiments_created_at 
                ON experiments(created_at)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_revision_history_experiment_id 
                ON revision_history(experiment_id)
            ''')
            
            conn.commit()
            self.logger.info("Database initialized successfully")
    
    def save_experiment(self, experiment_data: Dict[str, Any]) -> str:
        """保存实验记录"""
        experiment_id = experiment_data.get("id") or str(uuid.uuid4())
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 准备数据
                validation_result = json.dumps(experiment_data.get("validation_result", {}))
                revision_markers = json.dumps(experiment_data.get("revision_markers", []))
                diff_comparison = json.dumps(experiment_data.get("diff_comparison", {}))
                metadata = json.dumps(experiment_data.get("metadata", {}))
                
                # 插入或更新实验记录
                cursor.execute('''
                    INSERT OR REPLACE INTO experiments (
                        id, title, template_id, user_modifications, 
                        original_template, revised_content, validation_result,
                        revision_markers, diff_comparison, metadata, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    experiment_id,
                    experiment_data.get("experiment_title", ""),
                    experiment_data.get("template_id", ""),
                    experiment_data.get("user_modifications", ""),
                    experiment_data.get("original_template", ""),
                    experiment_data.get("revised_content", ""),
                    validation_result,
                    revision_markers,
                    diff_comparison,
                    metadata,
                    datetime.now().isoformat()
                ))
                
                # 如果是新的实验记录，创建初始修订历史
                if not experiment_data.get("id"):
                    self._create_initial_revision(conn, experiment_id, experiment_data)
                
                conn.commit()
                self.logger.info(f"Experiment {experiment_id} saved successfully")
                
                return experiment_id
                
        except Exception as e:
            self.logger.error(f"Error saving experiment: {e}")
            raise
    
    def _create_initial_revision(self, conn: sqlite3.Connection, experiment_id: str, experiment_data: Dict[str, Any]):
        """创建初始修订历史记录"""
        cursor = conn.cursor()
        
        revision_id = str(uuid.uuid4())
        
        cursor.execute('''
            INSERT INTO revision_history (
                id, experiment_id, revision_number, change_type, 
                change_description, previous_content, new_content,
                user_prompt, validation_result
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            revision_id,
            experiment_id,
            1,
            "initial_creation",
            "创建初始实验记录",
            experiment_data.get("original_template", ""),
            experiment_data.get("revised_content", ""),
            experiment_data.get("user_modifications", ""),
            json.dumps(experiment_data.get("validation_result", {}))
        ))
    
    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """获取实验记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM experiments WHERE id = ?
                ''', (experiment_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # 转换为字典
                experiment = dict(row)
                
                # 解析JSON字段
                experiment["validation_result"] = json.loads(experiment["validation_result"] or "{}")
                experiment["revision_markers"] = json.loads(experiment["revision_markers"] or "[]")
                experiment["diff_comparison"] = json.loads(experiment["diff_comparison"] or "{}")
                experiment["metadata"] = json.loads(experiment["metadata"] or "{}")
                
                return experiment
                
        except Exception as e:
            self.logger.error(f"Error getting experiment {experiment_id}: {e}")
            return None
    
    def list_experiments(self, template_id: str = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """列出实验记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = '''
                    SELECT id, title, template_id, created_at, updated_at
                    FROM experiments
                '''
                params = []
                
                if template_id:
                    query += ' WHERE template_id = ?'
                    params.append(template_id)
                
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                
                experiments = []
                for row in cursor.fetchall():
                    experiments.append(dict(row))
                
                return experiments
                
        except Exception as e:
            self.logger.error(f"Error listing experiments: {e}")
            return []
    
    def update_experiment(self, experiment_id: str, updates: Dict[str, Any]) -> bool:
        """更新实验记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 构建更新语句
                set_clauses = []
                params = []
                
                for key, value in updates.items():
                    if key in ["title", "revised_content", "validation_result", 
                              "revision_markers", "diff_comparison", "metadata"]:
                        set_clauses.append(f"{key} = ?")
                        if key in ["validation_result", "revision_markers", "diff_comparison", "metadata"]:
                            params.append(json.dumps(value))
                        else:
                            params.append(value)
                
                if set_clauses:
                    set_clauses.append("updated_at = ?")
                    params.append(datetime.now().isoformat())
                    params.append(experiment_id)
                    
                    cursor.execute(f'''
                        UPDATE experiments 
                        SET {', '.join(set_clauses)}
                        WHERE id = ?
                    ''', params)
                    
                    conn.commit()
                    self.logger.info(f"Experiment {experiment_id} updated successfully")
                    return True
                
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating experiment {experiment_id}: {e}")
            return False
    
    def delete_experiment(self, experiment_id: str) -> bool:
        """删除实验记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM experiments WHERE id = ?', (experiment_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    self.logger.info(f"Experiment {experiment_id} deleted successfully")
                    return True
                
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting experiment {experiment_id}: {e}")
            return False
    
    def get_revision_history(self, experiment_id: str) -> List[Dict[str, Any]]:
        """获取修订历史"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM revision_history 
                    WHERE experiment_id = ?
                    ORDER BY revision_number ASC
                ''', (experiment_id,))
                
                history = []
                for row in cursor.fetchall():
                    revision = dict(row)
                    # 解析JSON字段
                    if revision["validation_result"]:
                        revision["validation_result"] = json.loads(revision["validation_result"])
                    history.append(revision)
                
                return history
                
        except Exception as e:
            self.logger.error(f"Error getting revision history for {experiment_id}: {e}")
            return []
    
    def add_revision(self, experiment_id: str, revision_data: Dict[str, Any]) -> str:
        """添加修订记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取当前修订号
                cursor.execute('''
                    SELECT MAX(revision_number) FROM revision_history 
                    WHERE experiment_id = ?
                ''', (experiment_id,))
                
                result = cursor.fetchone()
                next_revision = (result[0] or 0) + 1
                
                # 插入新修订记录
                revision_id = str(uuid.uuid4())
                
                cursor.execute('''
                    INSERT INTO revision_history (
                        id, experiment_id, revision_number, change_type,
                        change_description, previous_content, new_content,
                        user_prompt, validation_result
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    revision_id,
                    experiment_id,
                    next_revision,
                    revision_data.get("change_type", "modification"),
                    revision_data.get("change_description", ""),
                    revision_data.get("previous_content", ""),
                    revision_data.get("new_content", ""),
                    revision_data.get("user_prompt", ""),
                    json.dumps(revision_data.get("validation_result", {}))
                ))
                
                conn.commit()
                self.logger.info(f"Revision {next_revision} added for experiment {experiment_id}")
                
                return revision_id
                
        except Exception as e:
            self.logger.error(f"Error adding revision to experiment {experiment_id}: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 总实验数
                cursor.execute('SELECT COUNT(*) FROM experiments')
                total_experiments = cursor.fetchone()[0]
                
                # 按模板分组的实验数
                cursor.execute('''
                    SELECT template_id, COUNT(*) as count 
                    FROM experiments 
                    GROUP BY template_id
                ''')
                experiments_by_template = dict(cursor.fetchall())
                
                # 最近活动
                cursor.execute('''
                    SELECT COUNT(*) FROM experiments 
                    WHERE created_at >= datetime('now', '-7 days')
                ''')
                recent_experiments = cursor.fetchone()[0]
                
                return {
                    "total_experiments": total_experiments,
                    "experiments_by_template": experiments_by_template,
                    "recent_experiments_7_days": recent_experiments,
                    "database_size_mb": self.db_path.stat().st_size / (1024 * 1024)
                }
                
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {}