# Multi-stage build for smaller image size
FROM python:3.10-slim AS builder

# Configure sources and install dependencies based on enable_zh_CN environment variable
ARG enable_zh_CN=TRUE
ENV enable_zh_CN=${enable_zh_CN}

# Configure mirrors immediately after base image
RUN if [ "$enable_zh_CN" = "TRUE" ]; then \
        echo "Configuring Tsinghua mirrors for faster downloads..." && \
        rm -f /etc/apt/sources.list.d/debian.sources && \
        echo "Types: deb" > /etc/apt/sources.list.d/debian.sources && \
        echo "URIs: https://mirrors.tuna.tsinghua.edu.cn/debian" >> /etc/apt/sources.list.d/debian.sources && \
        echo "Suites: trixie trixie-updates" >> /etc/apt/sources.list.d/debian.sources && \
        echo "Components: main contrib non-free non-free-firmware" >> /etc/apt/sources.list.d/debian.sources && \
        echo "Signed-By: /usr/share/keyrings/debian-archive-keyring.pgp" >> /etc/apt/sources.list.d/debian.sources && \
        echo "" >> /etc/apt/sources.list.d/debian.sources && \
        echo "Types: deb" >> /etc/apt/sources.list.d/debian.sources && \
        echo "URIs: https://mirrors.tuna.tsinghua.edu.cn/debian-security" >> /etc/apt/sources.list.d/debian.sources && \
        echo "Suites: trixie-security" >> /etc/apt/sources.list.d/debian.sources && \
        echo "Components: main" >> /etc/apt/sources.list.d/debian.sources && \
        echo "Signed-By: /usr/share/keyrings/debian-archive-keyring.pgp" >> /etc/apt/sources.list.d/debian.sources && \
        apt-get clean; \
    fi

# Set working directory
WORKDIR /app

# Configure pip mirror before installing dependencies
RUN if [ "$enable_zh_CN" = "TRUE" ]; then \
        echo "Configuring pip to use Tsinghua mirror..." && \
        pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/ && \
        pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn; \
    else \
        echo "Using default pip sources"; \
    fi

# Copy requirements file first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set data recording password with multiple fallback options
# Priority 1: --build-arg DATA_RECORDING_PASSWORD (highest)
# Priority 2: Environment variable from docker-compose.yml
# Priority 3: Default value (fallback)
ARG DATA_RECORDING_PASSWORD=data2024
ENV DATA_RECORDING_PASSWORD=${DATA_RECORDING_PASSWORD}

# Install Chinese fonts if enable_zh_CN is TRUE
RUN if [ "$enable_zh_CN" = "TRUE" ]; then \
        echo "Installing Chinese fonts..." && \
        apt-get update && \
        apt-get install -y --no-install-recommends fonts-wqy-zenhei fonts-wqy-microhei && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*; \
    else \
        echo "No Chinese fonts installed"; \
    fi

# Production stage
FROM python:3.10-slim AS production

# Configure environment variables
ARG enable_zh_CN=TRUE
ENV enable_zh_CN=${enable_zh_CN}

# Configure mirrors for production stage
RUN if [ "$enable_zh_CN" = "TRUE" ]; then \
        echo "Configuring Tsinghua mirrors for production stage..." && \
        rm -f /etc/apt/sources.list.d/debian.sources && \
        echo "Types: deb" > /etc/apt/sources.list.d/debian.sources && \
        echo "URIs: https://mirrors.tuna.tsinghua.edu.cn/debian" >> /etc/apt/sources.list.d/debian.sources && \
        echo "Suites: trixie trixie-updates" >> /etc/apt/sources.list.d/debian.sources && \
        echo "Components: main contrib non-free non-free-firmware" >> /etc/apt/sources.list.d/debian.sources && \
        echo "Signed-By: /usr/share/keyrings/debian-archive-keyring.pgp" >> /etc/apt/sources.list.d/debian.sources && \
        echo "" >> /etc/apt/sources.list.d/debian.sources && \
        echo "Types: deb" >> /etc/apt/sources.list.d/debian.sources && \
        echo "URIs: https://mirrors.tuna.tsinghua.edu.cn/debian-security" >> /etc/apt/sources.list.d/debian.sources && \
        echo "Suites: trixie-security" >> /etc/apt/sources.list.d/debian.sources && \
        echo "Components: main" >> /etc/apt/sources.list.d/debian.sources && \
        echo "Signed-By: /usr/share/keyrings/debian-archive-keyring.pgp" >> /etc/apt/sources.list.d/debian.sources && \
        apt-get clean; \
    fi

# Set working directory
WORKDIR /app

# Install Chinese fonts if enable_zh_CN is TRUE (for production stage)
RUN if [ "$enable_zh_CN" = "TRUE" ]; then \
        echo "Installing Chinese fonts in production stage..." && \
        apt-get update && \
        apt-get install -y --no-install-recommends fonts-wqy-zenhei fonts-wqy-microhei && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*; \
    else \
        echo "No Chinese fonts installed"; \
    fi

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser

# Create directories for storing data
RUN mkdir -p /data/csv /data/images /data/results

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application files
COPY . .

# Change ownership of app directory to appuser
RUN chown -R appuser:appuser /app /data

# Switch to non-root user
USER appuser

# Configure environment variables
ARG enable_zh_CN=TRUE
ENV enable_zh_CN=${enable_zh_CN}
ARG DATA_RECORDING_PASSWORD=data2024
ENV DATA_RECORDING_PASSWORD=${DATA_RECORDING_PASSWORD}
ENV DOCKER_ENV=true
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
# Fix JSON encoding for Chinese characters
ENV JSON_AS_ASCII=false

# Expose port 8080 (internal port, external port is set in docker-compose.yml)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/', timeout=5)" || exit 1

# Create font configuration script
RUN echo '#!/bin/bash\n\
if [ "$enable_zh_CN" = "TRUE" ]; then\n\
    echo "Setting up Chinese fonts for matplotlib..."\n\
    python -c "import matplotlib.pyplot as plt; plt.rcParams[\"font.sans-serif\"] = [\"WenQuanYi Zen Hei\", \"DejaVu Sans\", \"sans-serif\"]; plt.rcParams[\"axes.unicode_minus\"] = False; print(\"Chinese fonts configured\")"\n\
else\n\
    echo "Setting up English fonts for matplotlib..."\n\
    python -c "import matplotlib.pyplot as plt; plt.rcParams[\"font.sans-serif\"] = [\"DejaVu Sans\", \"sans-serif\"]; plt.rcParams[\"axes.unicode_minus\"] = False; print(\"English fonts configured\")"\n\
fi' > /app/setup_fonts.sh && chmod +x /app/setup_fonts.sh

# Initialize database, setup fonts and run the application
CMD ["sh", "-c", "/app/setup_fonts.sh && python -c 'from app import init_db; init_db()' && python app.py"]