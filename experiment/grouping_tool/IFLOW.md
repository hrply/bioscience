# 生物科学分组工具

## 项目概述

这是一个基于 Flask 的科学分组工具，专为生物科学实验设计。该工具提供分层随机分组功能，可以根据指定的参数（如体重、摄食量等）对实验动物进行科学分组，确保各组间的参数分布均衡。系统采用智能优化算法，自动执行10次随机分组并返回最优结果。项目现已扩展为包含数据记录功能的综合实验管理平台，支持实验数据的录入、存储、可视化和导出。

系统具备完善的数据库迁移和版本管理功能，支持平滑升级和数据备份。通过多层次的密码保护机制和容器化部署，确保数据安全和系统稳定性。项目提供丰富的测试工具和详细的文档，便于开发和维护。

## 技术栈

- **后端**: Python 3.10 + Flask 3.1.2（已升级至最新版本以提高兼容性）
- **数据处理**: pandas 2.0.3, numpy <2.0
- **数据库**: SQLite (通过 SQLAlchemy 2.0.20)
- **前端**: HTML + CSS + JavaScript (原生)
- **可视化**: matplotlib 3.7.2 + matplotlib.dates
- **JSON处理**: orjson 3.9.10 (高性能JSON序列化)
- **容器化**: Docker + Docker Compose
- **其他依赖**: PyMySQL==1.1.0, requests==2.32.5

## 项目结构

```
grouping_tool/
├── app.py                    # 主应用程序文件（已优化，104 KB, 2730行）
├── requirements.txt          # Python 依赖
├── docker-compose.yml        # Docker 编排配置
├── Dockerfile               # Docker 镜像构建配置
├── README.md                # 项目说明
├── DOCKER-README.md         # Docker 部署说明
├── IFLOW.md                 # 项目文档
├── sample.csv               # 示例数据文件
├── group_tool.db            # SQLite 数据库文件(主数据库)
├── group_tool_sample.db     # 示例数据库文件
├── build.log                # Docker 构建日志
├── app.log                  # 应用程序日志文件
├── .dockerignore           # Docker 忽略文件
├── .env                    # 环境变量配置文件
├── DATABASE_SAMPLE_README.md      # 数据库示例和使用说明
├── __pycache__/            # Python 缓存目录
├── templates/              # HTML 模板目录
│   ├── index.html          # 主页界面
│   ├── scientific_grouping.html  # 科学分组界面
│   ├── fine_tuning.html    # 分组微调界面
│   ├── data_recording.html # 数据记录界面
│   ├── data_recording.html.backup # 数据记录界面备份
│   ├── data_export.html    # 数据导出界面
│   └── test_password_fixed.html # 密码验证测试页面
├── static/                 # 静态资源目录
│   └── test.html           # 测试页面
├── data/                   # 数据存储目录
│   ├── csv/                # CSV文件存储子目录
│   ├── images/             # 图片文件存储子目录
│   ├── results/            # 导出文件存储子目录
│   ├── group_tool.db       # 数据库文件
│   ├── debug.log           # 调试日志
│   └── test.log            # 测试日志
└── results/                # 导出文件存储目录（已移至data/results）
    └── *.csv               # 导出的分组结果文件和实验数据备份
```

## 核心功能

### 科学分组模块
1. **智能优化分组**: 系统自动执行10次随机分组，返回组间均值最接近、组内方差最小的最优结果
2. **参数化分组**: 支持自定义分组数量和参数类别
3. **分层随机化**: 基于指定参数进行分层，确保各组间参数分布均衡
4. **灵活分组方式**: 支持平均分组和自定义分组(精确控制每组大小)
5. **数据可视化**: 提供分组结果的表格展示和统计信息
6. **结果导出**: 支持将分组结果导出为 CSV 文件
7. **数据持久化**: 分组结果存储在 SQLite 数据库中
8. **中英文逗号支持**: 参数类别和分层随机化参数支持中英文逗号分隔

