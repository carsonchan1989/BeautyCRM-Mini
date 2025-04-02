"""
BeautyCRM后端服务主程序
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime

from .models import db
from .api.customer_routes import customer_bp
from .api.excel_routes import excel_bp

def create_app(config=None):
    """创建Flask应用实例"""
    app = Flask(__name__)
    
    # 配置跨域支持
    CORS(app)
    
    # 默认配置
    app.config.update(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'beauty-crm-secret-key'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URI', 'sqlite:///beauty_crm.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads'),
        EXPORT_FOLDER=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports'),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 最大16MB上传
    )
    
    # 应用自定义配置
    if config:
        app.config.update(config)
    
    # 初始化数据库
    db.init_app(app)
    
    # 注册蓝图
    app.register_blueprint(customer_bp, url_prefix='/api/customers')
    app.register_blueprint(excel_bp, url_prefix='/api/excel')
    
    # 创建文件夹
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)
    
    # 全局错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': '资源未找到'}), 404
    
    @app.errorhandler(500)
    def server_error(error):
        return jsonify({'error': '服务器内部错误'}), 500
    
    # 健康检查端点
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    # 创建与应用上下文
    with app.app_context():
        # 创建所有表
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
