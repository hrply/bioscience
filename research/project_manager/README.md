# AI科研助手 (AI Research Assistant)

> 基于大语言模型的智能科研实验设计、进度管理与结果分析系统

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-Web%20UI-red.svg)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docker.com)

## 🎯 项目概述

**AI科研助手**是一个基于大语言模型的智能科研系统，支持：
- 📚 RAGFlow知识库检索与实验设计
- 🤖 多模型支持（OpenAI、Claude、Gemini、iFlow等）
- 📊 实验进度管理与结果分析
- 🎨 Web UI和CLI双重交互
- 🔍 数据可视化与AI解释

### 核心特性

- **多模型统一API**: 支持OpenAI、Claude、Gemini、iFlow等多种模型
- **RAGFlow集成**: 基于知识库的智能实验设计
- **模板系统**: 9种内置实验模板
- **进度跟踪**: 实时监控实验进度
- **结果分析**: 数据可视化与AI解读
- **Docker部署**: 一键启动所有服务

## 🚀 快速开始

### Docker部署（推荐）

```bash
# 1. 克隆并配置
git clone <repository>
cd ai_researcher
cp .env.example .env
# 编辑.env添加API密钥

# 2. 启动服务
docker-compose up -d

# 3. 访问Web UI
# http://localhost:20339
```

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境
export OPENAI_API_KEY=your_key
export RAGFLOW_ENDPOINT=http://192.168.3.147:20334

# 启动Web UI
streamlit run ai_researcher/web_ui/main.py
```

## ⚙️ 系统架构

```
┌─────────────────────────────────────────┐
│           Web UI (Streamlit)            │
├─────────────────────────────────────────┤
│           Core Engine                   │
│  ┌─────────────┬────────────────────┐  │
│  │ RAGFlow KB  │  Model System      │  │
│  │   Client    │  (OpenAI/Claude)   │  │
│  └─────────────┴────────────────────┘  │
├─────────────────────────────────────────┤
│      Services (Redis/MongoDB)           │
└─────────────────────────────────────────┘
```

### 核心模块

| 模块 | 路径 | 功能 |
|------|------|------|
| **core** | `ai_researcher/core/` | 核心协调层 |
| ├─ agent.py | 主控制器 |
| ├─ ragflow.py | RAGFlow集成 |
| └─ models/ | 模型接口 |
| **web_ui** | `ai_researcher/web_ui/` | Web界面 |
| ├─ main.py | 主入口 |
| ├─ config.py | 配置管理 |
| └─ experiment_create.py | 实验创建 |
| **experiments** | `ai_researcher/experiments/` | 实验管理 |
| **templates** | `ai_researcher/templates/` | 模板系统 |
| **results** | `ai_researcher/results/` | 结果分析 |

## 🔧 配置指南

### 环境变量

必需配置：
```bash
# 至少配置一个模型提供商
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
GEMINI_API_KEY=your_key

# Token（加密密钥）
TOKEN=your_secure_password
```

RAGFlow知识库配置：
```bash
# RAGFlow服务端点
RAGFLOW_ENDPOINT=http://192.168.3.147:20334

# Docker端口映射（需与RAGFlow一致）
SVR_HTTP_PORT=20335
SVR_WEB_HTTP_PORT=20334
SVR_MCP_PORT=20337
```

代理配置（如需）：
```bash
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
NO_PROXY=localhost,127.0.0.1
```

### Web UI配置

1. 访问 `http://localhost:20339`
2. 进入「配置管理」
3. 配置API密钥和端点
4. 设置RAGFlow端口映射
5. 测试连接并保存

## 🐳 Docker部署

### 服务架构

```yaml
services:
  ai_researcher:  # 主应用
  redis:          # 缓存
  mongodb:        # 数据库
```

### 常用命令

```bash
# 启动
docker-compose up -d

# 查看日志
docker-compose logs -f ai_researcher

# 重启
docker-compose restart ai_researcher

# 停止
docker-compose down

# 进入容器
docker-compose exec ai_researcher bash

# 测试导入
docker-compose exec ai_researcher python -c "from ai_researcher.config import save_config; print('✅ OK')"
```

### 数据持久化

```yaml
volumes:
  - ai_researcher_data:/app/data      # 实验数据
  - ai_researcher_chroma:/app/chroma # 向量数据库
  - ai_researcher_uploads:/app/uploads # 上传文件
  - ./logs:/app/logs                  # 日志
  - ./backup:/backup                  # 备份
```

## 📚 RAGFlow配置

### 1. 确认RAGFlow服务

```bash
# 检查进程
ps aux | grep ragflow

# 检查端口
netstat -tuln | grep -E "20334|20335|20336|20337"
```

### 2. 配置端口映射

| 变量 | 默认值 | 用途 |
|------|--------|------|
| SVR_HTTP_PORT | 20335 | API调用端口 |
| SVR_WEB_HTTP_PORT | 20334 | Web界面端口 |
| SVR_MCP_PORT | 20337 | MCP服务端口 |

⚠️ **重要**: 端口需与RAGFlow docker-compose.yml完全一致！

### 3. 测试连接

```python
from ai_researcher.core.ragflow import RAGFlowClient

client = RAGFlowClient(
    endpoint='http://192.168.3.147:20334',
    ports={
        'SVR_HTTP_PORT': 20335,
        'SVR_WEB_HTTP_PORT': 20334,
    }
)

print("Health:", client.health_check())
datasets = client.list_datasets()
print("Datasets:", len(datasets))
```

## 🤖 模型系统

### 支持的提供商