### 分组微调模块
9. **基础微调功能**: 支持对已有分组结果进行精细调整优化
10. **高级微调算法**: 提供更灵活的参数配置和优化策略，支持自定义模拟次数、抽样数量和迭代次数
11. **优化趋势追踪**: 实时跟踪优化过程和改进趋势，提供可视化反馈
12. **中英文逗号支持**: 参数类别和分层随机化参数支持中英文逗号分隔

### 数据记录模块
13. **实验管理**: 创建和管理多个实验，支持实验信息的增删改查
14. **参数配置**: 为每个实验自定义记录参数(如体重、摄食量等)
15. **分组配置**: 支持平均分组和自定义分组两种方式
16. **平均分组优化**: 平均分组时只需输入一次动物数量，其他组自动分配
17. **实时数据保存**: 输入数据时自动保存，防止网页刷新导致数据丢失
18. **数据锁定机制**: 点击保存后自动锁定数据，输入框变为灰色不可编辑
19. **数据解锁功能**: 提供"修改数据"按钮解锁已锁定的数据
20. **数据可视化**: 自动生成折线图展示各组数据变化趋势
21. **CSV备份**: 锁定数据时自动导出CSV备份文件
22. **动态表结构**: 为每个实验动态创建独立的数据表
23. **图表缓存**: SVG图表自动缓存，提升性能
24. **密码保护**: 数据记录模块支持密码保护功能
25. **Day0日期设置**: 支持为每个实验设置Day0基准日期

### 数据导出模块
26. **参数化导出**: 按参数导出实验数据，每个参数生成独立的CSV文件
27. **双格式支持**: 提供"实验记录格式"和"GraphPad分析格式"两种导出格式
28. **实验记录格式**: 动物按行连续排列，适合常规数据记录
29. **GraphPad分析格式**: 按最大动物数量组的动物数重复留空，便于GraphPad软件分析
30. **智能文件命名**: 按照"实验名称_参数名称_导出格式_导出日期.csv"格式自动命名
31. **文件信息标注**: 导出文件末尾自动添加实验名称、参数名称和导出时间信息
32. **在线下载**: 导出成功后提供下载按钮，支持直接下载CSV文件

### 图表生成优化（完整实现）
33. **智能Y轴范围计算**: 基于各组平均值±标准差(SD)计算Y轴范围，而非原始数据极值
34. **百分比格式优化**: 
   - min<100%时，向下取5%的整数倍（如38.4%→35%）
   - min≥100%时，向下取20%的整数倍（如137%→120%）
   - max<100%时，向上取5%的整数倍（如36.34%→40%）
   - max≥100%时，向上取50%的整数倍（如138%→150%，162%→200%）
35. **比值格式优化**:
   - max≤10时，向上取0.5的整数倍
   - max>10时，向上取1.0的整数倍（如221.9→222.0）
36. **多格式支持**: 支持原始数值、比值、百分比和对数四种显示格式
37. **对数格式支持**: 新增log10格式，支持对数变换的数据可视化
38. **图表文件缓存**: 自动缓存SVG图表，支持强制重新生成

## API 接口

### POST /api/group
执行分层随机分组

**请求体**:
```json
{
  "data": "CSV格式的字符串数据",
  "group_count": 3,
  "layers": ["体重", "摄食量"],
  "group_sizes": [10, 10, 10]  // 可选，自定义每组大小
}
```
注意：layers参数支持字符串格式，可使用中文逗号（，）或英文逗号（,）分隔

**响应**:
```json
{
  "id": "ABC123",
  "result": {
    "group_1": [...],
    "group_2": [...],
    "group_3": [...]
  }
}
```

### POST /api/save-results
保存分组结果到文件

**请求体**:
```json
{
  "csv_content": "CSV格式的分组结果",
  "result_id": "ABC123"
}
```

### POST /api/fine-tune
对已有分组结果进行精细调整

**请求体**:
```json
{
  "result_id": "ABC123",
  "simulations_count": 100,
  "min_extract_count": 1,
  "max_extract_count": 5
}
```

**响应**:
```json
{
  "id": "DEF456",
  "result": {
    "group_1": [...],
    "group_2": [...],
    "group_3": [...]
  },
  "trend_data": [...],
  "statistics": {
    "original_variance": 0.5,
    "final_variance": 0.3,
    "improvement": 0.2
  }
}
```

