#!/bin/bash

# AI 模型微调系统部署脚本
# 支持 Docker 和原生部署

set -e  # 遇到错误时退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_blue() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    # 检查 Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    # 检查 GPU（可选）
    if command -v nvidia-smi &> /dev/null; then
        log_info "检测到 NVIDIA GPU"
        GPU_AVAILABLE=true
    else
        log_warn "未检测到 NVIDIA GPU，将使用 CPU 训练"
        GPU_AVAILABLE=false
    fi
    
    # 检查内存
    MEMORY_GB=$(free -g | awk 'NR==2{printf "%.1f", $2}')
    if (( $(echo "$MEMORY_GB < 8.0" | bc -l) )); then
        log_warn "系统内存少于 8GB，可能影响训练性能"
    fi
    
    # 检查磁盘空间
    DISK_SPACE_GB=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if (( DISK_SPACE_GB < 50 )); then
        log_warn "可用磁盘空间少于 50GB，可能影响模型存储"
    fi
    
    log_info "系统要求检查完成"
}

# 创建环境配置
setup_environment() {
    log_info "设置环境配置..."
    
    if [ ! -f .env ]; then
        log_info "创建环境配置文件..."
        cp .env.example .env
        
        # 生成随机密钥
        SECRET_KEY=$(openssl rand -base64 32)
        sed -i "s/your-secret-key-here-change-in-production-very-important/$SECRET_KEY/g" .env
        
        log_warn "请编辑 .env 文件并配置必要的参数"
        log_warn "特别是数据库密码、Hugging Face Token 等"
    else
        log_info "环境配置文件已存在"
    fi
    
    # 创建必要的目录
    mkdir -p uploads models logs ssl
    chmod 755 uploads models logs
    
    log_info "环境配置完成"
}

# Docker 部署
deploy_docker() {
    log_info "开始 Docker 部署..."
    
    # 构建镜像
    log_info "构建 Docker 镜像..."
    docker-compose build
    
    # 启动服务
    log_info "启动服务..."
    docker-compose up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        log_info "服务启动成功！"
        log_blue "前端地址: http://localhost:3000"
        log_blue "后端 API: http://localhost:8000"
        log_blue "API 文档: http://localhost:8000/docs"
    else
        log_error "服务启动失败，请检查日志"
        docker-compose logs
        exit 1
    fi
}

# 原生部署
deploy_native() {
    log_info "开始原生部署..."
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 未安装"
        exit 1
    fi
    
    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装"
        exit 1
    fi
    
    # 安装后端依赖
    log_info "安装后端依赖..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
    
    # 安装前端依赖
    log_info "安装前端依赖..."
    cd frontend
    npm install
    npm run build
    cd ..
    
    # 启动数据库（需要用户手动配置）
    log_warn "请确保 PostgreSQL 和 Redis 已安装并运行"
    log_warn "数据库配置请参考 .env 文件"
    
    # 创建启动脚本
    cat > start_backend.sh << 'EOF'
#!/bin/bash
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
EOF
    chmod +x start_backend.sh
    
    cat > start_celery.sh << 'EOF'
#!/bin/bash
cd backend
source venv/bin/activate
celery -A app.core.celery worker --loglevel=info
EOF
    chmod +x start_celery.sh
    
    cat > start_frontend.sh << 'EOF'
#!/bin/bash
cd frontend
npm run preview
EOF
    chmod +x start_frontend.sh
    
    log_info "原生部署准备完成"
    log_blue "请运行以下命令启动服务:"
    log_blue "1. 后端: ./start_backend.sh"
    log_blue "2. Celery: ./start_celery.sh"
    log_blue "3. 前端: ./start_frontend.sh"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 检查后端 API
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_info "✓ 后端 API 正常"
    else
        log_error "✗ 后端 API 异常"
    fi
    
    # 检查前端
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        log_info "✓ 前端服务正常"
    else
        log_error "✗ 前端服务异常"
    fi
    
    # 检查数据库连接
    if docker-compose exec backend python -c "from app.db.database import engine; engine.connect()" > /dev/null 2>&1; then
        log_info "✓ 数据库连接正常"
    else
        log_error "✗ 数据库连接异常"
    fi
    
    # 检查 Redis 连接
    if docker-compose exec redis redis-cli ping > /dev/null 2>&1; then
        log_info "✓ Redis 连接正常"
    else
        log_error "✗ Redis 连接异常"
    fi
}

# 清理函数
cleanup() {
    log_info "清理部署..."
    docker-compose down -v
    docker system prune -f
    rm -rf uploads/* models/* logs/*
}

# 备份函数
backup() {
    log_info "备份数据..."
    BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p $BACKUP_DIR
    
    # 备份数据库
    docker-compose exec db pg_dump -U ai_tuning_user ai_tuning_db > $BACKUP_DIR/database.sql
    
    # 备份上传的文件和模型
    cp -r uploads $BACKUP_DIR/
    cp -r models $BACKUP_DIR/
    
    # 创建备份压缩包
    tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
    rm -rf $BACKUP_DIR
    
    log_info "备份完成: $BACKUP_DIR.tar.gz"
}

# 恢复函数
restore() {
    if [ -z "$1" ]; then
        log_error "请指定备份文件: ./deploy.sh restore backup_file.tar.gz"
        exit 1
    fi
    
    log_info "恢复数据: $1"
    tar -xzf $1
    BACKUP_DIR=$(basename $1 .tar.gz)
    
    # 恢复数据库
    docker-compose exec -T db psql -U ai_tuning_user ai_tuning_db < $BACKUP_DIR/database.sql
    
    # 恢复文件
    cp -r $BACKUP_DIR/uploads/* uploads/
    cp -r $BACKUP_DIR/models/* models/
    
    rm -rf $BACKUP_DIR
    log_info "恢复完成"
}

# 主函数
main() {
    case "$1" in
        "docker")
            check_requirements
            setup_environment
            deploy_docker
            health_check
            ;;
        "native")
            check_requirements
            setup_environment
            deploy_native
            ;;
        "health")
            health_check
            ;;
        "cleanup")
            cleanup
            ;;
        "backup")
            backup
            ;;
        "restore")
            restore "$2"
            ;;
        "logs")
            docker-compose logs -f
            ;;
        "restart")
            docker-compose restart
            ;;
        "stop")
            docker-compose stop
            ;;
        "start")
            docker-compose start
            ;;
        *)
            echo "AI 模型微调系统部署脚本"
            echo ""
            echo "用法: $0 [命令]"
            echo ""
            echo "命令:"
            echo "  docker    - Docker 部署（推荐）"
            echo "  native    - 原生部署"
            echo "  health    - 健康检查"
            echo "  cleanup   - 清理部署"
            echo "  backup    - 备份数据"
            echo "  restore   - 恢复数据"
            echo "  logs      - 查看日志"
            echo "  restart   - 重启服务"
            echo "  stop      - 停止服务"
            echo "  start     - 启动服务"
            echo ""
            echo "示例:"
            echo "  $0 docker     # Docker 部署"
            echo "  $0 health     # 健康检查"
            echo "  $0 backup     # 备份数据"
            echo ""
            ;;
    esac
}

# 执行主函数
main "$@"
