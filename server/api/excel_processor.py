"""
Excel导入数据处理模块 - 解析Excel文件并保存到数据库
"""
import os
import pandas as pd
from datetime import datetime
from flask import current_app
from server.models import db, Customer, Service, ServiceItem

def process_excel_file(file_path):
    """
    处理Excel文件，导入数据到数据库
    
    Args:
        file_path: Excel文件路径
        
    Returns:
        dict: 导入结果统计
    """
    current_app.logger.info(f"开始处理Excel文件: {file_path}")
    
    if not os.path.exists(file_path):
        current_app.logger.error(f"文件不存在: {file_path}")
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 统计结果
    stats = {
        'customers': 0,
        'services': 0,
        'service_items': 0,
        'errors': []
    }
    
    # 读取Excel文件
    try:
        # 确定工作表
        xlsx = pd.ExcelFile(file_path)
        sheet_names = xlsx.sheet_names
        current_app.logger.info(f"Excel文件包含工作表: {sheet_names}")
        
        # 查找客户和消耗表
        customer_sheet = None
        service_sheet = None
        
        for sheet in sheet_names:
            if any(keyword in sheet for keyword in ['客户', '档案', '基础', '信息']):
                customer_sheet = sheet
            elif any(keyword in sheet for keyword in ['消耗', '服务', '消费']):
                service_sheet = sheet
        
        current_app.logger.info(f"识别出的客户表: {customer_sheet}, 消耗表: {service_sheet}")
        
        # 处理客户数据
        if customer_sheet:
            stats['customers'] = import_customers(xlsx, customer_sheet)
        
        # 处理消耗数据
        if service_sheet:
            service_stats = import_services(xlsx, service_sheet)
            stats['services'] = service_stats['services']
            stats['service_items'] = service_stats['items']
        
        current_app.logger.info(f"Excel导入完成，结果: {stats}")
        return stats
        
    except Exception as e:
        current_app.logger.error(f"处理Excel文件出错: {str(e)}")
        stats['errors'].append(str(e))
        raise e


