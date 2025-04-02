"""
启动Flask服务器的入口脚本
"""
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置Flask环境变量
os.environ['FLASK_APP'] = 'server.app'
os.environ['FLASK_ENV'] = 'development'

# 导入并运行应用
from server.app import create_app

if __name__ == '__main__':
    # 获取是否重置数据库的环境变量
    reset_db = os.environ.get('RESET_DB', 'false').lower() == 'true'
    
    # 创建并运行应用
    app = create_app(reset_db=reset_db)
    app.run(host='0.0.0.0', port=5000, debug=True)