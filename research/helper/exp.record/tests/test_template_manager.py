"""
单元测试 - 模板管理器
"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.template_manager import TemplateManager


class TestTemplateManager:
    """模板管理器测试"""
    
    def setup_method(self):
        """创建临时目录用于测试"""
        self.temp_dir = tempfile.mkdtemp()
        self.template_manager = TemplateManager(templates_dir=self.temp_dir)
    
    def teardown_method(self):
        """清理临时目录"""
        shutil.rmtree(self.temp_dir)
    
    def test_create_template(self):
        """测试创建模板"""
        template_data = {
            "name": "测试模板",
            "category": "测试分类",
            "version": "1.0",
            "description": "这是一个测试模板",
            "content": "# 测试模板\n\n这是测试内容"
        }
        
        template_id = self.template_manager.create_template(template_data)
        
        assert template_id is not None
        assert self.template_manager.get_template(template_id) is not None
    
    def test_get_template(self):
        """测试获取模板"""
        template_data = {
            "name": "测试模板",
            "category": "测试分类", 
            "content": "# 测试模板\n\n这是测试内容"
        }
        
        template_id = self.template_manager.create_template(template_data)
        retrieved_template = self.template_manager.get_template(template_id)
        
        assert retrieved_template is not None
        assert retrieved_template["name"] == "测试模板"
        assert retrieved_template["category"] == "测试分类"
    
    def test_list_templates(self):
        """测试列出模板"""
        # 创建多个模板
        for i in range(3):
            template_data = {
                "name": f"测试模板{i}",
                "category": "测试分类",
                "content": f"# 测试模板{i}\n这是测试内容{i}"
            }
            self.template_manager.create_template(template_data)
        
        templates = self.template_manager.list_templates()
        assert len(templates) >= 3
    
    def test_update_template(self):
        """测试更新模板"""
        template_data = {
            "name": "原始模板",
            "category": "测试分类",
            "content": "# 原始模板\n原始内容"
        }
        
        template_id = self.template_manager.create_template(template_data)
        
        # 更新模板
        updates = {
            "name": "更新后的模板",
            "description": "更新后的描述"
        }
        
        success = self.template_manager.update_template(template_id, updates)
        assert success is True
        
        # 验证更新
        updated_template = self.template_manager.get_template(template_id)
        assert updated_template["name"] == "更新后的模板"
        assert updated_template["description"] == "更新后的描述"
    
    def test_delete_template(self):
        """测试删除模板"""
        template_data = {
            "name": "待删除模板",
            "category": "测试分类",
            "content": "# 待删除模板\n内容"
        }
        
        template_id = self.template_manager.create_template(template_data)
        assert self.template_manager.get_template(template_id) is not None
        
        # 删除模板
        success = self.template_manager.delete_template(template_id)
        assert success is True
        
        # 验证删除
        assert self.template_manager.get_template(template_id) is None
    
    def test_search_templates(self):
        """测试搜索模板"""
        # 创建测试模板
        template_data = {
            "name": "细胞培养模板",
            "category": "细胞生物学",
            "description": "用于细胞培养的模板",
            "content": "# 细胞培养\n细胞培养步骤"
        }
        
        self.template_manager.create_template(template_data)
        
        # 搜索测试
        results = self.template_manager.search_templates("细胞")
        assert len(results) > 0
        
        # 验证搜索结果
        found = False
        for result in results:
            if "细胞" in result["name"] or "细胞" in result["description"]:
                found = True
                break
        assert found is True
    
    def test_validate_template(self):
        """测试模板验证"""
        # 有效模板
        valid_template = """---
name: "有效模板"
version: "1.0"
category: "测试"
---

# 有效模板

这是有效模板的内容
"""
        
        result = self.template_manager.validate_template(valid_template)
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        
        # 无效模板（缺少YAML结束标记）
        invalid_template = """---
name: "无效模板"
version: "1.0"
category: "测试"

# 无效模板

这是无效模板的内容
"""
        
        result = self.template_manager.validate_template(invalid_template)
        assert result["valid"] is False
        assert len(result["errors"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
