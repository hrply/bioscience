"""
备份与恢复页面
提供数据备份和恢复功能
"""

import streamlit as st
import os
import shutil
import tarfile
import json
from datetime import datetime
from pathlib import Path


def run():
    st.title("💾 数据备份与恢复")

    # 标签页
    tab1, tab2 = st.tabs(["📦 数据备份", "📥 数据恢复"])

    with tab1:
        st.subheader("📦 备份数据")

        st.info("""
        💡 备份说明：
        - 备份将包含：实验数据、结果、配置文件、模板文件
        - 向量数据库（ChromaDB）将单独备份到 chroma 子目录
        - 上传文件也将被包含在备份中
        - 备份文件格式：tar.gz
        """)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**备份内容预览：**")
            backup_items = [
                "✅ /app/data - 实验数据、结果、配置、模板",
                "✅ /app/chroma - 向量数据库",
                "✅ /app/uploads - 上传文件"
            ]
            for item in backup_items:
                st.markdown(item)

        with col2:
            st.markdown("**备份配置：**")
            backup_name = st.text_input(
                "备份名称：",
                value=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                help="备份文件的名称（不包含扩展名）"
            )

            include_chroma = st.checkbox(
                "包含ChromaDB向量数据库",
                value=True,
                help="是否备份向量数据库（通常较大）"
            )

        st.markdown("---")

        if st.button("🚀 开始备份", type="primary", use_container_width=True):
            with st.spinner("正在创建备份..."):
                try:
                    backup_result = create_backup(
                        backup_name=backup_name,
                        include_chroma=include_chroma
                    )

                    if backup_result['success']:
                        st.success(f"✅ 备份成功完成！")
                        st.markdown(f"📁 备份文件：`{backup_result['backup_path']}`")
                        st.markdown(f"📊 备份大小：{backup_result['size']}")

                        # 提供下载链接
                        if os.path.exists(backup_result['backup_path']):
                            with open(backup_result['backup_path'], 'rb') as f:
                                st.download_button(
                                    "⬇️ 下载备份文件",
                                    data=f,
                                    file_name=os.path.basename(backup_result['backup_path']),
                                    mime='application/gzip'
                                )
                    else:
                        st.error(f"❌ 备份失败：{backup_result['error']}")

                except Exception as e:
                    st.error(f"❌ 备份过程中出现异常：{e}")

        # 备份历史
        st.markdown("---")
        st.subheader("📚 历史备份")

        backup_history = list_backups()

        if backup_history:
            for backup in backup_history:
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.markdown(f"📦 **{backup['name']}**")
                    st.caption(f"创建时间：{backup['created']} | 大小：{backup['size']}")

                with col2:
                    if st.button("📥 恢复", key=f"restore_{backup['name']}"):
                        st.session_state['restore_backup'] = backup['name']
                        st.rerun()

                with col3:
                    if st.button("🗑️ 删除", key=f"delete_{backup['name']}"):
                        if st.checkbox(f"确认删除 {backup['name']}？", key=f"confirm_delete_{backup['name']}"):
                            try:
                                os.remove(backup['path'])
                                st.success(f"✅ 备份已删除")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ 删除失败：{e}")
        else:
            st.info("📭 暂无备份文件")

    with tab2:
        st.subheader("📥 恢复数据")

        st.warning("""
        ⚠️ 恢复说明：
        - 恢复操作将覆盖当前数据！
        - 建议在恢复前先创建当前数据的备份
        - 恢复过程可能需要几分钟时间
        """)

        # 选择恢复源
        restore_source = st.radio(
            "选择恢复方式：",
            options=["上传备份文件", "从备份目录选择"],
            horizontal=True
        )

        backup_file_path = None

        if restore_source == "上传备份文件":
            uploaded_file = st.file_uploader(
                "选择备份文件：",
                type=['tar', 'gz', 'tgz'],
                help="上传之前创建的备份文件"
            )

            if uploaded_file:
                # 保存上传的文件
                backup_dir = "/backup"
                os.makedirs(backup_dir, exist_ok=True)
                backup_file_path = os.path.join(
                    backup_dir,
                    f"uploaded_{uploaded_file.name}"
                )

                with open(backup_file_path, 'wb') as f:
                    f.write(uploaded_file.getvalue())

                st.success(f"✅ 文件已上传：{uploaded_file.name}")

        else:
            # 从备份目录选择
            backup_history = list_backups()

            if backup_history:
                backup_options = {
                    f"{b['name']} ({b['size']})": b['path']
                    for b in backup_history
                }

                selected_backup = st.selectbox(
                    "选择要恢复的备份：",
                    options=list(backup_options.keys())
                )

                backup_file_path = backup_options[selected_backup]
            else:
                st.warning("⚠️ 备份目录中没有找到备份文件")
                st.info("请先创建备份，或使用文件上传方式")

        # 恢复选项
        if backup_file_path:
            st.markdown("---")
            st.subheader("⚙️ 恢复选项")

            restore_items = st.multiselect(
                "选择要恢复的内容：",
                options=[
                    ("/app/data", "主数据（实验数据、结果、配置、模板）"),
                    ("/app/chroma", "向量数据库（ChromaDB）"),
                    ("/app/uploads", "上传文件")
                ],
                default=[
                    ("/app/data", "主数据（实验数据、结果、配置、模板）"),
                    ("/app/chroma", "向量数据库（ChromaDB）"),
                    ("/app/uploads", "上传文件")
                ],
                format_func=lambda x: x[1]
            )

            # 确认恢复
            st.markdown("---")

            if st.button("⚠️ 开始恢复", type="primary", use_container_width=True):
                if st.checkbox("我已确认要覆盖当前数据", key="confirm_restore"):
                    with st.spinner("正在恢复数据，请稍候..."):
                        try:
                            restore_result = restore_from_backup(
                                backup_path=backup_file_path,
                                restore_items=restore_items
                            )

                            if restore_result['success']:
                                st.success("✅ 数据恢复成功！")
                                st.markdown(f"已恢复：{', '.join([item[1] for item in restore_items])}")
                                st.info("💡 建议重启应用以确保所有更改生效")
                            else:
                                st.error(f"❌ 恢复失败：{restore_result['error']}")

                        except Exception as e:
                            st.error(f"❌ 恢复过程中出现异常：{e}")
                else:
                    st.warning("⚠️ 请先勾选确认框")


