"""
文献库页面模块
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import settings


def library_page():
    """文献库页面内容"""
    st.title("📚 文献库管理")
    
    # 数据集管理
    st.markdown("## 🗂️ 数据集管理")
    
    # 刷新数据集列表
    if st.button("🔄 刷新数据集", key="refresh_datasets"):
        with st.spinner("正在获取数据集列表..."):
            try:
                datasets = st.session_state.ragflow_client.list_datasets()
                st.session_state.datasets = datasets
                st.success(f"成功获取 {len(datasets)} 个数据集")
            except Exception as e:
                st.error(f"获取数据集失败: {e}")
                st.session_state.datasets = []
    
    # 显示数据集列表
    datasets = st.session_state.get('datasets', [])
    
    if datasets:
        # 创建数据集选择器
        dataset_options = {f"{ds.name} ({ds.document_count} 文档)": ds.id for ds in datasets}
        selected_dataset_name = st.selectbox(
            "选择数据集",
            options=list(dataset_options.keys()),
            index=0 if st.session_state.current_dataset is None else 
                   list(dataset_options.keys()).index(
                       next((k for k, v in dataset_options.items() 
                            if v == st.session_state.current_dataset), "")
                   )
        )
        
        if selected_dataset_name:
            selected_dataset_id = dataset_options[selected_dataset_name]
            st.session_state.current_dataset = selected_dataset_id
            
            # 显示数据集详细信息
            selected_dataset = next((ds for ds in datasets if ds.id == selected_dataset_id), None)
            if selected_dataset:
                display_dataset_info(selected_dataset)
                
                # 文档管理
                st.markdown("---")
                st.markdown("## 📄 文档管理")
                
                # 文档操作选项
                doc_action = st.selectbox(
                    "选择操作",
                    ["查看文档列表", "上传文档", "搜索文档", "删除文档"],
                    key="doc_action"
                )
                
                if doc_action == "查看文档列表":
                    display_document_list(selected_dataset_id)
                elif doc_action == "上传文档":
                    upload_document_form(selected_dataset_id)
                elif doc_action == "搜索文档":
                    search_documents_form(selected_dataset_id)
                elif doc_action == "删除文档":
                    delete_document_form(selected_dataset_id)
    else:
        st.info("暂无数据集，请先在RAGFlow中创建数据集")
        
        # 创建新数据集的表单
        with st.expander("创建新数据集"):
            with st.form("create_dataset_form"):
                new_dataset_name = st.text_input("数据集名称")
                new_dataset_desc = st.text_area("数据集描述")
                
                if st.form_submit_button("创建数据集"):
                    if new_dataset_name:
                        with st.spinner("正在创建数据集..."):
                            try:
                                new_dataset = st.session_state.ragflow_client.create_dataset(
                                    name=new_dataset_name,
                                    description=new_dataset_desc
                                )
                                if new_dataset:
                                    st.success(f"数据集 '{new_dataset_name}' 创建成功")
                                    # 刷新数据集列表
                                    datasets = st.session_state.ragflow_client.list_datasets()
                                    st.session_state.datasets = datasets
                                else:
                                    st.error("数据集创建失败")
                            except Exception as e:
                                st.error(f"创建数据集时出错: {e}")
                    else:
                        st.error("请输入数据集名称")


def display_dataset_info(dataset):
    """显示数据集详细信息"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("文档数量", dataset.document_count)
    
    with col2:
        st.metric("创建时间", dataset.created_at[:10] if dataset.created_at else "未知")
    
    with col3:
        st.metric("更新时间", dataset.updated_at[:10] if dataset.updated_at else "未知")
    
    with col4:
        st.metric("数据集ID", dataset.id[:8] + "...")
    
    # 数据集描述
    if dataset.description:
        st.markdown(f"**描述**: {dataset.description}")


def display_document_list(dataset_id):
    """显示文档列表"""
    with st.spinner("正在获取文档列表..."):
        try:
            documents = st.session_state.ragflow_client.list_documents(dataset_id)
            
            if documents:
                # 创建文档数据表
                doc_data = []
                for doc in documents:
                    doc_data.append({
                        "ID": doc.id[:8] + "...",
                        "名称": doc.name,
                        "内容预览": doc.content[:100] + "..." if len(doc.content) > 100 else doc.content,
                        "元数据": str(doc.metadata)[:50] + "..." if len(str(doc.metadata)) > 50 else str(doc.metadata)
                    })
                
                df = pd.DataFrame(doc_data)
                st.dataframe(df, use_container_width=True)
                
                # 文档详情查看
                selected_doc_index = st.selectbox(
                    "选择文档查看详情",
                    options=range(len(documents)),
                    format_func=lambda x: documents[x].name
                )
                
                if st.button("查看详情", key="view_doc_detail"):
                    selected_doc = documents[selected_doc_index]
                    display_document_detail(selected_doc)
            else:
                st.info("该数据集中暂无文档")
        except Exception as e:
            st.error(f"获取文档列表失败: {e}")


