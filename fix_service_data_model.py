"""
修复服务数据模型和数据处理逻辑问题
"""
from flask import Flask
from datetime import datetime
import pandas as pd
import os
import sys

# 添加服务器目录到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "server"))

# 导入模型
from models import db, Service, ServiceItem, Customer
from app import create_app

def fix_duplicate_services():
    """
    修复问题1：去除重复的服务记录
    """
    app = create_app()
    with app.app_context():
        # 查找所有服务
        services = Service.query.all()
        
        # 按客户ID和服务日期分组，找出重复项
        service_dict = {}
        for service in services:
            key = f"{service.customer_id}_{service.service_date}"
            if key in service_dict:
                # 已存在相同客户相同日期的记录，标记为重复
                service_dict[key].append(service)
            else:
                service_dict[key] = [service]
        
        # 处理重复项，保留一个，删除其余的
        duplicates_removed = 0
        for key, service_list in service_dict.items():
            if len(service_list) > 1:
                # 有重复记录，保留第一个，删除其余的
                for service in service_list[1:]:
                    # 删除服务项目
                    ServiceItem.query.filter_by(service_id=service.service_id).delete()
                    # 删除服务
                    db.session.delete(service)
                    duplicates_removed += 1
        
        # 提交更改
        if duplicates_removed > 0:
            db.session.commit()
            print(f"已删除 {duplicates_removed} 条重复的服务记录")
        else:
            print("未发现重复的服务记录")

def generate_fixed_md_report(customer_id="C003"):
    """
    修复问题2和3：根据正确格式生成MD报告
    """
    app = create_app()
    with app.app_context():
        customer = Customer.query.get(customer_id)
        if not customer:
            print(f"找不到客户ID: {customer_id}")
            return
        
        # 获取客户的服务记录
        services = Service.query.filter_by(customer_id=customer_id).order_by(Service.service_date.desc()).all()
        
        # 生成MD格式的服务记录
        md_content = f"## 客户: {customer.name} ({customer_id})\n\n"
        md_content += "### 服务记录\n\n"
        md_content += "| 到店时间 | 离店时间 | 总耗卡次数 | 总耗卡金额 | 服务满意度 | 项目详情1 | 项目详情2 | 项目详情3 | 项目详情4 | 项目详情5 |\n"
        md_content += "|----------|----------|------------|------------|------------|-----------|-----------|-----------|-----------|------------|\n"
        
        for service in services:
            # 获取服务项目详情
            service_items = ServiceItem.query.filter_by(service_id=service.service_id).all()
            
            # 按照新的格式创建项目详情字段
            project_details = []
            for item in service_items:
                # 格式：项目内容\操作美容师\耗卡金额\是否指定
                is_specified = "✓指定" if item.beautician_name else "未指定"
                detail = f"{item.project_name} - {item.beautician_name} - {item.unit_price}元 - {is_specified}"
                project_details.append(detail)
            
            # 确保有足够的项目详情字段（最多5个）
            while len(project_details) < 5:
                project_details.append("")
            
            # 限制到最多5个
            project_details = project_details[:5]
            
            # 格式化日期时间
            arrival_time = service.service_date.strftime('%Y-%m-%d %H:%M:%S') if service.service_date else ""
            departure_time = service.departure_time.strftime('%Y-%m-%d %H:%M:%S') if service.departure_time else ""
            
            # 添加行
            row = f"| {arrival_time} | {departure_time} | {len(service_items)} | {service.total_amount} | {service.satisfaction} | "
            row += " | ".join(project_details)
            row += " |\n"
            
            md_content += row
        
        # 保存到文件
        output_file = f"{customer_id}_服务记录_修复版.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(md_content)
        
        print(f"已生成修复版服务记录报告: {output_file}")

if __name__ == "__main__":
    # 修复重复的服务记录
    fix_duplicate_services()
    
    # 生成修复版的MD报告
    generate_fixed_md_report("C003")