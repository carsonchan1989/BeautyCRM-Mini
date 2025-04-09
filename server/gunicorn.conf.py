"""
Gunicorn配置文件 - BeautyCRM服务器配置
"""
import os
import multiprocessing

# 服务器套接字配置
bind = "0.0.0.0:5000"
backlog = 2048

# 工作进程配置
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2

# 日志配置
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"
access_log_format = '%({x-real-ip}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# 进程名称
proc_name = "beauty-crm"

# 进程管理
daemon = True  # 设置为后台运行
pidfile = "beauty-crm.pid"
umask = 0
user = None
group = None

# 工作目录
chdir = os.path.dirname(os.path.abspath(__file__))

# 其他配置
worker_tmp_dir = "/dev/shm"
max_requests = 1000
max_requests_jitter = 50
graceful_timeout = 30
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# 热重载
reload = True
reload_engine = "auto"
reload_extra_files = [
    "app.py",
    "models.py",
    "wsgi.py"
]