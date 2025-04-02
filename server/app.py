"""
BeautyCRM后端服务主程序
"""
import os
import sys
# 添加当前目录到Python路径中
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime

from models import db
from api.customer_routes import customer_bp
from api.excel_routes import excel_bp
from api.project_routes import project_bp
from api.service_routes import service_bp

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
    app.register_blueprint(project_bp, url_prefix='/api/projects')
    app.register_blueprint(service_bp, url_prefix='/api/services')

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
        # 只在环境变量RESET_DB=true时重置数据库
        should_reset_db = os.environ.get('RESET_DB', '').lower() == 'true'
        
        # 初始化数据库
        if should_reset_db:
            # 强制删除并重建数据库表
            db.drop_all()
            db.create_all()
            
            # 创建测试数据
            try:
                from models import Customer, Communication, Service, ServiceItem
                # 添加测试客户
                test_customer = Customer(
                    id="C001",
                    name="测试客户",
                    gender="女",
                    age=30,
                    store="总店"
                )
                db.session.add(test_customer)
                
                # 添加测试沟通记录
                test_comm1 = Communication(
                    customer_id="C001",
                    communication_date=datetime.strptime("2023-08-15 14:30:00", "%Y-%m-%d %H:%M:%S"),
                    communication_type="电话",
                    communication_location="总店前台",
                    staff_name="王小明",
                    communication_content="询问客户近期护肤情况，客户反馈皮肤状态良好"
                )
                db.session.add(test_comm1)
                
                test_comm2 = Communication(
                    customer_id="C001",
                    communication_date=datetime.strptime("2023-09-20 16:45:00", "%Y-%m-%d %H:%M:%S"),
                    communication_type="门店面谈",
                    communication_location="分店A VIP室",
                    staff_name="李芳",
                    communication_content="介绍新款面膜产品，客户表示感兴趣",
                    customer_feedback="希望有优惠活动时通知",
                    follow_up_action="下周活动开始时电话通知"
                )
                db.session.add(test_comm2)
                
                # 添加测试服务记录1
                test_service1 = Service(
                    service_id="S001",
                    customer_id="C001",
                    customer_name="测试客户",
                    service_date=datetime.strptime("2023-08-05 20:15:00", "%Y-%m-%d %H:%M:%S"),
                    total_amount=293,
                    payment_method="刷卡",
                    operator="张美容师"
                )
                db.session.add(test_service1)
                db.session.flush()  # 获取ID
                
                # 添加服务项目1
                test_service_item1 = ServiceItem(
                    service_id=test_service1.service_id,
                    project_name="深层补水",
                    beautician_name="张美容师",
                    unit_price=293,
                    quantity=1
                )
                db.session.add(test_service_item1)
                
                # 添加测试服务记录2
                test_service2 = Service(
                    service_id="S002",
                    customer_id="C001",
                    customer_name="测试客户",
                    service_date=datetime.strptime("2023-09-02 20:45:00", "%Y-%m-%d %H:%M:%S"),
                    total_amount=1840,
                    payment_method="消费卡",
                    operator="李美容师"
                )
                db.session.add(test_service2)
                db.session.flush()
                
                # 添加服务项目2-1
                test_service_item2_1 = ServiceItem(
                    service_id=test_service2.service_id,
                    project_name="肌肤管理",
                    beautician_name="李美容师",
                    unit_price=1200,
                    quantity=1
                )
                db.session.add(test_service_item2_1)
                
                # 添加服务项目2-2
                test_service_item2_2 = ServiceItem(
                    service_id=test_service2.service_id,
                    project_name="背部SPA",
                    beautician_name="王按摩师",
                    unit_price=640,
                    quantity=1
                )
                db.session.add(test_service_item2_2)
                
                db.session.commit()
                print("测试数据创建成功")
            except Exception as e:
                db.session.rollback()
                print(f"测试数据创建失败: {str(e)}")
        else:
            # 确保表存在但不清除数据
            db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)