### POST /api/advanced-fine-tuning
高级分组微调API端点

**请求体**:
```json
{
  "data": "CSV格式的字符串数据",
  "layers": ["体重", "摄食量"],
  "simulation_count": 100,
  "sample_size": 1,
  "iteration_count": 5
}
```
注意：layers参数支持字符串格式，可使用中文逗号（，）或英文逗号（,）分隔

**响应**:
```json
{
  "id": "GHI789",
  "trend_data": [...],
  "statistics": {
    "best_sample_size": 2,
    "min_variance": 0.25,
    "improvement": 0.25
  }
}
```

### GET /api/test-db
测试数据库连接和存储功能

### GET /api/experiments
获取所有实验名称列表

**响应**:
```json
{
  "experiments": ["实验1", "实验2", "实验3"]
}
```

### POST /api/experiments
创建新实验或更新已有实验

**请求体**:
```json
{
  "experiment_name": "实验名称",
  "parameters": "体重,摄食量,活动量",
  "group_count": 3,
  "group_type": "average",
  "group_info": [
    {"name": "对照组", "animal_count": 10, "cage_animals": "5,5"},
    {"name": "实验组A", "animal_count": 10, "cage_animals": "5,5"},
    {"name": "实验组B", "animal_count": 10, "cage_animals": "5,5"}
  ]
}
```

**响应**:
```json
{
  "status": "success",
  "message": "实验创建成功"
}
```

### GET /api/experiments/<experiment_name>
获取特定实验的详细信息

**响应**:
```json
{
  "parameters": "体重,摄食量,活动量",
  "group_count": 3,
  "group_type": "average",
  "group_info": [
    {"name": "对照组", "animal_count": 10, "cage_animals": "5,5"},
    {"name": "实验组A", "animal_count": 10, "cage_animals": "5,5"},
    {"name": "实验组B", "animal_count": 10, "cage_animals": "5,5"}
  ]
}
```

### POST /api/experiment-data
保存实验数据

**请求体**:
```json
{
  "experiment_name": "实验名称",
  "date": "2025-01-16",
  "data": [
    {
      "animal_id": "WT-01",
      "group_name": "对照组",
      "体重": 18.6,
      "摄食量": 5.2
    }
  ]
}
```

**响应**:
```json
{
  "status": "success",
  "message": "数据保存成功"
}
```

### GET /api/experiment-data/<experiment_name>
获取实验数据用于可视化

**响应**:
```json
{
  "data": {
    "体重": {
      "对照组": {
        "dates": ["2025-01-16", "2025-01-17"],
        "values": [18.5, 18.7]
      },
      "实验组A": {
        "dates": ["2025-01-16", "2025-01-17"],
        "values": [19.2, 19.5]
      }
    }
  },
  "parameters": ["体重", "摄食量"]
}
```

### GET /data/<filename>
提供data目录下的文件访问(用于SVG图表等静态资源)

### POST /api/export-experiment-data
导出实验数据为CSV格式

**请求体**:
```json
{
  "experiment_name": "实验名称",
  "parameter_name": "参数名称",
  "export_format": "实验记录格式"  // 或 "GraphPad分析格式"
}
```

**响应**:
```json
{
  "status": "success",
  "filename": "实验名称_参数名称_导出格式_2025-01-16.csv",
  "filepath": "/path/to/file.csv",
  "message": "数据导出成功"
}
```

### GET /api/download-export/<filename>
下载导出的CSV文件

### POST /api/experiment-data/realtime
实时保存单个数据点

**请求体**:
```json
{
  "experiment_name": "实验名称",
  "date": "2025-01-16",
  "animal_id": "动物编号",
  "group_name": "组别名称",
  "parameter_name": "参数名称",
  "parameter_value": "参数值"
}
```

**响应**:
```json
{
  "status": "success",
  "message": "数据保存成功"
}
```

### POST /api/experiment-data/lock
锁定实验数据

**请求体**:
```json
{
  "experiment_name": "实验名称",
  "date": "2025-01-16",
  "locked_by": "用户标识"
}
```

**响应**:
```json
{
  "status": "success",
  "message": "数据已锁定并导出"
}
```

