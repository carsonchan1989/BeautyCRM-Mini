"""
清理数据库中的重复服务记录
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db, Service, ServiceItem
from sqlalchemy import func

def fix_duplicate_service_records():
    """查找并清理重复的服务记录"""
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URI', 'sqlite:///beauty_crm.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )
    db.init_app(app)
    
    with app.app_context():
        try:
            # 查找重复记录
            duplicate_groups = db.session.query(
                Service.customer_id,
                Service.service_date,
                Service.operator,
                Service.total_amount,
                func.count(Service.service_id).label('count')
            ).group_by(
                Service.customer_id,
                Service.service_date,
                Service.operator,
                Service.total_amount
            ).having(
                func.count(Service.service_id) > 1
            ).all()
            
            print(f"发现 {len(duplicate_groups)} 组重复的服务记录")
            
            total_deleted = 0
            
            # 处理每组重复记录
            for group in duplicate_groups:
                customer_id, service_date, operator, total_amount, count = group
                
                duplicate_services = Service.query.filter_by(
                    customer_id=customer_id,
                    service_date=service_date,
                    operator=operator,
                    total_amount=total_amount
                ).order_by(Service.created_at).all()
                
                # 保留最早创建的记录，删除其余记录
                keep_service = duplicate_services[0]
                delete_services = duplicate_services[1:]
                
                print(f"保留服务记录: {keep_service.service_id}, 创建于 {keep_service.created_at}")
                
                for service in delete_services:
                    print(f"    删除重复记录: {service.service_id}, 创建于 {service.created_at}")
                    
                    # 先删除关联的服务项目
                    for item in service.service_items:
                        db.session.delete(item)
                    
                    # 删除服务记录
                    db.session.delete(service)
                    total_deleted += 1
            
            # 提交事务
            db.session.commit()
            print(f"成功删除 {total_deleted} 条重复的服务记录")
            
        except Exception as e:
            db.session.rollback()
            print(f"清理重复记录失败: {str(e)}")

if __name__ == "__main__":
    fix_duplicate_service_records()