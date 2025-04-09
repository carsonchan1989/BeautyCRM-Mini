#!/bin/bash

# 确保在服务器目录下运行
cd "$(dirname "$0")"

# 创建必要的目录
mkdir -p logs
mkdir -p uploads
mkdir -p exports

# 安装依赖
pip install -r requirements.txt

# 更新数据库
python update_db.py

# 启动Gunicorn服务器
gunicorn -c gunicorn.conf.py app:app