def create_backup(backup_name: str, include_chroma: bool = True) -> dict:
    """
    创建数据备份

    Args:
        backup_name: 备份名称
        include_chroma: 是否包含ChromaDB

    Returns:
        dict: 包含成功状态、路径和大小信息的字典
    """
    try:
        # 创建备份目录
        backup_dir = "/backup"
        os.makedirs(backup_dir, exist_ok=True)

        # 备份文件名
        backup_filename = f"{backup_name}.tar.gz"
        backup_path = os.path.join(backup_dir, backup_filename)

        # 创建tar.gz备份
        with tarfile.open(backup_path, "w:gz") as tar:
            # 备份主数据卷
            if os.path.exists("/app/data"):
                tar.add("/app/data", arcname="data")

            # 备份上传文件卷
            if os.path.exists("/app/uploads"):
                tar.add("/app/uploads", arcname="uploads")

            # 单独备份ChromaDB到chroma子目录
            if include_chroma and os.path.exists("/app/chroma"):
                tar.add("/app/chroma", arcname="chroma")

        # 获取备份大小
        backup_size = os.path.getsize(backup_path)
        size_str = format_size(backup_size)

        return {
            'success': True,
            'backup_path': backup_path,
            'size': size_str
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def restore_from_backup(backup_path: str, restore_items: list) -> dict:
    """
    从备份恢复数据

    Args:
        backup_path: 备份文件路径
        restore_items: 要恢复的项目列表

    Returns:
        dict: 包含成功状态的字典
    """
    try:
        # 创建临时目录
        temp_dir = "/tmp/restore_temp"
        os.makedirs(temp_dir, exist_ok=True)

        # 解压备份文件
        with tarfile.open(backup_path, "r:gz") as tar:
            tar.extractall(temp_dir)

        # 恢复各个组件
        restore_map = {
            ("/app/data", "主数据（实验数据、结果、配置、模板）"): "data",
            ("/app/chroma", "向量数据库（ChromaDB）"): "chroma",
            ("/app/uploads", "上传文件"): "uploads"
        }

        for item_path, item_name in restore_items:
            # 从restore_items中获取实际的项目路径
            arcname = None
            for restore_item in restore_items:
                if restore_item[0] == item_path:
                    arcname = restore_map.get(restore_item, None)
                    break

            if not arcname:
                continue

            # 源路径（从备份中）
            source_path = os.path.join(temp_dir, arcname)

            if os.path.exists(source_path):
                # 目标路径（容器内）
                target_path = item_path

                # 如果目标目录存在，先备份
                if os.path.exists(target_path):
                    backup_current = f"{target_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.move(target_path, backup_current)

                # 创建目标目录
                os.makedirs(os.path.dirname(target_path), exist_ok=True)

                # 复制文件
                if os.path.isdir(source_path):
                    shutil.copytree(source_path, target_path)
                else:
                    shutil.copy2(source_path, target_path)

        # 清理临时目录
        shutil.rmtree(temp_dir)

        return {
            'success': True,
            'message': '恢复完成'
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def list_backups() -> list:
    """
    列出所有可用的备份

    Returns:
        list: 备份信息列表
    """
    backup_dir = "/backup"
    backups = []

    if not os.path.exists(backup_dir):
        return backups

    for filename in os.listdir(backup_dir):
        if filename.endswith('.tar.gz') or filename.endswith('.tgz'):
            filepath = os.path.join(backup_dir, filename)

            # 获取文件信息
            stat = os.stat(filepath)
            created = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            size = format_size(stat.st_size)

            backups.append({
                'name': filename.replace('.tar.gz', '').replace('.tgz', ''),
                'path': filepath,
                'created': created,
                'size': size
            })

    # 按创建时间倒序排列
    backups.sort(key=lambda x: x['created'], reverse=True)

    return backups


def format_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 字节大小

    Returns:
        str: 格式化后的大小字符串
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
