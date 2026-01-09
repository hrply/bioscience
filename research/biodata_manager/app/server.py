#!/usr/bin/env python3
"""
生物信息学数据管理系统Web服务器
提供API接口连接前端和后端功能
"""

import json
import os
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import cgi
import backend
from metadata_config_manager import MetadataConfigManager, get_config_manager as _get_config_manager

# 获取配置管理器的辅助函数（使用正确的数据库路径）
def get_config_manager():
    # 使用环境变量指定的数据库路径，或者默认的 /bioraw/biodata.db
    db_path = os.environ.get('BIODATA_DB_PATH', '/bioraw/biodata.db')
    return _get_config_manager(db_path)

class BioDataAPIHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # 从环境变量获取路径，如果未设置则使用默认值
        base_dir = os.environ.get('BIODATA_BASE_DIR', 'data')
        download_dir = os.environ.get('BIODATA_DOWNLOAD_DIR', 'downloads')
        results_dir = os.environ.get('BIODATA_RESULTS_DIR', 'results')
        analysis_dir = os.environ.get('BIODATA_ANALYSIS_DIR', 'analysis')
        self.manager = backend.BioDataManager(base_dir, download_dir, results_dir, analysis_dir)
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            # 返回主页
            self.serve_file('index.html', 'text/html')
        elif parsed_path.path == '/styles.css':
            self.serve_file('styles.css', 'text/css')
        elif parsed_path.path == '/app.js':
            self.serve_file('app.js', 'application/javascript')
        elif parsed_path.path.startswith('/api/'):
            self.handle_api_get(parsed_path)
        else:
            # 尝试提供静态文件
            self.serve_static_file(parsed_path.path[1:])
    
    def do_POST(self):
        """处理POST请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path.startswith('/api/'):
            self.handle_api_post(parsed_path)
        else:
            self.send_error(404)
    
    def serve_file(self, filename, content_type):
        """提供文件"""
        file_path = Path(__file__).parent / filename
        if file_path.exists():
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.send_header('Content-length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404)
    
    def serve_static_file(self, filepath):
        """提供静态文件"""
        file_path = Path(__file__).parent / filepath
        if file_path.exists() and file_path.is_file():
            content_type = self.get_content_type(file_path.suffix)
            self.serve_file(filepath, content_type)
        else:
            self.send_error(404)
    
    def get_content_type(self, extension):
        """根据文件扩展名获取内容类型"""
        content_types = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.gif': 'image/gif',
            '.ico': 'image/x-icon'
        }
        return content_types.get(extension.lower(), 'application/octet-stream')
    
    def handle_api_get(self, parsed_path):
        """处理API GET请求"""
        try:
            if parsed_path.path == '/api/projects':
                # 获取所有项目
                projects = self.manager.get_all_projects()
                self.send_json_response(projects)
            
            elif parsed_path.path == '/api/scan-downloads':
                # 扫描下载目录
                results = self.manager.scan_download_directory()
                self.send_json_response(results)
            
            elif parsed_path.path == '/api/directory-tree':
                # 获取目录树
                content = self.manager.generate_directory_tree()
                self.send_json_response({'content': content})
            
            elif parsed_path.path == '/api/add-data-to-project':
                # 添加数据到现有项目
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                project_id = data.get('projectId')
                download_folder = data.get('downloadFolder')
                
                result = self.manager.add_data_to_existing_project(project_id, download_folder)
                self.send_json_response(result)
            
            elif parsed_path.path.startswith('/api/project/'):
                # 获取特定项目
                project_id = parsed_path.path.split('/')[-1]
                project = self.manager.get_project_by_id(project_id)

                if project:
                    self.send_json_response(project)
                else:
                    self.send_json_response({'success': False, 'message': 'Project not found'}, 404)

            elif parsed_path.path == '/api/list-folder-files':
                # 获取文件夹内文件列表
                from urllib.parse import parse_qs
                query_params = parse_qs(parsed_path.query)
                folder_name = query_params.get('folder', [''])[0]

                if folder_name:
                    files = self.manager.list_folder_files(folder_name)
                    self.send_json_response(files)
                else:
                    self.send_json_response({'success': False, 'message': 'Folder name required'}, 400)
            
            elif parsed_path.path == '/api/scan-directory':
                # 扫描指定目录的所有文件（通用扫描端点）
                from urllib.parse import parse_qs
                query_params = parse_qs(parsed_path.query)
                dir_path = query_params.get('path', [''])[0]
                base_path = query_params.get('base_path', [''])[0]

                if dir_path:
                    # 安全检查：只允许扫描特定目录
                    allowed_bases = [
                        str(self.manager.base_dir),
                        str(self.manager.downloads_dir),
                        str(self.manager.analysis_dir)
                    ]
                    
                    if base_path:
                        target_base = Path(base_path).resolve()
                    else:
                        target_base = Path(dir_path).resolve()
                    
                    # 检查是否在允许的目录内
                    is_allowed = False
                    for allowed_base in allowed_bases:
                        try:
                            target_base.relative_to(Path(allowed_base).resolve())
                            is_allowed = True
                            break
                        except ValueError:
                            continue
                    
                    if not is_allowed:
                        self.send_json_response({'success': False, 'message': '不允许访问此目录'}, 403)
                        return
                    
                    files = self.manager.scan_directory_files(dir_path, base_path)
                    self.send_json_response(files)
                else:
                    self.send_json_response({'success': False, 'message': 'Path parameter required'}, 400)
            
            elif parsed_path.path == '/api/advanced-import':
                # 高级导入功能
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                result = self.manager.advanced_import(data)
                self.send_json_response(result)
            
            elif parsed_path.path == '/api/processed-data':
                # 获取处理数据列表
                project_id = self.get_query_param(parsed_path, 'project_id')
                processed_data = self.manager.get_processed_data_list(project_id)
                self.send_json_response(processed_data)
            
            elif parsed_path.path.startswith('/api/processed-data/'):
                # 获取特定处理数据
                processed_data_id = parsed_path.path.split('/')[-1]
                processed_data = self.manager.get_processed_data_detail(processed_data_id)
                
                if processed_data:
                    self.send_json_response(processed_data)
                else:
                    self.send_error(404, 'Processed data not found')
            
            elif parsed_path.path == '/api/scan-analysis':
                # 扫描分析目录
                analysis_results = self.manager.scan_analysis_directory()
                self.send_json_response(analysis_results)
            
            elif parsed_path.path == '/api/metadata/config':
                # 获取所有元数据配置
                config_manager = get_config_manager()
                configs = config_manager.get_all_configs()
                self.send_json_response(configs)

            elif parsed_path.path == '/api/metadata/config/deleted':
                # 获取已删除的配置列表
                config_manager = get_config_manager()
                deleted_configs = config_manager.get_deleted_configs()
                self.send_json_response(deleted_configs)

            elif parsed_path.path == '/api/metadata/cache-info':
                # 获取缓存信息
                config_manager = get_config_manager()
                cache_info = config_manager.get_cache_info()
                self.send_json_response(cache_info)

            elif parsed_path.path.startswith('/api/metadata/config/'):
                # 获取单个元数据配置
                field_name = parsed_path.path.split('/')[-1]
                config_manager = get_config_manager()
                config = config_manager.get_config(field_name)

                if config:
                    self.send_json_response(config)
                else:
                    self.send_json_response({'success': False, 'message': 'Config not found'}, 404)

            else:
                self.send_json_response({'success': False, 'message': 'Not found'}, 404)

        except Exception as e:
            self.send_json_response({'success': False, 'message': str(e)}, 500)
    
    def handle_api_post(self, parsed_path):
        """处理API POST请求"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            if parsed_path.path == '/api/create-project':
                # 创建项目
                data = json.loads(post_data.decode('utf-8'))
                result = self.manager.create_project(data)
                self.send_json_response(result)
            
            elif parsed_path.path == '/api/import-download':
                # 导入下载
                data = json.loads(post_data.decode('utf-8'))
                project = self.manager.import_download_folder(
                    data['folder_path'], 
                    data['project_info']
                )
                self.send_json_response(project)
            
            elif parsed_path.path == '/api/advanced-import':
                # 高级导入功能
                data = json.loads(post_data.decode('utf-8'))
                result = self.manager.advanced_import(data)
                self.send_json_response(result)
            
            elif parsed_path.path.startswith('/api/update-project/'):
                # 更新项目
                project_id = parsed_path.path.split('/')[-1]
                print(f"DEBUG: 收到更新请求 project_id={project_id}")
                try:
                    data = json.loads(post_data.decode('utf-8'))
                    print(f"DEBUG: 解析后的data={data}")
                except Exception as e:
                    print(f"DEBUG: JSON解析失败: {e}")
                    self.send_json_response({'success': False, 'message': f'JSON解析失败: {str(e)}'}, 400)
                    return

                result = self.manager.update_project(project_id, data)
                print(f"DEBUG: update_project结果={result}")
                if result.get('success'):
                    # 获取更新后的项目数据
                    project = self.manager.get_project_by_id(project_id)
                    print(f"DEBUG: 获取到的project={project}")
                    # 将项目数据包装在success响应中
                    self.send_json_response({'success': True, 'message': '更新成功', 'project': project})
                else:
                    print(f"DEBUG: 更新失败: {result.get('message')}")
                    self.send_json_response({'success': False, 'message': result.get('message', 'Update failed')}, 400)
            
            elif parsed_path.path.startswith('/api/delete-project/'):
                # 删除项目
                project_id = parsed_path.path.split('/')[-1]
                result = self.manager.delete_project(project_id)
                self.send_json_response(result)
            
            elif parsed_path.path == '/api/organize-files':
                # 组织文件
                data = json.loads(post_data.decode('utf-8'))
                success = self.manager.organize_project_files(data['project_id'])
                self.send_json_response({'success': success})
            
            elif parsed_path.path == '/api/import-analysis':
                # 导入分析数据
                data = json.loads(post_data.decode('utf-8'))
                result = self.manager.import_analysis_data(
                    data['folder_path'],
                    data.get('project_id')
                )
                self.send_json_response(result)
            
            elif parsed_path.path == '/api/import-processed-file':
                # 导入处理数据文件
                data = json.loads(post_data.decode('utf-8'))
                result = self.manager.import_processed_file(
                    data['file_path'],
                    data['project_id'],
                    data.get('title', ''),
                    data.get('analysis_type', 'other')
                )
                self.send_json_response(result)
            
            elif parsed_path.path.startswith('/api/delete-processed-data/'):
                # 删除处理数据
                processed_data_id = parsed_path.path.split('/')[-1]
                result = self.manager.delete_processed_data(processed_data_id)
                self.send_json_response(result)
            
            elif parsed_path.path == '/api/metadata/config/batch':
                # 批量更新元数据配置
                data = json.loads(post_data.decode('utf-8'))
                config_manager = get_config_manager()
                results = config_manager.batch_update_configs(data)
                self.send_json_response(results)
            
            elif parsed_path.path == '/api/metadata/config/add':
                # 添加单个元数据配置
                data = json.loads(post_data.decode('utf-8'))
                config_manager = get_config_manager()
                success = config_manager.add_config(data)
                self.send_json_response({'success': success})
            
            elif parsed_path.path == '/api/metadata/config/update':
                # 更新单个元数据配置
                data = json.loads(post_data.decode('utf-8'))
                field_name = data.get('field_name')
                config_manager = get_config_manager()
                success = config_manager.update_config(field_name, data)
                self.send_json_response({'success': success})
            
            elif parsed_path.path == '/api/metadata/config/delete':
                # 删除元数据配置
                data = json.loads(post_data.decode('utf-8'))
                field_name = data.get('field_name')
                config_manager = get_config_manager()
                success = config_manager.delete_config(field_name)
                self.send_json_response({'success': success})
            
            elif parsed_path.path == '/api/metadata/config/refresh':
                # 刷新配置缓存
                config_manager = get_config_manager()
                config_manager.clear_cache()
                configs = config_manager.get_all_configs()
                self.send_json_response(configs)
            
            elif parsed_path.path == '/api/metadata/config/deleted':
                # 获取已删除的配置列表
                config_manager = get_config_manager()
                deleted_configs = config_manager.get_deleted_configs()
                self.send_json_response(deleted_configs)
            
            elif parsed_path.path == '/api/metadata/config/restore':
                # 恢复已删除的配置
                data = json.loads(post_data.decode('utf-8'))
                field_name = data.get('field_name')
                config_manager = get_config_manager()
                success = config_manager.restore_config(field_name)
                self.send_json_response({'success': success})
            
            elif parsed_path.path == '/api/metadata/config/permanent-delete':
                # 永久删除配置（并清除项目数据）
                data = json.loads(post_data.decode('utf-8'))
                field_name = data.get('field_name')
                config_manager = get_config_manager()
                success = config_manager.permanent_delete_config(field_name)
                self.send_json_response({'success': success})
            
            else:
                self.send_error(404)
        
        except Exception as e:
            # 使用JSON响应而不是send_error来支持中文
            self.send_json_response({'success': False, 'message': str(e)}, 500)
    
    def get_query_param(self, parsed_path, param_name):
        """获取查询参数"""
        query_params = parse_qs(parsed_path.query)
        if param_name in query_params:
            return query_params[param_name][0]
        return None
    
    def send_json_response(self, data, status_code=200):
        """发送JSON响应"""
        response_data = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
        
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Content-length', str(len(response_data)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(response_data)
    
    def do_OPTIONS(self):
        """处理OPTIONS请求（CORS预检）"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run_server(port=8000):
    """运行服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, BioDataAPIHandler)
    
    print(f"生物信息学数据管理系统服务器已启动")
    print(f"访问地址: http://localhost:{port}")
    print(f"按 Ctrl+C 停止服务器")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        httpd.server_close()

if __name__ == '__main__':
    import sys
    port = 8000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    run_server(port)