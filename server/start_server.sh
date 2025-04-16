#!/bin/bash

# BeautyCRM服务器启动脚本
# 用于启动后端服务，包含权限检查和错误处理机制

# 设置日志文件
LOG_FILE="$(dirname "$0")/server.log"
INSTANCE_DIR="$(dirname "$0")/instance"
DB_FILE="$INSTANCE_DIR/beauty_crm.db"

# 创建日志文件和设置权限
touch "$LOG_FILE"
chmod 666 "$LOG_FILE"

# 确保instance目录存在
mkdir -p "$INSTANCE_DIR"
chmod 777 "$INSTANCE_DIR"

# 检查数据库文件是否存在，如果存在则设置权限
if [ -f "$DB_FILE" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 检查数据库文件权限: $DB_FILE" | tee -a "$LOG_FILE"
    chmod 777 "$DB_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 已设置数据库文件权限: $DB_FILE" | tee -a "$LOG_FILE"
fi

# 检查端口是否被占用
PORT=5000
if netstat -tuln | grep -q ":$PORT "; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 端口 $PORT 已被占用，尝试关闭占用进程..." | tee -a "$LOG_FILE"
    PID=$(lsof -ti:$PORT)
    if [ ! -z "$PID" ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - 关闭PID为 $PID 的进程..." | tee -a "$LOG_FILE"
        kill -9 $PID
    fi
fi

# 启动Flask应用
echo "$(date '+%Y-%m-%d %H:%M:%S') - 启动BeautyCRM服务..." | tee -a "$LOG_FILE"
cd "$(dirname "$0")"

# 检查是否存在虚拟环境
VENV_PATH="/var/www/BeautyCRM-Mini/venv"
if [ -d "$VENV_PATH" ] && [ -f "$VENV_PATH/bin/python" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 使用虚拟环境Python启动" | tee -a "$LOG_FILE"
    nohup "$VENV_PATH/bin/python" "$(dirname "$0")/app.py" > "$LOG_FILE" 2>&1 &
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 使用系统Python启动" | tee -a "$LOG_FILE"
    nohup python3 "$(dirname "$0")/app.py" > "$LOG_FILE" 2>&1 &
fi
APP_PID=$!

# 检查应用是否成功启动
sleep 3
if kill -0 $APP_PID 2>/dev/null; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - BeautyCRM服务已成功启动，PID: $APP_PID" | tee -a "$LOG_FILE"
    echo $APP_PID > "$(dirname "$0")/server.pid"
    echo "服务状态: 运行中"
    echo "访问: http://localhost:5000/health 检查服务状态"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 启动失败，请检查日志文件: $LOG_FILE" | tee -a "$LOG_FILE"
    echo "服务状态: 启动失败"
    tail -n 20 "$LOG_FILE"
fi 