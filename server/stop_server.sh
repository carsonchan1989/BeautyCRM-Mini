#!/bin/bash

# BeautyCRM服务器停止脚本
# 用于安全停止后端服务

# 设置日志文件
LOG_FILE="$(dirname "$0")/server.log"
PID_FILE="$(dirname "$0")/server.pid"

# 检查PID文件是否存在
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 停止PID为 $PID 的BeautyCRM服务..." | tee -a "$LOG_FILE"
    
    # 检查进程是否正在运行
    if kill -0 $PID 2>/dev/null; then
        # 尝试优雅地停止
        kill $PID
        
        # 等待进程结束
        COUNTER=0
        while kill -0 $PID 2>/dev/null && [ $COUNTER -lt 10 ]; do
            echo "等待服务停止中..." | tee -a "$LOG_FILE"
            sleep 1
            COUNTER=$((COUNTER+1))
        done
        
        # 如果进程仍在运行，则强制终止
        if kill -0 $PID 2>/dev/null; then
            echo "$(date '+%Y-%m-%d %H:%M:%S') - 服务未能正常停止，强制终止..." | tee -a "$LOG_FILE"
            kill -9 $PID
        fi
        
        echo "$(date '+%Y-%m-%d %H:%M:%S') - BeautyCRM服务已停止" | tee -a "$LOG_FILE"
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - PID为 $PID 的进程不存在" | tee -a "$LOG_FILE"
    fi
    
    # 删除PID文件
    rm -f "$PID_FILE"
else
    # 如果PID文件不存在，尝试查找并停止所有Flask服务
    PIDS=$(lsof -ti:5000)
    if [ ! -z "$PIDS" ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - 发现在端口5000上运行的进程: $PIDS" | tee -a "$LOG_FILE"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - 停止所有相关进程..." | tee -a "$LOG_FILE"
        kill -9 $PIDS
        echo "$(date '+%Y-%m-%d %H:%M:%S') - 所有相关进程已停止" | tee -a "$LOG_FILE"
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - 未发现运行中的BeautyCRM服务" | tee -a "$LOG_FILE"
    fi
fi

echo "BeautyCRM服务状态: 已停止" 