### POST /api/experiment-data/unlock
解锁实验数据

**请求体**:
```json
{
  "experiment_name": "实验名称",
  "date": "2025-01-16"
}
```

**响应**:
```json
{
  "status": "success",
  "message": "数据已解锁"
}
```

### GET /api/experiment-data/lock-status
获取实验数据锁定状态

**查询参数**:
- experiment_name: 实验名称
- date: 日期

**响应**:
```json
{
  "is_locked": true,
  "locked_at": "2025-01-16 10:30:00",
  "locked_by": "用户标识"
}
```

### POST /api/experiment-data/overwrite
强制覆写实验数据

**请求体**:
```json
{
  "experiment_name": "实验名称",
  "date": "2025-01-16",
  "data": [
    {
      "animal_id": "WT-01",
      "group_name": "对照组",
      "体重": 18.6,
      "摄食量": 5.2
    }
  ]
}
```

**响应**:
```json
{
  "status": "success",
  "message": "数据覆写成功"
}
```

### GET /api/experiment-data/<experiment_name>/<date>
获取特定实验特定日期的数据

**响应**:
```json
{
  "data": [
    {
      "animal_id": "WT-01",
      "group_name": "对照组",
      "体重": 18.6,
      "摄食量": 5.2,
      "recorded_at": "2025-01-16 10:30:00"
    }
  ],
  "is_locked": false
}
```

### GET /api/experiment-charts/<experiment_name>
获取实验图表缓存信息（支持多种显示格式）

**查询参数**:
- display_format: 显示格式（可选，默认为"原始数值"）
  - "原始数值": 显示原始数据值
  - "比值": 显示相对于Day0的比值
  - "百分比": 显示相对于Day0的百分比
  - "对数值": 显示对数变换的值
- force: 是否强制重新生成图表（可选，默认为false）
- day_zero_date: 自定义Day0日期（可选，格式：YYYY-MM-DD）

**响应**:
```json
{
  "charts": [
    {
      "parameter_name": "体重",
      "file_path": "/data/实验名称_体重_abc123.svg",
      "display_format": "百分比",
      "updated_at": "2025-01-16 10:30:00"
    }
  ],
  "parameters": ["体重", "摄食量"],
  "display_format": "百分比",
  "day_zero_date": "2025-01-16"
}
```

### GET /api/experiment-day-zero/<experiment_name>
获取实验的Day0日期

**响应**:
```json
{
  "day_zero_date": "2025-01-16"
}
```

### POST /api/experiment-day-zero
设置或更新实验的Day0日期

**请求体**:
```json
{
  "experiment_name": "实验名称",
  "day_zero_date": "2025-01-16"
}
```

**响应**:
```json
{
  "status": "success",
  "message": "Day0日期设置成功"
}
```

## Web 界面路由

### GET /
主页界面，提供功能导航

### GET /scientific-grouping
科学分组界面，支持分组参数设置和结果查看

### GET /fine-tuning
分组微调界面，提供分组结果优化功能

### GET /data-recording
数据记录界面，支持实验数据的录入和管理

### GET /data-export
数据导出界面，支持按参数导出实验数据为CSV格式

### GET /test
测试页面，用于验证应用运行状态

### GET /test-fixed
密码验证测试页面，用于测试密码修复功能

## 数据库结构

### `group_results` 表
存储科学分组结果

- `id`: 分组结果的唯一标识符 (VARCHAR(10), PRIMARY KEY)
- `data`: JSON格式的分组结果数据 (TEXT NOT NULL)
- `group_count`: 分组数量 (INTEGER NOT NULL)
- `layers`: 使用的分层参数,逗号分隔 (TEXT)
- `timestamp`: 创建时间戳 (DATETIME, DEFAULT CURRENT_TIMESTAMP)

### `experiments` 表
存储实验基本信息

