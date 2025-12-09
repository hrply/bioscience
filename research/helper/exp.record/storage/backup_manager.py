"""
备份管理器 - 自动备份实验数据和模板
"""

import logging
import json
import shutil
import zipfile
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
import os


class BackupManager:
    """备份管理器"""
    
    def __init__(self, backup_dir: str = None, settings=None):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # 设置备份目录
        if backup_dir is None:
            if settings:
                backup_dir = settings.data_dir / "backups"
            else:
                backup_dir = Path.home() / ".lab_notebook_agent" / "backups"
        
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 备份配置
        self.max_backups = settings.max_backups if settings else 10
        self.auto_backup_enabled = settings.auto_backup_enabled if settings else True
        self.backup_interval_hours = settings.backup_interval_hours if settings else 24
    
    def create_backup(self, description: str = "", include_templates: bool = True, 
                     include_experiments: bool = True, include_config: bool = True) -> str:
        """创建完整备份"""
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / f"{backup_id}.zip"
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                # 备份实验数据
                if include_experiments and self.settings:
                    db_path = self.settings.db_path
                    if db_path and db_path.exists():
                        backup_zip.write(db_path, "experiments.db")
                
                # 备份模板
                if include_templates and self.settings:
                    templates_dir = self.settings.templates_dir
                    if templates_dir and templates_dir.exists():
                        for template_file in templates_dir.glob("*.md"):
                            backup_zip.write(
                                template_file, 
                                f"templates/{template_file.name}"
                            )
                
                # 备份配置
                if include_config and self.settings:
                    config_file = Path(__file__).parent.parent / "config" / "settings.py"
                    if config_file.exists():
                        backup_zip.write(config_file, "config/settings.py")
                    
                    # 备份环境变量（如果有.env文件）
                    env_file = Path(__file__).parent.parent / ".env"
                    if env_file.exists():
                        backup_zip.write(env_file, ".env")
                
                # 创建备份元数据
                metadata = {
                    "backup_id": backup_id,
                    "created_at": datetime.now().isoformat(),
                    "description": description,
                    "includes": {
                        "templates": include_templates,
                        "experiments": include_experiments,
                        "config": include_config
                    },
                    "version": "1.0"
                }
                
                backup_zip.writestr("backup_metadata.json", json.dumps(metadata, indent=2))
            
            # 清理旧备份
            self._cleanup_old_backups()
            
            self.logger.info(f"Backup created: {backup_path}")
            return backup_id
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            raise
    
    def restore_backup(self, backup_id: str, restore_templates: bool = True, 
                      restore_experiments: bool = True, restore_config: bool = False) -> bool:
        """恢复备份"""
        backup_path = self.backup_dir / f"{backup_id}.zip"
        
        if not backup_path.exists():
            self.logger.error(f"Backup file not found: {backup_path}")
            return False
        
        try:
            with zipfile.ZipFile(backup_path, 'r') as backup_zip:
                # 读取备份元数据
                if "backup_metadata.json" in backup_zip.namelist():
                    metadata_content = backup_zip.read("backup_metadata.json").decode('utf-8')
                    metadata = json.loads(metadata_content)
                    self.logger.info(f"Restoring backup: {metadata.get('description', 'No description')}")
                
                # 恢复实验数据
                if restore_experiments and "experiments.db" in backup_zip.namelist():
                    if self.settings:
                        db_path = self.settings.db_path
                        if db_path:
                            # 创建备份目录
                            db_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            # 恢复数据库
                            backup_zip.extract("experiments.db", db_path.parent)
                            self.logger.info("Experiment data restored")
                
                # 恢复模板
                if restore_templates and self.settings:
                    templates_dir = self.settings.templates_dir
                    if templates_dir:
                        templates_dir.mkdir(parents=True, exist_ok=True)
                        
                        for file_info in backup_zip.filelist:
                            if file_info.filename.startswith("templates/"):
                                backup_zip.extract(file_info, templates_dir.parent)
                                self.logger.info(f"Template restored: {file_info.filename}")
                
                # 恢复配置（需要谨慎）
                if restore_config:
                    config_files = ["config/settings.py", ".env"]
                    for config_file in config_files:
                        if config_file in backup_zip.namelist():
                            # 创建备份原配置
                            original_path = Path(__file__).parent.parent / config_file
                            if original_path.exists():
                                backup_original = original_path.with_suffix(
                                    f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                                )
                                shutil.copy2(original_path, backup_original)
                            
                            # 恢复配置
                            backup_zip.extract(config_file, Path(__file__).parent.parent)
                            self.logger.info(f"Config restored: {config_file}")
            
            self.logger.info(f"Backup {backup_id} restored successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring backup {backup_id}: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""
        backups = []
        
        for backup_file in self.backup_dir.glob("backup_*.zip"):
            try:
                with zipfile.ZipFile(backup_file, 'r') as backup_zip:
                    # 读取元数据
                    metadata = {}
                    if "backup_metadata.json" in backup_zip.namelist():
                        metadata_content = backup_zip.read("backup_metadata.json").decode('utf-8')
                        metadata = json.loads(metadata_content)
                    
                    # 获取文件信息
                    stat = backup_file.stat()
                    
                    backups.append({
                        "backup_id": backup_file.stem,
                        "file_path": str(backup_file),
                        "file_size_mb": stat.st_size / (1024 * 1024),
                        "created_at": metadata.get("created_at") or datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "description": metadata.get("description", ""),
                        "includes": metadata.get("includes", {}),
                        "version": metadata.get("version", "Unknown")
                    })
                    
            except Exception as e:
                self.logger.error(f"Error reading backup {backup_file}: {e}")
                continue
        
        # 按创建时间排序
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        
        return backups
    
    def delete_backup(self, backup_id: str) -> bool:
        """删除备份"""
        backup_path = self.backup_dir / f"{backup_id}.zip"
        
        try:
            if backup_path.exists():
                backup_path.unlink()
                self.logger.info(f"Backup deleted: {backup_id}")
                return True
            else:
                self.logger.warning(f"Backup not found: {backup_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting backup {backup_id}: {e}")
            return False
    
    def _cleanup_old_backups(self):
        """清理旧备份"""
        if self.max_backups <= 0:
            return
        
        backups = self.list_backups()
        
        if len(backups) > self.max_backups:
            # 删除最旧的备份
            backups_to_delete = backups[self.max_backups:]
            
            for backup in backups_to_delete:
                self.delete_backup(backup["backup_id"])
                self.logger.info(f"Deleted old backup: {backup['backup_id']}")
    
    def auto_backup_check(self) -> Optional[str]:
        """检查是否需要自动备份"""
        if not self.auto_backup_enabled:
            return None
        
        backups = self.list_backups()
        
        if not backups:
            # 没有备份，创建第一个
            return self.create_backup("Initial automatic backup")
        
        # 检查最近备份的时间
        latest_backup = backups[0]
        latest_time = datetime.fromisoformat(latest_backup["created_at"])
        
        # 如果超过间隔时间，创建新备份
        if datetime.now() - latest_time > timedelta(hours=self.backup_interval_hours):
            return self.create_backup("Scheduled automatic backup")
        
        return None
    
    def export_backup(self, backup_id: str, export_path: str) -> bool:
        """导出备份到指定路径"""
        backup_path = self.backup_dir / f"{backup_id}.zip"
        export_path = Path(export_path)
        
        if not backup_path.exists():
            self.logger.error(f"Backup not found: {backup_id}")
            return False
        
        try:
            shutil.copy2(backup_path, export_path)
            self.logger.info(f"Backup exported to: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting backup: {e}")
            return False
    
    def import_backup(self, backup_file_path: str) -> str:
        """导入外部备份文件"""
        backup_file_path = Path(backup_file_path)
        
        if not backup_file_path.exists():
            raise ValueError(f"Backup file not found: {backup_file_path}")
        
        # 生成新的备份ID
        backup_id = f"imported_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        new_backup_path = self.backup_dir / f"{backup_id}.zip"
        
        try:
            # 复制文件到备份目录
            shutil.copy2(backup_file_path, new_backup_path)
            
            # 验证备份文件
            with zipfile.ZipFile(new_backup_path, 'r') as backup_zip:
                if "backup_metadata.json" not in backup_zip.namelist():
                    # 如果没有元数据，创建基本元数据
                    metadata = {
                        "backup_id": backup_id,
                        "created_at": datetime.now().isoformat(),
                        "description": f"Imported from {backup_file_path.name}",
                        "includes": {"templates": True, "experiments": True, "config": False},
                        "version": "1.0"
                    }
                    
                    # 重新创建zip文件包含元数据
                    temp_files = {}
                    for file_info in backup_zip.filelist:
                        temp_files[file_info.filename] = backup_zip.read(file_info.filename)
                    
                    with zipfile.ZipFile(new_backup_path, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                        for filename, content in temp_files.items():
                            new_zip.writestr(filename, content)
                        new_zip.writestr("backup_metadata.json", json.dumps(metadata, indent=2))
            
            self.logger.info(f"Backup imported: {backup_id}")
            return backup_id
            
        except Exception as e:
            # 清理失败的文件
            if new_backup_path.exists():
                new_backup_path.unlink()
            self.logger.error(f"Error importing backup: {e}")
            raise
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """获取备份统计信息"""
        backups = self.list_backups()
        
        if not backups:
            return {
                "total_backups": 0,
                "total_size_mb": 0,
                "latest_backup": None,
                "oldest_backup": None
            }
        
        total_size = sum(b["file_size_mb"] for b in backups)
        
        return {
            "total_backups": len(backups),
            "total_size_mb": total_size,
            "latest_backup": backups[0]["created_at"],
            "oldest_backup": backups[-1]["created_at"],
            "backup_directory": str(self.backup_dir),
            "auto_backup_enabled": self.auto_backup_enabled,
            "max_backups": self.max_backups
        }