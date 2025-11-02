#!/bin/bash

# AI 模型微调系统前端启动脚本

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Node.js
check_node() {
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装，请先安装 Node.js 18+"
        exit 1
    fi
    
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 16 ]; then
        log_error "Node.js 版本过低，需要 16+ 版本"
        exit 1
    fi
    
    log_info "Node.js 版本: $(node --version)"
}

# 检查 npm
check_npm() {
    if ! command -v npm &> /dev/null; then
        log_error "npm 未安装"
        exit 1
    fi
    
    log_info "npm 版本: $(npm --version)"
}

# 安装依赖
install_deps() {
    log_info "安装依赖..."
    
    if [ ! -d "node_modules" ]; then
        npm install
    else
        log_info "依赖已安装，检查更新..."
        npm audit fix --audit-level moderate || true
    fi
    
    log_info "依赖安装完成"
}

# 开发模式
dev() {
    log_info "启动开发服务器..."
    npm run dev
}

# 构建生产版本
build() {
    log_info "构建生产版本..."
    npm run build
    log_info "构建完成，文件位于 dist/ 目录"
}

# 预览生产版本
preview() {
    log_info "预览生产版本..."
    if [ ! -d "dist" ]; then
        log_warn "未找到构建文件，先执行构建..."
        build
    fi
    npm run preview
}

# 代码检查
lint() {
    log_info "执行代码检查..."
    npm run lint
}

# 清理
clean() {
    log_info "清理构建文件和依赖..."
    rm -rf dist/
    rm -rf node_modules/
    rm -rf .vite/
    log_info "清理完成"
}

# 依赖分析
analyze() {
    log_info "分析依赖..."
    if ! npm list --depth=0; then
        log_warn "发现依赖问题，尝试修复..."
        npm install
    fi
}

# 主函数
main() {
    case "$1" in
        "dev")
            check_node
            check_npm
            install_deps
            dev
            ;;
        "build")
            check_node
            check_npm
            install_deps
            build
            ;;
        "preview")
            check_node
            check_npm
            preview
            ;;
        "lint")
            check_node
            check_npm
            lint
            ;;
        "clean")
            clean
            ;;
        "install")
            check_node
            check_npm
            install_deps
            ;;
        "analyze")
            check_node
            check_npm
            analyze
            ;;
        *)
            echo "AI 模型微调系统前端启动脚本"
            echo ""
            echo "用法: $0 [命令]"
            echo ""
            echo "命令:"
            echo "  dev      - 启动开发服务器"
            echo "  build    - 构建生产版本"
            echo "  preview  - 预览生产版本"
            echo "  lint     - 代码检查"
            echo "  clean    - 清理文件"
            echo "  install  - 安装依赖"
            echo "  analyze  - 分析依赖"
            echo ""
            echo "示例:"
            echo "  $0 dev      # 开发模式"
            echo "  $0 build    # 构建"
            echo ""
            ;;
    esac
}

main "$@"