def import_customers(xlsx, sheet_name):
    """导入客户数据"""
    current_app.logger.info(f"开始导入客户数据，表名: {sheet_name}")
    
    # 读取客户表数据
    df = pd.read_excel(xlsx, sheet_name=sheet_name)
    current_app.logger.info(f"读取到 {len(df)} 行客户数据")
    
    # 标准字段映射 - 将Excel中的列名映射到数据库字段
    field_mapping = {
        'ID': 'id',
        '客户ID': 'id',
        '编号': 'id',
        '姓名': 'name',
        '名称': 'name',
        '性别': 'gender',
        '年龄': 'age',
        '门店': 'store',
        '门店归属': 'store',
        '店面': 'store',
        '籍贯': 'hometown',
        '家乡': 'hometown',
        '现居地': 'residence',
        '居住地': 'residence',
        '居住时长': 'residence_years',
        '居住年限': 'residence_years',
        '家庭构成': 'family_structure',
        '家庭成员': 'family_structure',
        '家庭人员年龄分布': 'family_age_distribution',
        '家庭年龄分布': 'family_age_distribution',
        '居住情况': 'living_condition',
        '家庭居住情况': 'living_condition',
        '性格类型': 'personality_tags',
        '性格标签': 'personality_tags',
        '消费决策': 'consumption_decision',
        '消费决策方式': 'consumption_decision',
        '风险敏感度': 'risk_sensitivity',
        '兴趣爱好': 'hobbies',
        '爱好': 'hobbies',
        '作息规律': 'routine',
        '作息': 'routine',
        '饮食偏好': 'diet_preference',
        '饮食习惯': 'diet_preference',
        '职业': 'occupation',
        '工作': 'occupation',
        '单位性质': 'work_unit_type',
        '工作单位性质': 'work_unit_type',
        '年收入': 'annual_income',
        '收入': 'annual_income'
    }
    
    # 处理每行数据
    imported_count = 0
    
    for _, row in df.iterrows():
        try:
            # 检查必要字段
            customer_id = None
            customer_name = None
            
            # 尝试获取ID
            for col in ['ID', '客户ID', '编号']:
                if col in row and not pd.isna(row[col]):
                    customer_id = str(row[col]).strip()
                    break
            
            # 尝试获取姓名
            for col in ['姓名', '名称', '客户姓名']:
                if col in row and not pd.isna(row[col]):
                    customer_name = str(row[col]).strip()
                    break
            
            # 检查必要字段是否存在
            if not customer_id or not customer_name:
                current_app.logger.warning(f"跳过行，缺少必要字段: ID={customer_id}, 姓名={customer_name}")
                continue
            
            # 检查客户是否已存在
            existing_customer = Customer.query.get(customer_id)
            if existing_customer:
                current_app.logger.info(f"更新已存在的客户: {customer_id}")
                update_customer = existing_customer
            else:
                current_app.logger.info(f"创建新客户: {customer_id}")
                update_customer = Customer(id=customer_id)
                
            # 设置姓名
            update_customer.name = customer_name
            
            # 映射其他字段
            for excel_col, db_col in field_mapping.items():
                if excel_col in row and not pd.isna(row[excel_col]) and excel_col not in ['ID', '客户ID', '编号', '姓名', '名称', '客户姓名']:
                    value = row[excel_col]
                    
                    # 特殊处理某些字段类型
                    if db_col == 'age' and not pd.isna(value):
                        try:
                            value = int(value)
                        except:
                            value = None
                    
                    # 设置属性
                    if hasattr(update_customer, db_col):
                        setattr(update_customer, db_col, value)
            
            # 设置时间戳
            now = datetime.now()
            if not existing_customer:
                update_customer.created_at = now
            update_customer.updated_at = now
            
            # 保存到数据库
            db.session.add(update_customer)
            imported_count += 1
            
            # 每50条提交一次
            if imported_count % 50 == 0:
                db.session.commit()
                current_app.logger.info(f"已导入 {imported_count} 条客户数据")
                
        except Exception as e:
            current_app.logger.error(f"导入客户数据出错: {str(e)}")
            db.session.rollback()
    
    # 最后提交一次
    db.session.commit()
    current_app.logger.info(f"客户数据导入完成，共导入 {imported_count} 条")
    
    return imported_count


