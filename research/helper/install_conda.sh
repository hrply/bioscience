#!/bin/bash

echo "🔬 实验记录智能助手 - Conda环境安装脚本"
echo "======================================="

# 检查conda是否可用
if ! command -v conda &> /dev/null; then
    echo "❌ 未找到conda，请先安装Anaconda或Miniconda"
    exit 1
fi

echo "✅ Conda已安装"

# 显示conda信息
echo "📍 Conda信息:"
conda info

# 创建新的conda环境（可选）
ENV_NAME="lab_notebook_agent"
echo ""
echo "🤔 是否创建新的conda环境 '$ENV_NAME'？"
echo "  - 选择 'y': 创建新环境（推荐）"
echo "  - 选择 'n': 使用当前环境"
read -p "创建新环境? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📦 创建新的conda环境: $ENV_NAME"
    conda create -n $ENV_NAME python=3.10 -y
    echo "✅ 环境创建成功"
    echo "🔄 激活新环境..."
    source $(conda info --base)/etc/profile.d/conda.sh
    conda activate $ENV_NAME
    echo "✅ 环境已激活: $ENV_NAME"
else
    echo "📍 使用当前conda环境"
    ENV_NAME=$(conda info --envs | grep '*' | awk '{print $1}')
    echo "当前环境: $ENV_NAME"
fi

# 显示当前Python路径
echo ""
echo "📍 Python环境信息:"
which python
python --version

# 显示pip路径
echo ""
echo "📍 pip路径:"
which pip
pip --version

# 确认安装路径不是系统目录
pip_path=$(pip show pip | grep Location | awk '{print $2}')
echo ""
echo "📍 包安装路径: $pip_path"

if [[ "$pip_path" == "/usr"* ]]; then
    echo "⚠️ 警告: 检测到系统路径，建议使用conda环境"
    read -p "是否继续? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 安装已取消"
        exit 1
    fi
else
    echo "✅ 安装路径正确，仅在conda环境中"
fi

# 安装依赖
echo ""
echo "📚 开始安装依赖包..."

# 使用conda安装核心包（如果可用）
echo "🔧 尝试使用conda安装核心包..."
conda install -c conda-forge requests pyyaml -y || echo "⚠️ conda安装部分包失败，将使用pip"

# 使用pip安装其余包
echo "📦 使用pip安装streamlit等包..."
pip install --no-warn-script-location streamlit>=1.28.0
pip install --no-warn-script-location pydantic>=2.0.0
pip install --no-warn-script-location python-dotenv>=1.0.0
pip install --no-warn-script-location markdown>=3.4.0
pip install --no-warn-script-location python-dateutil>=2.8.0

# 可选包
echo "🔧 安装可选包..."
pip install --no-warn-script-location pytest>=7.4.0 || echo "⚠️ pytest安装失败"
pip install --no-warn-script-location psutil>=5.9.0 || echo "⚠️ psutil安装失败"
pip install --no-warn-script-location Pillow>=10.0.0 || echo "⚠️ Pillow安装失败"
pip install --no-warn-script-location pypdf2>=3.0.0 || echo "⚠️ pypdf2安装失败"
pip install --no-warn-script-location chromadb>=0.4.0 || echo "⚠️ chromadb安装失败"

# 验证安装
echo ""
echo "🔍 验证关键包安装..."

packages=("streamlit" "pydantic" "requests" "yaml")
for package in "${packages[@]}"; do
    if python -c "import $package" 2>/dev/null; then
        echo "✅ $package 安装成功"
    else
        echo "❌ $package 安装失败"
    fi
done

# 显示环境信息
echo ""
echo "📋 环境安装总结:"
echo "  Conda环境: $ENV_NAME"
echo "  Python路径: $(which python)"
echo "  包安装路径: $pip_path"

echo ""
echo "✅ 安装完成！"
echo ""
echo "🚀 启动应用:"
echo "1. 确保环境激活: conda activate $ENV_NAME"
echo "2. 配置API密钥: export QWEN_API_KEY=your_key"
echo "3. 启动应用: streamlit run main.py"
echo ""
echo "📝 后续使用:"
echo "- 激活环境: conda activate $ENV_NAME"
echo "- 退出环境: conda deactivate"
echo "- 查看环境: conda info --envs"