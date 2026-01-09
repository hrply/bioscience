# 生物信息学数据管理系统 iFlow 上下文

## 项目概述

这是一个专为生物信息学数据设计的管理系统，用于组织、记录和管理各种类型的生物学数据，包括测序结果、基因芯片、蛋白组学、质谱流式数据等。系统采用前后端分离架构，提供现代化的Web界面和强大的数据管理功能。

### 核心功能
- **项目管理**: 按文献DOI、数据库编号等创建和管理项目
- **自动分类**: 根据数据类型（转录组、单细胞、蛋白组等）自动分类
- **智能识别**: 自动检测DOI、数据库编号和数据类型
- **文件操作**: 批量导入、组织和浏览数据文件
- **处理数据管理**: 管理基于原始数据分析后的结果数据
- **可视化界面**: 基于Bootstrap 5的响应式设计

### 新增功能
- **处理数据管理**: 支持分析结果数据的导入和管理
- **分析目录扫描**: 自动扫描包含Markdown说明的分析文件夹
- **双模式导入**: 支持文件夹导入和单个文件导入
- **项目关联**: 处理数据可与原始项目关联
- **Docker化部署**: 完整的容器化解决方案

## 技术架构

### 前端技术
- **HTML5**: 页面结构和语义化标记
- **CSS3**: 使用Bootstrap 5框架的响应式设计
- **JavaScript**: 原生ES6+实现交互功能
- **Bootstrap Icons**: 本地图标库（避免CDN依赖）
- **Chart.js**: 数据可视化图表

### 后端技术
- **Python 3.10+**: 后端开发语言
- **SQLite**: 轻量级数据库存储
- **HTTPServer**: Python内置HTTP服务器
- **Pathlib**: 现代文件路径处理
- **Watchdog**: 开发环境代码热重载

### 数据存储
- **SQLite数据库**: 项目和处理数据元数据存储
- **文件系统**: 基于目录结构的分层存储
- **Markdown**: 项目文档和分析说明文件

### 容器化
- **Docker**: 完整的容器化部署方案
- **Docker Compose**: 多服务编排
- **多阶段构建**: 优化的镜像构建

## 项目结构

```
/home/hrply/software/bioscience/research/biodata_manager/
├── app/                    # 应用代码目录
│   ├── index.html         # 主页面HTML
│   ├── styles.css         # 自定义样式文件
│   ├── app.js             # 前端JavaScript逻辑
│   ├── backend.py         # 后端数据处理逻辑
│   ├── server.py          # Web服务器和API接口
│   ├── database.py        # SQLite数据库操作
│   ├── docker-entrypoint.sh # 容器启动脚本
│   ├── init_db.py         # 数据库初始化
│   ├── migrate.py         # 数据迁移工具
│   └── libs/              # 前端库文件
│       ├── bootstrap/     # Bootstrap框架
│       ├── bootstrap-icons/ # 图标库
│       └── chartjs/       # 图表库
├── docker-compose.yml     # Docker Compose配置
├── Dockerfile            # Docker镜像构建文件
├── .dockerignore         # Docker忽略文件
├── pip.conf              # pip配置文件
├── README.md             # 项目说明文档
└── IFLOW.md              # iFlow上下文文件

# 数据目录（宿主机路径）
/ssd/bioraw/
├── raw_data/             # 原始数据存储
│   └── PRJ001_项目名/     # 项目文件夹
│       ├── README.md      # 项目说明文档
│       └── 数据文件...
├── downloads/            # 下载目录
├── results/              # 处理结果存储
│   └── PRD001_处理数据/   # 处理数据文件夹
├── analysis/             # 分析数据目录
│   └── analysis_folder/  # 分析文件夹
│       ├── README.md     # 分析说明文件
│       └── 分析结果文件...
└── biodata.db           # SQLite数据库文件

# 容器内路径映射
/bioraw/data/           # → /ssd/bioraw/raw_data
/bioraw/downloads/      # → /ssd/bioraw/downloads
/bioraw/results/        # → /ssd/bioraw/results
/bioraw/analysis/       # → /ssd/bioraw/analysis
/bioraw/biodata.db      # → /ssd/bioraw/biodata.db
```

## 构建和运行

### 系统要求
- Python 3.10+
- Docker & Docker Compose
- 现代Web浏览器（Chrome、Firefox、Safari、Edge）
- Linux操作系统（推荐Ubuntu 18.04+）

### Docker部署（推荐）

#### 1. 使用Docker Compose启动
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f biodata-manager

