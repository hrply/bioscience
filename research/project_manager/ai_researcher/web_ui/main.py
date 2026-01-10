"""
AI科研助手 Web UI
基于Streamlit的交互式界面
优化版本：移除调试代码，移向后端逻辑，提升性能
"""

import streamlit as st
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 添加 ai_researcher 目录到路径（用于页面模块导入）
ai_researcher_dir = Path(__file__).parent.parent
sys.path.insert(0, str(ai_researcher_dir))

# Streamlit页面配置 - 优化性能
st.set_page_config(
    page_title="AI科研助手",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None,  # 隐藏Streamlit菜单
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        padding: 1rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# 侧边栏导航 - 性能优化
st.sidebar.title("🔬 AI科研助手")

# 简化Logo显示
st.sidebar.markdown("#### 版本 v1.0", help="AI科研助手主界面")

# 缓存API状态检查（避免重复加载）
@st.cache_data(ttl=300)  # 5分钟缓存
def get_api_status():
    """获取API配置状态 - 带缓存"""
    try:
        from ai_researcher.secrets_manager import check_api_keys
        return check_api_keys()
    except Exception:
        return {}

api_status = get_api_status()

# 显示API状态（简化）
if api_status:
    st.sidebar.success("✅ 已配置")
else:
    st.sidebar.info("ℹ️ 首次使用请先配置")

# 页面导航
pages = {
    "🏠 首页": "home",
    "🔬 创建实验": "experiment_create",
    "📋 实验列表": "experiment_list",
    "📊 结果分析": "result_analysis",
    "📝 模板管理": "templates",
    "💾 备份恢复": "backup",
    "⚙️ 配置管理": "config"
}

selected_page = st.sidebar.radio("请选择功能", list(pages.keys()))

# =============== 页面路由 - 优化版 ===============

# 页面映射 - 所有模块都是run()函数
PAGE_IMPORTS = {
    "home": "web_ui.home",
    "experiment_create": "web_ui.experiment_create",
    "experiment_list": "web_ui.experiment_list",
    "result_analysis": "web_ui.result_analysis",
    "templates": "web_ui.templates",
    "backup": "web_ui.backup",
    "config": "web_ui.config",
}

# 动态加载页面（仅在选择时加载）
selected_module = pages[selected_page]

if selected_module in PAGE_IMPORTS:
    module_name = PAGE_IMPORTS[selected_module]
    try:
        # 动态导入模块
        module = __import__(module_name, fromlist=["run"])
        # 所有模块都有run()函数
        module.run()
    except ImportError as e:
        st.error(f"❌ 无法加载页面模块: {module_name}")
        st.info(f"错误详情: {str(e)[:100]}")
    except AttributeError as e:
        st.error(f"❌ 页面函数缺失: {module_name}")
        st.info(f"错误详情: {str(e)[:100]}")
    except Exception as e:
        st.error(f"❌ 页面执行错误: {str(e)[:100]}")
else:
    st.error("❌ 页面不存在")
