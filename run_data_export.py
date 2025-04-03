#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import requests
import logging
import json
from datetime import datetime
import subprocess
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DataExport')

# API 基础 URL
BASE_URL = 'http://localhost:5000/api'

def validate_data_process():
    """验证数据处理流程：上传Excel -> 数据处理 -> 数据库 -> 导出MD文档"""
    logger.info("开始验证数据处理流程")
    
    # 步骤1: 运行Excel处理测试
    logger.info("步骤1: 运行Excel处理测试")
    subprocess.run(['python', 'test_excel.py'], check=True)
    logger.info("Excel处理测试完成")
    
    # 步骤2: 上传Excel文件到服务器
    logger.info("步骤2: 上传Excel文件到服务器")
    subprocess.run(['python', 'upload_excel.py'], check=True)
    logger.info("Excel文件上传完成")
    
    # 给服务器一些处理时间
    time.sleep(1)
    
    # 步骤3: 导出数据到Markdown
    logger.info("步骤3: 导出数据到Markdown")
    export_data_to_markdown()
    logger.info("数据导出完成")
    
    logger.info("数据处理流程验证完成")
    return True

def get_unique_key_for_consumption(consumption):
    """为消费记录创建唯一键"""
    date_str = consumption['date'] if 'date' in consumption else ''
    project = consumption['project_name'] if 'project_name' in consumption else ''
    amount = str(consumption['amount']) if 'amount' in consumption and consumption['amount'] is not None else ''
    payment = consumption['payment_method'] if 'payment_method' in consumption else ''
    return f"{date_str}_{project}_{amount}_{payment}"

def get_unique_key_for_service(service):
    """为服务记录创建唯一键"""
    date_str = service['service_date'] if 'service_date' in service else ''
    service_id = service.get('service_id', '')  # 使用service_id作为唯一标识
    if service_id:
        return f"{service_id}"  # 如果有service_id，直接使用它作为唯一键
    
    # 兼容旧结构，使用组合字段作为唯一键
    items = service.get('service_items', [])
    # 如果service_items是列表，使用第一个项目的名称，否则直接使用
    item_name = items[0]['project_name'] if isinstance(items, list) and len(items) > 0 else ''
    beautician = items[0].get('beautician_name', '') if isinstance(items, list) and len(items) > 0 else ''
    amount = str(service.get('total_amount', 0))
    is_specified = "1" if items and isinstance(items, list) and len(items) > 0 and items[0].get('is_specified', False) else "0"
    
    return f"{date_str}_{item_name}_{beautician}_{amount}_{is_specified}"

def get_unique_key_for_communication(comm):
    """为沟通记录生成唯一键"""
    if not comm:
        return None
    
    # 使用沟通时间、地点和内容创建唯一键
    # 使用正确的字段名
    time_str = str(comm['communication_date']) if 'communication_date' in comm else ''
    location = str(comm['communication_location']) if 'communication_location' in comm else ''
    content = str(comm['communication_content']) if 'communication_content' in comm else ''
    
    # 组合成唯一键
    key = f"{time_str}_{location}_{content}"
    return key

