# BioData Manager - 项目概览与开发指南

## 项目概述

这是一个专为生物信息学研究设计的数据管理系统，用于组织、记录和管理各种类型的生物学数据，包括测序结果、基因芯片、蛋白组学、质谱流式数据等。

**核心功能：**
- 项目管理：按文献DOI、数据库编号等创建和管理项目
- 自动分类：根据数据类型（转录组、单细胞、蛋白组等）自动分类
- 智能识别：自动检测DOI、数据库编号（GEO、ENA、SRA等）
- 文件操作：批量导入、组织和浏览数据文件
- 处理数据管理：管理基于原始数据分析后的结果数据
- 可视化界面：基于Bootstrap 5的响应式Web界面

## 技术架构

### 后端技术栈
- **Python 3.10+**：主要开发语言
- **SQLite 3.x**：轻量级数据库，支持FTS5全文搜索
- **HTTPServer**：Python内置HTTP服务器
- **Pathlib**：现代文件路径处理
- **Watchdog**：开发环境代码热重载

### 前端技术栈
- **HTML5**：页面结构
- **Bootstrap 5**：响应式CSS框架
- **JavaScript (ES6+)**：前端交互逻辑
- **Bootstrap Icons**：本地图标库
- **Chart.js**：数据可视化图表

### 部署方案
- **Docker**：容器化部署
- **Docker Compose**：多服务编排
- **Dockerfile**：多阶段构建优化

## 项目结构

```
/home/hrply/software/bioscience/research/biodata_manager/
├── app/                          # 应用代码目录
│   ├── index.html               # 主页面
│   ├── styles.css               # 自定义样式
│   ├── app.js                   # 前端JavaScript逻辑
│   ├── backend.py               # 后端数据处理逻辑
│   ├── server.py                # Web服务器和API接口
│   ├── database.py              # SQLite数据库操作
│   ├── docker-entrypoint.sh     # 容器启动脚本
│   ├── init_db.py               # 数据库初始化脚本
│   ├── migrate.py               # 数据迁移工具
│   ├── metadata_config_manager.py  # 元数据配置管理
│   ├── metadata-config-ui.js    # 元数据配置UI
│   ├── metadata-form.js         # 元数据表单
│   ├── test_*.py                # 测试文件
│   └── libs/                    # 前端库文件
│       ├── bootstrap/           # Bootstrap框架
│       ├── bootstrap-icons/     # 图标库
│       └── chartjs/             # 图表库
│   └── data/
│       └── biodata.db           # SQLite数据库（运行时）
├── docker-compose.yml          # Docker Compose配置
├── Dockerfile                   # Docker镜像构建文件
├── .dockerignore                # Docker忽略文件
├── pip.conf                     # pip配置（清华源）
├── README.md                    # 项目文档（中文）
├── IFLOW.md                     # iFlow上下文文件
├── requirements_async.txt       # 异步依赖包
└── test_analysis/               # 测试数据目录
    └── differential_genes.csv  # 差异表达基因测试数据
```

### 数据目录（宿主机路径映射）

```
/ssd/bioraw/
├── raw_data/         → /bioraw/data (原始数据存储)
├── downloads/        → /bioraw/downloads (下载目录)
├── results/          → /bioraw/results (分析结果)
├── analysis/         → /bioraw/analysis (处理数据存储)
└── biodata.db        → /bioraw/biodata.db (SQLite数据库)
```

## 构建和运行

### 系统要求
- Python 3.10+
- Docker & Docker Compose
- 现代Web浏览器（Chrome、Firefox、Safari、Edge）
- Linux操作系统（推荐Ubuntu 18.04+）

### Docker部署（推荐）

#### 启动服务
```bash
# 启动所有服务（后台运行）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看实时日志
docker-compose logs -f biodata-manager

# 停止服务
docker-compose down
```

#### 访问地址
- **Web界面**: http://localhost:20425
- **容器端口**: 8000（映射到宿主机20425）

#### 环境变量
可以通过 `docker-compose.yml` 配置：
- `BIODATA_BASE_DIR`: 原始数据存储目录（默认: /bioraw/data）
- `BIODATA_DOWNLOAD_DIR`: 下载目录（默认: /bioraw/downloads）
- `BIODATA_RESULTS_DIR`: 分析结果目录（默认: /bioraw/results）
- `BIODATA_ANALYSIS_DIR`: 处理数据目录（默认: /bioraw/analysis）
- `BIODATA_USE_MOVE_MODE`: 存储模式（true=移动模式, false=复制模式）

