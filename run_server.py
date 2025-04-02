"""
BeautyCRM-Mini 服务器启动脚本
解决Python导入错误问题
"""
import os
import sys

# 将当前目录添加到Python路径
sys.path.insert(0, os.path.abspath('.'))

def run_server():
    """启动Flask服务器"""
    # 导入Flask应用
    from server.app import create_app
    
    # 检查是否需要重置数据库
    reset_db = os.environ.get('RESET_DB', 'false').lower() == 'true'
    if reset_db:
        print("数据库将被重置...")
    
    # 创建应用
    app = create_app()
    
    # 设置主机和端口
    host = os.environ.get('HOST', '0.0.0.0')  # 默认监听所有网络接口
    port = int(os.environ.get('PORT', 5000))  # 默认端口5000
    
    # 打印服务器信息
    print(f"\n服务器启动信息:")
    print(f"* 监听地址: {host}:{port}")
    print(f"* 访问URL: http://{host if host != '0.0.0.0' else '127.0.0.1'}:{port}/")
    if host == '0.0.0.0':
        import socket
        try:
            # 获取本地IP地址，用于手机访问
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            print(f"* 局域网访问: http://{local_ip}:{port}/")
        except:
            print("* 无法获取局域网IP地址")
    
    # 启动服务器
    app.run(host=host, port=port, debug=True)

if __name__ == '__main__':
    run_server()