- `id`: 实验ID (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `name`: 实验名称 (VARCHAR(100), UNIQUE, NOT NULL)
- `parameters`: 记录参数列表,逗号分隔 (TEXT, NOT NULL)
- `group_count`: 分组数量 (INTEGER, NOT NULL)
- `group_type`: 分组类型 (VARCHAR(20), NOT NULL) - "average"或"custom"
- `group_info`: 分组详细信息,JSON格式 (TEXT, NOT NULL)
- `created_at`: 创建时间戳 (DATETIME, DEFAULT CURRENT_TIMESTAMP)

### `experiment_data_<实验名称>` 动态表
为每个实验动态创建的数据记录表

- `id`: 记录ID (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `date`: 记录日期 (DATE, NOT NULL)
- `group_name`: 分组名称 (VARCHAR(50), NOT NULL)
- `animal_id`: 动物编号 (VARCHAR(50), NOT NULL)
- `parameter_name`: 参数名称 (VARCHAR(50), NOT NULL)
- `parameter_value`: 参数值 (TEXT, NOT NULL)
- `recorded_at`: 记录时间戳 (DATETIME, DEFAULT CURRENT_TIMESTAMP)

### `experiment_data_locks` 表
存储实验数据锁定状态

- `id`: 记录ID (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `experiment_name`: 实验名称 (VARCHAR(100), NOT NULL)
- `date`: 数据日期 (DATE, NOT NULL)
- `is_locked`: 是否锁定 (BOOLEAN, NOT NULL, DEFAULT 0)
- `locked_at`: 锁定时间 (DATETIME)
- `locked_by`: 锁定用户 (VARCHAR(100))
- UNIQUE(experiment_name, date): 唯一约束

### `experiment_charts` 表
存储实验图表缓存信息

- `id`: 记录ID (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `experiment_name`: 实验名称 (VARCHAR(100), NOT NULL)
- `parameter_name`: 参数名称 (VARCHAR(50), NOT NULL)
- `file_path`: 图表文件路径 (TEXT, NOT NULL)
- `data_hash`: 数据哈希值 (VARCHAR(64), NOT NULL)
- `updated_at`: 更新时间戳 (DATETIME, DEFAULT CURRENT_TIMESTAMP)
- `display_format`: 显示格式 (VARCHAR(20), DEFAULT '原始数值')
- `day_zero_date`: Day0日期 (DATE)
- UNIQUE(experiment_name, parameter_name, display_format): 唯一约束

### `experiment_day_zero` 表
存储实验Day0日期设置

- `id`: 记录ID (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `experiment_name`: 实验名称 (VARCHAR(100), NOT NULL)
- `day_zero_date`: Day0日期 (DATE, NOT NULL)
- `created_at`: 创建时间戳 (DATETIME, DEFAULT CURRENT_TIMESTAMP)
- `updated_at`: 更新时间戳 (DATETIME, DEFAULT CURRENT_TIMESTAMP)
- UNIQUE(experiment_name): 唯一约束

## 数据库索引

为了提高查询性能，系统创建了以下索引：

- `idx_experiments_name`: 实验名称索引
- `idx_experiments_created_at`: 实验创建时间索引
- `idx_group_results_timestamp`: 分组结果时间戳索引
- `idx_experiment_charts_exp_name`: 图表实验名称索引
- `idx_experiment_charts_param_name`: 图表参数名称索引
- `idx_experiment_charts_updated_at`: 图表更新时间索引
- `idx_data_locks_exp_name`: 数据锁定实验名称索引
- `idx_data_locks_date`: 数据锁定日期索引
- `idx_day_zero_exp_name`: Day0设置实验名称索引

## 数据库迁移和版本管理

### 迁移功能概述
系统支持数据库版本升级和数据迁移，确保在项目更新过程中数据的完整性和一致性。

### 迁移流程
1. **备份原数据库**: 自动创建备份文件
2. **创建新数据库**: 生成符合新结构的目标数据库
3. **数据迁移**: 完整保留所有原有数据，包括分组结果、实验配置和数据记录
4. **验证完整性**: 确保迁移后数据完整性和结构一致性

### 迁移文件说明
- `group_tool.db`: 当前使用的主数据库文件
- `group_tool_sample.db`: 示例数据库文件，用于测试和演示
- `DATABASE_SAMPLE_README.md`: 数据库示例和使用说明

### 版本管理特性
- **向后兼容**: 支持从旧版本平滑升级到新版本
- **数据完整性**: 迁移过程中保证所有数据完整保留
- **回滚支持**: 通过备份文件支持版本回滚
- **自动检测**: 系统启动时自动检测数据库版本和结构
- **文档记录**: 完整的迁移文档和变更记录

## 构建和运行

### 本地开发环境

1. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

2. **运行应用**:
   ```bash
   python app.py
   ```
   应用将在 http://localhost:8080 上运行

### Docker 环境

1. **构建并运行容器**:
   ```bash
   docker-compose up --build
   ```
   应用将在 http://localhost:20425 上运行

2. **后台运行容器**:
   ```bash
   docker-compose up -d
   ```

3. **停止容器**:
   ```bash
   docker-compose down
   ```

4. **数据记录模块的Docker支持**:
   - 数据库文件自动挂载到容器内
   - 实验数据CSV备份自动保存到 `./data/results` 目录
   - 数据记录文件保存在 `./data` 目录
   - 容器启动时自动初始化数据库表结构
   - SVG图表文件缓存在 `./data/images` 目录

5. **Docker构建特性**:
   - 支持中文字体配置(通过enable_zh_CN参数)
   - 使用清华大学镜像源(中国环境)
   - 多阶段构建优化镜像大小
   - 健康检查确保服务可用性
   - 资源限制配置(512M内存限制,256M内存预留)
   - 多级密码配置策略(构建参数 > 环境变量 > 默认值)
   - 数据库文件自动挂载和备份机制
   - 容器启动时自动检查和初始化数据库结构
   - 网络配置支持外部网络(baota_net)

## 开发约定

1. **代码风格**: 遵循 PEP 8 Python 代码规范
2. **数据库操作**: 使用 SQLAlchemy 进行数据库操作，确保连接正确关闭
3. **错误处理**: API 端点包含适当的错误处理和验证
4. **数据验证**: 对输入数据进行严格验证，确保数据完整性和正确性
5. **文件编码**: 使用 UTF-8 编码处理文件，确保中文支持
6. **容器化**: 使用多阶段构建优化 Docker 镜像大小
7. **健康检查**: 配置容器健康检查确保服务可用性
8. **资源管理**: Docker 环境中配置了内存限制和预留设置
9. **性能优化**: 使用orjson库提升JSON序列化性能
10. **图表缓存**: SVG图表自动缓存，避免重复生成
11. **字体配置**: 根据环境变量动态配置中英文字体
12. **代码优化**: 已移除所有debug代码，代码体积优化至104KB（2730行）

## 使用说明

### 科学分组模块使用流程
1. **设置分组参数**：动物总数、参数类别、分组组数等
2. **输入实验数据**：可手动输入或上传 CSV 文件
3. **执行分组**：系统将根据设定的分层参数进行智能优化分组(自动执行10次取最优)
4. **查看结果**：系统显示分组结果和各组参数统计信息
5. **导出结果**：可将分组结果导出为 CSV 文件,保存至 `data/results/` 目录

### 分组微调模块使用流程
6. **基础微调**：输入分组结果ID,设置模拟次数和抽样范围,进行精细调整
7. **高级微调**：使用更灵活的参数配置(模拟次数、抽样数量、迭代次数)进行深度优化
8. **查看优化趋势**：系统显示优化过程的趋势图和改进统计

### 数据记录模块使用流程
9. **创建实验**：输入实验名称、记录参数(如体重、摄食量)、分组信息
10. **配置分组**：选择平均分组或自定义分组,设置每组名称和大小
11. **设置Day0**：为实验设置基准日期，用于数据标准化显示
12. **录入数据**：选择实验和日期,按分组和动物编号录入各项参数数据
13. **实时保存**：输入数据时系统自动保存,防止意外丢失
14. **数据锁定**：点击"保存数据"按钮锁定当天的数据,输入框变为灰色
15. **解锁修改**：如需修改已锁定数据,点击"修改数据"按钮解锁
16. **查看图表**：系统自动生成折线图,展示各组各参数的变化趋势
17. **导出备份**：锁定数据时自动导出CSV备份文件,保存至 `data/results/` 目录
18. **密码保护**：可通过环境变量或构建参数设置数据记录模块访问密码

### 数据导出模块使用流程
19. **选择实验**：从下拉列表中选择要导出的实验
20. **选择参数**：选择要导出的参数(如体重、摄食量等)
21. **选择格式**：选择"实验记录格式"或"GraphPad分析格式"
22. **执行导出**：点击"导出数据"按钮生成CSV文件
23. **下载文件**：导出成功后点击"下载CSV文件"按钮下载
24. **文件命名**：导出文件自动命名为"实验名称_参数名称_导出格式_导出日期.csv"
25. **文件内容**：CSV文件包含组别名称、笼号、动物编号和各日期数据,末尾包含实验信息

### 图表查看使用流程
26. **选择显示格式**：可选择原始数值、比值、百分比或对数值格式
27. **自动Y轴调整**：Y轴范围基于各组平均值±标准差自动计算
28. **百分比格式**：按照5%或20%的整数倍自动调整刻度
29. **比值格式**：按照0.5或1.0的整数倍自动调整刻度
30. **图表缓存**：相同数据自动使用缓存，提升加载速度
31. **对数格式**：支持log10格式，适用于大范围数据变化

## 算法特点

### 分层随机分组算法
- 使用 pandas.cut 将连续变量分为5个等宽区间
- 基于分层键进行分组，确保各层在组间分布均衡
- 支持自定义分组大小，精确控制每组样本数量

### 智能优化算法
- 执行多次随机分组（默认10次）
- 评估分组质量：组间均值方差 + 组内方差
- 返回最优分组结果

### 微调算法
- 提取并重分配策略
- 多次模拟优化（可配置模拟次数）
- 提供改进趋势数据

### 高级微调算法
- 支持自定义模拟次数、抽样数量和迭代次数
- 提供更细粒度的优化控制
- 实时跟踪优化过程和改进趋势
- 从M到M+a的迭代过程，寻找最优抽样数量

### 图表生成算法
- 使用matplotlib生成SVG格式图表
- 支持中英文字体动态切换
- 自动检测数值型参数进行可视化
- 文件缓存机制提升性能
- Y轴范围基于平均值±SD智能计算
- 支持多种数据格式转换（原始、比值、百分比、对数）
- 智能刻度调整算法，优化图表可读性

## 注意事项

### 科学分组相关
- 分组参数必须是数值型数据
- 分层随机化参数应存在于输入数据中
- 自定义分组时,各组大小之和必须等于动物总数
- 系统会自动执行10次随机分组,返回组间均值方差最小的最优结果
- 分组结果会自动存储在数据库中,并生成唯一ID用于后续微调
- 参数类别和分层随机化参数支持中英文逗号分隔

### 分组微调相关
- 微调功能需要提供原始分组结果的ID
- 高级微调算法支持多种参数组合,可根据实验需求灵活调整
- 建议模拟次数设置在100-1000之间,以平衡优化效果和计算时间
- 抽样数量建议从1开始,逐步增加到5-10,观察优化趋势
- 参数类别和分层随机化参数支持中英文逗号分隔

### 数据记录相关
- 实验名称必须唯一,不能重复
- 记录参数名称使用逗号分隔,支持中文
- 每个实验会动态创建独立的数据表,表名格式为 `experiment_data_<实验名称>`
- 输入数据时系统自动实时保存,防止网页刷新或意外关闭导致数据丢失
- 点击"保存数据"按钮后自动锁定数据,输入框变为灰色不可编辑
- 锁定的数据无法修改,需要点击"修改数据"按钮解锁后方可编辑
- 数据录入时,只有数值型参数会被用于可视化图表
- CSV备份文件命名格式为 `<实验名称>_<日期>.csv`
- SVG图表文件缓存在data/images目录,支持强制重新生成
- 平均分组时只需输入一次动物数量，系统自动分配到其他组
- Day0日期设置用于标准化数据展示，便于比较不同时间点的数据变化

### 数据导出相关
- 导出数据前必须选择实验名称和参数名称
- 实验记录格式适合常规数据记录,动物按行连续排列
- GraphPad分析格式适合统计分析,按照最大动物数量组的动物数重复留空
- 导出文件格式为CSV,使用UTF-8-sig编码确保中文兼容性
- 导出文件末尾自动添加实验名称、参数名称和导出时间信息
- 导出的文件保存在 `data/results/` 目录

### 图表相关
- 图表Y轴范围基于各组平均值±标准差计算，避免极端值影响
- 百分比格式自动按规则调整刻度（5%或20%的倍数）
- 比值格式自动按规则调整刻度（0.5或1.0的倍数）
- 支持四种显示格式：原始数值、比值、百分比、对数值
- 图表文件自动缓存，相同数据不会重复生成
- 可通过force参数强制重新生成图表
- 对数格式适用于大范围数据变化，特别适合生物学实验数据

### 系统相关
- 结果文件保存在 `data/results/` 目录
- 数据库文件 `group_tool.db` 会自动创建并持久化存储所有数据
- 系统默认使用 UTF-8-sig 编码保存 CSV 文件,确保中文兼容性
- Docker 环境中配置了资源限制(512M内存)和健康检查,确保服务稳定性
- 数据记录模块使用 `/data` 目录进行数据持久化存储
- 容器重启后会保持数据库和结果文件的完整性
- 应用运行在80端口(容器内部),通过20425端口(宿主机)访问
- 支持通过环境变量enable_zh_CN控制中文字体支持
- 数据记录模块密码可通过多种方式配置(环境变量、构建参数、默认值)
- 数据库迁移功能支持版本升级和数据备份
- 项目已清理开发阶段的测试文件，保持代码库整洁

### 性能优化
- 使用orjson库替代标准json库,提升序列化性能
- SVG图表文件自动缓存,避免重复计算
- matplotlib字体配置全局化,避免重复设置
- 数据库连接池管理,提升并发性能
- 静态资源服务优化,支持文件缓存
- 数据库索引优化查询性能
- 代码已优化，移除所有debug代码，体积104KB（2730行）
- 图表智能缓存机制，支持数据变更检测

### 安全性
- 数据记录模块支持密码保护(默认密码: data2024)
- 输入数据严格验证,防止SQL注入
- 文件访问路径限制,防止目录遍历攻击
- 错误信息过滤,避免敏感信息泄露
- 密码可通过环境变量DATA_RECORDING_PASSWORD或Docker构建参数配置
- 提供密码验证测试页面(/test-fixed)用于验证密码功能
- 数据库迁移前自动创建备份文件,确保数据安全
- 支持多级密码配置策略,优先使用环境变量和构建参数
- 容器环境中的敏感信息通过环境变量传递,避免硬编码

### 测试功能
- /test: 基础测试页面，验证应用运行状态
- /test-fixed: 密码验证测试页面，用于测试密码修复功能
- /api/test-db: 数据库连接测试API端点
- 支持实时数据保存和覆写功能
- 提供数据锁定/解锁状态查询API
- DATABASE_SAMPLE_README.md: 数据库示例和使用说明
- 项目已清理开发测试文件，保留核心功能模块

## 项目版本信息

### 当前版本状态
- **版本标识**: final v2 (Git commit: 4ff6287)
- **代码规模**: 主应用文件104KB，2730行代码
- **功能完整性**: 所有核心模块已实现并经过测试
- **图表系统**: 完整支持四种显示格式（原始、比值、百分比、对数）
- **数据库**: SQLite数据库，支持完整的CRUD操作和数据迁移
- **容器化**: Docker支持完整，包含健康检查和资源限制
- **国际化**: 完整的中英文支持，动态字体配置

### 近期更新
- 完成百分比和比值格式的图表显示功能
- 实现对数格式支持，扩展数据可视化能力
- 优化Y轴范围计算算法，基于统计标准差
- 清理开发阶段测试文件，代码库更加整洁
- 完善Docker配置，支持生产环境部署
- 增强数据导出功能，支持多种格式和自动命名

### 技术债务清理
- 移除所有debug测试文件（debug_*.py, test_*.py等）
- 优化代码结构，提升可维护性
- 统一错误处理和日志记录
- 完善API文档和接口规范
- 增强数据验证和安全性检查