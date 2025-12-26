# 数据库示例说明 (DATABASE_SAMPLE_README.md)

## 概述

`group_tool_sample.db` 是项目的示例数据库，展示了系统的标准数据结构。该数据库包含一个示例实验，用于演示系统的功能。

## 数据库结构

### 1. 基础表

#### group_results - 分组结果表
- `id`: 分组结果的唯一标识符 (VARCHAR(10), PRIMARY KEY)
- `data`: JSON格式的分组结果数据 (TEXT NOT NULL)
- `group_count`: 分组数量 (INTEGER NOT NULL)
- `layers`: 使用的分层参数,逗号分隔 (TEXT)
- `timestamp`: 创建时间戳 (DATETIME, DEFAULT CURRENT_TIMESTAMP)

#### experiments - 实验信息表
- `id`: 实验ID (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `name`: 实验名称 (VARCHAR(100), UNIQUE, NOT NULL)
- `parameters`: 记录参数列表,逗号分隔 (TEXT, NOT NULL)
- `group_count`: 分组数量 (INTEGER, NOT NULL)
- `group_type`: 分组类型 (VARCHAR(20), NOT NULL) - "average"或"custom"
- `group_info`: 分组详细信息,JSON格式 (TEXT, NOT NULL)
- `created_at`: 创建时间戳 (DATETIME, DEFAULT CURRENT_TIMESTAMP)

#### experiment_charts - 图表缓存表
- `id`: 记录ID (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `experiment_name`: 实验名称 (VARCHAR(100), NOT NULL)
- `parameter_name`: 参数名称 (VARCHAR(50), NOT NULL)
- `file_path`: 图表文件路径 (TEXT, NOT NULL)
- `data_hash`: 数据哈希值 (VARCHAR(64), NOT NULL)
- `updated_at`: 更新时间戳 (DATETIME, DEFAULT CURRENT_TIMESTAMP)
- `display_format`: 显示格式 (VARCHAR(20), DEFAULT '原始数值')
- `day_zero_date`: Day0日期 (DATE)
- UNIQUE(experiment_name, parameter_name, display_format): 唯一约束

#### experiment_data_locks - 数据锁定表
- `id`: 记录ID (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `experiment_name`: 实验名称 (VARCHAR(100), NOT NULL)
- `date`: 数据日期 (DATE, NOT NULL)
- `is_locked`: 是否锁定 (BOOLEAN, NOT NULL, DEFAULT 0)
- `locked_at`: 锁定时间 (DATETIME)
- `locked_by`: 锁定用户 (VARCHAR(100))
- UNIQUE(experiment_name, date): 唯一约束

#### experiment_day_zero - Day0设置表
- `id`: 记录ID (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `experiment_name`: 实验名称 (VARCHAR(100), NOT NULL)
- `day_zero_date`: Day0日期 (DATE, NOT NULL)
- `created_at`: 创建时间戳 (DATETIME, DEFAULT CURRENT_TIMESTAMP)
- `updated_at`: 更新时间戳 (DATETIME, DEFAULT CURRENT_TIMESTAMP)
- UNIQUE(experiment_name): 唯一约束

### 2. 动态数据表

系统会为每个实验动态创建数据表，表名格式为 `experiment_data_<实验名称>`：

```
CREATE TABLE experiment_data_<实验名称> (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    group_name VARCHAR(50) NOT NULL,
    animal_id VARCHAR(50) NOT NULL,
    parameter_name VARCHAR(50) NOT NULL,
    parameter_value TEXT NOT NULL,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 3. 索引

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

## 示例数据

### 示例实验信息

```sql
INSERT INTO experiments (
    name, 
    parameters, 
    group_count, 
    group_type, 
    group_info
) VALUES (
    '示例实验',
    '体重,摄食量,体温',
    3,
    'average',
    '[{"name": "对照组", "animal_count": 10, "cage_animals": "5,5"}, {"name": "实验组A", "animal_count": 10, "cage_animals": "5,5"}, {"name": "实验组B", "animal_count": 10, "cage_animals": "5,5"}]'
);
```

这个示例实验展示了：
- 实验名称：示例实验
- 记录参数：体重、摄食量、体温
- 分组数量：3组
- 分组类型：平均分组
- 分组信息：对照组、实验组A、实验组B，每组10只动物，每笼5只

## 使用说明

1. **初始化项目时**：可以将 `group_tool_sample.db` 复制为 `group_tool.db` 作为起始数据库
2. **开发测试时**：示例实验可用于测试各项功能
3. **生产环境**：建议使用空的数据库结构，不包含示例数据

## 注意事项

1. 动态数据表的名称需要与实验名称完全匹配
2. 实验名称不能包含特殊字符，建议使用字母、数字、下划线和中文
3. 参数值存储为TEXT类型，支持数值和文本数据
4. 所有时间戳使用UTC时间，本地显示时会自动转换