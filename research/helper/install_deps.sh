#!/bin/bash

echo "🔬 实验记录智能助手 - 依赖安装脚本"
echo "=================================="

# 检测环境
if command -v conda &> /dev/null; then
    echo "✅ 检测到conda环境"
    CONDA_ENV=$(conda info --envs | grep '*' | awk '{print $1}')
    echo "📍 当前conda环境: $CONDA_ENV"
    PYTHON_CMD="python"
    PIP_CMD="pip"
elif command -v python3 &> /dev/null; then
    echo "✅ 使用系统Python3"
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
else
    echo "❌ 未找到Python环境"
    exit 1
fi

# 检查Python版本
python_version=$($PYTHON_CMD --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+')
echo "✅ Python版本: $python_version"

# 检查pip路径
pip_path=$($PIP_CMD show pip | grep Location | awk '{print $2}')
echo "📍 pip安装路径: $pip_path"

# 确认不会安装到系统目录
if [[ "$pip_path" == "/usr"* ]]; then
    echo "⚠️ 警告: 检测到系统pip，建议使用conda环境或虚拟环境"
    read -p "是否继续安装? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 安装已取消"
        exit 1
    fi
fi

# 升级pip（仅限当前环境）
echo "⬆️ 升级pip..."
$PIP_CMD install --upgrade pip --no-warn-script-location

# 安装核心依赖
echo "📚 安装核心依赖..."

# 分步安装，便于排查问题
echo "📚 安装核心依赖..."

echo "  安装 streamlit..."
$PIP_CMD install streamlit>=1.28.0 --no-warn-script-location

echo "  安装 pydantic..."
$PIP_CMD install pydantic>=2.0.0 --no-warn-script-location

echo "  安装 python-dotenv..."
$PIP_CMD install python-dotenv>=1.0.0 --no-warn-script-location

echo "  安装 requests..."
$PIP_CMD install requests>=2.31.0 --no-warn-script-location

echo "  安装 yaml..."
$PIP_CMD install pyyaml>=6.0 --no-warn-script-location

echo "  安装 markdown..."
$PIP_CMD install markdown>=3.4.0 --no-warn-script-location

echo "  安装 dateutil..."
$PIP_CMD install python-dateutil>=2.8.0 --no-warn-script-location

echo "  安装 pytest..."
$PIP_CMD install pytest>=7.4.0 --no-warn-script-location

echo "  安装 psutil..."
$PIP_CMD install psutil>=5.9.0 --no-warn-script-location

# 可选依赖（如果失败不影响核心功能）
echo "🔧 尝试安装可选依赖..."

echo "  安装 chromadb..."
$PIP_CMD install chromadb>=0.4.0 --no-warn-script-location || echo "⚠️ chromadb 安装失败，将使用基础功能"

echo "  安装 Pillow..."
$PIP_CMD install Pillow>=10.0.0 --no-warn-script-location || echo "⚠️ Pillow 安装失败，图像功能将受限"

echo "  安装 pypdf2..."
$PIP_CMD install pypdf2>=3.0.0 --no-warn-script-location || echo "⚠️ pypdf2 安装失败，PDF功能将受限"

# 验证安装
echo ""
echo "🔍 验证安装..."

echo "  检查 streamlit..."
if $PYTHON_CMD -c "import streamlit; print(f'Streamlit版本: {streamlit.__version__}')" 2>/dev/null; then
    echo "✅ streamlit 安装成功"
else
    echo "❌ streamlit 安装失败"
fi

echo "  检查 pydantic..."
if $PYTHON_CMD -c "import pydantic; print(f'Pydantic版本: {pydantic.__version__}')" 2>/dev/null; then
    echo "✅ pydantic 安装成功"
else
    echo "❌ pydantic 安装失败"
fi

# 显示安装路径
echo ""
echo "📍 安装信息:"
echo "  Python路径: $($PYTHON_CMD -c 'import sys; print(sys.executable)')"
echo "  包安装路径: $($PYTHON_CMD -c 'import site; print(site.getsitepackages()[0])')"

echo ""
echo "✅ 依赖安装完成！"
echo ""
echo "📝 接下来请："
echo "1. 配置API密钥: export QWEN_API_KEY=your_key"
echo "2. 启动应用: streamlit run main.py"
echo ""
echo "🎯 Conda环境使用提示:"
echo "- 激活环境: conda activate your_env_name"
echo "- 查看环境: conda info --envs"
echo "- 安装包仅限于当前conda环境，不会影响系统"
echo ""
echo "如果遇到问题，请尝试："
echo "- 使用国内镜像: pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ 包名"
echo "- 更新conda: conda update conda"