"""
单元测试 - 防幻觉验证模块
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.validation import AntiHallucinationValidator, SectionValidator, ImmutableSectionValidator, ModificationJustificationValidator


class TestSectionValidator:
    """章节完整性验证器测试"""
    
    def setup_method(self):
        self.validator = SectionValidator()
    
    def test_check_section_integrity_no_changes(self):
        """测试无修改的情况"""
        original = "# 引言\n\n这是引言内容\n\n# 方法\n\n这是方法内容"
        revised = "# 引言\n\n这是引言内容\n\n# 方法\n\n这是方法内容"
        
        result = self.validator.check_section_integrity(original, revised)
        
        assert result.is_valid is True
        assert result.confidence == 1.0
        assert len(result.issues) == 0
    
    def test_check_section_integrity_new_section(self):
        """测试新增章节"""
        original = "# 引言\n\n这是引言内容\n\n# 方法\n\n这是方法内容"
        revised = "# 引言\n\n这是引言内容\n\n# 方法\n\n这是方法内容\n\n# 结果\n\n这是结果内容"
        
        result = self.validator.check_section_integrity(original, revised)
        
        assert result.is_valid is False
        assert len(result.issues) > 0
        assert any("新增章节" in issue for issue in result.issues)
    
    def test_check_section_integrity_removed_section(self):
        """测试删除章节"""
        original = "# 引言\n\n这是引言内容\n\n# 方法\n\n这是方法内容\n\n# 结果\n\n这是结果内容"
        revised = "# 引言\n\n这是引言内容\n\n# 方法\n\n这是方法内容"
        
        result = self.validator.check_section_integrity(original, revised)
        
        assert result.is_valid is False
        assert len(result.issues) > 0
        assert any("删除章节" in issue for issue in result.issues)


class TestImmutableSectionValidator:
    """不可修改章节验证器测试"""
    
    def setup_method(self):
        self.validator = ImmutableSectionValidator()
    
    def test_check_immutable_sections_no_violation(self):
        """测试无违规修改"""
        content = """---
name: "测试模板"
immutable_sections: ["安全注意事项"]
---

# [不可修改] 安全注意事项

1. 注意事项1
2. 注意事项2

# 方法

这是方法内容
"""
        
        revised = """---
name: "测试模板"
immutable_sections: ["安全注意事项"]
---

# [不可修改] 安全注意事项

1. 注意事项1
2. 注意事项2

# 方法

这是修改后的方法内容
"""
        
        result = self.validator.check_immutable_sections(content, revised)
        
        assert result.is_valid is True
        assert len(result.issues) == 0
    
    def test_check_immutable_sections_violation(self):
        """测试违规修改"""
        content = """---
name: "测试模板"
immutable_sections: ["安全注意事项"]
---

# [不可修改] 安全注意事项

1. 注意事项1
2. 注意事项2

# 方法

这是方法内容
"""
        
        revised = """---
name: "测试模板"
immutable_sections: ["安全注意事项"]
---

# [不可修改] 安全注意事项

1. 修改后的注意事项1
2. 修改后的注意事项2

# 方法

这是方法内容
"""
        
        result = self.validator.check_immutable_sections(content, revised)
        
        assert result.is_valid is False
        assert len(result.issues) > 0
        assert any("不可修改章节" in issue for issue in result.issues)


class TestModificationJustificationValidator:
    """修改依据验证器测试"""
    
    def setup_method(self):
        self.validator = ModificationJustificationValidator()
    
    def test_verify_justification_valid(self):
        """测试有效修改依据"""
        user_prompt = "将培养基更换为DMEM+10%FBS"
        modifications = [
            {
                "section": "材料与试剂",
                "type": "replace",
                "modified_text": "培养基：DMEM+10%FBS"
            }
        ]
        
        result = self.validator.verify_modification_justification(user_prompt, modifications)
        
        assert result.confidence > 0.5
        assert len(result.modifications) > 0
    
    def test_verify_justification_invalid(self):
        """测试无效修改依据"""
        user_prompt = "修改细胞培养时间"
        modifications = [
            {
                "section": "材料与试剂",
                "type": "replace",
                "modified_text": "添加新的检测设备"
            }
        ]
        
        result = self.validator.verify_modification_justification(user_prompt, modifications)
        
        assert result.confidence < 0.5
        assert len(result.issues) > 0


class TestAntiHallucinationValidator:
    """防幻觉验证器主测试"""
    
    def setup_method(self):
        self.validator = AntiHallucinationValidator()
    
    def test_validate_revision_success(self):
        """测试成功的验证"""
        original_template = """# [不可修改] 安全注意事项

1. 注意事项1

# 材料

培养基：RPMI-1640
"""
        
        user_modifications = "将培养基更换为DMEM"
        ai_output = """# [不可修改] 安全注意事项

1. 注意事项1

# 材料

培养基：DMEM
"""
        
        result = self.validator.validate_revision(original_template, user_modifications, ai_output)
        
        assert result.is_valid is True
        assert result.confidence > 0.8
    
    def test_validate_revision_failure(self):
        """测试失败的验证"""
        original_template = """# [不可修改] 安全注意事项

1. 注意事项1

# 材料

培养基：RPMI-1640
"""
        
        user_modifications = "将培养基更换为DMEM"
        ai_output = """# [不可修改] 安全注意事项

1. 修改后的注意事项1

# 材料

培养基：DMEM

# 新增章节

这是新增的章节内容
"""
        
        result = self.validator.validate_revision(original_template, user_modifications, ai_output)
        
        assert result.is_valid is False
        assert len(result.issues) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
