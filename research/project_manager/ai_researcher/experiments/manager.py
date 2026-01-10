"""
实验进度管理系统
用于跟踪和管理实验进度
"""

import json
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


logger = logging.getLogger(__name__)


class ExperimentManager:
    """实验管理器"""

    def __init__(self, db_path: str = "experiments.db"):
        """
        初始化实验管理器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                id TEXT PRIMARY KEY,
                title TEXT,
                objective TEXT,
                plan TEXT,
                status TEXT DEFAULT 'planned',
                created_at TEXT,
                updated_at TEXT,
                relevant_docs TEXT,
                notes TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiment_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id TEXT,
                status TEXT,
                notes TEXT,
                data TEXT,
                timestamp TEXT,
                FOREIGN KEY (experiment_id) REFERENCES experiments (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiment_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id TEXT,
                results TEXT,
                analysis TEXT,
                created_at TEXT,
                FOREIGN KEY (experiment_id) REFERENCES experiments (id)
            )
        """)

        conn.commit()
        conn.close()

    def create_experiment(
        self,
        objective: str,
        plan: Dict[str, Any],
        relevant_docs: Optional[List[Dict]] = None,
        title: Optional[str] = None
    ) -> str:
        """
        创建新实验

        Args:
            objective: 实验目标
            plan: 实验方案
            relevant_docs: 相关文档
            title: 实验标题

        Returns:
            实验ID
        """
        experiment_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        created_at = datetime.now().isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO experiments (
                id, title, objective, plan, created_at, updated_at, relevant_docs
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            experiment_id,
            title or objective[:50],
            objective,
            json.dumps(plan, ensure_ascii=False),
            created_at,
            created_at,
            json.dumps(relevant_docs or [], ensure_ascii=False)
        ))

        # 添加初始进度记录
        cursor.execute("""
            INSERT INTO experiment_progress (
                experiment_id, status, notes, timestamp
            ) VALUES (?, ?, ?, ?)
        """, (experiment_id, "planned", "实验已创建", created_at))

        conn.commit()
        conn.close()

        logger.info(f"创建实验: {experiment_id}")
        return experiment_id

    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """
        获取实验信息

        Args:
            experiment_id: 实验ID

        Returns:
            实验信息字典
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM experiments WHERE id = ?
        """, (experiment_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "id": row[0],
            "title": row[1],
            "objective": row[2],
            "plan": json.loads(row[3]),
            "status": row[4],
            "created_at": row[5],
            "updated_at": row[6],
            "relevant_docs": json.loads(row[7]),
            "notes": row[8]
        }

    def update_progress(
        self,
        experiment_id: str,
        status: str,
        notes: Optional[str] = None,
        data: Optional[Dict] = None
    ) -> bool:
        """
        更新实验进度

        Args:
            experiment_id: 实验ID
            status: 实验状态
            notes: 进度备注
            data: 额外数据

        Returns:
            是否更新成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 更新实验状态
            updated_at = datetime.now().isoformat()
            cursor.execute("""
                UPDATE experiments
                SET status = ?, updated_at = ?, notes = ?
                WHERE id = ?
            """, (status, updated_at, notes, experiment_id))

            # 添加进度记录
            timestamp = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO experiment_progress (
                    experiment_id, status, notes, data, timestamp
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                experiment_id,
                status,
                notes,
                json.dumps(data or {}, ensure_ascii=False),
                timestamp
            ))

            conn.commit()
            logger.info(f"更新实验进度: {experiment_id} -> {status}")
            return True

        except Exception as e:
            logger.error(f"更新实验进度失败: {e}")
            return False

        finally:
            conn.close()

    def get_progress_history(self, experiment_id: str) -> List[Dict[str, Any]]:
        """获取实验进度历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT status, notes, data, timestamp
            FROM experiment_progress
            WHERE experiment_id = ?
            ORDER BY timestamp
        """, (experiment_id,))

        history = []
        for row in cursor.fetchall():
            history.append({
                "status": row[0],
                "notes": row[1],
                "data": json.loads(row[2]) if row[2] else {},
                "timestamp": row[3]
            })

        conn.close()
        return history

    def list_experiments(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        列出实验

        Args:
            status: 过滤状态
            limit: 返回数量限制

        Returns:
            实验列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if status:
            cursor.execute("""
                SELECT id, title, objective, status, created_at, updated_at
                FROM experiments
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (status, limit))
        else:
            cursor.execute("""
                SELECT id, title, objective, status, created_at, updated_at
                FROM experiments
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

        experiments = []
        for row in cursor.fetchall():
            experiments.append({
                "id": row[0],
                "title": row[1],
                "objective": row[2],
                "status": row[3],
                "created_at": row[4],
                "updated_at": row[5]
            })

        conn.close()
        return experiments

    def save_results(
        self,
        experiment_id: str,
        results: Dict[str, Any],
        analysis: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        保存实验结果

        Args:
            experiment_id: 实验ID
            results: 实验结果
            analysis: 分析结果

        Returns:
            是否保存成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            created_at = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO experiment_results (
                    experiment_id, results, analysis, created_at
                ) VALUES (?, ?, ?, ?)
            """, (
                experiment_id,
                json.dumps(results, ensure_ascii=False),
                json.dumps(analysis or {}, ensure_ascii=False),
                created_at
            ))

            conn.commit()
            logger.info(f"保存实验结果: {experiment_id}")
            return True

        except Exception as e:
            logger.error(f"保存实验结果失败: {e}")
            return False

        finally:
            conn.close()

    def get_results(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """获取实验结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT results, analysis, created_at
            FROM experiment_results
            WHERE experiment_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (experiment_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "results": json.loads(row[0]),
            "analysis": json.loads(row[1]) if row[1] else {},
            "created_at": row[2]
        }

    def delete_experiment(self, experiment_id: str) -> bool:
        """删除实验"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM experiment_progress WHERE experiment_id = ?", (experiment_id,))
            cursor.execute("DELETE FROM experiment_results WHERE experiment_id = ?", (experiment_id,))
            cursor.execute("DELETE FROM experiments WHERE id = ?", (experiment_id,))

            conn.commit()
            logger.info(f"删除实验: {experiment_id}")
            return True

        except Exception as e:
            logger.error(f"删除实验失败: {e}")
            return False

        finally:
            conn.close()

    def export_experiment(self, experiment_id: str, format: str = "json") -> Optional[str]:
        """
        导出实验

        Args:
            experiment_id: 实验ID
            format: 导出格式 ("json", "yaml")

        Returns:
            导出的内容
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return None

        results = self.get_results(experiment_id)
        progress = self.get_progress_history(experiment_id)

        export_data = {
            "experiment": experiment,
            "results": results,
            "progress_history": progress
        }

        if format.lower() == "json":
            return json.dumps(export_data, ensure_ascii=False, indent=2)
        elif format.lower() == "yaml":
            import yaml
            return yaml.dump(export_data, allow_unicode=True)
        else:
            raise ValueError(f"不支持的导出格式: {format}")
