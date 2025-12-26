#!/bin/bash

# 文献深度挖掘助手启动脚本

echo "🚀 启动文献深度挖掘助手..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "📋 Python版本: $python_version"

# 检查是否在虚拟环境中
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ 检测到虚拟环境: $VIRTUAL_ENV"
else
    echo "⚠️  建议在虚拟环境中运行"
    echo "💡 创建虚拟环境: python3 -m venv venv && source venv/bin/activate"
fi

# 检查依赖
echo "📦 检查依赖..."
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "❌ 缺少streamlit依赖"
    echo "💡 安装依赖: pip install -r requirements.txt"
    exit 1
fi

if ! python3 -c "import requests" 2>/dev/null; then
    echo "❌ 缺少requests依赖"
    echo "💡 安装依赖: pip install -r requirements.txt"
    exit 1
fi

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到.env配置文件"
    echo "💡 创建配置文件: cp .env.example .env"
    echo "📝 然后编辑.env文件，填入您的API密钥"
fi

# 设置环境变量
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 启动应用
echo "🌐 启动Web应用..."
echo "📍 访问地址: http://localhost:8501"
echo "🔄 如需修改端口，使用: streamlit run src/main.py --server.port 8502"

# 启动streamlit
streamlit run src/main.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless false \
    --browser.gatherUsageStats false \
    --theme.base light

echo "👋 应用已关闭"