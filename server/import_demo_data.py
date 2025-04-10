"""
导入演示数据到数据库中
"""
import os
import sys
import logging
from datetime import datetime, timedelta
import random

# 确保可以导入当前目录模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from app import create_app
from models import db, Customer, Project, Consumption, Service

# 客户示例数据
demo_customers = [
    {
        'id': 'C20250001',
        'name': '张三',
        'gender': '女',
        'age': 28,
        'store': '总店',
        'occupation': '白领'
    },
    {
        'id': 'C20250002',
        'name': '李四',
        'gender': '女',
        'age': 35,
        'store': '分店一',
        'occupation': '企业家'
    },
    {
        'id': 'C20250003',
        'name': '王五',
        'gender': '男',
        'age': 40,
        'store': '总店',
        'occupation': '公务员'
    }
]

# 项目示例数据
demo_projects = [
    {
        'name': '冰肌焕颜护理',
        'category': '面部护理',
        'effects': '深层补水、提亮肤色',
        'description': '纳米微针导入玻尿酸+蓝光镇定修复',
        'price': 2880,
        'sessions': 6,
        'duration': 90
    },
    {
        'name': '黄金射频紧致疗程',
        'category': '抗衰老',
        'effects': '提升轮廓、淡化细纹',
        'description': '多级射频热能刺激胶原再生',
        'price': 6800,
        'sessions': 5,
        'duration': 120
    },
    {
        'name': '经络排毒塑身',
        'category': '身体护理',
        'effects': '消水肿、塑形瘦身',
        'description': '中医穴位按摩+红外线热疗加速代谢',
        'price': 1980,
        'sessions': 10,
        'duration': 60
    }
]

# 美容师名单
beauticians = ["王美丽", "李春花", "张淑芬", "刘静", "赵云"]

def create_demo_consumption(customer, project, service, beautician, start_time):
    """创建一个消费记录"""
    # 随机项目时长
    duration = random.randint(40, 120)
    end_time = start_time + timedelta(minutes=duration)
    
    # 随机满意度
    satisfaction = random.choice([4.0, 4.5, 5.0, 3.5, 4.0])
    
    # 随机是否指定
    is_specified = random.choice([True, False])
    
    # 创建消费记录
    consumption = Consumption(
        customer_id=customer.id,
        start_time=start_time,
        end_time=end_time,
        project_name=project.name,
        project_category=project.category,
        amount=project.price / project.sessions,  # 每次消费金额
        satisfaction=satisfaction,
        beautician=beautician,
        is_specified=is_specified,
        service_id=service.id,
        project_id=project.id
    )
    return consumption

def main():
    """主函数，导入演示数据"""
    app = create_app()
    with app.app_context():
        # 检查是否已有数据
        customer_count = Customer.query.count()
        if customer_count > 0:
            logger.info(f"数据库中已有 {customer_count} 位客户，跳过客户导入")
        else:
            # 导入客户数据
            for customer_data in demo_customers:
                customer = Customer(**customer_data)
                db.session.add(customer)
            db.session.commit()
            logger.info(f"已导入 {len(demo_customers)} 位客户")
        
        # 检查是否已有项目
        project_count = Project.query.count()
        if project_count > 0:
            logger.info(f"数据库中已有 {project_count} 个项目，跳过项目导入")
            projects = Project.query.all()
        else:
            # 导入项目数据
            projects = []
            for project_data in demo_projects:
                project = Project(**project_data)
                db.session.add(project)
                projects.append(project)
            db.session.commit()
            logger.info(f"已导入 {len(demo_projects)} 个项目")
        
        # 创建服务和消费记录
        customers = Customer.query.all()
        
        # 为每个客户创建服务记录
        for customer in customers:
            # 创建3次服务记录
            for i in range(3):
                # 随机服务日期
                service_date = datetime.now() - timedelta(days=random.randint(1, 30))
                
                # 创建服务记录
                service = Service(
                    customer_id=customer.id,
                    service_date=service_date,
                    total_amount=0,  # 将由消费记录累加
                    total_duration=0  # 将由消费记录累加
                )
                db.session.add(service)
                db.session.flush()  # 获取ID
                
                # 每次服务随机1-3个项目
                project_count = random.randint(1, 3)
                service_projects = random.sample(projects, k=min(project_count, len(projects)))
                
                # 为每个项目创建消费记录
                total_amount = 0
                total_duration = 0
                for j, project in enumerate(service_projects):
                    # 每个项目开始时间递增
                    start_time = service_date + timedelta(minutes=30*j)
                    
                    # 随机美容师
                    beautician = random.choice(beauticians)
                    
                    # 创建消费记录
                    consumption = create_demo_consumption(
                        customer, project, service, beautician, start_time
                    )
                    db.session.add(consumption)
                    
                    # 累加服务金额和时长
                    total_amount += consumption.amount
                    if consumption.start_time and consumption.end_time:
                        duration_minutes = (consumption.end_time - consumption.start_time).total_seconds() / 60
                        total_duration += int(duration_minutes)
                
                # 更新服务记录的总金额和时长
                service.total_amount = total_amount
                service.total_duration = total_duration
                service.departure_time = service.service_date + timedelta(minutes=total_duration + 15)  # 加15分钟休息
                
                # 设置服务满意度为消费记录的平均值
                satisfactions = [c.satisfaction for c in service.consumption_records if c.satisfaction]
                if satisfactions:
                    service.satisfaction = sum(satisfactions) / len(satisfactions)
            
            # 每10个客户提交一次
            db.session.commit()
            logger.info(f"已为客户 {customer.name} 创建服务和消费记录")
        
        # 最终提交
        db.session.commit()
        
        # 总结导入结果
        customer_count = Customer.query.count()
        project_count = Project.query.count()
        service_count = Service.query.count()
        consumption_count = Consumption.query.count()
        
        logger.info("演示数据导入完成:")
        logger.info(f"- 客户: {customer_count}")
        logger.info(f"- 项目: {project_count}")
        logger.info(f"- 服务记录: {service_count}")
        logger.info(f"- 消费记录: {consumption_count}")

if __name__ == "__main__":
    main()