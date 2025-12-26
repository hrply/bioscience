# 生物科学研究助手项目

## 项目概述

这是一个基于Python的生物科学研究助手系统，专为实验记录管理和协议修订而设计。项目采用防幻觉技术，确保AI辅助的实验记录修订严格基于预定义模板和用户明确指令。

### 核心特性

- **防幻觉修订系统**：三重约束保障（约束提示词+验证层+用户确认）
- **模板驱动**：所有实验记录基于预定义protocol模板
- **完整修订追踪**：记录每次修改的依据和历史
- **多Agent架构**：模块化设计，支持功能扩展
- **Streamlit界面**：直观的Web界面，支持实时修订预览

## 技术栈

- **前端**：Streamlit 1.28+
- **后端**：Python 3.10+
- **数据库**：SQLite + ChromaDB (向量数据库)
- **AI模型**：通义千问API (可切换本地模型)
- **验证**：自定义防幻觉验证引擎

## 项目结构

```
bioscience/research/helper/
├── main.py                    # 简化版主入口
├── requirements.txt           # 核心依赖
├── install_conda.sh          # Conda安装脚本
├── install_deps.sh           # 依赖安装脚本
├── exp.record/               # 主项目目录
│   ├── main.py              # 完整版主入口
│   ├── start.sh             # 快速启动脚本
│   ├── requirements.txt     # 完整依赖清单
│   ├── README.md            # 项目详细说明
│   ├── config/              # 配置模块
│   │   ├── settings.py      # 应用配置
│   │   └── templates/       # 内置模板
│   ├── core/                # 核心模块
│   │   ├── agent_coordinator.py  # MCP协调器
│   │   ├── memory.py        # 内存管理
│   │   ├── validation.py    # 防幻觉验证核心
│   │   └── tools.py         # 工具集
│   ├── agents/              # Agent层
│   │   ├── base_agent.py    # 基础Agent类
│   │   ├── experiment_agent.py  # 实验记录Agent
│   │   └── literature_agent.py   # 文献Agent
│   ├── storage/             # 存储层
│   │   ├── experiment_store.py   # 实验存储
│   │   ├── template_manager.py   # 模板管理
│   │   ├── backup_manager.py     # 备份管理
│   │   └── vector_db.py          # 向量数据库
│   ├── interfaces/          # 界面层
│   │   ├── cli.py          # 命令行界面
│   │   └── streamlit_ui/   # Streamlit界面
│   │       ├── home.py     # 首页
│   │       ├── experiments_tab.py  # 实验记录页
│   │       ├── templates_tab.py    # 模板管理页
│   │       └── revision_review.py  # 修订审核页
│   ├── utils/              # 工具类
│   │   ├── ai_helpers.py   # AI助手
│   │   ├── diff_utils.py   # 差异对比
│   │   ├── pdf_utils.py    # PDF处理
│   │   └── image_utils.py  # 图像处理
│   └── tests/              # 测试模块
```

## 快速开始

### 方法1：使用快速启动脚本（推荐）

```bash
cd exp.record
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

## 核心功能

### 1. 实验记录修订

- 基于预定义模板进行修订
- 三重防幻觉保障
- 实时差异对比
- 修订历史追踪

### 2. 模板管理

- 内置常用实验协议模板
- 支持自定义模板上传
- 模板版本控制
- 不可修改章节标记

### 3. 防幻觉验证

- **章节完整性检查**：防止添加不存在的章节
- **不可修改章节验证**：保护关键部分不被篡改
- **修改依据验证**：确保每个修改都有用户提示依据

### 4. 数据存储

- SQLite存储实验记录
- ChromaDB向量存储支持语义搜索
- 自动备份机制
- 数据导出功能

## 配置说明

主要配置项在 `config/settings.py` 中：

```python
# API配置
QWEN_API_KEY: 通义千问API密钥
QWEN_MODEL: 使用的模型版本

# 防幻觉配置
validation_enabled: 是否启用验证
strict_mode: 严格模式
conservative_mode: 保守模式

# 存储配置
data_dir: 数据存储目录
db_path: 数据库路径
vector_db_path: 向量数据库路径
```

## 开发指南

### 添加新Agent

1. 继承 `BaseAgent` 类
2. 实现 `process` 方法
3. 定义 `CAPABILITIES` 列表
4. 在 `AgentCoordinator` 中注册

```python
from agents.base_agent import BaseAgent

class NewAgent(BaseAgent):
    CAPABILITIES = ["new_capability"]
    
    async def process(self, request_data):
        # 实现处理逻辑
        pass
```

### 添加新工具

使用 `@register_tool` 装饰器：

```python
from core.agent_coordinator import register_tool

@register_tool("new_tool", description="新工具描述")
def new_tool_function(param1, param2):
    # 工具实现
    pass
```

### 扩展验证规则

在 `core/validation.py` 中添加新的验证器：

```python
class NewValidator:
    def validate(self, original, user_prompt, ai_output):
        # 验证逻辑
        pass
```

## API接口

### 实验修订API

```python
# 请求数据
request_data = {
    "template_id": "template_id",
    "user_modifications": "修改描述",
    "experiment_title": "实验标题",
    "strict_mode": True,
    "conservative_mode": False
}

# 响应数据
response = {
    "success": True,
    "revised_content": "修订后内容",
    "validation_result": {
        "is_valid": True,
        "confidence": 0.95,
        "issues": [],
        "warnings": []
    },
    "revision_markers": [...],
    "diff_comparison": {...}
}
```

## 故障排除

### 常见问题

1. **依赖安装失败**
   - 使用虚拟环境
   - 尝试国内镜像源
   - 更新pip版本

2. **API连接失败**
   - 检查API密钥配置
   - 验证网络连接
   - 确认API密钥有效性

3. **验证失败**
   - 检查模板格式
   - 确认用户指令明确性
   - 考虑使用保守模式

### 日志查看

```bash
# 查看应用日志
tail -f ~/.lab_notebook_agent/logs/app.log

# 查看错误日志
tail -f ~/.lab_notebook_agent/logs/error.log
```

## 性能优化

- 使用缓存减少API调用
- 异步处理提高响应速度
- 向量数据库加速语义搜索
- 分页加载大量数据

## 扩展计划

- 支持更多AI模型
- 增强验证规则
- 添加协作功能
- 集成文献数据库
- 支持多语言

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

*最后更新: 2025-12-10*