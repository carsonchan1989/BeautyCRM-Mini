#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复服务项目数据 - 从Excel读取消耗项目信息并更新到数据库
"""

import os
import sys
import json
import logging
import sqlite3
import pandas as pd
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Excel文件路径
EXCEL_FILE = 'D:\\BeautyCRM-Mini\\模拟-客户信息档案.xlsx'
# 数据库文件路径
DB_FILE = 'D:\\BeautyCRM-Mini\\server\\app.db'

def get_excel_service_data():
    """从Excel文件中读取消耗项目数据"""
    logger.info(f"开始从Excel读取消耗项目数据: {EXCEL_FILE}")
    
    try:
        # 读取Excel文件的消耗sheet
        df = pd.read_excel(EXCEL_FILE, sheet_name='消耗')
        logger.info(f"成功读取消耗表，形状: {df.shape}")
        
        # 检查数据结构
        if df.shape[0] == 0 or df.shape[1] < 10:
            logger.error("消耗表数据结构异常或为空")
            return []
        
        # 查找表头行
        header_row = None
        for i in range(min(5, df.shape[0])):
            row = df.iloc[i]
            if '客户ID' in row.values:
                header_row = i
                break
        
        if header_row is None:
            logger.error("未找到包含'客户ID'的表头行")
            return []
        
        # 使用表头行作为列名
        headers = df.iloc[header_row].tolist()
        df.columns = headers
        df = df.iloc[header_row+1:].reset_index(drop=True)
        
        logger.info(f"处理后的列名: {list(df.columns)}")
        
        # 解析服务数据
        services = []
        
        # 定义关键列索引
        customer_id_col = '客户ID'
        customer_name_col = '姓名'
        service_date_col = '到店时间'
        
        # 服务项目组，每组4列(项目内容、操作美容师、耗卡金额、是否指定)
        # 根据Excel的列名结构进行映射
        project_columns = [
            {'name': '项目内容', 'beautician': '操作美容师', 'amount': '耗卡金额', 'specified': '是否指定'}
        ]
        
        # 检查是否有多组项目列
        for i in range(1, 5):  # 最多再查找4组项目
            name_col = f'项目内容.{i}' if i > 1 else '项目内容'
            beautician_col = f'操作美容师.{i}' if i > 1 else '操作美容师'
            amount_col = f'耗卡金额.{i}' if i > 1 else '耗卡金额'
            specified_col = f'是否指定.{i}' if i > 1 else '是否指定'
            
            # 检查Excel中是否存在这些列
            if name_col in df.columns or beautician_col in df.columns or amount_col in df.columns:
                logger.info(f"找到第{i}组项目列: {name_col}")
                project_columns.append({
                    'name': name_col,
                    'beautician': beautician_col,
                    'amount': amount_col,
                    'specified': specified_col
                })
        
        # 如果没有找到完整的列映射，尝试使用数字索引方式
        if len(project_columns) <= 1:
            project_columns = []
            for i in range(1, 6):  # 最多5组项目
                project_columns.append({
                    'name': f'项目{i}',
                    'beautician': f'美容师{i}',
                    'amount': f'金额{i}',
                    'specified': f'是否指定{i}'
                })
        
        # 打印Excel的实际列名，帮助调试
        logger.info(f"Excel真实列名: {list(df.columns)}")
        
        # 处理每一行数据
        for idx, row in df.iterrows():
            try:
                # 获取客户信息
                customer_id = row[customer_id_col]
                if pd.isna(customer_id):
                    continue
                
                customer_id = str(customer_id).strip()
                customer_name = str(row[customer_name_col]).strip() if not pd.isna(row[customer_name_col]) else ""
                
                # 解析服务日期
                service_date = row[service_date_col]
                if pd.isna(service_date):
                    continue
                
                service_date_str = None
                try:
                    if isinstance(service_date, str):
                        if '/' in service_date:
                            dt = datetime.strptime(service_date, "%Y/%m/%d %H:%M")
                        else:
                            dt = datetime.strptime(service_date, "%Y-%m-%d %H:%M")
                        service_date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        dt = pd.to_datetime(service_date)
                        service_date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    logger.warning(f"解析到店时间出错 [{service_date}]: {str(e)}")
                    continue
                
                # 提取服务项目
                service_items = []
                for col_group in project_columns:
                    try:
                        name_col = col_group['name']
                        beautician_col = col_group['beautician']
                        amount_col = col_group['amount']
                        specified_col = col_group['specified']
                        
                        # 检查列是否存在
                        if name_col not in row.index:
                            logger.warning(f"列 {name_col} 不存在于当前行")
                            continue
                        
                        logger.info(f"处理列 {name_col}: 值={row[name_col]}")
                        
                        # 获取项目名称
                        project_name = row[name_col]
                        if pd.isna(project_name) or not str(project_name).strip():
                            continue
                        
                        project_name = str(project_name).strip()
                        
                        # 获取美容师
                        beautician_name = ""
                        if beautician_col in row.index and not pd.isna(row[beautician_col]):
                            beautician_name = str(row[beautician_col]).strip()
                        
                        # 获取金额
                        amount = 0.0
                        if amount_col in row.index and not pd.isna(row[amount_col]):
                            try:
                                amount = float(row[amount_col])
                            except:
                                logger.warning(f"解析项目金额出错 [{row[amount_col]}]")
                        
                        # 获取是否指定
                        is_specified = False
                        if specified_col in row.index and not pd.isna(row[specified_col]):
                            if isinstance(row[specified_col], str):
                                is_specified = row[specified_col].strip() in ['✓', '√', '是', 'Yes', 'yes', 'TRUE', 'true', 'True', '1', 'Y', 'y']
                            else:
                                is_specified = bool(row[specified_col])
                        
                        service_items.append({
                            'project_name': project_name,
                            'beautician_name': beautician_name,
                            'amount': amount,
                            'is_specified': is_specified
                        })
                        
                        logger.info(f"发现服务项目: {project_name} - {beautician_name} - {amount}元 - {'指定' if is_specified else '未指定'}")
                    except Exception as e:
                        logger.warning(f"处理项目列 {col_group} 时出错: {str(e)}")
                        continue
                
                if not service_items:
                    continue
                
                services.append({
                    'customer_id': customer_id,
                    'customer_name': customer_name,
                    'service_date': service_date_str,
                    'service_items': service_items
                })
                
                logger.info(f"读取到服务记录: 客户{customer_id}, 日期{service_date_str}, 项目数{len(service_items)}")
            
            except Exception as e:
                logger.error(f"处理行 {idx} 时出错: {str(e)}")
                continue
        
        logger.info(f"Excel数据解析完成，共 {len(services)} 条服务记录")
        return services
    
    except Exception as e:
        logger.error(f"读取Excel文件时出错: {str(e)}")
        return []

def update_service_items_in_db(services):
    """将服务项目数据更新到数据库"""
    logger.info(f"准备更新数据库服务项目: {DB_FILE}")
    
    if not services:
        logger.warning("没有可更新的服务项目数据")
        return
    
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 检查数据库表结构
        cursor.execute("PRAGMA table_info(service_items)")
        columns = [row[1] for row in cursor.fetchall()]
        logger.info(f"服务项目表结构: {columns}")
        
        # 获取所有服务记录ID和日期的映射关系
        cursor.execute("SELECT service_id, customer_id, service_date FROM services")
        service_mapping = {}
        for row in cursor.fetchall():
            service_id, customer_id, service_date = row
            key = f"{customer_id}_{service_date}"
            service_mapping[key] = service_id
        
        logger.info(f"数据库中找到 {len(service_mapping)} 条服务记录")
        
        # 清空现有的服务项目数据（可选）
        cursor.execute("DELETE FROM service_items")
        logger.info("已清空现有的服务项目数据")
        
        # 为每条服务记录添加项目
        total_updated = 0
        total_items = 0
        
        for service in services:
            customer_id = service['customer_id']
            service_date = service['service_date']
            service_items = service['service_items']
            
            # 查找对应的服务ID
            key = f"{customer_id}_{service_date}"
            if key not in service_mapping:
                logger.warning(f"未找到对应的服务记录: 客户{customer_id}, 日期{service_date}")
                continue
            
            service_id = service_mapping[key]
            logger.info(f"找到服务记录ID: {service_id}")
            
            # 添加服务项目
            for item in service_items:
                try:
                    project_name = item['project_name']
                    beautician_name = item['beautician_name']
                    amount = item['amount']
                    is_specified = item['is_specified']
                    
                    cursor.execute("""
                        INSERT INTO service_items 
                        (service_id, project_name, beautician_name, card_deduction, is_specified, is_satisfied, created_at, updated_at) 
                        VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                    """, (
                        service_id, 
                        project_name, 
                        beautician_name, 
                        amount, 
                        1 if is_specified else 0, 
                        1  # 默认满意
                    ))
                    
                    total_items += 1
                    logger.info(f"添加服务项目: {service_id} - {project_name}")
                
                except Exception as e:
                    logger.error(f"添加服务项目时出错: {str(e)}")
            
            total_updated += 1
        
        # 提交更改
        conn.commit()
        logger.info(f"数据库更新完成: 更新了 {total_updated} 条服务记录, {total_items} 个服务项目")
        
        # 关闭连接
        cursor.close()
        conn.close()
    
    except Exception as e:
        logger.error(f"更新数据库时出错: {str(e)}")

def main():
    """主函数"""
    logger.info("开始修复服务项目数据")
    
    # 从Excel获取服务项目数据
    services = get_excel_service_data()
    
    # 更新数据库
    update_service_items_in_db(services)
    
    logger.info("服务项目数据修复完成")

if __name__ == "__main__":
    main()