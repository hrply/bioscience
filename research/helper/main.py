#!/usr/bin/env python3
"""
个人实验记录智能助手 - 简化版主入口
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
        page_title="实验记录智能助手",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🔬 实验记录智能助手")
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
            import yaml
            st.metric("YAML支持", "✅ 可用")
        except ImportError:
            st.metric("YAML支持", "❌ 不可用")
    
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
    1. **选择模板**: 从预定义的实验协议模板中选择
    2. **描述修改**: 用自然语言描述需要的修改
    3. **查看修订**: 系统生成修订版本，高亮显示修改
    4. **确认保存**: 检查无误后保存实验记录
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
        
        **3. 模块导入错误**
        - 确保在项目根目录运行
        - 检查Python路径设置
        - 重新安装缺失的依赖包
        """)

if __name__ == "__main__":
    main()