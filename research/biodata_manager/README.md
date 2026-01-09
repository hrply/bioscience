# 生物信息学数据管理系统

一个专为生物信息学数据设计的管理系统，用于组织、记录和管理各种类型的生物学数据，包括测序结果、基因芯片、蛋白组学、质谱流式数据等。

## 功能特性

### 📊 数据管理
- **项目管理**: 按文献DOI、数据库编号等创建和管理项目
- **自动分类**: 根据数据类型（转录组、单细胞、蛋白组等）自动分类
- **分层存储**: 按数据类型和组织类型进行分层存储
- **项目追踪**: 每个项目生成详细的Markdown描述文件

### 🔍 智能识别
- **DOI检测**: 自动识别文件夹名称和文件内容中的DOI号
- **数据库编号识别**: 支持GEO、ENA、SRA、ArrayExpress等数据库编号
- **数据类型检测**: 根据文件扩展名自动识别数据类型
- **引文文件解析**: 支持EndNote (.enw) 和 RIS 格式引文文件

### 📁 文件操作
- **下载目录扫描**: 自动扫描下载目录中的待处理文件
- **批量导入**: 一键导入下载的文件夹到项目库
- **文件组织**: 自动按数据类型重新组织文件结构
- **目录树生成**: 自动生成完整的数据目录结构文档

### 🎨 用户界面
- **现代化界面**: 基于Bootstrap 5的响应式设计
- **交互式操作**: 直观的项目管理和文件浏览界面
- **实时搜索**: 支持全文搜索和筛选功能
- **数据可视化**: 项目统计和分布图表

## 系统要求

- Python 3.6+
- 现代Web浏览器（Chrome、Firefox、Safari、Edge）
- Linux操作系统（推荐Ubuntu 18.04+）

## 安装和启动

### 方式一：传统部署

#### 1. 克隆或下载系统文件
```bash
# 确保文件位于 /ssd/bioraw/data_manager/ 目录下
cd /ssd/bioraw/data_manager/
```

#### 2. 设置权限
```bash
chmod +x start.sh
chmod +x backend.py
chmod +x server.py
```

#### 3. 启动系统
```bash
# 使用启动脚本
./start.sh

# 或直接启动Python服务器
python3 server.py
```

#### 4. 访问系统
打开浏览器访问: http://localhost:8000

### 方式二：Docker部署

#### 1. 使用Docker构建和运行
```bash
# 构建Docker镜像
docker build -t biodata-manager .

# 运行容器
docker run -d \
  --name biodata-manager \
  -p 8000:8000 \
  -v $(pwd)/data:/ssd/bioraw/data \
  -v $(pwd)/downloads:/ssd/bioraw/downloads \
  biodata-manager

# 查看容器状态
docker ps

# 查看日志
docker logs biodata-manager
```

#### 2. 使用Docker Compose（推荐）
```bash
# 创建数据目录
mkdir -p data downloads

# 启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 3. Docker环境变量配置
```bash
# 自定义端口
docker run -d \
  --name biodata-manager \
  -p 8080:8000 \
  -e PORT=8080 \
  -v $(pwd)/data:/ssd/bioraw/data \
  -v $(pwd)/downloads:/ssd/bioraw/downloads \
  biodata-manager

# 自定义数据目录
docker run -d \
  --name biodata-manager \
  -p 8000:8000 \
  -e BIODATA_BASE_DIR=/app/data \
  -e BIODATA_DOWNLOAD_DIR=/app/downloads \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/downloads:/app/downloads \
  biodata-manager

# 使用复制模式（保留原始文件）
docker run -d \
  --name biodata-manager \
  -p 8000:8000 \
  -e BIODATA_USE_MOVE_MODE=false \
  -v $(pwd)/data:/ssd/bioraw/data \
  -v $(pwd)/downloads:/ssd/bioraw/downloads \
  biodata-manager
```

#### 4. 存储模式说明

**移动模式（默认）**
- 环境变量：`BIODATA_USE_MOVE_MODE=true`
- 优点：节省存储空间，避免重复文件
- 行为：先复制文件到目标位置，确认成功后再删除源文件
- 安全机制：复制失败时自动清理，删除失败时保留复制的文件
- 适用：生产环境，空间有限的场景

**复制模式**
- 环境变量：`BIODATA_USE_MOVE_MODE=false`
- 优点：保留原始文件作为备份
- 行为：只复制文件，保留原始文件不变
- 安全机制：复制失败时自动清理已复制的文件
- 适用：开发环境，需要备份重要数据的场景

**存储空间对比**
- 移动模式：文件只存储一份，节省50%空间
- 复制模式：文件存储两份，占用双倍空间

#### 4. 访问系统
打开浏览器访问: http://localhost:8000

#### 5. 国内网络优化（推荐）
```bash
# 使用优化的构建脚本
./build-docker.sh

# 或手动构建时指定代理（如果需要）
docker build \
  --build-arg HTTP_PROXY=http://proxy.example.com:8080 \
  --build-arg HTTPS_PROXY=http://proxy.example.com:8080 \
  -t biodata-manager .
