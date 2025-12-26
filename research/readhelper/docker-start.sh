#!/bin/bash

# 文献深度挖掘助手 - Docker启动脚本

echo "🐳 文献深度挖掘助手 - Docker启动脚本"
echo "=================================="

# 检查Docker和Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 检查.env文件
if [ ! -f .env ]; then
    echo "📝 创建.env配置文件..."
    cp .env.example .env
    echo "✅ 已创建.env文件，请编辑配置后重新运行"
    echo "💡 编辑命令: nano .env"
    exit 0
fi

# 解析命令行参数
COMMAND=${1:-"up"}

case $COMMAND in
    "up")
        echo "🚀 启动所有服务..."
        docker-compose up -d
        echo ""
        echo "✅ 服务启动完成！"
        echo "📱 文献挖掘助手: http://localhost:8501"
        echo "🔧 RAGFlow管理界面: http://localhost:9380"
        ;;
    
    "up-local")
        echo "🚀 启动包含本地大模型的服务..."
        docker-compose --profile local-llm up -d
        echo ""
        echo "✅ 服务启动完成！"
        echo "📱 文献挖掘助手: http://localhost:8501"
        echo "🔧 RAGFlow管理界面: http://localhost:9380"
        echo "🤖 本地大模型API: http://localhost:11434"
        ;;
    
    "down")
        echo "🛑 停止所有服务..."
        docker-compose down
        echo "✅ 服务已停止"
        ;;
    
    "restart")
        echo "🔄 重启应用服务..."
        docker-compose restart literature-miner
        echo "✅ 应用已重启"
        ;;
    
    "logs")
        echo "📋 查看应用日志..."
        docker-compose logs -f literature-miner
        ;;
    
    "status")
        echo "📊 服务状态:"
        docker-compose ps
        ;;
    
    "shell")
        echo "🐚 进入应用容器..."
        docker exec -it literature-miner /bin/bash
        ;;
    
    "clean")
        echo "🧹 清理Docker资源..."
        docker-compose down -v
        docker system prune -f
        echo "✅ 清理完成"
        ;;
    
    "help"|*)
        echo "使用方法: $0 [命令]"
        echo ""
        echo "可用命令:"
        echo "  up        - 启动所有服务（默认）"
        echo "  up-local  - 启动包含本地大模型的服务"
        echo "  down      - 停止所有服务"
        echo "  restart   - 重启应用服务"
        echo "  logs      - 查看应用日志"
        echo "  status    - 查看服务状态"
        echo "  shell     - 进入应用容器"
        echo "  clean     - 清理Docker资源"
        echo "  help      - 显示此帮助信息"
        ;;
esac