### 传统部署

#### 安装依赖
```bash
# 安装Python依赖
pip3 install watchdog aiofiles
```

#### 启动服务器
```bash
# 进入应用目录
cd app/

# 启动服务器（默认端口8000）
python3 server.py

# 指定端口启动
python3 server.py 8080
```

#### 访问地址
- http://localhost:8000（或指定端口）

## API接口文档

### 项目管理API

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/projects` | 获取所有项目 |
| POST | `/api/create-project` | 创建新项目 |
| GET | `/api/project/{id}` | 获取特定项目 |
| POST | `/api/update-project/{id}` | 更新项目 |
| POST | `/api/delete-project/{id}` | 删除项目 |

### 文件操作API

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/scan-downloads` | 扫描下载目录 |
| POST | `/api/import-download` | 导入下载文件 |
| POST | `/api/organize-files` | 组织项目文件 |
| GET | `/api/directory-tree` | 获取目录树 |

### 处理数据管理API

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/processed-data` | 获取处理数据列表 |
| GET | `/api/processed-data/{id}` | 获取特定处理数据 |
| GET | `/api/scan-analysis` | 扫描分析目录 |
| POST | `/api/import-analysis` | 导入分析数据 |
| POST | `/api/import-processed-file` | 导入单个处理文件 |
| POST | `/api/delete-processed-data/{id}` | 删除处理数据 |

### 元数据配置API

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/metadata/config` | 获取所有元数据配置 |
| POST | `/api/metadata/config/batch` | 批量更新元数据配置 |
| POST | `/api/metadata/config/add` | 添加单个元数据配置 |
| POST | `/api/metadata/config/update` | 更新单个元数据配置 |
| POST | `/api/metadata/config/delete` | 删除元数据配置 |
| POST | `/api/metadata/config/refresh` | 刷新配置缓存 |

## 数据库架构

### 核心表结构

**projects 表**
- `id` (TEXT PRIMARY KEY): 项目ID
- `title` (TEXT): 项目标题
- `doi` (TEXT): DOI标识符
- `db_id` (TEXT): 数据库编号
- `db_link` (TEXT): 数据库链接
- `data_type` (TEXT): 数据类型
- `organism` (TEXT): 物种
- `authors` (TEXT): 作者
- `journal` (TEXT): 期刊
- `description` (TEXT): 描述
- `created_date` (TEXT): 创建日期
- `path` (TEXT): 项目路径

**files 表**
- `id` (INTEGER PRIMARY KEY): 文件ID
- `project_id` (TEXT): 关联项目ID
- `name` (TEXT): 文件名
- `path` (TEXT): 文件路径
- `size` (TEXT): 文件大小（可读格式）
- `size_bytes` (INTEGER): 文件大小（字节）
- `type` (TEXT): 文件类型
- `modified` (TEXT): 修改时间

**processed_data 表**
- `id` (TEXT PRIMARY KEY): 处理数据ID
- `project_id` (TEXT): 关联项目ID
- `title` (TEXT): 标题
- `description` (TEXT): 描述
- `analysis_type` (TEXT): 分析类型
- `software` (TEXT): 使用软件
- `parameters` (TEXT): 参数
- `created_date` (TEXT): 创建日期
- `path` (TEXT): 存储路径

**tags 表**
- `id` (INTEGER PRIMARY KEY): 标签ID
- `project_id` (TEXT): 关联项目ID
- `tag` (TEXT): 标签内容

### 全文搜索
使用 SQLite FTS5 虚拟表 `projects_fts` 实现项目全文搜索，自动触发器保持索引同步。

## 数据类型支持

### 原始数据类型
- **转录组**: `.fastq`, `.sam`, `.bam`
- **单细胞转录组**: `.h5ad`, `.mtx`
- **空间转录组**: 专用格式
- **蛋白组**: `.raw`, `.mzml`, `.wiff`
- **磷酸化组**: 专用格式
- **质谱流式**: `.fcs`
- **多组学**: 混合格式
- **其他**: 各种格式

### 处理数据类型
- **differential**: 差异表达分析
- **enrichment**: 富集分析
- **pathway**: 通路分析
- **clustering**: 聚类分析
- **network**: 网络分析
- **other**: 其他分析

