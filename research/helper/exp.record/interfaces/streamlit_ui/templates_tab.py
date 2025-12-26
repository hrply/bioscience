"""
模板管理界面 - 上传、编辑和管理实验模板
"""

import streamlit as st
import logging
from datetime import datetime
from typing import Dict, Any, List
import tempfile
import os

from config.settings import Settings
from storage.template_manager import TemplateManager


def render_templates_tab():
    """渲染模板管理标签页"""
    st.title("📋 模板管理")
    st.markdown("---")
    
    # 初始化会话状态
    if "template_action" not in st.session_state:
        st.session_state.template_action = "list"
    if "editing_template" not in st.session_state:
        st.session_state.editing_template = None
    
    # 侧边栏操作选择
    with st.sidebar:
        st.markdown("### 🛠️ 模板操作")
        
        if st.button("📋 模板列表", key="list_templates"):
            st.session_state.template_action = "list"
            st.session_state.editing_template = None
            st.rerun()
        
        if st.button("➕ 创建模板", key="create_template"):
            st.session_state.template_action = "create"
            st.session_state.editing_template = None
            st.rerun()
        
        if st.button("📤 上传模板", key="upload_template"):
            st.session_state.template_action = "upload"
            st.session_state.editing_template = None
            st.rerun()
        
        # 模板统计
        st.markdown("---")
        st.markdown("### 📊 模板统计")
        
        try:
            template_manager = TemplateManager()
            stats = template_manager.get_template_statistics()
            st.metric("总模板数", stats["total_templates"])
            st.metric("分类数", len(stats["categories"]))
        except Exception as e:
            st.error(f"统计加载失败: {e}")
    
    # 渲染主要内容
    if st.session_state.template_action == "list":
        _render_template_list()
    elif st.session_state.template_action == "create":
        _render_template_creator()
    elif st.session_state.template_action == "upload":
        _render_template_upload()
    elif st.session_state.template_action == "edit":
        _render_template_editor()
    elif st.session_state.template_action == "view":
        _render_template_viewer()


def _render_template_list():
    """渲染模板列表"""
    st.markdown("## 📋 模板列表")
    
    try:
        template_manager = TemplateManager()
        
        # 分类筛选
        categories = ["全部"] + template_manager.get_categories()
        selected_category = st.selectbox("筛选分类:", categories)
        
        # 搜索
        search_query = st.text_input("搜索模板:", placeholder="输入关键词搜索...")
        
        # 获取模板列表
        if selected_category == "全部":
            templates = template_manager.list_templates()
        else:
            templates = template_manager.list_templates(selected_category)
        
        # 搜索过滤
        if search_query:
            templates = template_manager.search_templates(search_query)
        
        if not templates:
            st.info("没有找到匹配的模板")
            return
        
        # 显示模板卡片
        for template in templates:
            with st.expander(f"📄 {template['name']} (v{template['version']})"):
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**分类**: {template['category']}")
                    st.markdown(f"**描述**: {template['description']}")
                    st.markdown(f"**更新时间**: {template['updated_at'][:10]}")
                    
                    if template.get('immutable_sections'):
                        st.warning(f"不可修改章节: {', '.join(template['immutable_sections'])}")
                
                with col2:
                    if st.button("👁️ 查看", key=f"view_{template['id']}"):
                        st.session_state.editing_template = template
                        st.session_state.template_action = "view"
                        st.rerun()
                
                with col3:
                    if st.button("✏️ 编辑", key=f"edit_{template['id']}"):
                        st.session_state.editing_template = template
                        st.session_state.template_action = "edit"
                        st.rerun()
                    
                    if st.button("🗑️ 删除", key=f"delete_{template['id']}"):
                        _delete_template(template['id'])
    
    except Exception as e:
        st.error(f"加载模板列表失败: {e}")


