#!/usr/bin/env python3
"""
生物信息学数据管理系统后端
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import time
import re
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

from database import BioDataDB


class SimpleFileWatcher:
    """轻量级文件监控器"""
    def __init__(self, watch_path: str, callback=None):
        self.watch_path = Path(watch_path)
        self.callback = callback
        self.last_scan_time = {}
        self.is_running = False
        self._thread = None
    
    def start_monitoring(self):
        """启动监控"""
        if not self.is_running:
            self.is_running = True
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()
            print(f"开始监控目录: {self.watch_path}")
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=1)
    
    def _monitor_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                self._check_changes()
                time.sleep(2)  # 每2秒检查一次
            except Exception as e:
                print(f"监控异常: {e}")
                time.sleep(5)
    
    def _check_changes(self):
        """检查目录变化"""
        if not self.watch_path.exists():
            return
        
        current_time = time.time()
        changes_detected = False
        
        try:
            for item in self.watch_path.iterdir():
                if item.is_dir():
                    dir_mtime = item.stat().st_mtime
                    last_mtime = self.last_scan_time.get(str(item), 0)
                    
                    if dir_mtime > last_mtime:
                        self.last_scan_time[str(item)] = dir_mtime
                        changes_detected = True
            
            if changes_detected and self.callback:
                self.callback("目录有新变化")
                
        except (PermissionError, OSError):
            pass
    
    def force_refresh(self):
        """强制刷新缓存"""
        self.last_scan_time.clear()


class BioDataManager:
    """生物信息学数据管理器"""
    
    def __init__(self, base_dir: str = "/bioraw/data", download_dir: str = "/bioraw/downloads",
                 results_dir: str = "/bioraw/results", analysis_dir: str = "/bioraw/analysis"):
        self.base_dir = Path(base_dir)
        
        # 检查下载目录是否存在，如果不存在使用默认路径
        download_path = Path(download_dir)
        if not download_path.exists():
            # 使用相对路径作为备用
            alt_download_path = Path(__file__).parent.parent / 'downloads'
            if alt_download_path.exists():
                download_dir = str(alt_download_path)
        
        self.download_dir = Path(download_dir)
        self.downloads_dir = self.download_dir  # 添加这个属性以兼容现有代码
        self.results_dir = Path(results_dir)
        self.analysis_dir = Path(analysis_dir)
        
        # 初始化SQLite数据库 - 使用环境变量指定的数据库路径
        db_path = os.environ.get('BIODATA_DB_PATH', 'data/biodata.db')
        self.db = BioDataDB(db_path)
        
        # 配置选项：是否使用移动模式（避免重复存储）
        self.use_move_mode = os.environ.get('BIODATA_USE_MOVE_MODE', 'true').lower() == 'true'
        
        # 确保基础目录存在（如果可能）
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            self.download_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            print(f"警告：无法创建目录（可能是在测试环境中）: {e}")
        
        # 缓存机制
        self._scan_cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5分钟缓存
        
        # 文件扩展名到数据类型的映射
        self.file_type_mapping = {
            '.fastq': 'transcriptomics',
            '.fq': 'transcriptomics',
            '.fasta': 'transcriptomics',
            '.fa': 'transcriptomics',
            '.sam': 'transcriptomics',
            '.bam': 'transcriptomics',
            '.h5ad': 'scrna-seq',
            '.mtx': 'scrna-seq',
            '.fcs': 'cytof',
            '.raw': 'proteomics',
            '.mzml': 'proteomics',
            '.wiff': 'proteomics',
            '.zip': 'other',
            '.tar': 'other',
            '.gz': 'other'
        }
        
        # 数据库编号模式
        self.db_patterns = [
            r'gs[exm]\d+',
            r'prjna\d+',
            r's[re]r\d+',
            r'err\d+',
            r'mtab_\d+',
            r'pxd\d+',
        ]

    def _on_directory_change(self, message: str):
        """目录变化回调"""
        print(f"检测到变化: {message}")
        # 清除缓存，下次扫描会重新执行
        self._scan_cache = None
        self._cache_timestamp = None

    def generate_project_id(self) -> str:
        """生成项目ID"""
        projects = self.db.get_all_projects()
        if not projects:
            return "PRJ001"
        
        max_id = 0
        for project in projects:
            match = re.match(r'PRJ(\d+)', project.get('id', ''))
            if match:
                num = int(match.group(1))
                if num > max_id:
                    max_id = num
        
        return f"PRJ{max_id + 1:03d}"

    def sanitize_filename(self, filename: str) -> str:
        """清理文件名"""
        # 移除或替换不安全的字符
        sanitized = re.sub(r'[^\w\-_\.]', '_', filename)
        # 限制长度
        return sanitized[:50]

    def detect_doi_and_db_id(self, folder_name: str, folder_path: Path) -> Tuple[Optional[str], Optional[str]]:
        """检测DOI和数据库编号"""
        doi = None
        db_id = None
        
        # 检查文件夹名称 - 快速方法
        for pattern in self.db_patterns:
            match = re.search(pattern, folder_name, re.IGNORECASE)
            if match:
                db_id = match.group()
                break
        
        # 检测DOI - 快速方法
        doi_patterns = [
            r'10\.\d{4}/.*doi\.org/10\.\d{4}/.*',
            r'doi:\s*10\.\d{4}/[^\\s]+',
            r'(?:PMID|pmid)\s*(\d+)',
            r'10\.\d{4}/.*',
            r'gs[exm]\d+',
            r'prjna\d+',
            r's[re]r\d+',
            r'err\d+',
            r'mtab_\d+',
            r'pxd\d+',
        ]
        
        for pattern in doi_patterns:
            match = re.search(pattern, folder_name, re.IGNORECASE)
            if match:
                doi = match.group()
                break
        
        return doi, db_id

    def detect_doi_and_db_id_fast(self, folder_name: str) -> Tuple[Optional[str], Optional[str]]:
        """基于文件夹名的快速DOI和数据库检测"""
        doi = None
        db_id = None
        
        # 只检查文件夹名称，不读取文件内容
        for pattern in self.db_patterns:
            match = re.search(pattern, folder_name, re.IGNORECASE)
            if match:
                db_id = match.group()
                break
        
        return doi, db_id

    def detect_data_type_from_name(self, folder_name: str) -> str:
        """基于文件夹名检测数据类型"""
        folder_lower = folder_name.lower()
        
        # 检查关键词
        if any(keyword in folder_lower for keyword in ['scrna', 'single-cell', 'single cell', '10x']):
            return 'scrna-seq'
        elif any(keyword in folder_lower for keyword in ['spatial', 'visium', 'slide-seq']):
            return 'spatial'
        elif any(keyword in folder_lower for keyword in ['proteomics', 'protein', 'phospho', 'mass spec']):
            return 'proteomics'
        elif any(keyword in folder_lower for keyword in ['cytof', 'mass cytometry']):
            return 'cytof'
        elif any(keyword in folder_lower for keyword in ['multiomics', 'multi-omics']):
            return 'multiomics'
        else:
            return 'transcriptomics'

    def detect_database_ids_from_name(self, folder_name: str) -> List[str]:
        """从文件夹名检测数据库编号"""
        ids = []
        folder_upper = folder_name.upper()
        
        # GEO系列
        geo_matches = re.findall(r'GS[EM]\d+', folder_upper)
        ids.extend(geo_matches)
        
        # SRA/ENA
        sra_matches = re.findall(r'[SE]RR\d+', folder_upper)
        ids.extend(sra_matches)
        
        # BioProject
        prjna_matches = re.findall(r'PRJNA\d+', folder_upper)
        ids.extend(prjna_matches)
        
        # ArrayExpress
        mtab_matches = re.findall(r'MTAB_\d+', folder_upper)
        ids.extend(mtab_matches)
        
        # ProteomeXchange
        pxd_matches = re.findall(r'PXD\d+', folder_upper)
        ids.extend(pxd_matches)
        
        return ids

    def scan_download_directory(self) -> List[Dict]:
        """异步优化的下载目录扫描"""
        current_time = time.time()
        
        # 缓存机制：5分钟内不重复扫描
        if (self._cache_timestamp and 
            current_time - self._cache_timestamp < self._cache_ttl and
            self._scan_cache):
            print("使用缓存数据")
            return self._scan_cache
        
        # 获取下载目录
        download_path = Path(self.downloads_dir)
        
        if not download_path.exists() or not download_path.is_dir():
            print(f"下载目录不存在: {download_path}")
            return []
        
        print(f"开始异步扫描目录: {download_path}")
        start_time = time.time()
        
        try:
            # 异步扫描实现
            scan_results = asyncio.run(self._async_scan_directories(download_path))
            
            # 更新缓存
            self._scan_cache = scan_results
            self._cache_timestamp = current_time
            
            elapsed_time = time.time() - start_time
            print(f"异步扫描完成，找到 {len(scan_results)} 个目录，耗时 {elapsed_time:.2f} 秒")
            
            return scan_results
            
        except Exception as e:
            print(f"异步扫描失败，回退到同步模式: {e}")
            # 回退到简单的同步扫描
            return self._fallback_scan(download_path)
    
    async def _async_scan_directories(self, download_path: Path) -> List[Dict]:
        """异步扫描目录"""
        # 获取目录列表
        directories = []
        try:
            for item in download_path.iterdir():
                if item.is_dir():
                    directories.append(item)
                    if len(directories) >= 15:  # 限制数量
                        break
        except PermissionError:
            print("权限错误，跳过一些目录")
        
        print(f"找到 {len(directories)} 个一级目录")
        
        # 使用线程池并行处理目录
        with ThreadPoolExecutor(max_workers=4) as executor:
            loop = asyncio.get_event_loop()
            tasks = []
            
            for directory in directories:
                task = loop.run_in_executor(
                    executor, 
                    self._process_directory_async, 
                    directory
                )
                tasks.append(task)
            
            # 等待所有任务完成，但设置超时
            try:
                scan_results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=12.0  # 12秒超时
                )
            except asyncio.TimeoutError:
                print("异步扫描超时")
                # 返回已完成的结果
                completed_tasks = [task for task in tasks if task.done()]
                scan_results = [task.result() for task in completed_tasks if not task.exception()]
        
        # 过滤异常结果
        valid_results = []
        for result in scan_results:
            if isinstance(result, dict):
                valid_results.append(result)
            elif isinstance(result, Exception):
                print(f"目录处理异常: {result}")
        
        return valid_results
    
    def _process_directory_async(self, directory: Path) -> Dict:
        """单个目录的异步处理函数"""
        try:
            # 快速获取目录基本信息
            dir_stat = directory.stat()
            
            dir_info = {
                'name': directory.name,
                'path': str(directory),
                'relativePath': f"/downloads/{directory.name}",
                'files': 0,
                'size': '0 B',
                'size_bytes': 0,
                'type': 'folder',
                'data_type': 'unknown',
                'db_ids': [],
                'contains_fastq': False,
                'contains_bam': False,
                'contains_h5ad': False,
                'modified': dir_stat.st_mtime
            }
            
            # 扫描目录：递归计算文件数量和总大小
            try:
                total_size = 0
                file_count = 0
                has_fastq = False
                has_bam = False
                has_h5ad = False
                has_citation = False
                
                # 递归扫描目录
                for item in directory.rglob('*'):
                    try:
                        if item.is_file():
                            file_count += 1
                            file_size = item.stat().st_size
                            total_size += file_size
                            
                            # 基于扩展名快速检测
                            name_lower = item.name.lower()
                            if name_lower.endswith(('.fastq', '.fq')):
                                has_fastq = True
                            elif name_lower.endswith('.bam'):
                                has_bam = True
                            elif name_lower.endswith('.h5ad'):
                                has_h5ad = True
                            elif name_lower.endswith(('.enw', '.ris')):
                                has_citation = True
                    except (PermissionError, OSError):
                        continue
                
                # 格式化文件大小
                dir_info['files'] = file_count
                dir_info['size'] = self._format_size(total_size)
                dir_info['size_bytes'] = total_size
                dir_info['contains_fastq'] = has_fastq
                dir_info['contains_bam'] = has_bam
                dir_info['contains_h5ad'] = has_h5ad
                dir_info['citationFile'] = has_citation
                
            except (PermissionError, OSError) as e:
                print(f"扫描目录 {directory.name} 时出错: {e}")
            
            # 基于目录名快速检测
            dir_info['data_type'] = self.detect_data_type_from_name(directory.name)
            dir_info['db_ids'] = self.detect_database_ids_from_name(directory.name)
            
            # 添加检测到的信息（用于前端显示）
            if dir_info['db_ids']:
                dir_info['detectedDbId'] = ', '.join(dir_info['db_ids'])
            else:
                dir_info['detectedDbId'] = None
            
            dir_info['detectedType'] = dir_info['data_type']
            dir_info['detectedDOI'] = None  # 需要在更详细的检测中实现
            
            return dir_info
            
        except Exception as e:
            print(f"处理目录 {directory.name} 失败: {e}")
            return None
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小为可读格式"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def _fallback_scan(self, download_path: Path) -> List[Dict]:
        """回退的简单同步扫描"""
        print("使用回退同步扫描")
        scan_results = []
        
        try:
            for directory in download_path.iterdir():
                if directory.is_dir():
                    dir_info = {
                        'name': directory.name,
                        'path': str(directory),
                        'relativePath': f"/downloads/{directory.name}",
                        'files': 0,
                        'size': '0 B',
                        'type': 'folder',
                        'data_type': self.detect_data_type_from_name(directory.name),
                        'db_ids': self.detect_database_ids_from_name(directory.name),
                        'contains_fastq': False,
                        'contains_bam': False,
                        'contains_h5ad': False,
                        'modified': directory.stat().st_mtime
                    }
                    scan_results.append(dir_info)
                    
                if len(scan_results) >= 10:  # 限制数量
                    break
                    
        except Exception as e:
            print(f"回退扫描失败: {e}")
        
        return scan_results

    def import_download_folder(self, folder_name: str, project_id: str, project_name: str,
                              data_type: str = "transcriptomics", organism: str = "human",
                              doi: str = "", description: str = "", delete_after_import: bool = False) -> Dict:
        """导入下载文件夹到项目"""
        try:
            # 验证输入
            if not folder_name or not project_id:
                return {"success": False, "message": "文件夹名称和项目ID不能为空"}
            
            # 安全检查：防止路径遍历攻击
            if '..' in folder_name or folder_name.startswith('/'):
                return {"success": False, "message": "非法文件夹名称"}
            
            folder_path = (self.downloads_dir / folder_name).resolve()
            
            # 验证解析后的路径仍在下载目录内
            try:
                folder_path.relative_to(self.downloads_dir.resolve())
            except ValueError:
                return {"success": False, "message": "非法文件夹路径"}
            
            if not folder_path.exists() or not folder_path.is_dir():
                return {"success": False, "message": f"文件夹不存在: {folder_name}"}
            
            # 创建项目目录
            project_dir = self.base_dir / project_id
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # 移动或复制文件夹
            target_path = project_dir / folder_name
            target_path = target_path.resolve()
            
            # 验证目标路径在项目目录内
            try:
                target_path.relative_to(project_dir.resolve())
            except ValueError:
                return {"success": False, "message": "目标路径非法"}
            
            # 始终使用复制导入（不使用 move）
            shutil.copytree(str(folder_path), str(target_path))
            
            # 复制完成后，根据用户选择决定是否删除源文件
            if delete_after_import:
                shutil.rmtree(str(folder_path))
                action = "复制并删除源文件"
            else:
                action = "复制"
            
            # 更新数据库
            project_data = {
                'id': project_id,
                'name': project_name,
                'data_type': data_type,
                'organism': organism,
                'doi': doi,
                'description': description,
                'created_at': datetime.now().isoformat(),
                'folder_count': 1,
                'file_count': self._count_files_in_directory(target_path)
            }
            
            self.db.insert_project(project_data)
            
            # 生成README
            self._generate_project_readme(project_data, project_dir)
            
            # 更新目录树
            self.generate_directory_tree()
            
            return {
                "success": True,
                "message": f"成功{action}文件夹到项目 {project_id}",
                "project_id": project_id,
                "action": action
            }
            
        except Exception as e:
            return {"success": False, "message": f"导入失败: {str(e)}"}

    def _count_files_in_directory(self, directory: Path) -> int:
        """计算目录中的文件数量"""
        count = 0
        try:
            for root, dirs, files in os.walk(directory):
                count += len(files)
                # 限制递归深度避免性能问题
                level = root.replace(str(directory), '').count(os.sep)
                if level >= 3:
                    continue
        except Exception:
            pass
        return count

    def _generate_project_readme(self, project: Dict, project_dir: Path):
        """生成项目README文件"""
        readme_content = f"""# {project.get('title', project.get('name', '未命名项目'))}

