# AI 模型微调系统 - 安装和使用指南

## 📋 系统概述

这是一个完整的 AI 模型微调 Web 系统，支持教师上传历史作业和评分数据，自动进行模型微调，并提供训练监控和模型部署功能。

### 🎯 主要功能

- **文件上传**: 支持 ZIP、CSV、XLSX 格式的作业和评分数据上传
- **数据处理**: 自动解析和预处理训练数据
- **模型微调**: 使用 LoRA/PEFT 技术微调大语言模型
- **实时监控**: 训练进度、日志、系统资源监控
- **模型管理**: 模型下载、部署、API 服务
- **Web 界面**: 直观的前端操作界面

### 🛠️ 技术栈

- **前端**: React 18 + TypeScript + Tailwind CSS + Vite
- **后端**: FastAPI + SQLAlchemy + Celery + Redis
- **AI/ML**: PyTorch + Transformers + PEFT + LoRA
- **数据库**: PostgreSQL
- **部署**: Docker + Nginx

## 🔧 系统要求

### 硬件要求

- **CPU**: 4核以上推荐
- **内存**: 8GB 以上推荐，16GB 更佳
- **存储**: 50GB 以上可用空间
- **GPU**: NVIDIA GPU（可选，用于加速训练）

### 软件要求

- **操作系统**: Linux (Ubuntu 20.04+)、macOS、Windows
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **NVIDIA Docker**: 如果使用 GPU

## 🚀 快速部署

### 方法一：Docker 部署（推荐）

1. **下载项目**
```bash
# 如果你有 git 仓库
git clone <your-repo-url>
cd ai-tuning-system

# 或者解压下载的文件
unzip ai-tuning-system.zip
cd ai-tuning-system
```

2. **配置环境**
```bash
# 复制环境配置文件
cp .env.example .env

# 编辑配置文件（重要！）
nano .env
```

3. **一键部署**
```bash
# 执行部署脚本
./deploy.sh docker
```

4. **访问系统**
- 前端界面: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

### 方法二：原生部署

1. **安装依赖**
```bash
# Python 3.9+
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv

# Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Redis
sudo apt-get install redis-server
```

2. **配置数据库**
```bash
sudo -u postgres createdb ai_tuning_db
sudo -u postgres createuser ai_tuning_user
sudo -u postgres psql -c "ALTER USER ai_tuning_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ai_tuning_db TO ai_tuning_user;"
```

3. **部署应用**
```bash
./deploy.sh native
```

## 🔧 详细配置

### 环境变量配置

编辑 `.env` 文件配置以下重要参数：

```bash
# 数据库配置
DATABASE_URL=postgresql://ai_tuning_user:your_password@localhost:5432/ai_tuning_db

# 安全配置（生产环境必须修改）
SECRET_KEY=your-generated-secret-key

# Hugging Face Token（使用受限模型时需要）
HUGGINGFACE_TOKEN=your-hf-token

# GPU 配置
CUDA_VISIBLE_DEVICES=0

# 文件上传限制
MAX_UPLOAD_SIZE=104857600  # 100MB
```

### GPU 支持配置

如果你有 NVIDIA GPU：

1. **安装 NVIDIA Docker**
```bash
# 添加 NVIDIA Docker 仓库
distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
   && curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add - \
   && curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# 安装 NVIDIA Docker
sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

2. **验证 GPU 支持**
```bash
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

## 📖 使用指南

### 1. 文件上传

1. 进入"文件上传"页面
2. 拖拽或选择文件上传
3. 支持的格式：
   - **ZIP 文件**: 包含作业文件和评分 CSV
   - **CSV 文件**: 评分数据（需包含 student_id, assignment, score 列）
   - **XLSX 文件**: Excel 格式的评分数据

### 2. 训练配置

1. 上传文件后，进入"训练配置"页面
2. 配置训练参数：
   - **任务名称**: 自定义训练任务名称
   - **模型选择**: 选择基础模型（LLaMA2、StarCoder 等）
   - **训练轮数**: 通常 2-5 轮
   - **批次大小**: 根据 GPU 内存调整
   - **学习率**: 推荐 2e-4
   - **LoRA 配置**: 高级用户可调整

### 3. 监控训练

1. 进入"训练进度"页面
2. 实时查看：
   - 训练进度条
   - 损失曲线
   - 训练日志
   - 系统资源使用

### 4. 模型管理

1. 训练完成后，进入"模型管理"页面
2. 可以进行：
   - **下载模型**: 下载训练好的模型文件
   - **部署模型**: 部署为 REST API 服务
   - **测试预测**: 在线测试模型效果
   - **删除模型**: 清理不需要的模型

## 🔍 故障排除

### 常见问题

**Q: 训练任务启动失败**
A: 检查以下项目：
- GPU 内存是否足够
- 数据格式是否正确
- 模型是否需要 Hugging Face Token

**Q: 前端无法访问后端 API**
A: 检查：
- 后端服务是否启动
- 端口是否被占用
- 防火墙设置

**Q: GPU 训练速度慢**
A: 优化建议：
- 使用 FP16 混合精度
- 启用量化（如果支持）
- 调整批次大小

### 查看日志

```bash
# Docker 部署查看日志
./deploy.sh logs

# 查看特定服务日志
docker-compose logs backend
docker-compose logs celery-worker

# 原生部署查看日志
tail -f logs/app.log
```

### 健康检查

```bash
# 执行系统健康检查
./deploy.sh health
```

## 🔄 维护和更新

### 备份数据

```bash
# 备份系统数据
./deploy.sh backup
```

### 恢复数据

```bash
# 恢复指定备份
./deploy.sh restore backup_20231201_120000.tar.gz
```

### 重启服务

```bash
# 重启所有服务
./deploy.sh restart

# 停止服务
./deploy.sh stop

# 启动服务
./deploy.sh start
```

### 清理系统

```bash
# 清理所有数据（谨慎使用）
./deploy.sh cleanup
```

## 🛡️ 安全建议

### 生产环境部署

1. **修改默认密码**
   - 数据库密码
   - JWT 密钥
   - 管理员密码

2. **配置 HTTPS**
   - 使用 SSL 证书
   - 配置 Nginx HTTPS

3. **防火墙设置**
   - 只开放必要端口
   - 限制访问来源

4. **定期备份**
   - 自动备份数据库
   - 备份模型文件

### 访问控制

系统默认没有用户认证，生产环境建议：
- 配置反向代理认证
- 集成企业 SSO
- 设置 IP 白名单

## 📞 技术支持

### 获取帮助

1. **查看文档**: 详细阅读此文档
2. **检查日志**: 查看系统日志找出错误原因
3. **社区支持**: 搜索相关技术论坛
4. **Issue 反馈**: 在项目仓库提交 Issue

### 性能优化

1. **数据库优化**
   - 定期清理日志
   - 优化查询索引

2. **存储优化**
   - 清理旧模型文件
   - 使用外部存储

3. **内存优化**
   - 调整 Worker 数量
   - 监控内存使用

## 📈 扩展开发

### 添加新模型

1. 在 `backend/app/core/config.py` 中添加模型名称
2. 在 `backend/app/training/trainer.py` 中添加模型特定配置
3. 测试新模型的训练流程

### 自定义界面

1. 修改 `frontend/src/components/` 中的组件
2. 调整 `frontend/src/styles/` 中的样式
3. 重新构建前端

### API 扩展

1. 在 `backend/app/api/api_v1/endpoints/` 中添加新端点
2. 定义相应的数据模型
3. 更新 API 文档

---

**祝你使用愉快！** 🎉

如有问题，请参考故障排除章节或寻求技术支持。