def _render_template_creator():
    """渲染模板创建器"""
    st.markdown("## ➕ 创建新模板")
    
    with st.form("create_template_form"):
        # 基本信息
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("模板名称*", placeholder="例如: 细胞培养基础协议")
            category = st.text_input("分类*", placeholder="例如: 细胞生物学")
            version = st.text_input("版本", value="1.0")
        
        with col2:
            description = st.text_area("描述", placeholder="简要描述模板用途和内容")
        
        # 不可修改章节
        st.markdown("### 🚫 不可修改章节")
        st.markdown("输入不可修改的章节名称，每行一个:")
        immutable_sections_text = st.text_area(
            "不可修改章节:",
            placeholder="安全注意事项\n基本原理",
            height=100
        )
        
        # 模板内容
        st.markdown("### 📝 模板内容")
        st.markdown("""
        **格式说明**:
        - 使用Markdown格式编写
        - 使用 # ## ### 表示章节标题
        - 在章节标题前添加 `[不可修改]` 标记不可修改章节
        - 支持YAML前置元数据
        """)
        
        template_content = st.text_area(
            "模板内容*:",
            height=400,
            placeholder="""---
name: "示例模板"
version: "1.0"
category: "示例"
immutable_sections: ["安全注意事项", "基本原理"]
---

# [不可修改] 安全注意事项

1. 所有操作必须在生物安全柜中进行
2. 佩戴适当的个人防护装备

# [不可修改] 基本原理

简要描述实验原理...

# [可修改] 材料与试剂

### 细胞系
- 细胞名称：[请填写具体细胞系]

### 培养基
- 基础培养基：[请填写]

# [可修改] 实验步骤

1. 步骤一：[请详细描述]
2. 步骤二：[请详细描述]
"""
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("取消"):
                st.session_state.template_action = "list"
                st.rerun()
        
        with col2:
            if st.form_submit_button("创建模板", type="primary"):
                _create_template({
                    "name": name,
                    "category": category,
                    "version": version,
                    "description": description,
                    "content": template_content,
                    "immutable_sections": [s.strip() for s in immutable_sections_text.split('\n') if s.strip()]
                })


def _render_template_upload():
    """渲染模板上传"""
    st.markdown("## 📤 上传模板文件")
    
    st.markdown("""
    ### 上传说明
    - 支持 `.md` 格式的Markdown文件
    - 文件可以包含YAML前置元数据
    - 不可修改章节可以使用 `[不可修改]` 标记
    """)
    
    uploaded_file = st.file_uploader(
        "选择模板文件:",
        type=['md'],
        help="选择要上传的Markdown模板文件"
    )
    
    if uploaded_file:
        try:
            # 读取文件内容
            content = uploaded_file.read().decode('utf-8')
            
            st.markdown("### 📄 文件预览")
            st.text_area("文件内容:", content, height=300, disabled=True)
            
            # 验证模板格式
            template_manager = TemplateManager()
            validation_result = template_manager.validate_template(content)
            
            if validation_result['valid']:
                st.success("✅ 模板格式验证通过")
            else:
                st.error("❌ 模板格式验证失败")
                for error in validation_result['errors']:
                    st.write(f"- {error}")
            
            if validation_result['warnings']:
                st.warning("⚠️ 警告信息:")
                for warning in validation_result['warnings']:
                    st.write(f"- {warning}")
            
            # 上传确认
            if st.button("确认上传", type="primary", disabled=not validation_result['valid']):
                _upload_template(uploaded_file.name, content)
        
        except Exception as e:
            st.error(f"读取文件失败: {e}")


def _render_template_editor():
    """渲染模板编辑器"""
    if not st.session_state.editing_template:
        st.session_state.template_action = "list"
        st.rerun()
    
    template = st.session_state.editing_template
    st.markdown(f"## ✏️ 编辑模板: {template['name']}")
    
    with st.form("edit_template_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("模板名称:", value=template['name'])
            category = st.text_input("分类:", value=template['category'])
            version = st.text_input("版本:", value=template['version'])
        
        with col2:
            description = st.text_area("描述:", value=template['description'])
        
        # 不可修改章节
        immutable_sections = template.get('immutable_sections', [])
        immutable_sections_text = '\n'.join(immutable_sections)
        
        st.markdown("### 🚫 不可修改章节")
        immutable_sections_text = st.text_area(
            "不可修改章节:",
            value=immutable_sections_text,
            height=100
        )
        
        # 模板内容
        st.markdown("### 📝 模板内容")
        edited_content = st.text_area(
            "模板内容:",
            value=template['content'],
            height=400
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.form_submit_button("取消"):
                st.session_state.template_action = "list"
                st.session_state.editing_template = None
                st.rerun()
        
        with col2:
            if st.form_submit_button("保存"):
                _update_template(template['id'], {
                    "name": name,
                    "category": category,
                    "version": version,
                    "description": description,
                    "content": edited_content,
                    "immutable_sections": [s.strip() for s in immutable_sections_text.split('\n') if s.strip()]
                })
        
        with col3:
            if st.form_submit_button("预览"):
                st.session_state.template_action = "view"
                st.rerun()


def _render_template_viewer():
    """渲染模板查看器"""
    if not st.session_state.editing_template:
        st.session_state.template_action = "list"
        st.rerun()
    
    template = st.session_state.editing_template
    
    st.markdown(f"## 👁️ 查看模板: {template['name']}")
    
    # 基本信息
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("分类", template['category'])
    
    with col2:
        st.metric("版本", template['version'])
    
    with col3:
        st.metric("更新时间", template['updated_at'][:10])
    
    with col4:
        immutable_count = len(template.get('immutable_sections', []))
        st.metric("不可修改章节", immutable_count)
    
    # 描述
    if template['description']:
        st.markdown(f"**描述**: {template['description']}")
    
    # 不可修改章节
    if template.get('immutable_sections'):
        st.warning(f"🚫 不可修改章节: {', '.join(template['immutable_sections'])}")
    
    # 模板内容
    st.markdown("### 📝 模板内容")
    st.markdown(template['content'])
    
    # 操作按钮
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("返回列表"):
            st.session_state.template_action = "list"
            st.session_state.editing_template = None
            st.rerun()
    
    with col2:
        if st.button("编辑模板"):
            st.session_state.template_action = "edit"
            st.rerun()


def _create_template(template_data: Dict[str, Any]):
    """创建模板"""
    try:
        template_manager = TemplateManager()
        
        # 验证必填字段
        if not template_data.get('name') or not template_data.get('category'):
            st.error("模板名称和分类为必填项")
            return
        
        if not template_data.get('content'):
            st.error("模板内容不能为空")
            return
        
        # 创建模板
        template_id = template_manager.create_template(template_data)
        
        st.success(f"✅ 模板创建成功！ID: {template_id}")
        st.session_state.template_action = "list"
        st.session_state.editing_template = None
        st.rerun()
        
    except Exception as e:
        st.error(f"创建模板失败: {e}")
        logging.error(f"Create template error: {e}")


def _update_template(template_id: str, updates: Dict[str, Any]):
    """更新模板"""
    try:
        template_manager = TemplateManager()
        
        if template_manager.update_template(template_id, updates):
            st.success("✅ 模板更新成功！")
            st.session_state.template_action = "list"
            st.session_state.editing_template = None
            st.rerun()
        else:
            st.error("更新模板失败")
            
    except Exception as e:
        st.error(f"更新模板失败: {e}")
        logging.error(f"Update template error: {e}")


def _delete_template(template_id: str):
    """删除模板"""
    try:
        template_manager = TemplateManager()
        
        if template_manager.delete_template(template_id):
            st.success("✅ 模板删除成功！")
            st.rerun()
        else:
            st.error("删除模板失败")
            
    except Exception as e:
        st.error(f"删除模板失败: {e}")
        logging.error(f"Delete template error: {e}")


def _upload_template(filename: str, content: str):
    """上传模板"""
    try:
        template_manager = TemplateManager()
        
        # 从文件名生成模板ID
        template_id = filename.replace('.md', '').replace(' ', '_')
        
        # 创建模板数据
        template_data = {
            "id": template_id,
            "name": template_id.replace('_', ' ').title(),
            "content": content
        }
        
        # 创建模板
        created_id = template_manager.create_template(template_data)
        
        st.success(f"✅ 模板上传成功！ID: {created_id}")
        st.session_state.template_action = "list"
        st.rerun()
        
    except Exception as e:
        st.error(f"上传模板失败: {e}")
        logging.error(f"Upload template error: {e}")