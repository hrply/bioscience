#!/bin/bash

# 生物信息学数据管理系统 Docker 容器启动脚本

# 设置颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}生物信息学数据管理系统 Docker 容器启动中...${NC}"

# 设置环境变量默认值
export BIODATA_BASE_DIR=${BIODATA_BASE_DIR:-"/bioraw/data"}
export BIODATA_DOWNLOAD_DIR=${BIODATA_DOWNLOAD_DIR:-"/bioraw/downloads"}
export BIODATA_RESULTS_DIR=${BIODATA_RESULTS_DIR:-"/bioraw/results"}
export BIODATA_ANALYSIS_DIR=${BIODATA_ANALYSIS_DIR:-"/bioraw/analysis"}
export BIODATA_USE_MOVE_MODE=${BIODATA_USE_MOVE_MODE:-"true"}

# 确保必要的目录存在
echo -e "${YELLOW}检查并创建必要的目录...${NC}"
mkdir -p "$BIODATA_BASE_DIR"
mkdir -p "$BIODATA_DOWNLOAD_DIR"
mkdir -p "$BIODATA_RESULTS_DIR"
mkdir -p "$BIODATA_ANALYSIS_DIR"

# 设置正确的权限
chmod 755 "$BIODATA_BASE_DIR"
chmod 755 "$BIODATA_DOWNLOAD_DIR"
chmod 755 "$BIODATA_RESULTS_DIR"
chmod 755 "$BIODATA_ANALYSIS_DIR"

# 检查端口设置
PORT=${PORT:-8000}
echo -e "${GREEN}服务器端口: $PORT${NC}"
echo -e "${GREEN}数据目录: $BIODATA_BASE_DIR${NC}"
echo -e "${GREEN}下载目录: $BIODATA_DOWNLOAD_DIR${NC}"
echo -e "${GREEN}处理结果目录: $BIODATA_RESULTS_DIR${NC}"
echo -e "${GREEN}分析数据目录: $BIODATA_ANALYSIS_DIR${NC}"

# 显示存储模式
if [ "$BIODATA_USE_MOVE_MODE" = "true" ]; then
    echo -e "${GREEN}存储模式: 安全移动模式（先复制后删除，节省空间且保证数据安全）${NC}"
else
    echo -e "${YELLOW}存储模式: 复制模式（保留原始文件，占用更多空间）${NC}"
fi

# 启动服务器
echo -e "${GREEN}启动生物信息学数据管理系统服务器...${NC}"
echo -e "${YELLOW}访问地址: http://localhost:$PORT${NC}"
echo -e "${YELLOW}按 Ctrl+C 停止服务器${NC}"

# 执行Python服务器
cd /app

# 检查是否为开发环境（代码挂载模式）
if [ -f "/app/server.py" ]; then
    echo -e "${GREEN}检测到开发环境，启用代码热重载模式${NC}"
    echo -e "${YELLOW}提示: 修改Python代码后服务器会自动重载，修改HTML/CSS/JS文件后请刷新浏览器${NC}"
    # 使用Python的简单重载脚本
    python3 -c "
import os
import sys
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_restart = 0
        
    def on_modified(self, event):
        if event.is_directory:
            return
        
        # 只监控Python文件变化来重载服务器
        if event.src_path.endswith('.py'):
            current_time = time.time()
            # 防止频繁重启（至少间隔2秒）
            if current_time - self.last_restart > 2:
                print(f'检测到Python文件变化: {event.src_path}')
                print('服务器将在2秒后重启...')
                self.last_restart = current_time
                time.sleep(2)
                print('服务器重启中...')
                os.execl(sys.executable, sys.executable, *sys.argv)

if __name__ == '__main__':
    # 设置文件监控
    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path='/app', recursive=True)
    observer.start()
    
    try:
        # 启动服务器
        subprocess.run([sys.executable, 'server.py'] + sys.argv[1:])
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
" "$PORT"
else
    # 生产环境模式
    python3 server.py "$PORT"
fi