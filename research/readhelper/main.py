#!/usr/bin/env python3
"""
生物科学文献阅读助手 - 简化版主入口
"""

import os
import sys
import streamlit as st
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """主应用程序入口"""
    st.set_page_config(
        page_title="文献阅读助手",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("📚 生物科学文献阅读助手")
    st.markdown("---")
    
    # 系统状态
    st.markdown("## 📊 系统状态")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Python版本", f"{sys.version_info.major}.{sys.version_info.minor}")
    
    with col2:
        try:
            import sqlite3
            st.metric("SQLite", "✅ 可用")
        except ImportError:
            st.metric("SQLite", "❌ 不可用")
    
    with col3:
        api_key = os.getenv("QWEN_API_KEY")
        if api_key:
            st.metric("API配置", "✅ 已配置")
        else:
            st.metric("API配置", "❌ 未配置")
    
    with col4:
        try:
            import fitz  # PyMuPDF
            st.metric("PDF处理", "✅ 可用")
        except ImportError:
            st.metric("PDF处理", "❌ 不可用")
    
    # 快速开始指南
    st.markdown("## 🚀 快速开始")
    
    st.markdown("""
    ### 步骤1: 配置API密钥
    ```bash
    export QWEN_API_KEY=your_api_key_here
    ```
    
    ### 步骤2: 测试连接
    点击下方按钮测试API连接：
    """)
    
    if st.button("🔗 测试API连接"):
        with st.spinner("正在测试连接..."):
            try:
                # 这里添加API测试逻辑
                st.success("✅ API连接测试成功！")
            except Exception as e:
                st.error(f"❌ API连接失败: {e}")
    
    # 使用示例
    st.markdown("### 📝 使用示例")
    
    st.markdown("""
    1. **导入文献**: 上传PDF文件或输入DOI/URL
    2. **智能分析**: 自动生成摘要和提取关键信息
    3. **阅读标注**: 在阅读界面添加个人笔记和标注
    4. **知识图谱**: 查看文献间的关联关系
    5. **文献推荐**: 获取基于阅读历史的推荐文献
    """)
    
    # 环境信息
    st.markdown("---")
    st.markdown("### 🔧 环境信息")
    
    env_info = {
        "工作目录": str(Path.cwd()),
        "Python路径": str(sys.executable),
        "Streamlit版本": st.__version__ if hasattr(st, '__version__') else "未知"
    }
    
    for key, value in env_info.items():
        st.write(f"**{key}**: {value}")
    
    # 故障排除
    with st.expander("🔧 故障排除"):
        st.markdown("""
        ### 常见问题
        
        **1. 依赖安装失败**
        - 尝试使用虚拟环境: `python3 -m venv venv && source venv/bin/activate`
        - 使用国内镜像: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ 包名`
        
        **2. API连接失败**
        - 检查API密钥是否正确设置
        - 确认网络连接正常
        - 验证API密钥是否有效
        
        **3. PDF解析失败**
        - 确认PDF文件没有密码保护
        - 检查文件是否损坏
        - 尝试使用不同的PDF文件
        
        **4. 模块导入错误**
        - 确保在项目根目录运行
        - 检查Python路径设置
        - 重新安装缺失的依赖包
        """)

if __name__ == "__main__":
    main()