```

**国内网络优化特性：**
- **清华APT源**: 配置APT使用清华大学镜像源，加速系统包下载
- **pip清华源**: 配置pip使用清华大学PyPI镜像，加速Python包下载
- **中文字体支持**: 预装中文字体，支持中文显示
- **字体缓存**: 预先构建字体缓存，提高启动速度

**存储优化特性：**
- **移动模式**: 默认使用移动模式，导入文件后自动清理下载目录，节省存储空间
- **复制模式**: 可选择复制模式，保留原始文件作为备份
- **智能清理**: 移动模式下自动删除空目录，保持文件系统整洁

**支持的中文字体：**
- 文泉驿正黑 (WenQuanYi Zen Hei)
- 文泉驿微米黑 (WenQuanYi Micro Hei)
- AR PL UKai (楷体)
- AR PL UMing (明体)

### Docker部署优势
- **环境隔离**: 避免Python版本和依赖冲突
- **快速部署**: 一键启动，无需配置环境
- **数据持久化**: 通过Volume挂载保存数据
- **易于管理**: 支持容器编排和自动重启
- **跨平台**: 支持Windows、macOS和Linux
- **网络优化**: 国内网络环境下构建和下载速度更快
- **中文支持**: 完整的中文字体和显示支持

## 目录结构

```
/ssd/bioraw/data_manager/
├── index.html          # 主页面
├── styles.css          # 样式文件
├── app.js              # 前端JavaScript
├── backend.py          # 后端数据处理逻辑
├── server.py           # Web服务器
├── start.sh            # 启动脚本
└── README.md           # 说明文档

/ssd/biodata/raw/       # 数据存储目录
├── projects.json       # 项目数据文件
├── directory_tree.md   # 目录结构文档
├── PRJ001_项目名/      # 项目文件夹
│   ├── README.md       # 项目说明文档
│   ├── 转录组/         # 数据类型子目录
│   └── 文件...
└── ...

/ssd/bioraw/downloads/  # 下载目录
└── 待处理文件夹...
```

## 使用指南

### 创建新项目

1. 点击"项目管理"标签
2. 点击"创建新项目"按钮
3. 填写项目信息：
   - 项目标题
   - DOI（可选）
   - 数据库编号和链接（可选）
   - 数据类型
   - 物种
   - 作者和期刊信息
   - 项目描述
   - 标签
4. 可以上传引文文件（.enw或.ris格式）自动填充信息
5. 点击"创建项目"

### 导入下载数据

1. 将下载的文件夹放入 `/ssd/bioraw/downloads/` 目录
2. 点击"导入下载"标签
3. 系统会自动扫描并识别下载文件夹
4. 检查识别的信息（DOI、数据库编号、数据类型等）
5. 点击"预览"查看详细信息
6. 点击"导入"将数据移入项目库

### 浏览和管理数据

1. **仪表板**: 查看项目概览和统计信息
2. **项目管理**: 浏览、编辑、删除项目
3. **浏览数据**: 按类型查看项目和文件
4. **目录结构**: 查看完整的数据目录树

### 文件组织

系统支持按以下方式组织文件：

```
项目文件夹/
├── README.md           # 项目说明文档
├── 数据类型/
│   ├── 组织类型/
│   │   └── 数据文件...
│   └── 其他文件...
└── 其他文件...
```

## 支持的数据类型

### 转录组
- RNA-seq (.fastq, .sam, .bam)
- 单细胞RNA-seq (.h5ad, .mtx)
- 空间转录组

### 蛋白组学
- 蛋白组数据 (.raw, .mzml, .wiff)
- 磷酸化组数据

### 其他数据
- 质谱流式 (.fcs)
- 多组学数据
- 基因芯片数据

## 支持的数据库编号

- **GEO**: GSExxxxx, GSMxxxxx
- **ENA**: ERRxxxxx, SRRxxxxx
- **NCBI BioProject**: PRJNAxxxxx
- **ArrayExpress**: MTAB_xxxx
- **ProteomeXchange**: PXDxxxxx

## API接口

系统提供RESTful API接口：

### 项目管理
- `GET /api/projects` - 获取所有项目
- `POST /api/create-project` - 创建新项目
- `GET /api/project/{id}` - 获取特定项目
- `POST /api/update-project/{id}` - 更新项目
- `POST /api/delete-project/{id}` - 删除项目

### 文件操作
- `GET /api/scan-downloads` - 扫描下载目录
- `POST /api/import-download` - 导入下载文件
- `POST /api/organize-files` - 组织项目文件

### 目录管理
- `GET /api/directory-tree` - 获取目录树

## 常见问题

### Q: 如何修改数据存储目录？
A: 修改 `backend.py` 中的 `base_dir` 和 `download_dir` 参数，或启动时指定命令行参数。

### Q: 系统支持哪些引文文件格式？
A: 目前支持 EndNote (.enw) 和 RIS 格式的引文文件。

### Q: 如何批量导入多个项目？
A: 将多个文件夹放入下载目录，系统会自动识别每个文件夹，可以逐个或批量导入。

### Q: 项目文件被错误删除了怎么办？
A: 系统会在删除前提示确认，建议定期备份 `/ssd/biodata/raw/` 目录。

### Q: 如何更改服务器端口？
A: 修改启动脚本中的端口号，或使用 `python3 server.py 端口号` 指定端口。

## 技术支持

如有问题或建议，请：
1. 检查浏览器控制台的错误信息
2. 确认Python和目录权限设置正确
3. 查看系统日志输出

## 更新日志

### v1.0.0 (2024-01-XX)
- 初始版本发布
- 基础项目管理功能
- 下载目录扫描和导入
- 引文文件解析
- 目录树生成

---

*本系统专为生物信息学研究设计，致力于提高数据管理效率和研究可重现性。*