#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复Service数据库模型结构
将旧的Service模型转换为新的Service+ServiceItem结构
"""

import os
import sys
import logging
import sqlite3
from datetime import datetime
from flask import Flask
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ServiceModelFixer')

def generate_service_id():
    """生成服务记录ID"""
    import uuid
    return f"SVC{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"

def fix_service_model(db_path='instance/beauty_crm.db'):
    """修复服务记录模型结构"""
    logger.info(f"开始修复服务记录模型结构: {db_path}")
    
    if not os.path.exists(db_path):
        logger.error(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 检查数据库表结构
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"现有数据库表: {tables}")
        
        # 检查是否存在旧的services表
        if 'services' in tables:
            # 查看services表结构
            cursor.execute("PRAGMA table_info(services)")
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]
            logger.info(f"services表结构: {column_names}")
            
            # 检查主键类型
            id_column = next((col for col in columns if col[1] == 'id'), None)
            service_id_column = next((col for col in columns if col[1] == 'service_id'), None)
            
            # 如果存在id列但不存在service_id列，说明是旧结构
            if id_column and not service_id_column:
                logger.info("检测到旧的services表结构，进行转换")
                
                # 创建临时表备份原数据
                cursor.execute("CREATE TABLE services_backup AS SELECT * FROM services")
                logger.info("已创建services_backup表作为备份")
                
                # 获取所有服务记录
                cursor.execute("SELECT * FROM services_backup")
                old_services = cursor.fetchall()
                logger.info(f"从services_backup表读取到 {len(old_services)} 条服务记录")
                
                # 检查是否存在service_items表
                if 'service_items' not in tables:
                    # 创建service_items表
                    cursor.execute("""
                    CREATE TABLE service_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service_id TEXT NOT NULL,
                        project_id TEXT,
                        project_name TEXT NOT NULL,
                        beautician_name TEXT,
                        card_deduction REAL,
                        quantity INTEGER DEFAULT 1,
                        unit_price REAL,
                        is_specified INTEGER DEFAULT 0,
                        remark TEXT,
                        is_satisfied INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE
                    )
                    """)
                    logger.info("已创建service_items表")
                
                # 删除原services表
                cursor.execute("DROP TABLE services")
                logger.info("已删除原services表")
                
                # 创建新的services表
                cursor.execute("""
                CREATE TABLE services (
                    service_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    customer_name TEXT,
                    service_date TEXT NOT NULL,
                    departure_time TEXT,
                    total_amount REAL DEFAULT 0,
                    total_sessions INTEGER DEFAULT 0,
                    payment_method TEXT,
                    operator TEXT,
                    remark TEXT,
                    satisfaction TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                )
                """)
                logger.info("已创建新的services表")
                
                # 创建服务记录唯一性索引
                cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS uix_service_record 
                ON services(customer_id, service_date, IFNULL(operator, ''), total_amount)
                """)
                
                # 创建服务项目索引
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_service_items_service_id ON service_items(service_id)")
                
                # 从备份表导入数据到新表
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                for old_service in old_services:
                    try:
                        # 生成新的service_id
                        service_id = generate_service_id()
                        customer_id = old_service['customer_id']
                        
                        # 获取customer_name
                        cursor.execute("SELECT name FROM customers WHERE id = ?", (customer_id,))
                        customer_row = cursor.fetchone()
                        customer_name = customer_row['name'] if customer_row else None
                        
                        # 基本字段映射
                        service_date = old_service['service_date']
                        departure_time = old_service['departure_time']
                        total_amount = old_service['total_amount'] or 0
                        satisfaction = old_service['satisfaction']
                        created_at = old_service['created_at'] if 'created_at' in old_service.keys() else now
                        updated_at = old_service['updated_at'] if 'updated_at' in old_service.keys() else now
                        
                        # 插入新的服务记录
                        cursor.execute("""
                        INSERT INTO services (
                            service_id, customer_id, customer_name, service_date, departure_time,
                            total_amount, satisfaction, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            service_id, customer_id, customer_name, service_date, departure_time,
                            total_amount, satisfaction, created_at, updated_at
                        ))
                        
                        # 处理服务项目
                        # 尝试从service_items字段解析项目
                        service_items = []
                        service_items_text = old_service.get('service_items', '')
                        beautician = old_service.get('beautician', '')
                        service_amount = old_service.get('service_amount', 0)
                        is_specified = old_service.get('is_specified', False)
                        
                        # 如果service_items是字符串，尝试作为单个项目处理
                        if service_items_text and isinstance(service_items_text, str):
                            service_items.append({
                                'project_name': service_items_text,
                                'beautician_name': beautician,
                                'unit_price': service_amount,
                                'is_specified': is_specified
                            })
                        
                        # 如果没有解析到项目，创建一个默认项目
                        if not service_items:
                            service_items.append({
                                'project_name': '服务项目',
                                'beautician_name': beautician,
                                'unit_price': service_amount,
                                'is_specified': is_specified
                            })
                        
                        # 插入服务项目
                        for item in service_items:
                            # 处理is_specified字段，确保它是布尔值
                            is_specified_val = 1 if item.get('is_specified') else 0
                            
                            cursor.execute("""
                            INSERT INTO service_items (
                                service_id, project_name, beautician_name, unit_price, 
                                is_specified, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                service_id, 
                                item.get('project_name', '服务项目'),
                                item.get('beautician_name', ''),
                                item.get('unit_price', 0),
                                is_specified_val,
                                created_at,
                                updated_at
                            ))
                        
                        logger.info(f"成功导入服务记录: {service_id} - {customer_name}")
                    
                    except Exception as e:
                        logger.error(f"导入服务记录出错: {str(e)}")
                        raise
                
                logger.info("服务记录导入完成，提交事务")
                conn.commit()
                
                logger.info("检查新表中的记录数")
                cursor.execute("SELECT COUNT(*) FROM services")
                new_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM service_items")
                items_count = cursor.fetchone()[0]
                
                logger.info(f"新services表中有 {new_count} 条记录")
                logger.info(f"service_items表中有 {items_count} 条记录")
                
                if new_count == len(old_services):
                    logger.info("记录数匹配，转换成功")
                else:
                    logger.warning(f"记录数不匹配: 原 {len(old_services)} 条，新 {new_count} 条")
                
            else:
                logger.info("服务记录表结构已经是最新的，不需要转换")
        
        else:
            logger.info("未找到services表，创建新表")
            
            # 创建services表
            cursor.execute("""
            CREATE TABLE services (
                service_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                customer_name TEXT,
                service_date TEXT NOT NULL,
                departure_time TEXT,
                total_amount REAL DEFAULT 0,
                total_sessions INTEGER DEFAULT 0,
                payment_method TEXT,
                operator TEXT,
                remark TEXT,
                satisfaction TEXT,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
            """)
            
            # 创建service_items表
            cursor.execute("""
            CREATE TABLE service_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_id TEXT NOT NULL,
                project_id TEXT,
                project_name TEXT NOT NULL,
                beautician_name TEXT,
                card_deduction REAL,
                quantity INTEGER DEFAULT 1,
                unit_price REAL,
                is_specified INTEGER DEFAULT 0,
                remark TEXT,
                is_satisfied INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE
            )
            """)
            
            # 创建索引
            cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS uix_service_record 
            ON services(customer_id, service_date, IFNULL(operator, ''), total_amount)
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_service_items_service_id ON service_items(service_id)")
            
            logger.info("成功创建services和service_items表")
        
        conn.close()
        logger.info("服务记录模型结构修复完成")
        return True
        
    except Exception as e:
        logger.error(f"修复服务记录模型结构时出错: {str(e)}")
        return False

def main():
    """脚本主函数"""
    logger.info("开始运行服务记录模型修复脚本")
    
    # 确定数据库路径
    db_path = 'instance/beauty_crm.db'
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    if fix_service_model(db_path):
        logger.info("服务记录模型修复成功")
        return 0
    else:
        logger.error("服务记录模型修复失败")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 