# 停止服务
docker-compose down
```

#### 2. 访问地址
- **默认端口**: http://localhost:20425
- **容器端口**: 8000（映射到宿主机20425）

#### 3. 环境变量配置
```yaml
environment:
  - BIODATA_BASE_DIR=/bioraw/data
  - BIODATA_DOWNLOAD_DIR=/bioraw/downloads
  - BIODATA_RESULTS_DIR=/bioraw/results
  - BIODATA_ANALYSIS_DIR=/bioraw/analysis
  - BIODATA_USE_MOVE_MODE=true
```

### 传统部署

#### 1. 安装依赖
```bash
pip3 install watchdog
```

#### 2. 启动服务
```bash
cd app/
python3 server.py 8000
```

## API接口

### 项目管理API
- `GET /api/projects` - 获取所有项目
- `POST /api/create-project` - 创建新项目
- `GET /api/project/{id}` - 获取特定项目
- `POST /api/update-project/{id}` - 更新项目
- `POST /api/delete-project/{id}` - 删除项目

### 文件操作API
- `GET /api/scan-downloads` - 扫描下载目录
- `POST /api/import-download` - 导入下载文件
- `POST /api/organize-files` - 组织项目文件

### 处理数据管理API
- `GET /api/processed-data` - 获取处理数据列表
- `GET /api/processed-data/{id}` - 获取特定处理数据
- `GET /api/scan-analysis` - 扫描分析目录
- `POST /api/import-analysis` - 导入分析数据
- `POST /api/import-processed-file` - 导入单个处理文件
- `POST /api/delete-processed-data/{id}` - 删除处理数据

### 目录管理API
- `GET /api/directory-tree` - 获取目录树

## 数据库架构

### 项目表 (projects)
- `id` - 项目ID（主键）
- `title` - 项目标题
- `doi` - DOI标识符
- `db_id` - 数据库编号
- `db_link` - 数据库链接
- `data_type` - 数据类型
- `organism` - 物种
- `authors` - 作者
- `journal` - 期刊
- `description` - 描述
- `created_date` - 创建日期
- `path` - 项目路径

### 处理数据表 (processed_data)
- `id` - 处理数据ID（主键）
- `project_id` - 关联项目ID（可为空）
- `title` - 标题
- `description` - 描述
- `analysis_type` - 分析类型
- `software` - 使用软件
- `parameters` - 参数
- `created_date` - 创建日期
- `path` - 存储路径

### 文件表 (files & processed_files)
- 关联项目和文件的详细信息
- 文件名、路径、大小、类型等

### 标签表 (tags)
- 项目标签管理
- 支持多标签分类

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
- **差异表达分析**: `differential`
- **富集分析**: `enrichment`
- **通路分析**: `pathway`
- **聚类分析**: `clustering`
- **网络分析**: `network`
- **其他分析**: `other`

## 数据库编号识别

系统支持自动识别以下数据库编号：
- **GEO**: `GSExxxxx`, `GSMxxxxx`
- **ENA**: `ERRxxxxx`, `SRRxxxxx`
- **NCBI BioProject**: `PRJNAxxxxx`
- **ArrayExpress**: `MTAB_xxxx`
- **ProteomeXchange**: `PXDxxxxx`

## 处理数据管理

### 分析目录结构
```
/bioraw/analysis/
└── analysis_folder/
    ├── README.md           # 必需的分析说明文件
    ├── result_file1.csv    # 分析结果文件
    ├── result_file2.png    # 图表文件
    └── ...
```

### Markdown说明文件格式
```markdown
# 分析结果标题

**项目ID**: PRJ001
**分析类型**: differential
**软件**: DESeq2
**参数**: --method wald --alpha 0.05
**日期**: 2024-12-28
**描述**: 分析结果描述

## 分析结果
- 总共检测到 15000 个基因
- 上调基因: 2341 个
- 下调基因: 1876 个

