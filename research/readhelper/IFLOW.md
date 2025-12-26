# 生物科学文献阅读助手项目

## 项目概述

这是一个基于Python的生物科学文献阅读助手系统，专为科研人员设计，帮助高效阅读、分析和整理科学文献。项目采用AI技术，提供文献摘要生成、关键信息提取、文献分类和智能搜索等功能。

### 核心特性

- **智能文献摘要**：自动生成文献摘要和关键点提取
- **多源文献管理**：支持PDF、网页、DOI等多种文献来源
- **主题分类**：自动将文献按研究领域和主题分类
- **知识图谱构建**：构建文献间的关联关系图
- **交互式阅读**：提供标注、笔记和高亮功能
- **文献推荐**：基于阅读历史推荐相关文献

## 技术栈

- **前端**：Streamlit 1.28+
- **后端**：Python 3.10+
- **数据库**：SQLite + ChromaDB (向量数据库)
- **AI模型**：通义千问API (可切换本地模型)
- **文档处理**：PyPDF2, pdfplumber, BeautifulSoup
- **文本分析**：NLTK, spaCy, scikit-learn

## 项目结构

```
bioscience/research/readhelper/
├── main.py                    # 简化版主入口
├── requirements.txt           # 核心依赖
├── install_conda.sh          # Conda安装脚本
├── install_deps.sh           # 依赖安装脚本
├── src/                       # 主项目目录
│   ├── main.py              # 完整版主入口
│   ├── start.sh             # 快速启动脚本
│   ├── requirements.txt     # 完整依赖清单
│   ├── README.md            # 项目详细说明
│   ├── config/              # 配置模块
│   │   ├── settings.py      # 应用配置
│   │   └── prompts/         # AI提示词模板
│   ├── core/                # 核心模块
│   │   ├── document_processor.py  # 文档处理核心
│   │   ├── ai_analyzer.py   # AI分析引擎
│   │   ├── knowledge_graph.py     # 知识图谱构建
│   │   └── search_engine.py       # 搜索引擎
│   ├── services/            # 服务层
│   │   ├── literature_service.py  # 文献服务
│   │   ├── summary_service.py     # 摘要服务
│   │   ├── classification_service.py  # 分类服务
│   │   └── recommendation_service.py  # 推荐服务
│   ├── storage/             # 存储层
│   │   ├── literature_store.py     # 文献存储
│   │   ├── annotation_store.py     # 标注存储
│   │   ├── graph_store.py          # 图数据库
│   │   └── vector_db.py            # 向量数据库
│   ├── interfaces/          # 界面层
│   │   ├── cli.py          # 命令行界面
│   │   └── streamlit_ui/   # Streamlit界面
│   │       ├── home.py     # 首页
│   │       ├── library_tab.py    # 文献库页
│   │       ├── reader_tab.py     # 阅读器页
│   │       ├── search_tab.py     # 搜索页
│   │       └── notes_tab.py      # 笔记页
│   ├── utils/              # 工具类
│   │   ├── pdf_utils.py    # PDF处理
│   │   ├── text_utils.py   # 文本处理
│   │   ├── web_utils.py    # 网页处理
│   │   └── ai_helpers.py   # AI助手
│   └── tests/              # 测试模块
```

## 快速开始

### 方法1：使用快速启动脚本（推荐）

```bash
cd src
chmod +x start.sh
./start.sh
```

### 方法2：手动安装

1. **创建虚拟环境**
```bash
python3 -m venv venv
source venv/bin/activate
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置API密钥**
```bash
export QWEN_API_KEY=your_api_key_here
# 或创建 .env 文件
cp .env.example .env
# 编辑 .env 文件添加 API 密钥
```

4. **启动应用**
```bash
streamlit run main.py
```

### 方法3：Docker Compose直接运行

1. **确保配置正确**
```bash
cp .env.example .env
# 编辑 .env 文件添加 API 密钥
```

2. **构建并启动服务**
```bash
docker-compose build
docker-compose up -d
```

3. **访问应用**
- 文献挖掘助手: http://localhost:20422
- RAGFlow管理界面: http://localhost:9380

## 核心功能

### 1. 文献导入与管理

- 支持PDF文件批量导入
- DOI自动解析和元数据获取
- 网页文献一键保存
- 文献库分类管理

### 2. 智能阅读辅助

- 自动生成文献摘要
- 关键信息提取和标注
- 术语解释和背景知识
- 交互式问答系统

### 3. 知识图谱构建

- 文献间关联分析
- 作者合作关系图
- 研究主题演化图
- 引用网络可视化

### 4. 个性化推荐

- 基于阅读历史的推荐
- 研究领域热点追踪
- 相关文献自动发现
- 定制化提醒服务

## 配置说明

主要配置项在 `config/settings.py` 中：

```python
# API配置
QWEN_API_KEY: 通义千问API密钥
QWEN_MODEL: 使用的模型版本

# 文献处理配置
max_pdf_size: PDF文件最大大小
supported_formats: 支持的文件格式
auto_extract_metadata: 是否自动提取元数据

# 存储配置
data_dir: 数据存储目录
db_path: 数据库路径
vector_db_path: 向量数据库路径
```

## 开发指南

### 添加新服务

1. 创建服务类在 `services/` 目录
2. 实现核心处理逻辑
3. 在主应用中注册服务

```python
from services.base_service import BaseService

class NewService(BaseService):
    def __init__(self, config):
        super().__init__(config)
    
    async def process(self, request_data):
        # 实现处理逻辑
        pass
```

### 扩展文档处理器

在 `core/document_processor.py` 中添加新的文档类型支持：

```python
class NewDocumentProcessor(BaseProcessor):
    def can_process(self, file_path):
        # 检查是否支持该文件类型
        pass
    
    def extract_content(self, file_path):
        # 提取文档内容
        pass
```

## API接口

### 文献分析API

```python
# 请求数据
request_data = {
    "document_id": "doc_id",
    "analysis_type": "summary|keywords|entities",
    "options": {
        "length": "short|medium|long",
        "language": "zh|en"
    }
}

# 响应数据
response = {
    "success": True,
    "analysis_result": {
        "summary": "文献摘要",
        "keywords": ["关键词1", "关键词2"],
        "entities": [{"name": "实体名", "type": "实体类型"}]
    },
    "confidence": 0.95
}
```

## 故障排除

### 常见问题

1. **PDF解析失败**
   - 检查PDF文件是否损坏
   - 尝试使用不同的PDF处理引擎
   - 确认文件权限设置

2. **API连接失败**
   - 检查API密钥配置
   - 验证网络连接
   - 确认API密钥有效性

3. **内存使用过高**
   - 调整批处理大小
   - 使用流式处理大文件
   - 清理缓存数据

### 日志查看

```bash
# 查看应用日志
tail -f ~/.literature_helper/logs/app.log

# 查看错误日志
tail -f ~/.literature_helper/logs/error.log
```

## 性能优化

- 使用缓存减少重复计算
- 异步处理提高响应速度
- 向量数据库加速语义搜索
- 分页加载大量文献

## 扩展计划

- 支持更多文档格式
- 增强AI分析能力
- 添加协作功能
- 集成更多文献数据库
- 支持多语言文献处理

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支
3. 提交更改
4. 发起 Pull Request

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue: [GitHub Issues](https://github.com/hrply/bioscience/issues)
- 邮箱: [your-email@example.com]

---

*最后更新: 2025-12-19*