def export_data_to_markdown():
    """从API获取数据并导出到Markdown文件"""
    logger.info("获取客户数据...")
    customers_response = requests.get(f'{BASE_URL}/customers')
    customers_data = customers_response.json()
    
    # 确认我们获取到了客户列表
    if isinstance(customers_data, str):
        customers = json.loads(customers_data)
    else:
        customers = customers_data
    
    if not isinstance(customers, list):
        logger.info(f"API返回的数据格式: {type(customers)}")
        if isinstance(customers, dict):
            if 'items' in customers:
                logger.info(f"从'items'字段中提取客户列表，包含 {len(customers['items'])} 条记录")
                customers = customers['items'] 
            elif 'data' in customers:
                logger.info("从'data'字段中提取客户列表")
                customers = customers['data']
            else:
                logger.error(f"无法从dict中提取客户列表，键: {list(customers.keys())}")
                customers = []
        else:
            logger.error(f"无法解析客户数据: {customers}")
            customers = []
    
    logger.info(f"获取到 {len(customers)} 个客户记录")
    result_data = {}
    
    for customer in customers:
        if isinstance(customer, str):
            try:
                customer = json.loads(customer)
            except:
                logger.error(f"无法解析客户数据字符串: {customer}")
                continue
        
        if not isinstance(customer, dict):
            logger.error(f"客户数据格式无效，预期为字典: {customer}")
            continue
            
        customer_id = customer.get('id')
        if not customer_id:
            logger.error(f"客户数据缺少ID字段: {customer}")
            continue
        
        logger.info(f"处理客户数据: {customer_id} - {customer.get('name', '未知')}")
        
        # 获取健康档案
        logger.info(f"获取客户 {customer_id} 的健康档案...")
        health_response = requests.get(f'{BASE_URL}/customers/{customer_id}/health')
        health_data = health_response.json()
        
        # 处理健康档案响应
        if isinstance(health_data, str):
            try:
                health_record = json.loads(health_data)
            except:
                health_record = {}
        elif isinstance(health_data, dict):
            if 'items' in health_data and health_data['items']:
                health_record = health_data['items'][0]
            else:
                health_record = health_data
        elif isinstance(health_data, list) and len(health_data) > 0:
            health_record = health_data[0]
        else:
            health_record = {}
        
        # 获取消费记录
        logger.info(f"获取客户 {customer_id} 的消费记录...")
        consumption_response = requests.get(f'{BASE_URL}/customers/{customer_id}/consumption')
        consumption_data = consumption_response.json()
        
        # 处理消费记录响应
        if isinstance(consumption_data, str):
            try:
                consumption_records = json.loads(consumption_data)
            except:
                consumption_records = []
        elif isinstance(consumption_data, list):
            consumption_records = consumption_data
        elif isinstance(consumption_data, dict):
            if 'items' in consumption_data:
                consumption_records = consumption_data['items']
            elif 'data' in consumption_data:
                consumption_records = consumption_data['data']
            else:
                logger.warning(f"消费记录数据结构无法解析: {list(consumption_data.keys())}")
                consumption_records = []
        else:
            consumption_records = []
        
        # 消费记录去重
        processed_consumption_records = []
        seen_consumption_keys = set()
        
        for consumption in consumption_records:
            key = get_unique_key_for_consumption(consumption)
            if key not in seen_consumption_keys:
                seen_consumption_keys.add(key)
                processed_consumption_records.append(consumption)
        
        # 获取服务记录
        logger.info(f"获取客户 {customer_id} 的服务记录...")
        service_response = requests.get(f'{BASE_URL}/customers/{customer_id}/service')
        service_data = service_response.json()
        
        # 处理服务记录响应
        if isinstance(service_data, str):
            try:
                service_records = json.loads(service_data)
            except:
                service_records = []
        elif isinstance(service_data, list):
            service_records = service_data
        elif isinstance(service_data, dict):
            if 'items' in service_data:
                service_records = service_data['items']
            elif 'data' in service_data:
                service_records = service_data['data']
            else:
                logger.warning(f"服务记录数据结构无法解析: {list(service_data.keys())}")
                service_records = []
        else:
            service_records = []
        
        logger.info(f"客户 {customer_id} 获取到 {len(service_records)} 条服务记录")
        
        # 服务记录处理：去重并有效性检查
        valid_service_records = []
        seen_service_keys = set()
        
        for service in service_records:
            # 处理服务日期前先检查service是否为字典
            if not isinstance(service, dict):
                logger.warning(f"跳过非字典格式的服务记录: {service}")
                continue
                
            if service.get('service_date'):  # 确保有服务日期
                key = get_unique_key_for_service(service)
                if key not in seen_service_keys:
                    seen_service_keys.add(key)
                    # 确保服务项目为列表而不是默认为空列表
                    if 'service_items' not in service:
                        service['service_items'] = []
                    # 确保service_items是一个列表
                    if not isinstance(service['service_items'], list):
                        service['service_items'] = [service['service_items']]
                    valid_service_records.append(service)
        
        # 按服务日期排序
        valid_service_records = sorted(
            valid_service_records, 
            key=lambda x: x.get('service_date', ''), 
            reverse=True
        )
        
        logger.info(f"客户 {customer_id} 原始服务记录数: {len(service_records)}, 处理后记录数: {len(valid_service_records)}")
        
        # 获取沟通记录
        logger.info(f"获取客户 {customer_id} 的沟通记录...")
        communication_response = requests.get(f'{BASE_URL}/customers/{customer_id}/communication')
        communication_data = communication_response.json()
        
        # 处理沟通记录响应
        if isinstance(communication_data, str):
            try:
                communication_records = json.loads(communication_data)
            except:
                communication_records = []
        elif isinstance(communication_data, list):
            communication_records = communication_data
        elif isinstance(communication_data, dict):
            if 'items' in communication_data:
                communication_records = communication_data['items']
            elif 'data' in communication_data:
                communication_records = communication_data['data']
            else:
                logger.warning(f"沟通记录数据结构无法解析: {list(communication_data.keys())}")
                communication_records = []
        else:
            communication_records = []
        
        # 沟通记录去重
        processed_communication_records = []
        seen_communication_keys = set()
        
        for comm in communication_records:
            key = get_unique_key_for_communication(comm)
            if key not in seen_communication_keys:
                seen_communication_keys.add(key)
                processed_communication_records.append(comm)
        
        # 存储客户数据
        result_data[customer_id] = {
            'customer': customer,
            'health_record': health_record,
            'consumption_records': processed_consumption_records,
            'service_records': valid_service_records,
            'communication_records': processed_communication_records
        }
    
    # 将数据写入 Markdown 文件
    with open('database_records.md', 'w', encoding='utf-8') as f:
        f.write("# 客户数据记录导出\n\n")
        f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"总客户数: {len(customers)}\n\n")
        f.write("---\n\n")
        
        # 按客户ID逆序排列
        for customer_id in sorted(result_data.keys(), reverse=True):
            data = result_data[customer_id]
            customer = data['customer']
            health_record = data['health_record']
            consumption_records = data['consumption_records']
            service_records = data['service_records']
            communication_records = data['communication_records']
            
            # 客户基本信息
            f.write(f"## 客户: {customer.get('name', '未知')} ({customer.get('id', '未知')})\n\n")
            
            # 基本信息表格
            f.write("### 基本信息\n\n")
            f.write("| 字段 | 值 |\n")
            f.write("|------|----|")  # 表头分隔符
            
            # 客户主要字段
            fields = [
                ('姓名', 'name'), ('性别', 'gender'), ('年龄', 'age'), 
                ('门店归属', 'store'), ('籍贯', 'hometown'),
                ('现居地', 'residence'), ('居住时长', 'residence_years'),
                ('家庭成员构成', 'family_structure'), ('家庭人员年龄分布', 'family_age_distribution'),
                ('家庭居住情况', 'living_condition'), ('性格类型标签', 'personality_tags'),
                ('消费决策主导', 'consumption_decision'), ('兴趣爱好', 'hobbies'),
                ('作息规律', 'routine'), ('饮食偏好', 'diet_preference'),
                ('职业', 'occupation'), ('单位性质', 'work_unit_type'), ('年收入', 'annual_income'),
                ('工作性质', 'work_nature')
            ]
            
            for label, field in fields:
                if field in customer and customer.get(field):
                    f.write(f"\n| {label} | {customer.get(field, '')} |")
            
            f.write("\n\n")
            
            # 健康档案
            if health_record:
                f.write("### 健康档案\n\n")
                f.write("| 类别 | 字段 | 值 |\n")
                f.write("|------|------|----|")
                
                # 皮肤状况
                skin_fields = [
                    ('皮肤状况', '肤质类型', 'skin_type'),
                    ('皮肤状况', '水油平衡', 'oil_water_balance'),
                    ('皮肤状况', '毛孔与黑头', 'pores_blackheads'),
                    ('皮肤状况', '皱纹与纹理', 'wrinkles_texture'),
                    ('皮肤状况', '色素沉着', 'pigmentation'),
                    ('皮肤状况', '光老化与炎症', 'photoaging_inflammation')
                ]
                
                for category, label, field in skin_fields:
                    if field in health_record and health_record[field]:
                        f.write(f"\n| {category} | {label} | {health_record[field]} |")
                
                # 中医体质
                tcm_fields = [
                    ('中医体质', '体质类型', 'tcm_constitution'),
                    ('中医体质', '舌象特征', 'tongue_features'),
                    ('中医体质', '脉象数据', 'pulse_data')
                ]
                
                for category, label, field in tcm_fields:
                    if field in health_record and health_record[field]:
                        f.write(f"\n| {category} | {label} | {health_record[field]} |")
                
                # 生活习惯
                lifestyle_fields = [
                    ('生活习惯', '作息规律', 'sleep_routine'),
                    ('生活习惯', '运动频率', 'exercise_pattern'),
                    ('生活习惯', '饮食禁忌', 'diet_restrictions')
                ]
                
                for category, label, field in lifestyle_fields:
                    if field in health_record and health_record[field]:
                        f.write(f"\n| {category} | {label} | {health_record[field]} |")
                
                # 护理需求
                care_fields = [
                    ('护理需求', '时间灵活度', 'care_time_flexibility'),
                    ('护理需求', '手法力度偏好', 'massage_pressure_preference'),
                    ('护理需求', '环境氛围', 'environment_requirements')
                ]
                
                for category, label, field in care_fields:
                    if field in health_record and health_record[field]:
                        f.write(f"\n| {category} | {label} | {health_record[field]} |")
                
                # 美容健康目标
                goal_fields = [
                    ('美容健康目标', '短期美丽目标', 'short_term_beauty_goal'),
                    ('美容健康目标', '长期美丽目标', 'long_term_beauty_goal'),
                    ('美容健康目标', '短期健康目标', 'short_term_health_goal'),
                    ('美容健康目标', '长期健康目标', 'long_term_health_goal')
                ]
                
                for category, label, field in goal_fields:
                    if field in health_record and health_record[field]:
                        f.write(f"\n| {category} | {label} | {health_record[field]} |")
                
                # 健康记录
                health_history_fields = [
                    ('健康记录', '医美操作史', 'medical_cosmetic_history'),
                    ('健康记录', '大健康服务史', 'wellness_service_history'),
                    ('健康记录', '过敏史', 'allergies'),
                    ('健康记录', '重大疾病历史', 'major_disease_history')
                ]
                
                for category, label, field in health_history_fields:
                    if field in health_record and health_record[field]:
                        f.write(f"\n| {category} | {label} | {health_record[field]} |")
                
                f.write("\n\n")
            
            # 消费记录
            if consumption_records:
                f.write("### 消费记录\n\n")
                f.write("| 序号 | 消费时间 | 项目名称 | 消费金额 | 支付方式 | 总次数 | 耗卡完成时间 | 满意度 |\n")
                f.write("|------|----------|----------|----------|----------|--------|--------------|--------|")
                
                for idx, record in enumerate(consumption_records, 1):
                    # 获取并格式化日期字段，只保留年月日
                    consumption_date_raw = record.get('date', '')
                    completion_date_raw = record.get('completion_date', '')
                    
                    # 尝试将日期时间字符串转换为只有日期的格式
                    try:
                        if consumption_date_raw and isinstance(consumption_date_raw, str):
                            # 尝试解析日期时间字符串
                            if ' ' in consumption_date_raw:  # 如果包含时间部分
                                consumption_date = consumption_date_raw.split(' ')[0]  # 只取日期部分
                            else:
                                consumption_date = consumption_date_raw
                        else:
                            consumption_date = consumption_date_raw
                    except Exception:
                        consumption_date = consumption_date_raw
                        
                    try:
                        if completion_date_raw and isinstance(completion_date_raw, str):
                            # 尝试解析日期时间字符串
                            if ' ' in completion_date_raw:  # 如果包含时间部分
                                completion_date = completion_date_raw.split(' ')[0]  # 只取日期部分
                            else:
                                completion_date = completion_date_raw
                        else:
                            completion_date = completion_date_raw
                    except Exception:
                        completion_date = completion_date_raw
                    
                    project_name = record.get('project_name', '')
                    amount = record.get('amount', '')
                    payment_method = record.get('payment_method', '')
                    total_sessions = record.get('total_sessions', '')
                    satisfaction = record.get('satisfaction', '')
                    
                    f.write(f"\n| {idx} | {consumption_date} | {project_name} | {amount} | {payment_method} | {total_sessions} | {completion_date} | {satisfaction} |")
                
                f.write("\n\n")
            
            # 服务记录
            if service_records:
                f.write("### 服务记录\n\n")
                
                for idx, record in enumerate(service_records, 1):
                    service_date = record.get('service_date', '')
                    total_amount = record.get('total_amount', 0)
                    total_sessions = record.get('total_sessions', 0)
                    satisfaction = record.get('satisfaction', '')
                    service_items = record.get('service_items', [])
                    
                    # 格式化满意度显示
                    if satisfaction:
                        # 尝试将满意度转为数字格式（如果是数字）
                        try:
                            sat_value = float(satisfaction)
                            satisfaction_display = f"{sat_value}/5"
                        except (ValueError, TypeError):
                            satisfaction_display = satisfaction
                    else:
                        satisfaction_display = "未评价"
                    
                    # 输出服务记录主信息，注意序号显示方式
                    f.write(f"服务记录 {idx}：服务时间 {service_date}, 总耗卡金额: {total_amount}, 总耗卡次数: {total_sessions}, 满意度: {satisfaction_display}\n")
                    
                    # 添加服务项目结构的调试日志
                    print(f"DEBUG - 服务项目结构: {service_items}")
                    
                    # 输出服务项目详情
                    if service_items:
                        # 检查service_items的类型
                        if isinstance(service_items, list):
                            # 新结构：service_items是对象列表
                            for item_idx, item in enumerate(service_items, 1):
                                # 打印服务项目详情的调试信息
                                print(f"DEBUG - 服务项目详情: {item}")
                                
                                # 获取项目数据，优先使用真实数据
                                project_name = item.get('project_name', '')
                                beautician_name = item.get('beautician_name', '')
                                amount = item.get('card_deduction', 0) or item.get('unit_price', 0)
                                is_specified = item.get('is_specified', False)
                                
                                # 显示真实数据而不是默认"无详情"
                                project_display = project_name if project_name else "无项目名称"
                                beautician_display = beautician_name if beautician_name else "无美容师"
                                amount_display = amount if amount else "无金额"
                                
                                # 指定状态转为中文
                                specified_text = "是" if is_specified else "否"
                                
                                f.write(f"  - 项目{item_idx}: {project_display}, 美容师: {beautician_display}, 金额: {amount_display}, 是否指定: {specified_text}\n")
                        else:
                            # 兼容旧结构：service_items可能是字符串
                            project_name = service_items if isinstance(service_items, str) else "无项目名称"
                            beautician_name = record.get('beautician', '无美容师')
                            amount = record.get('service_amount', '无金额')
                            is_specified = record.get('is_specified', False)
                            specified_text = "是" if is_specified else "否"
                            
                            f.write(f"  - 项目1: {project_name}, 美容师: {beautician_name}, 金额: {amount}, 是否指定: {specified_text}\n")
                    else:
                        f.write("  - 无项目详情\n")
                    
                    f.write("\n")
            
            # 沟通记录
            if communication_records:
                f.write("### 沟通记录\n\n")
                f.write("| 序号 | 沟通时间 | 沟通地点 | 沟通内容 |\n")
                f.write("|------|----------|----------|----------|")
                
                for idx, record in enumerate(communication_records, 1):
                    communication_time = record.get('communication_date', '')
                    location = record.get('communication_location', '')
                    content = record.get('communication_content', '')
                    
                    f.write(f"\n| {idx} | {communication_time} | {location} | {content} |")
                
                f.write("\n\n")
            
            f.write("---\n\n")
    
    logger.info(f"数据导出完成: database_records.md")
    print(f"数据库记录已导出到: database_records.md")

if __name__ == "__main__":
    # 验证整个数据处理流程
    validate_data_process()