## 文件说明
- `differential_genes.csv`: 差异表达基因列表
- `volcano_plot.png`: 火山图
- `heatmap.png`: 热图
```

### 导入模式
1. **文件夹导入**: 扫描分析目录，导入包含README.md的文件夹
2. **单个文件导入**: 通过文件路径导入单个处理数据文件

## 引文文件解析

### 支持格式
- **EndNote**: `.enw` 格式
- **RIS**: `.ris` 格式

### 解析字段
- 标题 (Title)
- 作者 (Authors)
- 期刊 (Journal)
- DOI (Digital Object Identifier)
- 摘要 (Abstract)

## 开发约定

### 代码风格
- **Python**: 遵循PEP 8规范，使用类型注解
- **JavaScript**: 使用ES6+语法，采用驼峰命名
- **HTML**: 语义化标签，Bootstrap 5组件
- **CSS**: BEM命名规范，响应式设计

### 文件命名
- **Python文件**: 小写字母，下划线分隔 (`backend.py`)
- **JavaScript文件**: 小写字母，下划线分隔 (`app.js`)
- **HTML文件**: 小写字母，连字符分隔 (`index.html`)
- **CSS文件**: 小写字母，连字符分隔 (`styles.css`)

### 目录组织
- **app/**: 应用代码，支持热更新
- **根目录**: Docker构建必需文件
- **按数据类型分层存储**
- **每个项目自动生成README.md文档**
- **支持标签和元数据管理**

## 测试和调试

### 调试方法
1. **浏览器开发者工具**: 查看前端错误和网络请求
2. **容器日志**: `docker-compose logs biodata-manager`
3. **数据库检查**: 直接查看SQLite数据库内容
4. **文件系统验证**: 确认挂载目录和权限

### 开发环境特性
- **代码热重载**: 修改Python代码自动重启服务器
- **本地资源**: 所有前端资源本地化，避免CDN依赖
- **详细日志**: 开发模式下提供详细日志输出

### 常见问题
- **端口占用**: 使用docker-compose自动处理端口映射
- **权限问题**: 确保数据目录有正确的读写权限
- **挂载路径**: 检查docker-compose.yml中的卷挂载配置
- **数据库锁定**: SQLite文件权限问题

## 扩展和定制

### 添加新数据类型
1. 在 `backend.py` 的 `data_type_mapping` 中添加映射
2. 在 `file_type_mapping` 中添加文件扩展名
3. 更新前端 `app.js` 中的 `getDataTypeLabel` 函数

### 添加新数据库支持
1. 在 `backend.py` 的 `db_patterns` 列表中添加正则表达式
2. 更新文档说明

### 扩展处理数据类型
1. 在 `backend.py` 中添加新的分析类型
2. 更新前端界面选项
3. 修改Markdown解析逻辑

### 自定义样式
- 修改 `styles.css` 文件
- 遵循Bootstrap 5变量系统
- 使用CSS自定义属性

## 性能优化

### 文件处理
- 使用生成器处理大文件列表
- 异步文件操作避免阻塞
- 缓存目录扫描结果
- SQLite索引优化查询性能

### 前端优化
- 懒加载项目列表
- 虚拟滚动处理大量数据
- 防抖搜索功能
- 本地资源避免CDN延迟

### 数据库优化
- 为常用查询字段创建索引
- 使用全文搜索提高搜索性能
- 分页查询避免大量数据加载

## 安全考虑

### 文件安全
- 验证上传文件类型
- 限制文件大小
- 防止路径遍历攻击
- 容器隔离运行环境

### 数据保护
- 定期备份数据库文件
- 文件系统权限控制
- 敏感信息不记录日志
- 使用环境变量管理配置

## 部署建议

### 生产环境
- 使用Docker Compose进行编排
- 配置健康检查和自动重启
- 设置防火墙规则
- 定期备份数据目录和数据库
- 监控容器资源使用

### 开发环境
- 使用代码热重载功能
- 挂载本地目录进行开发
- 启用详细日志输出
- 使用浏览器开发者工具调试

### 网络优化
- 使用国内镜像源加速构建
- 本地化所有前端资源
- 优化Docker镜像大小
- 配置代理环境变量（如需要）

## 可访问性

### 已实现的改进
- 模态框焦点管理
- ARIA标签正确设置
- 键盘导航支持
- 屏幕阅读器兼容
- 符合WAI-ARIA规范

### 持续改进
- 定期进行可访问性测试
- 响应用户反馈
- 遵循Web内容可访问性指南(WCAG)

## 版本信息

- **当前版本**: v2.0.0
- **Python兼容性**: 3.10+
- **浏览器兼容性**: 现代浏览器（ES6支持）
- **Docker支持**: 完整容器化部署
- **数据库**: SQLite 3.x
- **最后更新**: 2024-12-28

### 更新日志
- **v2.0.0**: 添加处理数据管理功能，Docker化部署
- **v1.0.0**: 基础项目管理功能

---

*此文件由iFlow CLI自动生成，包含项目的完整上下文信息，用于指导后续的开发和维护工作。*