## 数据库编号识别

系统支持自动识别以下数据库编号：
- **GEO**: `GSExxxxx`, `GSMxxxxx`
- **ENA**: `ERRxxxxx`, `SRRxxxxx`
- **NCBI BioProject**: `PRJNAxxxxx`
- **ArrayExpress**: `MTAB_xxxx`
- **ProteomeXchange**: `PXDxxxxx`

## 开发约定

### 代码风格
- **Python**: 遵循PEP 8规范，使用类型注解
- **JavaScript**: 使用ES6+语法，驼峰命名
- **HTML**: 语义化标签，Bootstrap 5组件
- **CSS**: BEM命名规范，响应式设计

### 文件命名约定
- **Python文件**: 小写字母，下划线分隔（`backend.py`）
- **JavaScript文件**: 小写字母，下划线分隔（`app.js`）
- **HTML文件**: 小写字母，连字符分隔（`index.html`）
- **CSS文件**: 小写字母，连字符分隔（`styles.css`）

### 目录组织原则
- **app/**: 应用代码，支持热更新
- **根目录**: Docker构建必需文件
- **按数据类型分层存储**
- **每个项目自动生成README.md文档**
- **支持标签和元数据管理**

## 测试

### 测试文件
- `app/test_create_project.py`: 项目创建测试
- `app/test_metadata_api.py`: 元数据API测试
- `app/final_test.py`: 综合功能测试

### 运行测试
```bash
# 进入app目录
cd app/

# 运行特定测试
python3 test_create_project.py
python3 test_metadata_api.py

# 或使用pytest（如果已安装）
pytest test_*.py -v
```

## 常见任务

### 创建新项目
1. 通过Web界面访问"项目管理"标签
2. 点击"创建新项目"按钮
3. 填写项目信息（标题、DOI、数据类型等）
4. 可上传引文文件（.enw或.ris）自动填充信息

### 导入下载数据
1. 将下载文件夹放入 `/ssd/bioraw/downloads/` 目录
2. 系统自动扫描并识别下载文件夹
3. 检查识别信息（DOI、数据库编号、数据类型等）
4. 点击"导入"将数据移入项目库

### 添加新数据类型
1. 在 `app/backend.py` 的 `data_type_mapping` 中添加映射
2. 在 `file_type_mapping` 中添加文件扩展名
3. 更新前端 `app/app.js` 中的 `getDataTypeLabel` 函数

### 添加新数据库支持
1. 在 `app/backend.py` 的 `db_patterns` 列表中添加正则表达式
2. 更新文档说明

## 调试和日志

### 查看日志
```bash
# Docker部署
docker-compose logs -f biodata-manager

# 传统部署
# 查看控制台输出
```

### 调试方法
1. **浏览器开发者工具**: 查看前端错误和网络请求
2. **容器日志**: 检查后端错误
3. **数据库检查**: 直接查看SQLite数据库内容
4. **文件系统验证**: 确认挂载目录和权限

## 性能优化

### 已实现优化
- 使用生成器处理大文件列表
- SQLite索引优化查询性能
- FTS5全文搜索提高搜索效率
- 前端懒加载和虚拟滚动

### 存储模式
- **移动模式（默认）**: 导入文件后自动清理下载目录，节省存储空间
- **复制模式**: 保留原始文件作为备份

## 安全考虑

- 验证上传文件类型
- 限制文件大小
- 防止路径遍历攻击
- 容器隔离运行环境
- 定期备份数据库和数据目录

## 版本信息

- **当前版本**: v2.0.0
- **Python兼容性**: 3.10+
- **浏览器兼容性**: 现代浏览器（ES6支持）
- **Docker支持**: 完整容器化部署
- **数据库**: SQLite 3.x
- **最后更新**: 2024-12-28

### 更新日志
- **v2.0.0**: 添加处理数据管理功能，Docker化部署，元数据配置系统
- **v1.0.0**: 基础项目管理功能

## 联系和支持

如有问题或建议：
1. 检查浏览器控制台的错误信息
2. 查看Docker容器日志
3. 验证Python环境和依赖
4. 检查文件系统权限

---

*此文件由GEMINI CLI自动生成，包含项目的完整上下文信息，用于指导后续的开发和维护工作。*
