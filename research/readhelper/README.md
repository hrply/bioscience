# 文献深度挖掘助手

一个基于RAGFlow和大模型技术的智能文献分析平台，专为生物科学研究人员设计，帮助深度挖掘文献价值，发现研究趋势和知识空白。

## 🌟 核心特性

- **📚 文献库管理**: 连接RAGFlow，管理您的文献集合
- **🔍 智能搜索**: 基于语义的文献搜索和检索
- **⛏️ 深度挖掘**: AI驱动的文献深度分析和洞察
- **📊 趋势分析**: 研究趋势识别和知识图谱构建
- **💡 智能推荐**: 基于分析结果的研究建议
- **🌐 研究网络**: 作者合作、机构关联、主题网络分析
- **🔄 概念演化**: 关键概念的历史发展轨迹分析

## 🚀 快速开始

### 环境要求

- Python 3.8+
- RAGFlow服务
- 大模型API（OpenAI、通义千问、Claude或本地模型）

### 安装步骤

#### 方法1：Docker部署（推荐）

1. **克隆项目**
```bash
git clone <repository-url>
cd bioscience/research/readhelper
```

2. **启动服务**
```bash
# 直接使用Docker Compose
docker-compose up -d

# 如果需要本地大模型支持
docker-compose --profile local-llm up -d
```

3. **访问应用**
- 文献挖掘助手: http://localhost:20422
- RAGFlow管理界面: http://localhost:9380

**注意**: 确保 .env 配置文件已正确设置API密钥。

### 配置API密钥

```bash
# 编辑配置文件
nano .env

# 或使用启动脚本查看帮助
./docker-start.sh help
```

### Docker命令说明

Docker Compose会自动处理.env文件，无需手动初始化：

```bash
# 查看服务状态
docker-compose ps

# 查看应用日志
docker-compose logs -f literature-miner

# 重启服务
docker-compose restart literature-miner

# 停止所有服务
docker-compose down

# 进入应用容器
docker exec -it literature-miner /bin/bash
```

### 使用Makefile（可选）

项目提供了Makefile来简化常用操作：

```bash
# 查看所有可用命令
make help

# 启动服务
make up

# 查看服务状态
make status

# 查看应用日志
make logs

# 进入容器
make shell

# 重启服务
make restart

# 停止服务
make down

# 清理资源
make clean
```

#### 方法2：本地安装

1. **克隆项目**
```bash
git clone <repository-url>
cd bioscience/research/readhelper
```

2. **创建虚拟环境**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境**
```bash
cp .env.example .env
# 编辑.env文件，填入您的API密钥
```

5. **启动应用**
```bash
cd src
chmod +x start.sh
./start.sh
```

6. **访问应用**
打开浏览器访问: http://localhost:8501

## 📋 配置说明

### RAGFlow配置

1. **启动RAGFlow服务**
```bash
# 使用Docker启动RAGFlow
docker run -d --name ragflow -p 9380:9380 infiniflow/ragflow:main
```

