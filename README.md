# AI 模型微调 Web 系统

## 项目简介

这是一个完整的 Web 系统，允许教师上传历史作业和评分数据，自动微调 AI 模型，并提供训练结果展示和模型部署功能。

# AI 模型微调 Web 系统

## 📁 完整项目结构

```
ai-tuning-system/
├── README.md                          # 项目说明文档
├── INSTALL.md                         # 详细安装指南
├── .env.example                       # 环境变量示例
├── .gitignore                         # Git 忽略文件
├── docker-compose.yml                 # Docker Compose 配置
├── deploy.sh                          # 部署脚本
├── 
├── backend/                           # FastAPI 后端
│   ├── Dockerfile                     # 后端 Docker 配置
│   ├── main.py                       # 应用入口文件
│   ├── requirements.txt              # Python 依赖
│   └── app/
│       ├── core/                     # 核心配置
│       │   ├── config.py            # 系统配置
│       │   └── celery.py            # Celery 配置
│       ├── db/                       # 数据库
│       │   ├── database.py          # 数据库连接
│       │   └── models.py            # SQLAlchemy 模型
│       ├── schemas/                  # Pydantic 数据模式
│       │   └── schemas.py           # API 请求/响应模式
│       ├── api/api_v1/              # API 路由
│       │   ├── api.py               # 主路由
│       │   └── endpoints/           # 各功能端点
│       │       ├── upload.py        # 文件上传 API
│       │       ├── training.py      # 训练管理 API
│       │       ├── models.py        # 模型管理 API
│       │       └── monitoring.py    # 监控 API
│       ├── services/                # 业务逻辑服务
│       │   ├── data_processor.py    # 数据处理服务
│       │   ├── training_service.py  # 训练服务
│       │   └── model_service.py     # 模型服务
│       ├── tasks/                   # Celery 异步任务
│       │   └── training_tasks.py    # 训练任务
│       └── training/                # AI 训练模块
│           └── trainer.py           # LoRA/PEFT 训练器
├── 
└── frontend/                         # React 前端
    ├── README.md                     # 前端说明文档
    ├── Dockerfile                    # 前端 Docker 配置
    ├── nginx.conf                    # Nginx 配置
    ├── start.sh                      # 前端启动脚本
    ├── package.json                  # Node.js 依赖
    ├── vite.config.ts               # Vite 配置
    ├── tsconfig.json                # TypeScript 配置
    ├── tsconfig.node.json           # TypeScript Node 配置
    ├── tailwind.config.js           # Tailwind 配置
    ├── postcss.config.js            # PostCSS 配置
    ├── .eslintrc.cjs                # ESLint 配置
    ├── index.html                   # HTML 模板
    ├── public/
    │   └── vite.svg                 # 应用图标
    └── src/
        ├── main.tsx                 # React 入口
        ├── App.tsx                  # 主应用组件
        ├── index.css                # 全局样式
        ├── components/              # React 组件
        │   ├── Dashboard.tsx        # 仪表板
        │   ├── FileUpload.tsx       # 文件上传
        │   ├── TrainingConfig.tsx   # 训练配置
        │   ├── TrainingProgress.tsx # 训练进度
        │   ├── ModelList.tsx        # 模型管理
        │   ├── Notification.tsx     # 通知组件
        │   ├── Loading.tsx          # 加载组件
        │   └── Modal.tsx            # 模态框组件
        ├── services/                # API 服务
        │   └── api.ts               # API 调用函数
        └── types/                   # TypeScript 类型
            └── index.ts             # 类型定义
```

## 主要功能

1. **文件上传和管理**
   - 支持拖拽上传 ZIP 文件或文件夹
   - 自动解析作业和评分数据
   - 数据格式校验

2. **训练参数配置**
   - 模型选择（LLaMA2-Chat, StarCoder）
   - 训练参数调整（epochs, batch_size, learning_rate）
   - 优化选项（FP16, 量化）

3. **训练过程管理**
   - 实时训练日志展示
   - 训练进度跟踪
   - 多任务队列管理

4. **结果展示和部署**
   - 验证结果可视化
   - 模型下载
   - API 接口部署

## 技术栈

- **前端**: React 18 + TypeScript + Tailwind CSS + Vite
- **后端**: FastAPI + SQLAlchemy + Alembic
- **AI训练**: PyTorch + Transformers + PEFT + LoRA
- **任务队列**: Celery + Redis
- **数据库**: PostgreSQL
- **部署**: Docker + Nginx + Uvicorn

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 16+
- CUDA 11.8+ (用于 GPU 训练)
- Docker (可选)

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd ai-tuning-system
```

2. **后端设置**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

3. **前端设置**
```bash
cd frontend
npm install
```

4. **数据库设置**
```bash
# 安装 PostgreSQL
# 创建数据库
createdb ai_tuning_db
```

5. **启动服务**
```bash
# 启动后端
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 启动前端
cd frontend
npm run dev

# 启动 Celery (新终端)
cd backend
celery -A app.core.celery worker --loglevel=info

# 启动 Redis
redis-server
```

## 部署说明

详细部署说明请参考 `docs/deployment.md`

## API 文档

启动后端服务后，访问 `http://localhost:8000/docs` 查看 Swagger API 文档。

## 许可证

MIT License
