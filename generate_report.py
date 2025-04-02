"""
生成正确格式的客户服务记录报告
"""
import sys
import os
from datetime import datetime
from flask import Flask

# 添加服务器目录到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "server"))

# 导入模型
from models import db, Customer, Service, ServiceItem
from app import create_app

def generate_customer_report(customer_id="C003"):
    """
    生成客户服务记录报告，确保格式符合要求
    """
    app = create_app()
    
    with app.app_context():
        # 获取客户信息
        customer = Customer.query.get(customer_id)
        if not customer:
            print(f"找不到客户ID: {customer_id}")
            return
        
        # 获取客户的所有服务记录，按日期排序
        services = Service.query.filter_by(customer_id=customer_id).order_by(Service.service_date.desc()).all()
        
        # 准备MD文档内容
        md_content = [
            f"## 客户: {customer.name} ({customer_id})\n",
            "### 基本信息\n",
            "| 字段 | 值 |",
            "|------|----|",
            f"| 姓名 | {customer.name} |",
            f"| 性别 | {customer.gender} |",
            f"| 年龄 | {customer.age} |",
            f"| 门店归属 | {customer.store} |",
            f"| 籍贯 | {customer.hometown} |",
            f"| 现居地 | {customer.residence} |",
            f"| 居住时长 | {customer.residence_years} |",
            f"| 家庭成员构成 | {customer.family_structure} |",
            f"| 家庭人员年龄分布 | {customer.family_age_distribution} |",
            f"| 家庭居住情况 | {customer.living_condition} |",
            f"| 性格类型标签 | {customer.personality_tags} |",
            f"| 消费决策主导 | {customer.consumption_decision} |",
            f"| 兴趣爱好 | {customer.hobbies} |",
            f"| 作息规律 | {customer.routine} |",
            f"| 饮食偏好 | {customer.diet_preference} |",
            f"| 职业 | {customer.occupation} |",
            f"| 单位性质 | {customer.work_unit_type} |",
            f"| 年收入 | {customer.annual_income} |",
            "\n### 服务记录\n",
            "| 到店时间 | 离店时间 | 总耗卡次数 | 总耗卡金额 | 服务满意度 | 项目详情1 | 项目详情2 | 项目详情3 | 项目详情4 | 项目详情5 |",
            "|----------|----------|------------|------------|------------|-----------|-----------|-----------|-----------|------------|"
        ]
        
        # 添加服务记录
        for service in services:
            # 获取服务项目
            service_items = ServiceItem.query.filter_by(service_id=service.service_id).all()
            
            # 计算总耗卡次数
            total_sessions = len(service_items)
            
            # 格式化日期时间
            arrival_time = service.service_date.strftime('%Y-%m-%d %H:%M:%S') if service.service_date else ""
            departure_time = service.departure_time.strftime('%Y-%m-%d %H:%M:%S') if service.departure_time else ""
            
            # 准备项目详情
            project_details = []
            for item in service_items:
                # 格式: 项目内容-操作美容师-耗卡金额-是否指定
                specified = "✓指定" if item.is_specified else "未指定"
                detail = f"{item.project_name} - {item.beautician_name} - {item.unit_price}元 - {specified}"
                project_details.append(detail)
            
            # 确保有5个项目详情字段（不足的用空字符串填充）
            while len(project_details) < 5:
                project_details.append("")
            
            # 取前5个项目详情
            project_details = project_details[:5]
            
            # 添加服务记录行
            service_row = f"| {arrival_time} | {departure_time} | {total_sessions} | {service.total_amount} | {service.satisfaction} | {' | '.join(project_details)} |"
            md_content.append(service_row)
        
        # 将内容写入文件
        output_path = f"{customer_id}_报告.md"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_content))
        
        print(f"已生成客户报告: {output_path}")
        return output_path

if __name__ == "__main__":
    # 如果提供了命令行参数，使用它作为客户ID
    customer_id = sys.argv[1] if len(sys.argv) > 1 else "C003"
    generate_customer_report(customer_id)