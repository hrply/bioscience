"""
元数据配置管理器
支持LRU缓存、线程安全的单例模式
"""

import sqlite3
import re
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from functools import lru_cache
from datetime import datetime


class MetadataConfigManager:
    """
    元数据配置管理器（单例模式）
    
    功能：
    - 线程安全的单例模式
    - LRU缓存优化性能
    - 配置验证
    - 支持热更新
    """
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls, db_path: str = None):
        """
        单例模式实现
        
        Args:
            db_path: 数据库路径
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db_path: str = None):
        """
        初始化配置管理器
        
        Args:
            db_path: 数据库路径，默认为 app/data/biodata.db
        """
        if self._initialized:
            return
        
        if db_path is None:
            db_path = Path(__file__).parent / 'data' / 'biodata.db'
        
        self.db_path = str(db_path)
        self._cache = {}
        self._cache_timestamp = 0
        self._cache_ttl = 300  # 5分钟缓存
        self._cache_lock = threading.Lock()
        self._initialized = True
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建元数据配置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata_config (
                field_name TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('text', 'multi_select')),
                options TEXT,
                required BOOLEAN DEFAULT 0,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted BOOLEAN DEFAULT 0
            )
        """)
        
        # 创建选项表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata_field_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_name TEXT NOT NULL,
                option_value TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0,
                FOREIGN KEY (field_name) REFERENCES metadata_config(field_name)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _parse_options(self, options_str: str) -> List[str]:
        """
        解析选项字符串
        
        Args:
            options_str: 选项字符串，如 "transcriptomics,scrna-seq,spatial"
        
        Returns:
            List[str]: 选项列表
        """
        if not options_str:
            return []
        
        # 替换中文逗号为英文逗号，然后分割
        options = re.sub(r'[，,]', ',', options_str).split(',')
        # 清理空格和空选项
        return [opt.strip() for opt in options if opt.strip()]
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """
        验证配置数据
        
        Args:
            config: 配置字典
        
        Returns:
            bool: 是否有效
        """
        # 必需字段
        required_fields = ['field_name', 'label', 'type']
        for field in required_fields:
            if field not in config or not config[field]:
                return False
        
        # 类型验证
        if config['type'] not in ['text', 'multi_select']:
            return False
        
        # 如果是多选类型，必须有选项
        if config['type'] == 'multi_select' and not config.get('options'):
            return False
        
        # 验证选项格式
        if config.get('options'):
            options = self._parse_options(config['options'])
            if len(options) == 0:
                return False
        
        return True
    
    def _is_cache_valid(self) -> bool:
        """
        检查缓存是否有效
        
        Returns:
            bool: 缓存是否有效
        """
        if not self._cache:
            return False
        
        age = datetime.now().timestamp() - self._cache_timestamp
        return age < self._cache_ttl
    
    def _load_from_database(self) -> Dict[str, Dict]:
        """
        从数据库加载配置（仅加载未删除的配置）
        
        Returns:
            Dict[str, Dict]: 配置字典（按 field_name 索引）
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT field_name, label, type, options, required, sort_order
                FROM metadata_config
                WHERE deleted = 0
                ORDER BY sort_order
            """)
            
            configs = {}
            for row in cursor.fetchall():
                config = dict(row)
                # 从选项表加载选项
                config['parsed_options'] = self._load_field_options(conn, config['field_name'])
                configs[config['field_name']] = config
            
            conn.close()
            return configs
            
        except Exception as e:
            print(f"加载配置失败: {e}")
            return {}
    
    def _load_field_options(self, conn, field_name: str) -> List[str]:
        """
        从选项表加载字段选项
        
        Args:
            conn: 数据库连接
            field_name: 字段名
        
        Returns:
            List[str]: 选项列表
        """
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT option_value 
                FROM metadata_field_options 
                WHERE field_name = ? 
                ORDER BY sort_order, id
            """, (field_name,))
            
            options = [row[0] for row in cursor.fetchall()]
            
            # 如果选项表为空,尝试从options字段迁移
            if not options:
                cursor.execute("SELECT options FROM metadata_config WHERE field_name = ?", (field_name,))
                row = cursor.fetchone()
                if row and row[0]:
                    parsed_options = self._parse_options(row[0])
                    if parsed_options:
                        # 迁移数据到选项表
                        for idx, opt in enumerate(parsed_options):
                            cursor.execute("""
                                INSERT INTO metadata_field_options (field_name, option_value, sort_order)
                                VALUES (?, ?, ?)
                            """, (field_name, opt, idx))
                        conn.commit()
                        options = parsed_options
            
            return options
            
        except Exception as e:
            print(f"加载选项失败: {e}")
            return []
    
    def _refresh_cache(self):
        """刷新缓存"""
        with self._cache_lock:
            self._cache = self._load_from_database()
            self._cache_timestamp = datetime.now().timestamp()
    
    def clear_cache(self):
        """清除缓存"""
        with self._cache_lock:
            self._cache = {}
            self._cache_timestamp = 0
    
    def get_all_configs(self, force_refresh: bool = False) -> List[Dict]:
        """
        获取所有配置
        
        Args:
            force_refresh: 是否强制刷新缓存
        
        Returns:
            List[Dict]: 配置列表（按 sort_order 排序）
        """
        if force_refresh or not self._is_cache_valid():
            self._refresh_cache()
        
        with self._cache_lock:
            return list(self._cache.values())
    
    def get_config(self, field_name: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        获取单个配置
        
        Args:
            field_name: 字段名
            force_refresh: 是否强制刷新缓存
        
        Returns:
            Optional[Dict]: 配置字典，如果不存在返回 None
        """
        if force_refresh or not self._is_cache_valid():
            self._refresh_cache()
        
        with self._cache_lock:
            return self._cache.get(field_name)
    
    def get_configs_by_type(self, field_type: str, force_refresh: bool = False) -> List[Dict]:
        """
        按类型获取配置
        
        Args:
            field_type: 字段类型（'text' 或 'multi_select'）
            force_refresh: 是否强制刷新缓存
        
        Returns:
            List[Dict]: 配置列表
        """
        all_configs = self.get_all_configs(force_refresh)
        return [cfg for cfg in all_configs if cfg['type'] == field_type]
    
    def update_config(self, field_name: str, config_data: Dict) -> bool:
        """
        更新单个配置
        
        Args:
            field_name: 字段名
            config_data: 配置数据
        
        Returns:
            bool: 是否成功
        """
        # 验证配置
        if not self._validate_config(config_data):
            return False
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE metadata_config
                SET label = ?, type = ?, options = ?, required = ?, sort_order = ?
                WHERE field_name = ?
            """, (
                config_data.get('label'),
                config_data.get('type'),
                config_data.get('options'),
                config_data.get('required', 0),
                config_data.get('sort_order', 0),
                field_name
            ))
            
            conn.commit()
            conn.close()
            
            # 如果是多选类型,保存选项到选项表
            if config_data.get('type') == 'multi_select' and config_data.get('options'):
                self.save_field_options(field_name, config_data.get('options'))
            
            # 刷新缓存
            self._refresh_cache()
            
            return True
            
        except Exception as e:
            print(f"更新配置失败: {e}")
            return False
    
    def save_field_options(self, field_name: str, options_str: str) -> bool:
        """
        保存字段选项到选项表
        
        Args:
            field_name: 字段名
            options_str: 选项字符串
        
        Returns:
            bool: 是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 删除现有选项
            cursor.execute("DELETE FROM metadata_field_options WHERE field_name = ?", (field_name,))
            
            # 解析并插入新选项
            options = self._parse_options(options_str)
            for idx, opt in enumerate(options):
                cursor.execute("""
                    INSERT INTO metadata_field_options (field_name, option_value, sort_order)
                    VALUES (?, ?, ?)
                """, (field_name, opt, idx))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"保存选项失败: {e}")
            return False
    
    def add_config(self, config_data: Dict) -> bool:
        """
        添加新配置
        
        Args:
            config_data: 配置数据
        
        Returns:
            bool: 是否成功
        """
        # 验证配置
        if not self._validate_config(config_data):
            return False
        
        field_name = config_data.get('field_name')
        if not field_name:
            return False
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO metadata_config (field_name, label, type, options, required, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                field_name,
                config_data.get('label'),
                config_data.get('type'),
                config_data.get('options'),
                config_data.get('required', 0),
                config_data.get('sort_order', 0)
            ))
            
            conn.commit()
            conn.close()
            
            # 如果是多选类型,保存选项到选项表
            if config_data.get('type') == 'multi_select' and config_data.get('options'):
                self.save_field_options(field_name, config_data.get('options'))
            
            # 刷新缓存
            self._refresh_cache()
            
            return True
            
        except Exception as e:
            print(f"添加配置失败: {e}")
            return False
    
    def delete_config(self, field_name: str) -> bool:
        """
        删除配置（软删除，标记为deleted=1）
        
        Args:
            field_name: 字段名
        
        Returns:
            bool: 是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE metadata_config
                SET deleted = 1
                WHERE field_name = ?
            """, (field_name,))
            
            conn.commit()
            conn.close()
            
            # 刷新缓存
            self._refresh_cache()
            
            return True
            
        except Exception as e:
            print(f"删除配置失败: {e}")
            return False
    
    def get_deleted_configs(self) -> List[Dict]:
        """
        获取已删除的配置列表
        
        Returns:
            List[Dict]: 已删除配置列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT field_name, label, type, options, required, sort_order
                FROM metadata_config
                WHERE deleted = 1
                ORDER BY sort_order
            """)
            
            configs = []
            for row in cursor.fetchall():
                config = dict(row)
                # 从选项表加载选项
                config['parsed_options'] = self._load_field_options(conn, config['field_name'])
                configs.append(config)
            
            conn.close()
            return configs
            
        except Exception as e:
            print(f"获取已删除配置失败: {e}")
            return []
    
    def restore_config(self, field_name: str) -> bool:
        """
        恢复已删除的配置
        
        Args:
            field_name: 字段名
        
        Returns:
            bool: 是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE metadata_config
                SET deleted = 0
                WHERE field_name = ?
            """, (field_name,))
            
            conn.commit()
            conn.close()
            
            # 刷新缓存
            self._refresh_cache()
            
            return True
            
        except Exception as e:
            print(f"恢复配置失败: {e}")
            return False
    
    def permanent_delete_config(self, field_name: str) -> bool:
        """
        永久删除配置（从数据库中完全删除）
        
        Args:
            field_name: 字段名
        
        Returns:
            bool: 是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 删除选项
            cursor.execute("DELETE FROM metadata_field_options WHERE field_name = ?", (field_name,))
            
            # 删除配置
            cursor.execute("DELETE FROM metadata_config WHERE field_name = ? AND deleted = 1", (field_name,))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"永久删除配置失败: {e}")
            return False


# 全局实例
_config_manager = None
_config_manager_lock = threading.Lock()


def get_config_manager(db_path: str = None) -> MetadataConfigManager:
    """
    获取配置管理器实例
    
    Args:
        db_path: 数据库路径
    
    Returns:
        MetadataConfigManager: 配置管理器实例
    """
    global _config_manager
    
    if _config_manager is None:
        with _config_manager_lock:
            if _config_manager is None:
                _config_manager = MetadataConfigManager(db_path)
    
    return _config_manager