def import_services(xlsx, sheet_name):
    """导入服务消耗数据"""
    current_app.logger.info(f"开始导入消耗数据，表名: {sheet_name}")
    
    # 读取消耗表数据
    df = pd.read_excel(xlsx, sheet_name=sheet_name)
    current_app.logger.info(f"读取到 {len(df)} 行消耗数据")
    
    # 统计
    stats = {
        'services': 0,
        'items': 0
    }
    
    # 按客户ID和进店时间分组处理
    for _, row in df.iterrows():
        try:
            # 获取必要字段
            customer_id = None
            service_date = None
            
            # 尝试获取客户ID
            for col in ['客户ID', '顾客ID', 'ID']:
                if col in row and not pd.isna(row[col]):
                    customer_id = str(row[col]).strip()
                    break
            
            # 尝试获取服务日期
            for col in ['进店时间', '服务时间', '日期']:
                if col in row and not pd.isna(row[col]):
                    service_date_value = row[col]
                    if isinstance(service_date_value, str):
                        # 尝试解析日期字符串
                        try:
                            service_date = datetime.strptime(service_date_value, '%Y/%m/%d %H:%M:%S')
                        except:
                            try:
                                service_date = datetime.strptime(service_date_value, '%Y-%m-%d %H:%M:%S')
                            except:
                                pass
                    else:
                        # 可能是pandas时间戳
                        service_date = service_date_value
                    break
            
            # 检查必要字段
            if not customer_id or not service_date:
                current_app.logger.warning(f"跳过消耗记录，缺少必要字段: 客户ID={customer_id}, 进店时间={service_date}")
                continue
            
            # 检查客户是否存在
            customer = Customer.query.get(customer_id)
            if not customer:
                current_app.logger.warning(f"跳过消耗记录，客户不存在: {customer_id}")
                continue
            
            # 创建服务记录
            service = Service(
                customer_id=customer_id,
                customer_name=customer.name,
                service_date=service_date
            )
            
            # 设置离店时间
            if '离店时间' in row and not pd.isna(row['离店时间']):
                departure_value = row['离店时间']
                if isinstance(departure_value, str):
                    try:
                        departure_time = datetime.strptime(departure_value, '%Y/%m/%d %H:%M:%S')
                    except:
                        try:
                            departure_time = datetime.strptime(departure_value, '%Y-%m-%d %H:%M:%S')
                        except:
                            departure_time = None
                else:
                    departure_time = departure_value
                
                if departure_time:
                    service.departure_time = departure_time
            
            # 设置总金额
            for col in ['总耗卡金额', '总金额', '金额']:
                if col in row and not pd.isna(row[col]):
                    try:
                        service.total_amount = float(row[col])
                    except:
                        pass
                    break
            
            # 设置总消耗项目数
            for col in ['总消耗项目数', '项目总数', '消耗数']:
                if col in row and not pd.isna(row[col]):
                    try:
                        service.total_sessions = int(row[col])
                    except:
                        pass
                    break
            
            # 设置支付方式
            if '支付方式' in row and not pd.isna(row['支付方式']):
                service.payment_method = str(row['支付方式'])
            
            # 设置操作人
            if '操作人' in row and not pd.isna(row['操作人']):
                service.operator = str(row['操作人'])
            
            # 设置满意度
            if '服务满意度' in row and not pd.isna(row['服务满意度']):
                service.satisfaction = str(row['服务满意度'])
            
            # 添加服务项目
            items_count = 0
            
            # 查找项目列
            for i in range(1, 6):  # 最多处理5个项目
                project_col = f'项目{i}'
                beautician_col = f'美容师{i}'
                amount_col = f'金额{i}'
                specified_col = f'是否指定{i}'
                
                if project_col in row and not pd.isna(row[project_col]):
                    # 创建服务项目
                    service_item = ServiceItem(
                        project_name=str(row[project_col])
                    )
                    
                    # 设置美容师
                    if beautician_col in row and not pd.isna(row[beautician_col]):
                        service_item.beautician_name = str(row[beautician_col])
                    
                    # 设置金额
                    if amount_col in row and not pd.isna(row[amount_col]):
                        try:
                            service_item.unit_price = float(row[amount_col])
                        except:
                            service_item.unit_price = 0
                    
                    # 设置是否指定
                    if specified_col in row and not pd.isna(row[specified_col]):
                        specified_value = row[specified_col]
                        is_specified = False
                        
                        if isinstance(specified_value, str):
                            is_specified = specified_value.strip() in ['✓', '√', '是', 'True', 'YES', '1']
                        elif isinstance(specified_value, bool):
                            is_specified = specified_value
                        elif isinstance(specified_value, (int, float)):
                            is_specified = int(specified_value) == 1
                        
                        service_item.is_specified = 1 if is_specified else 0
                    
                    # 添加到服务记录
                    service.service_items.append(service_item)
                    items_count += 1
            
            # 保存服务记录
            db.session.add(service)
            stats['services'] += 1
            stats['items'] += items_count
            
            # 每20条提交一次
            if stats['services'] % 20 == 0:
                db.session.commit()
                current_app.logger.info(f"已导入 {stats['services']} 条服务记录，{stats['items']} 个服务项目")
            
        except Exception as e:
            current_app.logger.error(f"导入服务记录出错: {str(e)}")
            db.session.rollback()
    
    # 最后提交一次
    db.session.commit()
    current_app.logger.info(f"服务数据导入完成，共导入 {stats['services']} 条服务记录，{stats['items']} 个服务项目")
    
    return stats