# 生物信息学数据管理系统 Docker镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONIOENCODING=utf-8

# 完全替换为清华源 - 移除所有官方源
RUN rm -f /etc/apt/sources.list.d/* && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ trixie main contrib non-free" > /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ trixie-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security trixie-security main contrib non-free" >> /etc/apt/sources.list

# 更新包列表并安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    wget \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    fonts-arphic-ukai \
    fonts-arphic-uming \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# 安装高性能Python库
RUN pip3 install --no-cache-dir \
    aiofiles==23.2.0 \
    watchdog==3.0.0

# 复制pip配置文件（只对pip使用清华源）
COPY pip.conf /etc/pip.conf

# 安装Python依赖包
RUN pip3 install --no-cache-dir watchdog

# 配置字体缓存
RUN fc-cache -fv


# 创建必要的目录
RUN mkdir -p /bioraw/data /bioraw/downloads /bioraw/results /bioraw/analysis /app

# 复制应用代码文件
COPY app/ /app/

# 设置权限
RUN chmod +x /app/backend.py /app/server.py /app/docker-entrypoint.sh

# 暴露端口
EXPOSE 8000

# 设置启动命令
CMD ["/app/docker-entrypoint.sh"]