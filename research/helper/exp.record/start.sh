#!/bin/bash

# 实验记录智能助手 - 快速启动脚本

echo "🔬 实验记录智能助手启动脚本"
echo "================================"

# 检查Python版本
python_version=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ 错误: 需要Python 3.10或更高版本，当前版本: $python_version"
    exit 1
fi

echo "✅ Python版本检查通过: $python_version"

# 检查并创建虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "⬆️ 升级pip..."
pip install --upgrade pip

# 安装依赖
echo "📚 安装依赖包..."
pip install -r requirements.txt

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "⚠️ 警告: 未找到.env文件"
    echo "📝 复制示例配置文件..."
    cp .env.example .env
    echo "🔧 请编辑 .env 文件并配置您的API密钥"
    echo "   主要配置项: QWEN_API_KEY"
fi

# 检查API密钥
if [ -z "$QWEN_API_KEY" ]; then
    echo "⚠️ 警告: 未设置QWEN_API_KEY环境变量"
    echo "🔧 请设置API密钥: export QWEN_API_KEY=your_key_here"
    echo "   或编辑 .env 文件"
fi

# 创建数据目录
echo "📁 创建数据目录..."
mkdir -p ~/.lab_notebook_agent/{templates,backups,vector_db}

echo ""
echo "🚀 启动应用..."
echo "📱 浏览器将自动打开 http://localhost:8501"
echo "🛑 按 Ctrl+C 停止应用"
echo ""

# 启动Streamlit应用
streamlit run main.py --server.port 8501 --server.headless false