def display_document_detail(document):
    """显示文档详细信息"""
    st.markdown("### 📄 文档详情")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**文档ID**: {document.id}")
        st.markdown(f"**文档名称**: {document.name}")
    
    with col2:
        st.markdown(f"**内容长度**: {len(document.content)} 字符")
        st.markdown(f"**元数据项数**: {len(document.metadata)}")
    
    # 文档内容
    st.markdown("#### 📝 文档内容")
    content_length = len(document.content)
    
    if content_length > 5000:
        st.info(f"文档内容较长（{content_length}字符），显示前5000字符")
        st.text_area("内容", document.content[:5000], height=300, disabled=True)
        
        if st.button("显示完整内容", key="show_full_content"):
            st.text_area("完整内容", document.content, height=500, disabled=True)
    else:
        st.text_area("内容", document.content, height=300, disabled=True)
    
    # 元数据
    if document.metadata:
        st.markdown("#### 🏷️ 元数据")
        st.json(document.metadata)


def upload_document_form(dataset_id):
    """上传文档表单"""
    st.markdown("### 📤 上传新文档")
    
    with st.form("upload_document_form"):
        doc_name = st.text_input("文档名称")
        doc_content = st.text_area("文档内容", height=300)
        
        # 元数据输入
        st.markdown("#### 🏷️ 元数据（可选）")
        metadata_json = st.text_area(
            "元数据 (JSON格式)",
            placeholder='{"author": "作者名", "year": "2023", "journal": "期刊名"}'
        )
        
        chunk_size = st.number_input("分块大小", min_value=100, max_value=2000, value=512)
        chunk_overlap = st.number_input("分块重叠", min_value=0, max_value=500, value=50)
        
        if st.form_submit_button("上传文档"):
            if doc_name and doc_content:
                # 解析元数据
                metadata = {}
                if metadata_json:
                    try:
                        import json
                        metadata = json.loads(metadata_json)
                    except json.JSONDecodeError:
                        st.error("元数据JSON格式错误，使用空元数据")
                        metadata = {}
                
                with st.spinner("正在上传文档..."):
                    try:
                        from src.core.ragflow_client import Document
                        document = Document(
                            name=doc_name,
                            content=doc_content,
                            metadata=metadata,
                            chunk_size=int(chunk_size),
                            chunk_overlap=int(chunk_overlap)
                        )
                        
                        doc_id = st.session_state.ragflow_client.upload_document(dataset_id, document)
                        if doc_id:
                            st.success(f"文档上传成功，ID: {doc_id}")
                        else:
                            st.error("文档上传失败")
                    except Exception as e:
                        st.error(f"上传文档时出错: {e}")
            else:
                st.error("请填写文档名称和内容")


def search_documents_form(dataset_id):
    """搜索文档表单"""
    st.markdown("### 🔍 搜索文档")
    
    query = st.text_input("搜索查询")
    top_k = st.slider("返回结果数量", min_value=1, max_value=20, value=5)
    similarity_threshold = st.slider("相似度阈值", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
    
    if st.button("搜索", key="search_docs"):
        if query:
            with st.spinner("正在搜索..."):
                try:
                    results = st.session_state.ragflow_client.search(
                        dataset_id=dataset_id,
                        query=query,
                        top_k=top_k,
                        similarity_threshold=similarity_threshold
                    )
                    
                    if results:
                        st.success(f"找到 {len(results)} 个相关文档")
                        
                        for i, result in enumerate(results):
                            with st.expander(f"结果 {i+1}: {result.document_name} (相似度: {result.score:.3f})"):
                                st.markdown(f"**文档ID**: {result.document_id}")
                                st.markdown(f"**相似度**: {result.score:.3f}")
                                st.markdown(f"**内容预览**:")
                                st.text_area("", result.content[:500] + "..." if len(result.content) > 500 else result.content, 
                                           height=150, disabled=True, key=f"result_{i}")
                                
                                if result.metadata:
                                    st.markdown("**元数据**:")
                                    st.json(result.metadata)
                    else:
                        st.info("未找到相关文档")
                except Exception as e:
                    st.error(f"搜索失败: {e}")
        else:
            st.error("请输入搜索查询")


def delete_document_form(dataset_id):
    """删除文档表单"""
    st.markdown("### 🗑️ 删除文档")
    st.warning("⚠️ 此操作不可撤销，请谨慎操作")
    
    with st.spinner("正在获取文档列表..."):
        try:
            documents = st.session_state.ragflow_client.list_documents(dataset_id)
            
            if documents:
                doc_options = {f"{doc.name} ({doc.id[:8]}...)": doc.id for doc in documents}
                selected_doc_id = st.selectbox("选择要删除的文档", options=list(doc_options.keys()))
                
                if st.button("删除文档", key="delete_doc"):
                    doc_id_to_delete = doc_options[selected_doc_id]
                    confirm = st.checkbox("确认删除")
                    
                    if confirm:
                        with st.spinner("正在删除文档..."):
                            try:
                                success = st.session_state.ragflow_client.delete_document(dataset_id, doc_id_to_delete)
                                if success:
                                    st.success("文档删除成功")
                                else:
                                    st.error("文档删除失败")
                            except Exception as e:
                                st.error(f"删除文档时出错: {e}")
                    else:
                        st.error("请确认删除操作")
            else:
                st.info("该数据集中暂无文档")
        except Exception as e:
            st.error(f"获取文档列表失败: {e}")