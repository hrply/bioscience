模板管理器 - 专门管理实验模板

import logging
import yaml
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import re


class TemplateManager:
    """实验模板管理器"""
    
    def __init__(self, templates_dir: str = None, settings=None):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # 设置模板目录
        if templates_dir is None:
            if settings:
                templates_dir = settings.templates_dir
            else:
                templates_dir = Path(__file__).parent.parent / "config" / "templates"
        
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # 模板缓存
        self._template_cache = {}
        
        # 加载所有模板
        self._load_templates()
    
    def _load_templates(self):
        """加载所有模板"""
        self._template_cache.clear()
        
        for template_file in self.templates_dir.glob("*.md"):
            try:
                template_data = self._load_template_file(template_file)
                if template_data:
                    template_id = template_file.stem
                    self._template_cache[template_id] = template_data
                    self.logger.info(f"Loaded template: {template_id}")
            except Exception as e:
                self.logger.error(f"Error loading template {template_file}: {e}")
    
    def _load_template_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """加载单个模板文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析YAML前置元数据
            metadata = {}
            body_content = content
            
            # 检查是否有YAML前置元数据
            if content.startswith('---'):
                try:
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        metadata = yaml.safe_load(parts[1])
                        body_content = parts[2].strip()
                except yaml.YAMLError as e:
                    self.logger.warning(f"Error parsing YAML metadata in {file_path}: {e}")
            
            # 提取不可修改章节
            immutable_sections = self._extract_immutable_sections(body_content, metadata)
            
            return {
                "id": file_path.stem,
                "name": metadata.get("name", file_path.stem),
                "version": metadata.get("version", "1.0"),
                "category": metadata.get("category", "未分类"),
                "description": metadata.get("description", ""),
                "content": body_content,
                "full_content": content,  # 包含元数据的完整内容
                "metadata": metadata,
                "immutable_sections": immutable_sections,
                "file_path": str(file_path),
                "created_at": datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                "updated_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error loading template file {file_path}: {e}")
            return None
    
    def _extract_immutable_sections(self, content: str, metadata: Dict[str, Any]) -> List[str]:
        """提取不可修改章节列表"""
        immutable_sections = []
        
        # 从元数据中获取
        if "immutable_sections" in metadata:
            if isinstance(metadata["immutable_sections"], list):
                immutable_sections.extend(metadata["immutable_sections"])
        
        # 从内容中提取标记为不可修改的章节
        lines = content.split('\n')
        for line in lines:
            # 匹配标题格式
            header_match = re.match(r'^#{1,6}\s*\[不可修改\]\s*(.+)$', line)
            if header_match:
                section_name = header_match.group(1).strip()
                immutable_sections.append(section_name)
        
        return list(set(immutable_sections))  # 去重
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """获取模板"""
        return self._template_cache.get(template_id)
    
    def list_templates(self, category: str = None) -> List[Dict[str, Any]]:
        """列出模板"""
        templates = list(self._template_cache.values())
        
        if category:
            templates = [t for t in templates if t.get("category") == category]
        
        # 按名称排序
        templates.sort(key=lambda x: x.get("name", ""))
        
        return templates
    
    def get_categories(self) -> List[str]:
        """获取所有分类"""
        categories = set()
        for template in self._template_cache.values():
            categories.add(template.get("category", "未分类"))
        return sorted(list(categories))
    
    def search_templates(self, query: str) -> List[Dict[str, Any]]:
        """搜索模板"""
        query = query.lower()
        results = []
        
        for template_id, template in self._template_cache.items():
            # 在名称、描述、内容中搜索
            searchable_text = " ".join([
                template.get("name", ""),
                template.get("description", ""),
                template.get("content", "")
            ]).lower()
            
            if query in searchable_text:
                # 计算相关性分数
                score = 0
                if query in template.get("name", "").lower():
                    score += 3
                if query in template.get("description", "").lower():
                    score += 2
                if query in template.get("content", "").lower():
                    score += 1
                
                results.append({
                    **template,
                    "relevance_score": score
                })
        
        # 按相关性排序
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return results
    
    def create_template(self, template_data: Dict[str, Any]) -> str:
        """创建新模板"""
        template_id = template_data.get("id") or self._generate_template_id(template_data.get("name", ""))
        file_path = self.templates_dir / f"{template_id}.md"
        
        # 检查是否已存在
        if file_path.exists():
            raise ValueError(f"Template {template_id} already exists")
        
        # 构建模板内容
        content = self._build_template_content(template_data)
        
        # 写入文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 重新加载模板
            new_template = self._load_template_file(file_path)
            if new_template:
                self._template_cache[template_id] = new_template
            
            self.logger.info(f"Created template: {template_id}")
            return template_id
            
        except Exception as e:
            self.logger.error(f"Error creating template {template_id}: {e}")
            raise
    
    def update_template(self, template_id: str, updates: Dict[str, Any]) -> bool:
        """更新模板"""
        if template_id not in self._template_cache:
            return False
        
        template = self._template_cache[template_id].copy()
        
        # 更新字段
        for key, value in updates.items():
            if key in ["name", "version", "category", "description", "content"]:
                template[key] = value
        
        # 构建新内容
        content = self._build_template_content(template)
        
        # 写入文件
        file_path = Path(template["file_path"])
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 重新加载模板
            updated_template = self._load_template_file(file_path)
            if updated_template:
                self._template_cache[template_id] = updated_template
            
            self.logger.info(f"Updated template: {template_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating template {template_id}: {e}")
            return False
    
    def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        if template_id not in self._template_cache:
            return False
        
        template = self._template_cache[template_id]
        file_path = Path(template["file_path"])
        
        try:
            file_path.unlink()
            del self._template_cache[template_id]
            
            self.logger.info(f"Deleted template: {template_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting template {template_id}: {e}")
            return False
    
    def _generate_template_id(self, name: str) -> str:
        """生成模板ID"""
        # 简单的ID生成策略
        base_id = re.sub(r'[^\w\s-]', '', name).strip()
        base_id = re.sub(r'[-\s]+', '_', base_id)
        
        # 确保唯一性
        counter = 1
        template_id = base_id
        while template_id in self._template_cache:
            template_id = f"{base_id}_{counter}"
            counter += 1
        
        return template_id
    
    def _build_template_content(self, template_data: Dict[str, Any]) -> str:
        """构建模板文件内容"""
        # 构建YAML前置元数据
        metadata = {
            "name": template_data.get("name", ""),
            "version": template_data.get("version", "1.0"),
            "category": template_data.get("category", ""),
            "description": template_data.get("description", "")
        }
        
        # 添加不可修改章节
        if template_data.get("immutable_sections"):
            metadata["immutable_sections"] = template_data["immutable_sections"]
        
        yaml_content = yaml.dump(metadata, default_flow_style=False, allow_unicode=True)
        
        # 构建完整内容
        content = f"---\n{yaml_content}---\n\n{template_data.get('content', '')}"
        
        return content
    
    def validate_template(self, template_content: str) -> Dict[str, Any]:
        """验证模板格式"""
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            # 尝试解析YAML前置元数据
            if template_content.startswith('---'):
                parts = template_content.split('---', 2)
                if len(parts) >= 3:
                    try:
                        metadata = yaml.safe_load(parts[1])
                        
                        # 检查必需字段
                        required_fields = ["name", "version", "category"]
                        for field in required_fields:
                            if field not in metadata:
                                result["warnings"].append(f"Missing recommended field: {field}")
                        
                    except yaml.YAMLError as e:
                        result["errors"].append(f"Invalid YAML metadata: {e}")
                        result["valid"] = False
                else:
                    result["errors"].append("Invalid YAML front matter format")
                    result["valid"] = False
            
            # 检查内容结构
            if not re.search(r'^#{1,6}\s+', template_content, re.MULTILINE):
                result["warnings"].append("No headers found in template content")
            
        except Exception as e:
            result["errors"].append(f"Validation error: {e}")
            result["valid"] = False
        
        return result
    
    def reload_templates(self):
        """重新加载所有模板"""
        self._load_templates()
        self.logger.info("Templates reloaded")
    
    def get_template_statistics(self) -> Dict[str, Any]:
        """获取模板统计信息"""
        total_templates = len(self._template_cache)
        categories = self.get_categories()
        
        category_counts = {}
        for category in categories:
            category_counts[category] = len([t for t in self._template_cache.values() 
                                           if t.get("category") == category])
        
        return {
            "total_templates": total_templates,
            "categories": categories,
            "category_counts": category_counts,
            "templates_directory": str(self.templates_dir)
        }