2. **获取API密钥**
- 访问RAGFlow Web界面 (http://localhost:9380)
- 在设置页面生成API密钥
- 将密钥填入.env文件

### 大模型配置

#### 通义千问（推荐）
```env
LLM_PROVIDER=qwen
LLM_API_KEY=your_qwen_api_key
LLM_MODEL=qwen-turbo
```

#### OpenAI
```env
LLM_PROVIDER=openai
LLM_API_KEY=your_openai_api_key
LLM_MODEL=gpt-3.5-turbo
```

#### Claude
```env
LLM_PROVIDER=claude
LLM_API_KEY=your_anthropic_api_key
LLM_MODEL=claude-3-sonnet-20240229
```

#### 本地模型（Ollama）
```env
LLM_PROVIDER=local
LLM_BASE_URL=http://localhost:11434
LLM_MODEL=llama2
```

## 🎯 使用指南

### 1. 文献库管理

1. 在RAGFlow中创建数据集并上传文献
2. 在应用的"文献库"页面连接到数据集
3. 查看和管理文献内容

### 2. 深度挖掘

1. 选择研究主题（如"肿瘤免疫治疗"）
2. 选择分析范围（全面分析、快速分析等）
3. 调整参数（文档数量、相似度阈值）
4. 点击"开始挖掘"获取分析结果

### 3. 智能搜索

1. 选择搜索类型（语义搜索、关键词搜索等）
2. 输入搜索查询
3. 查看搜索结果和相关文献

### 4. 结果分析

挖掘结果包含：
- **总体摘要**: 研究领域的综合概述
- **关键发现**: 最重要的研究发现
- **研究趋势**: 领域发展趋势分析
- **知识空白**: 研究不足和机会
- **研究网络**: 作者、机构、主题关系
- **概念演化**: 关键概念的历史发展
- **研究建议**: 基于分析的建议

## 🐳 Docker部署

### 快速启动

使用Docker Compose可以一键启动整个系统，包括RAGFlow和文献挖掘助手：

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f literature-miner
```

### 配置选项

1. **环境变量配置**
```bash
# 编辑.env文件
RAGFLOW_API_KEY=your_ragflow_api_key
LLM_PROVIDER=qwen
LLM_API_KEY=your_llm_api_key
LLM_MODEL=qwen-turbo
```

2. **本地大模型支持**
```bash
# 启动包含Ollama的服务
docker-compose --profile local-llm up -d

# 在容器中下载模型
docker exec -it ollama ollama pull llama2
```

3. **数据持久化**
- RAGFlow数据：`ragflow_data`卷
- Ollama模型：`ollama_data`卷
- 应用数据：`./data`目录
- 日志文件：`./logs`目录

### 服务访问

启动后可以通过以下地址访问服务：

- **文献挖掘助手**: http://localhost:8501
- **RAGFlow管理界面**: http://localhost:9380
- **Ollama API**（如果启用）: http://localhost:11434

### 常用命令

```bash
# 停止所有服务
docker-compose down

# 重启特定服务
docker-compose restart literature-miner

# 进入容器调试
docker exec -it literature-miner /bin/bash

# 更新应用后重新构建
docker-compose up -d --build
```

## 🏗️ 项目结构

```
bioscience/research/readhelper/
├── src/                          # 源代码目录
│   ├── main.py                   # 应用入口
│   ├── start.sh                  # 启动脚本
│   ├── config/                   # 配置模块
│   │   ├── settings.py           # 应用配置
│   │   └── prompts.py           # AI提示词模板
│   ├── core/                     # 核心功能模块
│   │   ├── ragflow_client.py     # RAGFlow客户端
│   │   ├── llm_client.py        # 大模型客户端
│   │   ├── literature_miner.py  # 文献挖掘器
│   │   └── document_processor.py # 文档处理器
│   ├── interfaces/               # 用户界面
│   │   └── streamlit_ui/       # Streamlit界面
│   │       ├── home.py          # 首页
│   │       ├── library_tab.py    # 文献库页面
│   │       ├── mining_tab.py     # 深度挖掘页面
│   │       ├── search_tab.py     # 智能搜索页面
│   │       └── config_tab.py    # 配置页面
│   ├── services/                # 服务层（预留）
│   ├── storage/                 # 存储层（预留）
│   └── utils/                   # 工具类（预留）
├── requirements.txt             # 依赖列表
├── .env.example               # 环境变量示例
├── README.md                  # 项目说明
└── IFLOW.md                  # 详细文档
```

## 🔧 开发指南

### 添加新功能

1. **核心功能**: 在`src/core/`目录添加新模块
2. **用户界面**: 在`src/interfaces/streamlit_ui/`目录添加新页面
3. **配置**: 在`src/config/settings.py`添加新配置项

### 自定义提示词

编辑`src/config/prompts.py`文件，修改AI分析的提示词模板。

### 扩展大模型支持

在`src/core/llm_client.py`中添加新的客户端类，并在工厂类中注册。

## 🐛 故障排除

### 常见问题

1. **RAGFlow连接失败**
   - 检查RAGFlow服务是否正常运行
   - 确认API密钥是否正确
   - 验证网络连接

2. **大模型API调用失败**
   - 检查API密钥是否有效
   - 确认网络连接正常
   - 验证模型名称是否正确

3. **文献挖掘结果不准确**
   - 调整相似度阈值
   - 增加文档数量
   - 优化研究主题描述

4. **应用启动失败**
   - 检查Python版本是否符合要求
   - 确认所有依赖已安装
   - 查看错误日志

### 日志查看

应用日志位置: `~/.literature_helper/logs/app.log`

```bash
# 查看最新日志
tail -f ~/.literature_helper/logs/app.log
```

## 📊 性能优化

### 提高分析速度

1. **减少文档数量**: 降低挖掘时的最大文档数
2. **调整相似度阈值**: 提高阈值减少处理的文档
3. **使用更强大的硬件**: 增加CPU和内存资源

### 降低API成本

1. **选择合适的模型**: 根据需求选择不同成本的模型
2. **优化提示词**: 减少不必要的API调用
3. **启用缓存**: 重复查询使用缓存结果

## 🤝 贡献指南

1. Fork项目
2. 创建特性分支
3. 提交更改
4. 发起Pull Request

## 📄 许可证

本项目采用MIT许可证。详见LICENSE文件。

## 📞 支持

如有问题或建议，请通过以下方式联系：

- 提交Issue: [GitHub Issues](https://github.com/hrply/bioscience/issues)
- 邮箱: [your-email@example.com]

## 🙏 致谢

感谢以下开源项目的支持：

- [RAGFlow](https://github.com/infiniflow/ragflow) - 开源RAG引擎
- [Streamlit](https://streamlit.io/) - 快速构建数据应用
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF处理
- [Transformers](https://huggingface.co/transformers/) - 大模型支持

## 📈 更新日志

### v1.0.0 (2025-12-19)

- 🎉 首次发布文献深度挖掘助手
- 🔗 集成RAGFlow API连接
- 🤖 支持多种大模型（OpenAI、通义千问、Claude、本地模型）
- ⛏️ 文献深度挖掘功能
- 🔍 智能文献搜索
- 📊 研究趋势分析
- 💡 知识空白识别
- 🌐 研究网络构建
- 📈 概念演化分析

---

*最后更新: 2025-12-19*