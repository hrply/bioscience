# 实验记录智能助手（防幻觉版）

## 核心特性
- **严格模板驱动**：所有实验记录基于预定义protocol模板
- **三重防幻觉保障**：约束提示词+验证层+用户确认
- **完整修订追踪**：记录每次修改的依据和历史

## 30秒快速开始
1. 安装依赖: `pip install -r requirements.txt`
2. 配置API密钥: `export QWEN_API_KEY=your_key`
3. 启动应用: `streamlit run main.py`
4. 首次使用: 上传一个基础protocol模板（或使用内置示例）

## 使用示例
1. 选择"细胞培养"基础模板
2. 描述修改："将培养基更换为DMEM+10%FBS，细胞密度调整为5000 cells/cm²"
3. 系统生成修订版，高亮显示修改部分
4. 确认无误后保存为本次实验方案

## 系统要求
- Python 3.10+
- 8GB内存（推荐）
- 支持本地运行，无需云依赖

## 防幻觉机制说明
- **严格模式**：AI只能基于模板和用户明确指令进行修改
- **验证层**：自动检查是否添加了模板不存在的章节或修改了不可修改部分
- **保守模式**：当验证失败时，仅应用最明确、最安全的修改

## 项目结构
```
lab_notebook_agent/
├── main.py                 # 主入口
├── requirements.txt        # 依赖清单
├── config/                 # 配置文件
│   ├── settings.py        # 应用设置
│   └── templates/         # 内置模板
├── core/                   # 核心模块
│   ├── agent_coordinator.py
│   ├── memory.py
│   ├── validation.py      # 防幻觉验证核心
│   └── tools.py
├── agents/                 # Agent层
│   ├── base_agent.py
│   ├── experiment_agent.py # 实验记录Agent
│   └── literature_agent.py
├── storage/                # 存储层
│   ├── experiment_store.py
│   ├── template_manager.py
│   └── backup_manager.py
├── interfaces/             # 界面层
│   └── streamlit_ui/
└── utils/                  # 工具类
    ├── diff_utils.py       # 差异对比
    ├── ai_helpers.py       # AI助手
    ├── pdf_utils.py        # PDF处理
    └── image_utils.py      # 图像处理
```

## 配置说明
主要配置项在 `config/settings.py` 中：
- API配置：支持通义千问和本地模型
- 防幻觉设置：严格模式、保守模式
- 存储配置：本地数据库路径
- 界面配置：高亮颜色等

## 扩展接口
系统采用模块化设计，支持无缝扩展：
- 新增Agent：继承BaseAgent类
- 新增工具：使用@register_tool装饰器
- 新增AI模型：扩展AIHelper类

## 技术栈
- **前端**：Streamlit
- **后端**：Python 3.10+
- **数据库**：SQLite + ChromaDB
- **AI模型**：通义千问API（可切换本地模型）
- **验证**：自定义防幻觉验证引擎