| 提供商 | API格式 | 路径 |
|--------|---------|------|
| OpenAI | chat | /v1/chat/completions |
| Claude | messages | /v1/messages |
| Gemini | generateContent | /v1/generateContent |
| iFlow | chat | /v1/chat/completions |

### NEW-API代理

统一代理，自动根据模型名选择API格式：
- 含`gpt/openai` → chat
- 含`claude/anthropic` → messages  
- 含`gemini/google` → generateContent

```python
# 配置NEW-API
base_url = "https://your-api-proxy.com"
model_name = "gpt-4"  # 自动选择chat格式
```

## 📊 实验模板

内置9种实验类型：
1. **Cell Culture** - 细胞培养
2. **PCR Protocol** - PCR扩增
3. **Western Blot** - 蛋白印迹
4. **Flow Cytometry** - 流式细胞术
5. **Microscopy** - 显微观察
6. **ELISA** - 酶联免疫
7. **DNA Sequencing** - DNA测序
8. **Protein Purification** - 蛋白纯化
9. **Custom** - 自定义

使用方式：
```bash
# CLI创建实验
ai-researcher create --model-provider openai --model-name gpt-4 "研究目标描述"

# Web UI选择模板
# 实验创建 → 选择模板 → 填写参数 → 生成方案
```

## 🔍 结果分析

支持数据可视化：
- 📈 趋势分析图
- 📊 统计分布图
- 🔬 实验对比图
- 📋 数据表格

AI解读：
- 自动解释结果
- 发现异常模式
- 提供改进建议
- 生成分析报告

## 🧪 测试

### 完整测试套件

```bash
# 运行所有测试
python test_unified_api.py
python test_new_api.py
python test_proxy.py
python test_ragflow_config.py
python test_ragflow_sdk.py
```

### 专项测试

```bash
# 测试RAGFlow连接
python -c "
from ai_researcher.core.ragflow import RAGFlowClient
c = RAGFlowClient(endpoint='http://192.168.3.147:20334')
print('Health:', c.health_check())
"

# 测试模型配置
python -c "
from ai_researcher.models.config_manager import ModelConfigManager
m = ModelConfigManager()
print('Configs:', m.list_configs())
"
```

## 🛠️ 故障排除

### 常见问题

#### 1. 导入错误
```
ImportError: cannot import name 'save_config'
```
**解决**: 确保PYTHONPATH正确
```bash
# 检查Docker配置
docker-compose exec ai_researcher python -c "import sys; print(sys.path)"
```

#### 2. RAGFlow连接失败
```
Connection refused
```
**解决**: 
- 检查RAGFlow服务状态
- 确认端口映射正确
- 验证防火墙设置

#### 3. API密钥无效
```
Authentication error: API key is invalid
```
**解决**:
- 检查API密钥是否正确
- 确认账户有足够额度
- 验证代理设置

#### 4. 数据库错误
```
sqlite3.OperationalError
```
**解决**:
```bash
# 重建数据库
docker-compose restart mongodb
# 或
rm -f data/experiments/experiments.db
```

### 日志查看

```bash
# 应用日志
docker-compose logs -f ai_researcher

# 特定模块
docker-compose exec ai_researcher tail -f /app/logs/ragflow.log

# 所有服务
docker-compose logs
```

## 📝 备份与恢复

### 自动备份

```bash
# 备份脚本
./scripts/backup.sh

# 备份内容
- 实验数据库
- 向量索引
- 上传文件
- 配置文件
```

### 手动备份

```bash
# 停止服务
docker-compose down

# 备份数据目录
cp -r data/ backup/data_$(date +%Y%m%d)

# 或使用Docker卷备份
docker run --rm -v ai_researcher_data:/data -v $(pwd)/backup:/backup alpine tar czf /backup/data_$(date +%Y%m%d).tar.gz /data
```

### 恢复

```bash
# 停止服务
docker-compose down

# 恢复数据
cp backup/data_20240109/* data/

# 重启服务
docker-compose up -d
```

## 🔒 安全注意事项

1. **API密钥**: 
   - 使用环境变量存储
   - 定期轮换密钥
   - 监控使用量

2. **Token**:
   - 用于配置加密
   - 必须强密码
   - 不要泄露

3. **代理**:
   - 验证代理安全性
   - 监控流量
   - 敏感操作避免代理

4. **网络**:
   - 限制访问IP
   - 使用HTTPS
   - 防火墙保护

## 📈 性能优化

1. **RAGFlow**:
   - 启用查询缓存
   - 优化索引
   - 批量处理

2. **数据库**:
   - 添加索引
   - 定期清理
   - 连接池

3. **模型调用**:
   - 启用流式响应
   - 缓存结果
   - 批量请求

## 🤝 贡献指南

1. Fork项目
2. 创建特性分支
3. 提交变更
4. 推送到分支
5. 创建Pull Request

### 开发规范

- 遵循PEP8
- 添加类型提示
- 编写docstring
- 更新测试
- 保持向后兼容

## 📄 许可证

MIT License

## 🆘 支持

- 📧 Issues: 提交Bug报告
- 💬 Discussions: 讨论功能
- 📖 Wiki: 查看文档
- 📧 Email: 技术支持

## 🎉 致谢

- [RAGFlow](https://ragflow.io) - 知识库引擎
- [Streamlit](https://streamlit.io) - Web UI框架
- [OpenAI](https://openai.com) - 大语言模型
- [Anthropic](https://anthropic.com) - Claude模型

---

**AI科研助手** - 让科研更智能 🚀
