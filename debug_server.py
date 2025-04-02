import sys
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='server_debug.log',
    filemode='w'
)

# 设置环境变量
os.environ['RESET_DB'] = 'true'

# 将当前目录加入系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    logging.info("尝试导入 create_app")
    from server.app import create_app
    logging.info("成功导入 create_app")
    
    logging.info("创建应用实例")
    app = create_app()
    
    # 直接运行应用，app.py中已经处理了数据库初始化
    logging.info("应用初始化完成，准备运行")
    if __name__ == '__main__':
        app.run(debug=True, port=5000)

except Exception as e:
    logging.exception(f"发生错误: {str(e)}")
    print(f"错误: {str(e)}")