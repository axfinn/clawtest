#!/usr/bin/env bash
# deploy.sh — clawweb 部署脚本
# 用法：
#   ./deploy.sh             # 本地模式（构建 + 启动）
#   ./deploy.sh docker      # Docker 模式（构建镜像 + 启动容器）
#   ./deploy.sh stop        # 停止本地进程
#   ./deploy.sh docker stop # 停止 Docker 容器

set -e

# ─── 配置区（按需修改）─────────────────────────────────────────────────────────
BACKEND_DIR="$(cd "$(dirname "$0")/backend" && pwd)"
BINARY="$BACKEND_DIR/clawweb"
CONFIG="$BACKEND_DIR/config.yaml"
PID_FILE="/tmp/clawweb.pid"
LOG_FILE="/tmp/clawweb.log"

# Docker 相关
DOCKER_IMAGE="clawweb:latest"
DOCKER_CONTAINER="clawweb"
DOCKER_PORT="${PORT:-7991}"
# Docker 模式下挂载宿主机 ~/.claude 到容器 /home/autodev/.claude
CLAUDE_MOUNT="${CLAUDE_HOME_MOUNT:-$HOME/.claude}"
# ──────────────────────────────────────────────────────────────────────────────

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ─── 本地模式 ─────────────────────────────────────────────────────────────────

local_stop() {
    # 通过 PID 文件停止
    if [[ -f "$PID_FILE" ]]; then
        local pid
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            info "停止进程 PID=$pid"
            kill "$pid" && rm -f "$PID_FILE"
            sleep 1
        else
            warn "PID=$pid 已不存在，清理 PID 文件"
            rm -f "$PID_FILE"
        fi
    fi
    # 兜底：查杀所有同名进程
    local pids
    pids=$(pgrep -f "$BINARY" 2>/dev/null || true)
    if [[ -n "$pids" ]]; then
        info "杀掉残留进程: $pids"
        echo "$pids" | xargs kill 2>/dev/null || true
        sleep 1
    fi
}

local_build() {
    info "构建 Go 二进制..."
    cd "$BACKEND_DIR"
    go build -o clawweb . || error "构建失败"
    info "构建完成: $BINARY"
}

local_start() {
    if [[ ! -f "$CONFIG" ]]; then
        if [[ -f "$BACKEND_DIR/config.yaml.example" ]]; then
            warn "config.yaml 不存在，从 config.yaml.example 复制"
            cp "$BACKEND_DIR/config.yaml.example" "$CONFIG"
        else
            error "config.yaml 不存在，请先创建配置文件"
        fi
    fi

    info "启动 clawweb..."
    cd "$BACKEND_DIR"
    nohup "$BINARY" > "$LOG_FILE" 2>&1 &
    local pid=$!
    echo "$pid" > "$PID_FILE"
    sleep 1
    if kill -0 "$pid" 2>/dev/null; then
        info "启动成功 PID=$pid，日志: $LOG_FILE"
        info "访问地址: http://localhost:${PORT:-7991}"
    else
        error "启动失败，查看日志: $LOG_FILE"
    fi
}

# ─── Docker 模式 ──────────────────────────────────────────────────────────────

docker_stop() {
    if docker ps -q -f "name=$DOCKER_CONTAINER" | grep -q .; then
        info "停止容器 $DOCKER_CONTAINER"
        docker stop "$DOCKER_CONTAINER"
    fi
    if docker ps -aq -f "name=$DOCKER_CONTAINER" | grep -q .; then
        info "删除容器 $DOCKER_CONTAINER"
        docker rm "$DOCKER_CONTAINER"
    fi
}

docker_build() {
    local dockerfile="$(dirname "$0")/Dockerfile"
    if [[ ! -f "$dockerfile" ]]; then
        error "Dockerfile 不存在: $dockerfile"
    fi
    info "构建 Docker 镜像 $DOCKER_IMAGE..."
    docker build -t "$DOCKER_IMAGE" -f "$dockerfile" "$(dirname "$0")/.."
    info "镜像构建完成"
}

docker_start() {
    if [[ ! -f "$CONFIG" ]]; then
        if [[ -f "$BACKEND_DIR/config.yaml.example" ]]; then
            warn "config.yaml 不存在，从 config.yaml.example 复制"
            cp "$BACKEND_DIR/config.yaml.example" "$CONFIG"
        else
            error "config.yaml 不存在"
        fi
    fi

    info "启动 Docker 容器 $DOCKER_CONTAINER..."
    info "  - 端口: $DOCKER_PORT:7991"
    info "  - Claude skills 挂载: $CLAUDE_MOUNT -> /home/autodev/.claude"

    docker run -d \
        --name "$DOCKER_CONTAINER" \
        --restart unless-stopped \
        -p "${DOCKER_PORT}:7991" \
        -v "$BACKEND_DIR/config.yaml:/app/config.yaml:ro" \
        -v "$BACKEND_DIR/data:/app/data" \
        -v "$CLAUDE_MOUNT:/home/autodev/.claude:ro" \
        -e CLAUDE_HOME=/home/autodev \
        "$DOCKER_IMAGE"

    info "容器启动成功"
    info "访问地址: http://localhost:$DOCKER_PORT"
    info "查看日志: docker logs -f $DOCKER_CONTAINER"
}

# ─── 入口 ─────────────────────────────────────────────────────────────────────

MODE="${1:-local}"
ACTION="${2:-deploy}"

case "$MODE" in
    docker)
        case "$ACTION" in
            stop)   docker_stop ;;
            build)  docker_build ;;
            start)  docker_stop; docker_start ;;
            deploy) docker_stop; docker_build; docker_start ;;
            *)      error "未知 Docker action: $ACTION (stop|build|start|deploy)" ;;
        esac
        ;;
    stop)
        local_stop
        ;;
    local|deploy|"")
        local_stop
        local_build
        local_start
        ;;
    *)
        echo "用法: $0 [local|docker|stop] [stop|build|start|deploy]"
        echo ""
        echo "本地模式（默认）:"
        echo "  $0              # 停止旧进程 + 构建 + 启动"
        echo "  $0 stop         # 仅停止"
        echo ""
        echo "Docker 模式:"
        echo "  $0 docker           # 构建镜像 + 启动容器（自动挂载 ~/.claude）"
        echo "  $0 docker stop      # 停止容器"
        echo "  $0 docker build     # 仅构建镜像"
        echo "  $0 docker start     # 仅启动容器（不重新构建）"
        echo ""
        echo "环境变量:"
        echo "  PORT=8080           # 监听端口（默认 7991）"
        echo "  CLAUDE_HOME_MOUNT   # 挂载到容器的 .claude 目录（默认 ~/.claude）"
        exit 1
        ;;
esac
