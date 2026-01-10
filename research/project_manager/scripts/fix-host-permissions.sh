#!/bin/bash
# 宿主机权限修复脚本
# 用于修复Docker项目中需要挂载到容器的文件权限
# 确保Docker可以正确读取和运行这些文件

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录（相对于此脚本的位置）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${YELLOW}=== Docker项目权限修复工具 ===${NC}"
echo "项目根目录: $PROJECT_ROOT"
echo ""

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 1. 修复配置文件的权限
echo -e "${GREEN}[1/4] 修复配置文件权限...${NC}"
CONFIG_DIR="$PROJECT_ROOT/config"
if [ -d "$CONFIG_DIR" ]; then
    echo "扫描配置文件目录: $CONFIG_DIR"
    find "$CONFIG_DIR" -type f -name "*.conf" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" | while read -r file; do
        echo "  设置权限: $file"
        # 设置文件为644权限（所有者读写，组和其他用户只读）
        chmod 644 "$file"
    done
else
    echo -e "${YELLOW}  配置文件目录不存在: $CONFIG_DIR${NC}"
fi

# 2. 修复脚本文件的权限
echo -e "${GREEN}[2/4] 修复脚本文件权限...${NC}"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"
if [ -d "$SCRIPTS_DIR" ]; then
    echo "扫描脚本目录: $SCRIPTS_DIR"
    find "$SCRIPTS_DIR" -type f \( -name "*.sh" -o -name "*.js" \) | while read -r file; do
        echo "  设置权限: $file"
        # 设置脚本为755权限（所有者读写执行，组和其他用户读执行）
        chmod 755 "$file"
    done
else
    echo -e "${YELLOW}  脚本目录不存在: $SCRIPTS_DIR${NC}"
fi

# 3. 修复Docker相关文件的权限
echo -e "${GREEN}[3/4] 修复Docker相关文件权限...${NC}"
DOCKER_FILES=(
    "Dockerfile"
    "docker-compose.yml"
    "docker-compose.prod.yml"
    ".dockerignore"
)
for file in "${DOCKER_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        echo "  设置权限: $file"
        chmod 644 "$PROJECT_ROOT/$file"
    fi
done

# 4. 修复示例和模板文件权限
echo -e "${GREEN}[4/4] 修复示例和模板文件权限...${NC}"
TEMPLATE_DIRS=(
    "templates"
    "examples"
)
for dir in "${TEMPLATE_DIRS[@]}"; do
    TEMPLATE_PATH="$PROJECT_ROOT/$dir"
    if [ -d "$TEMPLATE_PATH" ]; then
        echo "扫描目录: $TEMPLATE_PATH"
        find "$TEMPLATE_PATH" -type f | while read -r file; do
            echo "  设置权限: $file"
            chmod 644 "$file"
        done
    fi
done

# 5. 创建权限检查报告
echo ""
echo -e "${YELLOW}=== 权限修复完成，生成报告 ===${NC}"

REPORT_FILE="$PROJECT_ROOT/permission-report.txt"
echo "权限修复报告 - $(date)" > "$REPORT_FILE"
echo "========================================" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "配置文件权限:" >> "$REPORT_FILE"
ls -lh "$PROJECT_ROOT/config/" 2>/dev/null | grep -v "^total" >> "$REPORT_FILE" || echo "  无配置文件" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "脚本文件权限:" >> "$REPORT_FILE"
ls -lh "$PROJECT_ROOT/scripts/" 2>/dev/null | grep -v "^total" >> "$REPORT_FILE" || echo "  无脚本文件" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "Docker文件权限:" >> "$REPORT_FILE"
for file in "${DOCKER_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        ls -lh "$PROJECT_ROOT/$file" >> "$REPORT_FILE"
    fi
done

echo ""
echo -e "${GREEN}权限修复完成！${NC}"
echo -e "${YELLOW}报告已保存到: $REPORT_FILE${NC}"
echo ""
echo -e "${YELLOW}现在可以启动Docker容器:${NC}"
echo -e "  ${GREEN}docker-compose up -d${NC}"
echo ""

# 可选：自动启动容器
read -p "是否现在启动Docker容器? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}启动Docker容器...${NC}"
    docker-compose up -d
    echo ""
    echo -e "${GREEN}容器状态:${NC}"
    docker-compose ps
fi
