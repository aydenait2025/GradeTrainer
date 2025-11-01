# 使用官方 Python 3.9 镜像作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p uploads models logs

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8000

# 创建启动脚本
RUN echo '#!/bin/bash\n\
# 等待数据库启动\n\
python -c "import time; import psycopg2; import os; \
attempts = 0; \
while attempts < 30: \
    try: \
        psycopg2.connect(os.environ[\"DATABASE_URL\"]); \
        print(\"Database is ready!\"); \
        break; \
    except psycopg2.OperationalError: \
        attempts += 1; \
        print(f\"Database not ready, attempt {attempts}/30\"); \
        time.sleep(2); \
else: \
    print(\"Could not connect to database\"); \
    exit(1)"\n\
\n\
# 运行数据库迁移\n\
python -c "from app.db.database import engine; from app.db import models; models.Base.metadata.create_all(bind=engine)"\n\
\n\
# 启动应用\n\
uvicorn main:app --host 0.0.0.0 --port 8000 --reload' > /app/start.sh

RUN chmod +x /app/start.sh

# 启动命令
CMD ["/app/start.sh"]
