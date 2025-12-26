.PHONY: help build up down logs clean restart shell

# 默认目标
help: ## 显示帮助信息
	@echo "文献深度挖掘助手 - Docker命令"
	@echo ""
	@echo "可用命令:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## 构建Docker镜像
	docker-compose build

up: ## 启动所有服务
	docker-compose up -d

up-local: ## 启动包含本地大模型的服务
	docker-compose --profile local-llm up -d

down: ## 停止所有服务
	docker-compose down

logs: ## 查看应用日志
	docker-compose logs -f literature-miner

logs-ragflow: ## 查看RAGFlow日志
	docker-compose logs -f ragflow

logs-all: ## 查看所有服务日志
	docker-compose logs -f

restart: ## 重启应用
	docker-compose restart literature-miner

restart-all: ## 重启所有服务
	docker-compose restart

shell: ## 进入应用容器
	docker exec -it literature-miner /bin/bash

shell-ragflow: ## 进入RAGFlow容器
	docker exec -it ragflow /bin/bash

status: ## 查看服务状态
	docker-compose ps

clean: ## 清理Docker资源
	docker-compose down -v
	docker system prune -f

pull: ## 拉取最新镜像
	docker-compose pull

update: ## 更新并重启服务
	git pull
	docker-compose up -d --build

install-ollama: ## 在Ollama中安装模型（需要先启动local-llm）
	docker exec -it ollama ollama pull llama2

dev: ## 开发模式启动（挂载源码）
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 环境检查
check-env: ## 检查环境配置
	@if [ ! -f .env ]; then \
		echo "❌ 未找到.env文件，请复制.env.example并配置"; \
		exit 1; \
	fi
	@echo "✅ 环境配置文件存在"

# 数据备份
backup: ## 备份数据
	mkdir -p backups
	docker run --rm -v ragflow_data:/data -v $(pwd)/backups:/backup alpine tar czf /backup/ragflow_data_$(shell date +%Y%m%d_%H%M%S).tar.gz -C /data .
	@echo "✅ 数据备份完成"

# 初始化项目（可选）
init: ## 初始化项目（首次运行）
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ 已创建.env文件，请编辑配置后运行 'make up'"; \
	else \
		echo "✅ .env文件已存在"; \
	fi