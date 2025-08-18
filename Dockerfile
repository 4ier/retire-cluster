# ======================================================
# Stage 1: Builder
# ======================================================
FROM python:3.9-slim as builder

# 可选代理参数（构建时传入）
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ENV HTTP_PROXY=${HTTP_PROXY} \
    HTTPS_PROXY=${HTTPS_PROXY} \
    NO_PROXY=${NO_PROXY} \
    http_proxy=${HTTP_PROXY} \
    https_proxy=${HTTPS_PROXY} \
    no_proxy=${NO_PROXY}

# APT 配置 + 切换阿里云源 + 安装构建依赖
RUN set -eux; \
    if [ -n "${HTTPS_PROXY:-}" ]; then echo "Acquire::https::Proxy \"${HTTPS_PROXY}\";" > /etc/apt/apt.conf.d/01proxy; fi; \
    if [ -n "${HTTP_PROXY:-}"  ]; then echo "Acquire::http::Proxy  \"${HTTP_PROXY}\";" >> /etc/apt/apt.conf.d/01proxy; fi; \
    rm -f /etc/apt/sources.list.d/debian.sources; \
    codename="$(. /etc/os-release && echo "$VERSION_CODENAME")"; \
    printf 'deb https://mirrors.aliyun.com/debian %s main contrib non-free non-free-firmware\n' "$codename" > /etc/apt/sources.list; \
    printf 'deb https://mirrors.aliyun.com/debian %s-updates main contrib non-free non-free-firmware\n' "$codename" >> /etc/apt/sources.list; \
    printf 'deb https://mirrors.aliyun.com/debian-security %s-security main contrib non-free non-free-firmware\n' "$codename" >> /etc/apt/sources.list; \
    apt-get update -o Acquire::Retries=5; \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        python3-dev; \
    rm -rf /var/lib/apt/lists/*; \
    rm -f /etc/apt/apt.conf.d/01proxy; \
    apt-get clean

WORKDIR /build

# 拷贝依赖文件
COPY requirements.txt .

# 安装 Python 依赖（到用户目录）
RUN pip install --user --no-cache-dir -r requirements.txt


# ======================================================
# Stage 2: Runtime
# ======================================================
FROM python:3.9-slim

LABEL maintainer="Retire-Cluster Team"
LABEL description="Main Node server for Retire-Cluster idle device management"
LABEL version="1.0.0"

# 可选代理参数
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ENV HTTP_PROXY=${HTTP_PROXY} \
    HTTPS_PROXY=${HTTPS_PROXY} \
    NO_PROXY=${NO_PROXY} \
    http_proxy=${HTTP_PROXY} \
    https_proxy=${HTTPS_PROXY} \
    no_proxy=${NO_PROXY}

# 切源 + 安装运行时依赖
RUN set -eux; \
    if [ -n "${HTTPS_PROXY:-}" ]; then echo "Acquire::https::Proxy \"${HTTPS_PROXY}\";" > /etc/apt/apt.conf.d/01proxy; fi; \
    if [ -n "${HTTP_PROXY:-}"  ]; then echo "Acquire::http::Proxy  \"${HTTP_PROXY}\";" >> /etc/apt/apt.conf.d/01proxy; fi; \
    rm -f /etc/apt/sources.list.d/debian.sources; \
    codename="$(. /etc/os-release && echo "$VERSION_CODENAME")"; \
    printf 'deb https://mirrors.aliyun.com/debian %s main contrib non-free non-free-firmware\n' "$codename" > /etc/apt/sources.list; \
    printf 'deb https://mirrors.aliyun.com/debian %s-updates main contrib non-free non-free-firmware\n' "$codename" >> /etc/apt/sources.list; \
    printf 'deb https://mirrors.aliyun.com/debian-security %s-security main contrib non-free non-free-firmware\n' "$codename" >> /etc/apt/sources.list; \
    apt-get update -o Acquire::Retries=5; \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        netcat-traditional \
        sqlite3; \
    rm -rf /var/lib/apt/lists/*; \
    rm -f /etc/apt/apt.conf.d/01proxy; \
    apt-get clean

# 创建非 root 用户
RUN useradd -m -u 1000 -s /bin/bash cluster && \
    mkdir -p /data/config /data/database /data/logs /app && \
    chown -R cluster:cluster /data /app

# 从 builder 拷贝已安装的 Python 包
COPY --from=builder --chown=cluster:cluster /root/.local /home/cluster/.local

# 工作目录
WORKDIR /app

# 应用代码
COPY --chown=cluster:cluster retire_cluster/ ./retire_cluster/
COPY --chown=cluster:cluster setup.py README.md LICENSE ./

# 配置文件示例（如果存在）
COPY --chown=cluster:cluster configs/main_config_example.json /data/config/

# 切换到非 root 用户
USER cluster

# 环境变量
ENV PYTHONPATH=/app:/home/cluster/.local/lib/python3.9/site-packages \
    PATH=/home/cluster/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    CLUSTER_HOST=0.0.0.0 \
    CLUSTER_PORT=8080 \
    WEB_PORT=5000 \
    DATABASE_PATH=/data/database/cluster.db

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# 暴露端口
EXPOSE 8080 5000

# 挂载点
VOLUME ["/data/config", "/data/database", "/data/logs"]

# 启动命令 - 直接运行Python主程序
CMD ["python", "-m", "retire_cluster.main_node"]