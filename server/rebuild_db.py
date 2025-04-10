"""
手动重建数据库表
"""
import os
import sys
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Customer, HealthRecord, Consumption, Service, Communication, ServiceItem

def rebuild_database():
    """重建数据库并添加测试数据"""
    print("开始重建数据库...")
    
    # 创建应用
    app = create_app()
    
    with app.app_context():
        # 删除并重建所有表
        print("删除旧表...")
        db.drop_all()
        
        print("创建新表...")
        db.create_all()
        
        print("添加测试数据...")
        
        try:
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
            
            # 提交所有更改
            db.session.commit()
            print("测试数据创建成功")
        except Exception as e:
            db.session.rollback()
            print(f"测试数据创建失败: {str(e)}")
    
    print("数据库重建完成")

if __name__ == "__main__":
    rebuild_database()