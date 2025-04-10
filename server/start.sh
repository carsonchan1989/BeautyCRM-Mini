#!/bin/bash

# 创建日志目录
mkdir -p logs

# 启动 gunicorn
gunicorn -c gunicorn.conf.py app:app