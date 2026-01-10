# AI科研助手 Dockerfile
# 支持多模型提供商和CLI工具的完整Docker镜像
# 基于Python 3.9 slim镜像 - 使用清华源加速构建

FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/ai_researcher \
    DEBIAN_FRONTEND=noninteractive \
    # 设置pip使用清华源
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple/ \
    PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

# ==================== 使用清华源配置 ====================

# 替换为清华源
RUN rm -f /etc/apt/sources.list.d/* && \
    rm -rf /etc/apt/sources.list

# 创建清华源sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ trixie main contrib non-free" > /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ trixie-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security trixie-security main contrib non-free" >> /etc/apt/sources.list

# 使用清华源更新包列表并安装系统依赖（最小化依赖）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    wget \
    git \
    build-essential \
    pkg-config \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 升级pip和安装基础包（使用清华源）
RUN pip install --upgrade pip setuptools wheel

# 复制依赖文件
COPY requirements.txt .

# ==================== 分阶段安装Python依赖 ====================
# 使用清华源 - 避免管道超时，优化构建速度

# 第一阶段：核心AI SDK（使用清华源）
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir openai>=1.0.0

# 第二阶段：Google Gemini和Anthropic SDK
RUN pip install --no-cache-dir google-generativeai>=0.3.0 anthropic>=0.7.0

# 第三阶段：iFlow SDK和CLI工具
RUN pip install --no-cache-dir iflow-cli-sdk>=0.1.0

# 第四阶段：数据处理库
RUN pip install --no-cache-dir pandas>=2.0.0 numpy>=1.24.0 scipy>=1.10.0

# 第五阶段：可视化库
RUN pip install --no-cache-dir matplotlib>=3.7.0 seaborn>=0.12.0 openpyxl>=3.1.0

# 第六阶段：知识库和数据库
RUN pip install --no-cache-dir requests>=2.31.0 pymongo>=4.5.0 chromadb>=0.4.0 faiss-cpu>=1.7.0

# 第七阶段：配置和工具
RUN pip install --no-cache-dir pyyaml>=6.0 click>=8.1.0 pydantic>=2.3.0 rich>=13.4.0 tqdm>=4.65.0 cryptography>=41.0.0

# 第八阶段：Web UI
RUN pip install --no-cache-dir streamlit>=1.28.0

# 第九阶段：实验管理
RUN pip install --no-cache-dir sqlalchemy>=2.0.0 alembic>=1.11.0

# 第十阶段：其他依赖
RUN pip install --no-cache-dir -r requirements.txt

# ==================== 创建必要目录 ====================
RUN mkdir -p /app/ai_researcher \
             /app/data/experiments \
             /app/data/results \
             /app/logs \
             /app/config \
             /app/templates \
             /app/examples

# ==================== 创建非root用户 ====================
RUN useradd -m -u 1000 researcher && \
    chown -R researcher:researcher /app

# 切换到非root用户
USER researcher

# ==================== 健康检查 ====================
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/_stcore/health || exit 1

# 暴露端口
EXPOSE 8000

# ==================== 设置启动命令 ====================
# 默认命令：启动Streamlit Web UI
CMD ["streamlit", "run", "ai_researcher/web_ui/main.py", \
     "--server.port=8000", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false"]

# ==================== 备用启动选项 ====================
# 如需启动CLI模式，可使用：
# CMD ["python", "-m", "ai_researcher.cli"]
