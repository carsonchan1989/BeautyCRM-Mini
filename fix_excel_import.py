"""
修复Excel导入逻辑，确保正确处理消耗数据
"""
import pandas as pd
import os
import sys
from datetime import datetime
from flask import Flask

# 添加服务器目录到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "server"))

# 导入模型
from models import db, Service, ServiceItem, Customer
from app import create_app

def import_consumption_data(excel_path="模拟-客户信息档案.xlsx", sheet_name="消耗"):
    """
    从Excel导入消耗数据，修复重复数据和格式问题
    """
    # 创建Flask应用上下文
    app = create_app()
    
    try:
        # 读取Excel文件
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        
        # 打印数据预览
        print("读取到的Excel数据预览：")
        print(df.head())
        
        with app.app_context():
            # 清除现有服务数据（可选，根据需要决定是否执行）
            # ServiceItem.query.delete()
            # Service.query.delete()
            # db.session.commit()
            
            # 按客户和到店时间分组，避免重复导入
            grouped = df.groupby(['客户ID', '进店时间'])
            
            success_count = 0
            for (customer_id, service_time), group in grouped:
                # 检查客户是否存在
                customer = Customer.query.get(customer_id)
                if not customer:
                    print(f"客户不存在: {customer_id}，跳过相关记录")
                    continue
                
                # 解析日期时间
                try:
                    if isinstance(service_time, str):
                        service_date = datetime.strptime(service_time, "%Y/%m/%d %H:%M:%S")
                    else:
                        service_date = service_time
                        
                    # 解析离店时间
                    departure_time_str = group['离店时间'].iloc[0]
                    if isinstance(departure_time_str, str):
                        departure_time = datetime.strptime(departure_time_str, "%Y/%m/%d %H:%M:%S")
                    else:
                        departure_time = departure_time_str
                except Exception as e:
                    print(f"日期解析错误: {e}，跳过记录")
                    continue
                
                # 检查该客户在该时间是否已有服务记录
                existing_service = Service.query.filter_by(
                    customer_id=customer_id,
                    service_date=service_date
                ).first()
                
                if existing_service:
                    print(f"服务记录已存在: {customer_id} - {service_date}，跳过")
                    continue
                
                # 创建新服务记录
                service = Service(
                    customer_id=customer_id,
                    customer_name=customer.name,
                    service_date=service_date,
                    departure_time=departure_time,
                    total_amount=float(group['总耗卡金额'].iloc[0]),
                    total_sessions=int(group['总耗卡次数'].iloc[0]),
                    satisfaction=group['服务满意度'].iloc[0],
                    payment_method=group['支付方式'].iloc[0] if '支付方式' in group.columns else None,
                    operator=group['操作人员'].iloc[0] if '操作人员' in group.columns else None
                )
                
                db.session.add(service)
                db.session.flush()  # 获取服务ID
                
                # 添加服务项目
                # 假设Excel中有项目详情列，如'项目1', '项目2'等
                for i in range(1, service.total_sessions + 1):
                    project_col = f'项目{i}'
                    beautician_col = f'美容师{i}'
                    amount_col = f'金额{i}'
                    specified_col = f'是否指定{i}'
                    
                    if project_col not in group.columns:
                        continue
                    
                    project_name = group[project_col].iloc[0]
                    if pd.isna(project_name) or not project_name:
                        continue
                    
                    beautician_name = group[beautician_col].iloc[0] if beautician_col in group.columns else None
                    amount = float(group[amount_col].iloc[0]) if amount_col in group.columns else 0.0
                    is_specified = True if specified_col in group.columns and group[specified_col].iloc[0] == "✓" else False
                    
                    service_item = ServiceItem(
                        service_id=service.service_id,
                        project_name=project_name,
                        beautician_name=beautician_name,
                        unit_price=amount,
                        is_specified=is_specified
                    )
                    
                    db.session.add(service_item)
                
                success_count += 1
            
            # 提交更改
            db.session.commit()
            print(f"成功导入 {success_count} 条服务记录")
            
    except Exception as e:
        print(f"导入失败: {e}")
        if 'db' in locals() and 'session' in dir(db):
            db.session.rollback()

def generate_md_report(customer_id="C003"):
    """
    根据数据库中的服务记录生成正确格式的MD报告
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
                is_specified = "✓指定" if item.is_specified else "未指定"
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
            row = f"| {arrival_time} | {departure_time} | {service.total_sessions} | {service.total_amount} | {service.satisfaction} | "
            row += " | ".join(project_details)
            row += " |\n"
            
            md_content += row
        
        # 保存到文件
        output_file = f"{customer_id}_服务记录_修复版.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(md_content)
        
        print(f"已生成修复版服务记录报告: {output_file}")

if __name__ == "__main__":
    # 导入消耗数据
    import_consumption_data()
    
    # 生成修复版的MD报告
    generate_md_report("C003")