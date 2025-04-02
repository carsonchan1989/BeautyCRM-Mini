"""
数据库迁移脚本 - 将服务记录从旧结构迁移到新结构
"""
import os
import sys
import logging
import sqlite3
from datetime import datetime
import traceback

# 设置日志级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('MigrateServiceData')

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'beauty_crm.db')

try:
    # 确保数据库文件存在
    if not os.path.exists(DB_PATH):
        logger.error(f"数据库文件不存在: {DB_PATH}")
        sys.exit(1)
    
    logger.info(f"连接数据库: {DB_PATH}")
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. 创建临时表保存旧数据
    logger.info("创建临时表保存旧数据")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS temp_services (
        id INTEGER PRIMARY KEY,
        customer_id VARCHAR(32) NOT NULL,
        service_date DATETIME NOT NULL,
        departure_time DATETIME,
        total_amount FLOAT,
        satisfaction VARCHAR(32),
        service_items VARCHAR(256),
        beautician VARCHAR(64),
        service_amount FLOAT,
        is_specified BOOLEAN,
        created_at DATETIME,
        updated_at DATETIME
    )
    """)
    
    # 2. 复制旧数据到临时表
    logger.info("复制旧数据到临时表")
    cursor.execute("""
    INSERT INTO temp_services
    SELECT * FROM services
    """)
    
    # 3. 获取旧服务记录的总数
    cursor.execute("SELECT COUNT(*) FROM temp_services")
    total_records = cursor.fetchone()[0]
    logger.info(f"旧服务记录总数: {total_records}")
    
    # 4. 删除旧表
    logger.info("删除旧的服务记录表")
    cursor.execute("DROP TABLE IF EXISTS services")
    
    # 5. 创建新的services表和service_items表
    logger.info("创建新的服务记录表结构")
    cursor.execute("""
    CREATE TABLE services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id VARCHAR(32) NOT NULL,
        service_date DATETIME NOT NULL,
        departure_time DATETIME,
        total_amount FLOAT,
        satisfaction VARCHAR(32),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE service_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        service_items VARCHAR(128) NOT NULL,
        beautician VARCHAR(64),
        service_amount FLOAT,
        is_specified BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE
    )
    """)
    
    # 6. 获取所有临时表数据
    logger.info("读取临时表数据")
    cursor.execute("SELECT * FROM temp_services")
    old_records = cursor.fetchall()
    
    # 7. 按客户和日期分组服务记录
    logger.info("开始按客户和日期分组服务记录")
    grouped_records = {}
    for record in old_records:
        key = (record['customer_id'], str(record['service_date']))
        if key not in grouped_records:
            grouped_records[key] = {
                'base': {
                    'customer_id': record['customer_id'],
                    'service_date': record['service_date'],
                    'departure_time': record['departure_time'],
                    'total_amount': record['total_amount'],
                    'satisfaction': record['satisfaction'],
                    'created_at': record['created_at'],
                    'updated_at': record['updated_at']
                },
                'items': []
            }
        
        # 如果有项目信息，添加到items列表
        if record['service_items']:
            grouped_records[key]['items'].append({
                'service_items': record['service_items'],
                'beautician': record['beautician'],
                'service_amount': record['service_amount'],
                'is_specified': record['is_specified']
            })
    
    logger.info(f"分组后得到 {len(grouped_records)} 条主服务记录")
    
    # 8. 插入数据到新表
    logger.info("开始插入数据到新表")
    services_added = 0
    items_added = 0
    
    for key, data in grouped_records.items():
        try:
            base = data['base']
            
            # 插入服务主表
            cursor.execute("""
            INSERT INTO services 
            (customer_id, service_date, departure_time, total_amount, satisfaction, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                base['customer_id'], 
                base['service_date'],
                base['departure_time'],
                base['total_amount'],
                base['satisfaction'],
                base['created_at'] or datetime.now(),
                base['updated_at'] or datetime.now()
            ))
            
            # 获取新插入记录的ID
            service_id = cursor.lastrowid
            services_added += 1
            
            # 插入服务项目
            for item in data['items']:
                cursor.execute("""
                INSERT INTO service_items
                (service_id, service_items, beautician, service_amount, is_specified)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    service_id,
                    item['service_items'],
                    item['beautician'],
                    item['service_amount'],
                    1 if item['is_specified'] else 0
                ))
                items_added += 1
                
        except Exception as e:
            logger.error(f"插入记录时出错: {str(e)}")
            logger.error(f"记录数据: {data}")
            logger.error(traceback.format_exc())
    
    # 9. 提交事务
    conn.commit()
    
    # 10. 删除临时表
    logger.info("删除临时表")
    cursor.execute("DROP TABLE temp_services")
    
    # 11. 重置自增ID
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='services'")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='service_items'")
    conn.commit()
    
    # 关闭连接
    cursor.close()
    conn.close()
    
    logger.info(f"数据迁移完成: 添加了 {services_added} 条服务记录和 {items_added} 个服务项目")
    print(f"数据迁移成功完成！添加了 {services_added} 条服务记录和 {items_added} 个服务项目")

except Exception as e:
    logger.exception(f"数据迁移失败: {str(e)}")
    print(f"数据迁移失败: {str(e)}")
    sys.exit(1)