**项目ID**: {project['id']}
**数据类型**: {project.get('dataType', project.get('data_type', '其他'))}
**物种**: {project.get('organism', 'Homo sapiens')}
**创建时间**: {project.get('created_at', project.get('created_date', '未知'))}

## 项目描述

{project.get('description', '暂无描述')}

## DOI

{project.get('doi', '未提供DOI')}

---

*此文件由生物信息学数据管理系统自动生成*
"""

        readme_path = project_dir / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)

    def generate_directory_tree(self):
        """生成目录树文件"""
        tree_file = self.base_dir / "directory_tree.md"
        
        try:
            with open(tree_file, 'w', encoding='utf-8') as f:
                f.write("# 项目目录结构\n\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for item in sorted(self.base_dir.iterdir()):
                    if item.is_dir():
                        f.write(f"## {item.name}/\n")
                        self._write_directory_tree(f, item, level=1)
                        f.write("\n")
        except Exception as e:
            print(f"生成目录树失败: {e}")

    def _write_directory_tree(self, f, directory: Path, level: int = 0):
        """递归写入目录树"""
        indent = "  " * level
        try:
            items = sorted(directory.iterdir())
            for item in items:
                if item.is_dir():
                    f.write(f"{indent}- {item.name}/\n")
                    if level < 2:  # 限制递归深度
                        self._write_directory_tree(f, item, level + 1)
                else:
                    f.write(f"{indent}- {item.name}\n")
        except PermissionError:
            f.write(f"{indent}- [权限不足，无法访问]\n")

    def get_all_projects(self) -> List[Dict]:
        """获取所有项目"""
        try:
            return self.db.get_all_projects()
        except Exception as e:
            print(f"获取项目列表失败: {e}")
            return []

    def get_project_by_id(self, project_id: str) -> Optional[Dict]:
        """根据ID获取项目"""
        try:
            return self.db.get_project(project_id)
        except Exception as e:
            print(f"获取项目失败: {e}")
            return None

    def update_project(self, project_id: str, updates: Dict) -> Dict:
        """更新项目信息"""
        try:
            # 先处理标签（在数据类型转换之前保存）
            tags = updates.pop('tags', None)
            tags_updated = False
            if tags is not None:
                # tags可能是字符串（逗号分隔）或数组
                if isinstance(tags, str):
                    tags_list = [t.strip() for t in tags.split(',') if t.strip()]
                else:
                    tags_list = tags
                tags_updated = self.db.update_project_tags(project_id, tags_list)

            # 更新项目基本信息
            success = self.db.update_project(project_id, updates)

            # 如果有任一更新成功，就返回成功
            if success or tags_updated:
                # 重新生成README
                project = self.get_project_by_id(project_id)
                if project:
                    # 确保项目目录存在
                    project_dir = self.base_dir / project_id
                    try:
                        if not project_dir.exists():
                            project_dir.mkdir(parents=True, exist_ok=True)
                            # 同时更新数据库中的path字段
                            self.db.update_project(project_id, {'path': str(project_dir)})
                        self._generate_project_readme(project, project_dir)
                    except Exception as readme_error:
                        # README生成失败不影响主流程，只记录警告
                        print(f"警告：生成README文件失败: {readme_error}")
                return {"success": True, "message": "项目更新成功"}
            else:
                return {"success": False, "message": "项目不存在或没有可更新的字段"}
        except Exception as e:
            return {"success": False, "message": f"更新失败: {str(e)}"}

    def delete_project(self, project_id: str) -> Dict:
        """删除项目（仅从数据库删除，不删除文件）"""
        try:
            # 安全检查：防止路径遍历攻击
            if '..' in project_id or project_id.startswith('/') or project_id.startswith('\\'):
                return {"success": False, "message": "非法项目ID"}
            
            # 从数据库删除
            success = self.db.delete_project(project_id)
            if not success:
                return {"success": False, "message": "项目不存在"}
            
            # 注意：不再删除文件目录，仅从数据库移除项目记录
            # 重新生成目录树
            self.generate_directory_tree()
            
            return {"success": True, "message": "项目删除成功（仅数据库记录已删除）"}
            
        except Exception as e:
            return {"success": False, "message": f"删除失败: {str(e)}"}

    def get_project_files(self, project_id: str) -> List[Dict]:
        """获取项目文件列表（递归扫描文件系统）"""
        try:
            # 递归扫描项目目录获取实际文件
            project_dir = self.base_dir / project_id
            if not project_dir.exists():
                return []
            
            files_list = []
            
            # 递归扫描目录
            for root, dirs, file_names in os.walk(project_dir):
                for file_name in file_names:
                    file_path = Path(root) / file_name
                    try:
                        relative_path = file_path.relative_to(project_dir)
                        file_stat = file_path.stat()
                        
                        file_info = {
                            'name': file_name,
                            'path': str(relative_path),
                            'size': self._format_file_size(file_stat.st_size),
                            'size_bytes': file_stat.st_size,
                            'type': 'file',
                            'modified': file_stat.st_mtime
                        }
                        files_list.append(file_info)
                            
                    except (OSError, ValueError):
                        continue
            
            # 按名称排序
            files_list.sort(key=lambda f: f.get('name', ''))
            
            return files_list
            
        except Exception as e:
            print(f"获取项目文件失败: {e}")
            return []

    def scan_directory_files(self, directory_path: str, base_path: str = None) -> List[Dict]:
        """
        扫描指定目录的所有文件（递归）
        
        Args:
            directory_path: 要扫描的目录路径（绝对路径或相对路径）
            base_path: 基础路径（用于计算相对路径），如果为None则使用directory_path
        
        Returns:
            List[Dict]: 文件列表
        """
        try:
            dir_path = Path(directory_path).resolve()
            
            # 安全检查：确保路径在允许的目录内
            if base_path:
                base = Path(base_path).resolve()
                try:
                    dir_path.relative_to(base)
                except ValueError:
                    return [{"error": "路径超出允许的范围"}]
            
            if not dir_path.exists() or not dir_path.is_dir():
                return []
            
            files_list = []
            base = Path(base_path).resolve() if base_path else dir_path
            
            # 递归扫描目录
            for root, dirs, file_names in os.walk(dir_path):
                for file_name in file_names:
                    file_path = Path(root) / file_name
                    try:
                        relative_path = file_path.relative_to(base)
                        file_stat = file_path.stat()
                        
                        file_info = {
                            'name': file_name,
                            'path': str(relative_path),
                            'size': self._format_file_size(file_stat.st_size),
                            'size_bytes': file_stat.st_size,
                            'type': 'file',
                            'modified': file_stat.st_mtime
                        }
                        files_list.append(file_info)
                            
                    except (OSError, ValueError):
                        continue
            
            # 按名称排序
            files_list.sort(key=lambda f: f.get('name', ''))
            
            return files_list
            
        except Exception as e:
            print(f"扫描目录文件失败: {e}")
            return []

    def create_project(self, project_data: Dict) -> Dict:
        """创建新项目"""
        try:
            # 使用传入的项目ID或生成新的项目ID
            project_id = project_data.get('id') or self.generate_project_id()

            # 提取tags
            tags = project_data.pop('tags', None)

            # 字段映射：将前端字段映射到数据库字段
            db_project_data = {
                'id': project_id,
                'title': project_data.get('title', ''),
                'doi': project_data.get('doi', ''),
                'dbId': project_data.get('dbId', ''),
                'dbLink': project_data.get('dbLink', ''),
                'dataType': project_data.get('dataType', '其他'),
                'organism': project_data.get('organism', 'Homo sapiens'),
                'authors': project_data.get('authors', ''),
                'journal': project_data.get('journal', ''),
                'description': project_data.get('description', ''),
                'created_date': datetime.now().isoformat().split('T')[0],
                'path': f'/bioraw/data/{project_id}'
            }

            # 创建项目目录
            project_dir = self.base_dir / project_id
            project_dir.mkdir(parents=True, exist_ok=True)

            # 保存到数据库
            self.db.insert_project(db_project_data)

            # 保存标签
            if tags:
                if isinstance(tags, str):
                    tags_list = [t.strip() for t in tags.split(',') if t.strip()]
                else:
                    tags_list = tags
                self.db.update_project_tags(project_id, tags_list)

            # 生成README
            self._generate_project_readme(db_project_data, project_dir)

            # 更新目录树
            self.generate_directory_tree()

            return {
                "success": True,
                "message": "项目创建成功",
                "project_id": project_id
            }

        except Exception as e:
            return {"success": False, "message": f"创建失败: {str(e)}"}

    # 处理数据管理方法
    def add_processed_data(self, processed_data: Dict) -> Dict:
        """添加处理数据记录"""
        try:
            processed_data['created_at'] = datetime.now().isoformat()
            self.db.insert_processed_data(processed_data)
            return {"success": True, "message": "处理数据添加成功"}
        except Exception as e:
            return {"success": False, "message": f"添加失败: {str(e)}"}

    def get_processed_data_by_project(self, project_id: str) -> List[Dict]:
        """获取项目的处理数据"""
        try:
            return self.db.get_all_processed_data(project_id)
        except Exception as e:
            print(f"获取处理数据失败: {e}")
            return []

    def delete_processed_data(self, data_id: str) -> Dict:
        """删除处理数据"""
        try:
            success = self.db.delete_processed_data(data_id)
            if success:
                return {"success": True, "message": "处理数据删除成功"}
            else:
                return {"success": False, "message": "处理数据不存在"}
        except Exception as e:
            return {"success": False, "message": f"删除失败: {str(e)}"}

    def list_folder_files(self, folder_name: str) -> Dict:
        """列出文件夹内的所有文件"""
        try:
            # 安全检查：防止路径遍历攻击
            # 验证 folder_name 不包含路径遍历字符
            if '..' in folder_name or folder_name.startswith('/'):
                return {"success": False, "message": "非法文件夹名称"}
            
            folder_path = (self.downloads_dir / folder_name).resolve()
            
            # 验证解析后的路径仍在下载目录内
            try:
                folder_path.relative_to(self.downloads_dir.resolve())
            except ValueError:
                return {"success": False, "message": "非法文件夹路径"}
            
            if not folder_path.exists() or not folder_path.is_dir():
                return {"success": False, "message": "文件夹不存在"}
            
            files = []
            total_size = 0
            
            for root, dirs, file_names in os.walk(folder_path):
                for file_name in file_names:
                    file_path = Path(root) / file_name
                    try:
                        relative_path = file_path.relative_to(folder_path)
                        file_stat = file_path.stat()
                        
                        file_info = {
                            "name": file_name,
                            "path": str(file_path),
                            "relativePath": str(relative_path),
                            "size": self._format_file_size(file_stat.st_size),
                            "modified": file_stat.st_mtime
                        }
                        
                        files.append(file_info)
                        total_size += file_stat.st_size
                        
                    except (OSError, ValueError):
                        continue
            
            return {
                "success": True,
                "files": files,
                "total_files": len(files),
                "total_size": self._format_file_size(total_size)
            }
            
        except Exception as e:
            return {"success": False, "message": f"获取文件列表失败: {str(e)}"}

    def advanced_import(self, import_data: Dict) -> Dict:
        """高级导入功能"""
        try:
            project_data = import_data.get('project', {})
            selected_files = import_data.get('files', [])
            delete_after_import = import_data.get('delete_after_import', False)

            print(f"DEBUG: advanced_import called with project_data:", file=sys.stderr)
            print(f"  {project_data}", file=sys.stderr)

            if not selected_files:
                return {"success": False, "message": "没有选择要导入的文件"}

            # 处理项目
            project_mode = project_data.get('mode', 'new')
            import_data_type = project_data.get('dataType', '其他')
            import_organism = project_data.get('organism', 'Homo sapiens')
            import_sample_type = project_data.get('tissue_type', None)

            print(f"DEBUG: Extracted values:", file=sys.stderr)
            print(f"  import_data_type: {import_data_type}", file=sys.stderr)
            print(f"  import_organism: {import_organism}", file=sys.stderr)
            print(f"  import_sample_type: {import_sample_type}", file=sys.stderr)

            if project_mode == 'new':
                # 创建新项目 - 添加字段映射
                mapped_project_data = {
                    'id': project_data.get('id'),
                    'title': project_data.get('name', ''),
                    'dataType': project_data.get('dataType', '其他'),
                    'organism': project_data.get('organism', 'Homo sapiens'),
                    'doi': project_data.get('doi', ''),
                    'description': project_data.get('description', '')
                }
                result = self.create_project(mapped_project_data)
                if not result.get('success'):
                    return result

                project_id = result['project_id']
                is_new_project = True
            else:
                # 使用现有项目
                project_id = project_data['id']

                # 获取现有项目信息
                existing_project = self.get_project_by_id(project_id)
                if existing_project:
                    # 合并数据类型到项目元数据中（用于显示）
                    existing_data_type = existing_project.get('dataType', 'other')
                    merged_data_type = self._merge_data_types(existing_data_type, import_data_type)

                    # 合并物种类型
                    existing_organism = existing_project.get('organism', 'human')
                    import_organism = project_data.get('organism', 'human')
                    merged_organism = self._merge_organisms(existing_organism, import_organism)

                    # 更新项目元数据（数据类型和物种都使用合并后的值）
                    update_data = {
                        'title': project_data.get('name', existing_project.get('title', '')),
                        'dataType': merged_data_type,
                        'organism': merged_organism,
                        'doi': project_data.get('doi', existing_project.get('doi', '')),
                        'description': project_data.get('description', existing_project.get('description', ''))
                    }
                else:
                    # 如果项目不存在，使用导入数据
                    update_data = {
                        'title': project_data['name'],
                        'dataType': import_data_type,
                        'organism': project_data['organism'],
                        'doi': project_data['doi'],
                        'description': project_data['description']
                    }

                self.update_project(project_id, update_data)
                is_new_project = False
            
            # 导入选中的文件（传入数据类型、物种和样本类型以创建子文件夹）
            import_result = self._import_selected_files(
                project_id,
                selected_files,
                delete_after_import,
                import_data_type,
                import_organism,
                import_sample_type
            )
            
            if import_result['success']:
                # 生成项目README
                project = self.get_project_by_id(project_id)
                if project:
                    project_dir = self.base_dir / project_id
                    self._generate_project_readme(project, project_dir)
                
                # 更新目录树
                self.generate_directory_tree()
                
                action = "创建并导入" if is_new_project else "导入到现有项目"
                return {
                    "success": True,
                    "message": f"成功{action}项目 {project_id}，共导入 {import_result['imported_files']} 个文件"
                }
            else:
                return import_result
                
        except Exception as e:
            return {"success": False, "message": f"导入失败: {str(e)}"}
    
    def _merge_data_types(self, existing_type: str, new_type: str) -> str:
        """
        合并数据类型
        
        Args:
            existing_type: 现有的数据类型
            new_type: 新的数据类型
        
        Returns:
            str: 合并后的数据类型（逗号分隔）
        """
        # 如果数据类型相同，直接返回
        if existing_type == new_type:
            return existing_type
        
        # 分割现有的数据类型（支持逗号分隔的多个类型）
        existing_types = set(t.strip() for t in existing_type.split(',') if t.strip())
        
        # 添加新类型
        existing_types.add(new_type)
        
        # 如果只有一种类型，且是other，则使用新类型
        if len(existing_types) == 1:
            return existing_types.pop()
        
        # 如果有多个类型，且包含other，则移除other
        if 'other' in existing_types and len(existing_types) > 1:
            existing_types.remove('other')
        
        # 返回排序后的类型列表（逗号分隔）
        return ','.join(sorted(existing_types))
    
    def _merge_organisms(self, existing_organism: str, new_organism: str) -> str:
        """
        合并物种类型
        
        Args:
            existing_organism: 现有的物种类型
            new_organism: 新的物种类型
        
        Returns:
            str: 合并后的物种类型（逗号分隔）
        """
        # 如果物种相同，直接返回
        if existing_organism == new_organism:
            return existing_organism
        
        # 分割现有的物种（支持逗号分隔的多个物种）
        existing_organisms = set(o.strip() for o in existing_organism.split(',') if o.strip())
        
        # 添加新物种
        existing_organisms.add(new_organism)
        
        # 如果只有一种物种，且是other，则使用新物种
        if len(existing_organisms) == 1:
            return existing_organisms.pop()
        
        # 如果有多个物种，且包含other，则移除other
        if 'other' in existing_organisms and len(existing_organisms) > 1:
            existing_organisms.remove('other')
        
        # 返回排序后的物种列表（逗号分隔）
        return ','.join(sorted(existing_organisms))

    def _import_selected_files(self, project_id: str, selected_files: List[str], delete_after_import: bool, data_type: str = None, organism: str = None, sample_type: str = None) -> Dict:
        """
        导入选中的文件

        Args:
            project_id: 项目ID
            selected_files: 选中的文件列表
            delete_after_import: 导入后是否删除源文件
            data_type: 数据类型（用于创建子文件夹）
            organism: 物种（用于创建子文件夹）
            sample_type: 样本类型（用于创建子文件夹）
        """
        try:
            print(f"DEBUG: _import_selected_files called with:", file=sys.stderr)
            print(f"  project_id: {project_id}", file=sys.stderr)
            print(f"  data_type: {data_type}", file=sys.stderr)
            print(f"  organism: {organism}", file=sys.stderr)
            print(f"  sample_type: {sample_type}", file=sys.stderr)

            project_dir = self.base_dir / project_id
            imported_files = 0
            failed_files = []

            # 从数据库查询缩写
            data_type_abbr = None
            organism_abbr = None
            sample_type_abbr = None

            if data_type:
                data_type_abbr = self.db.get_data_type_abbreviation(data_type)
                if not data_type_abbr:
                    # 如果数据库中没有缩写，使用原始值
                    data_type_abbr = data_type

            if organism:
                organism_abbr = self.db.get_organism_abbreviation(organism)
                if not organism_abbr:
                    # 如果数据库中没有缩写，使用原始值
                    organism_abbr = organism

            if sample_type:
                sample_type_abbr = self.db.get_sample_type_abbreviation(sample_type)
                if not sample_type_abbr:
                    # 如果数据库中没有缩写，使用原始值
                    sample_type_abbr = sample_type

            print(f"DEBUG: Abbreviations:", file=sys.stderr)
            print(f"  data_type_abbr: {data_type_abbr}", file=sys.stderr)
            print(f"  organism_abbr: {organism_abbr}", file=sys.stderr)
            print(f"  sample_type_abbr: {sample_type_abbr}", file=sys.stderr)
            print(f"  sample_type_abbr is None: {sample_type_abbr is None}", file=sys.stderr)
            print(f"  sample_type_abbr == '': {sample_type_abbr == ''}", file=sys.stderr)
            print(f"  bool(sample_type_abbr): {bool(sample_type_abbr)}", file=sys.stderr)

            for file_path in selected_files:
                try:
                    source_path = Path(file_path).resolve()  # 解析绝对路径，消除符号链接等
                    
                    # 安全检查：确保文件在下载目录内（防止路径遍历攻击）
                    try:
                        source_path.relative_to(self.downloads_dir.resolve())
                    except ValueError:
                        failed_files.append(f"{file_path} (非法路径，不允许访问)")
                        continue
                    
                    if not source_path.exists():
                        failed_files.append(f"{file_path} (文件不存在)")
                        continue
                    
                    # 计算相对路径
                    relative_path = source_path.relative_to(self.downloads_dir.resolve())

                    # 目标路径 - 按照数据类型/物种/样本类型三级子目录结构
                    if data_type_abbr and data_type_abbr != 'other':
                        # 第一级：数据类型缩写
                        type_subdir = project_dir / data_type_abbr
                        type_subdir.mkdir(parents=True, exist_ok=True)

                        # 第二级：物种缩写
                        if organism_abbr:
                            organism_subdir = type_subdir / organism_abbr
                            organism_subdir.mkdir(parents=True, exist_ok=True)

                            # 第三级：样本类型缩写（可选）
                            if sample_type_abbr:
                                sample_subdir = organism_subdir / sample_type_abbr
                                sample_subdir.mkdir(parents=True, exist_ok=True)
                                target_path = sample_subdir / relative_path.name
                            else:
                                # 未选择样本类型，存于物种子文件夹内
                                target_path = organism_subdir / relative_path.name
                        else:
                            # 未选择物种，存于数据类型子文件夹内
                            target_path = type_subdir / relative_path.name
                    else:
                        # 保持原有的目录结构
                        target_path = project_dir / relative_path
                    
                    target_path = target_path.resolve()  # 解析目标路径
                    
                    # 防止目标路径超出项目目录
                    try:
                        target_path.relative_to(project_dir.resolve())
                    except ValueError:
                        failed_files.append(f"{file_path} (目标路径非法)")
                        continue
                    
                    # 创建目标目录
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 检查目标文件是否已存在
                    if target_path.exists():
                        failed_files.append(f"{file_path} (目标文件已存在)")
                        continue
                    
                    # 始终使用复制导入（不使用 move）
                    shutil.copy2(str(source_path), str(target_path))
                    action = "复制"
                    
                    # 复制完成后，根据用户选择决定是否删除源文件
                    if delete_after_import:
                        os.remove(str(source_path))
                    
                    imported_files += 1
                    
                    # 记录到数据库
                    file_info = {
                        'name': source_path.name,
                        'path': str(target_path.relative_to(self.base_dir)),
                        'size': source_path.stat().st_size,
                        'type': 'file',
                        'imported_at': datetime.now().isoformat()
                    }
                    self.db.insert_file(project_id, file_info)
                    
                except Exception as e:
                    failed_files.append(f"{source_path.name} ({str(e)})")
            
            result_message = f"成功导入 {imported_files} 个文件"
            if failed_files:
                result_message += f"，失败 {len(failed_files)} 个文件: {', '.join(failed_files[:3])}"
                if len(failed_files) > 3:
                    result_message += "..."
            
            return {
                "success": True,
                "imported_files": imported_files,
                "failed_files": failed_files,
                "message": result_message
            }
            
        except Exception as e:
            return {"success": False, "message": f"文件导入失败: {str(e)}"}

    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}"

    def get_processed_data_list(self, project_id: str = None) -> List[Dict]:
        """获取处理数据列表"""
        try:
            return self.db.get_all_processed_data(project_id)
        except Exception as e:
            print(f"获取处理数据失败: {e}")
            return []

    def scan_analysis_directory(self) -> List[Dict]:
        """扫描分析目录"""
        try:
            analysis_path = Path(self.analysis_dir)
            if not analysis_path.exists():
                return []
            
            results = []
            try:
                for item in analysis_path.iterdir():
                    if item.is_dir():
                        dir_info = {
                            'name': item.name,
                            'path': str(item),
                            'relativePath': f"/analysis/{item.name}",
                            'files': 0,
                            'size': '0 B',
                            'type': 'folder',
                            'modified': item.stat().st_mtime
                        }
                        
                        # 快速文件计数
                        try:
                            file_count = len([f for f in item.iterdir() if f.is_file()])
                            dir_info['files'] = file_count
                        except (PermissionError, OSError):
                            pass
                        
                        results.append(dir_info)
                        
                        # 限制数量
                        if len(results) >= 20:
                            break
                            
            except (PermissionError, OSError):
                pass
            
            return results
            
        except Exception as e:
            print(f"扫描分析目录失败: {e}")
            return []

    def export_projects_to_json(self, file_path: str = None) -> str:
        """导出项目数据到JSON"""
        if file_path is None:
            file_path = self.base_dir / "projects_export.json"
        
        try:
            projects = self.get_all_projects()
            export_data = {
                "export_time": datetime.now().isoformat(),
                "total_projects": len(projects),
                "projects": projects
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return str(file_path)
            
        except Exception as e:
            print(f"导出失败: {e}")
            return None

# 实例化管理器
manager = BioDataManager()