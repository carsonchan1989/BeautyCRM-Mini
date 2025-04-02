"""
导入项目消耗数据到数据库 - 美容客户管理系统

此脚本用于将Excel中的消耗数据导入到数据库中，生成服务记录和消耗记录。
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any

# 添加父目录到路径，以便导入models等模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, Customer, Service, ServiceItem, ConsumedSession, Consumption, Project
from utils.read_service_consumption_excel import process_and_import_consumption_data

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_or_create_project(service_name: str) -> Project:
    """根据服务名称查找或创建项目"""
    # 尝试查找现有项目
    project = Project.query.filter(Project.name == service_name).first()
    
    # 如果项目不存在，创建新项目
    if not project:
        project = Project(
            name=service_name,
            category='未分类',  # 默认分类
            status='active'
        )
        db.session.add(project)
        db.session.flush()  # 生成ID但不提交事务
        logger.info(f"创建新项目: {service_name} (ID: {project.id})")
        
    return project

def import_service_records(service_records: List[Dict], service_items: List[Dict]) -> Dict:
    """导入服务记录和服务项目到数据库"""
    results = {
        "services_created": 0,
        "service_items_created": 0,
        "consumption_sessions_created": 0,
        "errors": []
    }
    
    # 按客户ID分组服务项目
    service_items_by_key = {}
    for item in service_items:
        key = (item['customer_id'], item['service_date'].isoformat() if isinstance(item['service_date'], datetime) else str(item['service_date']))
        if key not in service_items_by_key:
            service_items_by_key[key] = []
        service_items_by_key[key].append(item)
    
    # 处理每条服务记录
    for record in service_records:
        try:
            # 检查客户是否存在
            customer_id = record['customer_id']
            customer = Customer.query.get(customer_id)
            
            if not customer:
                logger.warning(f"客户ID不存在: {customer_id}，跳过服务记录")
                results["errors"].append(f"客户ID不存在: {customer_id}")
                continue
            
            # 创建服务记录
            service_date = record['service_date']
            
            # 检查是否已存在相同的服务记录
            existing_service = Service.query.filter_by(
                customer_id=customer_id,
                service_date=service_date
            ).first()
            
            if existing_service:
                service = existing_service
                logger.info(f"找到现有服务记录: ID={service.id}, 客户={customer_id}, 日期={service_date}")
            else:
                service = Service(
                    customer_id=customer_id,
                    service_date=service_date,
                    total_amount=record.get('total_amount', 0)
                )
                db.session.add(service)
                db.session.flush()  # 生成ID但不提交事务
                results["services_created"] += 1
                logger.info(f"创建新服务记录: ID={service.id}, 客户={customer_id}, 日期={service_date}")
            
            # 获取此服务记录对应的服务项目
            key = (customer_id, service_date.isoformat() if isinstance(service_date, datetime) else str(service_date))
            items = service_items_by_key.get(key, [])
            
            # 创建服务项目
            for item in items:
                service_name = item.get('service_name', '未知项目')
                
                # 查找或创建项目
                project = find_or_create_project(service_name)
                
                # 检查是否已存在相同的服务项目
                existing_item = ServiceItem.query.filter_by(
                    service_id=service.id,
                    service_name=service_name,
                    beautician=item.get('beautician')
                ).first()
                
                if existing_item:
                    service_item = existing_item
                    logger.info(f"找到现有服务项目: ID={service_item.id}, 服务={service_name}")
                else:
                    service_item = ServiceItem(
                        service_id=service.id,
                        service_name=service_name,
                        beautician=item.get('beautician'),
                        amount=item.get('amount', 0),
                        project_id=project.id
                    )
                    db.session.add(service_item)
                    db.session.flush()  # 生成ID但不提交事务
                    results["service_items_created"] += 1
                    logger.info(f"创建新服务项目: ID={service_item.id}, 服务={service_name}")
                
                # 查找相关消费记录
                consumption = Consumption.query.filter_by(
                    customer_id=customer_id,
                    project_name=service_name
                ).order_by(Consumption.date.desc()).first()
                
                if consumption:
                    # 创建消耗记录
                    consumed_session = ConsumedSession(
                        service_item_id=service_item.id,
                        consumption_id=consumption.id,
                        consumed_at=service_date
                    )
                    db.session.add(consumed_session)
                    results["consumption_sessions_created"] += 1
                    logger.info(f"创建消耗记录: 服务项目ID={service_item.id}, 消费ID={consumption.id}")
                else:
                    logger.warning(f"未找到客户 {customer_id} 的项目 '{service_name}' 消费记录")
            
        except Exception as e:
            logger.error(f"导入服务记录时出错: {str(e)}")
            results["errors"].append(str(e))
    
    # 提交事务
    try:
        db.session.commit()
        logger.info("所有服务记录导入完成，已提交到数据库")
    except Exception as e:
        db.session.rollback()
        error_msg = f"提交服务记录到数据库时出错: {str(e)}"
        logger.error(error_msg)
        results["errors"].append(error_msg)
    
    return results

def main():
    """主函数"""
    # 搜索Excel文件
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    excel_files = []
    
    for root, _, files in os.walk(current_dir):
        for file in files:
            if file.endswith('.xlsx') and '客户' in file and '信息' in file:
                excel_files.append(os.path.join(root, file))
    
    if not excel_files:
        logger.error("未找到客户信息相关的Excel文件")
        return
    
    excel_path = excel_files[0]
    logger.info(f"找到Excel文件: {excel_path}")
    
    # 处理Excel数据
    processed_data = process_and_import_consumption_data(excel_path)
    
    if 'error' in processed_data:
        logger.error(f"处理Excel数据出错: {processed_data['error']}")
        return
    
    # 导入数据到数据库
    service_records = processed_data.get('service_records', [])
    service_items = processed_data.get('service_items', [])
    
    logger.info(f"准备导入 {len(service_records)} 条服务记录和 {len(service_items)} 条服务项目")
    
    import_results = import_service_records(service_records, service_items)
    
    # 打印导入结果
    logger.info("导入结果:")
    logger.info(f"- 创建服务记录: {import_results['services_created']}条")
    logger.info(f"- 创建服务项目: {import_results['service_items_created']}条")
    logger.info(f"- 创建消耗记录: {import_results['consumption_sessions_created']}条")
    
    if import_results['errors']:
        logger.warning(f"导入过程中有 {len(import_results['errors'])} 个错误")
        for i, error in enumerate(import_results['errors'][:5], 1):
            logger.warning(f"错误 {i}: {error}")
        if len(import_results['errors']) > 5:
            logger.warning(f"... 以及其他 {len(import_results['errors']) - 5} 个错误")

if __name__ == "__main__":
    main()