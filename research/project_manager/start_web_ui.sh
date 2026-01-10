#!/bin/bash
# AI科研助手 Web UI 启动脚本

echo "=================================="
echo "  AI科研助手 Web UI 启动脚本"
echo "=================================="
echo ""

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ 错误: Docker未运行或未安装"
    echo "请先启动Docker"
    exit 1
fi

# 检查docker-compose是否可用
if ! command -v docker-compose &> /dev/null; then
    echo "❌ 错误: docker-compose未安装"
    echo "请安装docker-compose"
    exit 1
fi

# 读取环境变量（如果存在）
if [ -f ".env" ]; then
    echo "✓ 加载环境变量文件 .env"
    export $(grep -v '^#' .env | xargs)
fi

echo "1. 构建Docker镜像..."
docker-compose build

echo ""
echo "2. 启动服务..."
docker-compose up -d

echo ""
echo "✓ AI科研助手 Web UI 已启动！"
echo ""
echo "访问地址: http://localhost:${APP_PORT:-20339}"
echo ""
echo "常用命令:"
echo "  - 查看日志: docker-compose logs -f"
echo "  - 停止服务: docker-compose down"
echo ""
