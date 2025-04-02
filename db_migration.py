"""
数据库迁移脚本 - 添加缺失字段并修复服务记录表结构
"""
import sqlite3
import os
import sys
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('DBMigration')

def migrate_database(db_path):
    """
    迁移数据库结构，添加缺失字段
    """
    logger.info(f"开始迁移数据库: {db_path}")
    
    if not os.path.exists(db_path):
        logger.error(f"数据库文件不存在: {db_path}")
        return False
    
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查services表结构
        cursor.execute("PRAGMA table_info(services)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        logger.info(f"当前services表字段: {column_names}")
        
        # 检查是否需要添加total_sessions字段
        if 'total_sessions' not in column_names:
            logger.info("添加total_sessions字段到services表")
            cursor.execute("ALTER TABLE services ADD COLUMN total_sessions INTEGER DEFAULT 0")
        
        # 检查ServiceItem表是否有is_specified字段
        cursor.execute("PRAGMA table_info(service_items)")
        item_columns = cursor.fetchall()
        item_column_names = [col[1] for col in item_columns]
        
        logger.info(f"当前service_items表字段: {item_column_names}")
        
        if 'is_specified' not in item_column_names:
            logger.info("添加is_specified字段到service_items表")
            cursor.execute("ALTER TABLE service_items ADD COLUMN is_specified BOOLEAN DEFAULT 0")
        
        # 提交更改
        conn.commit()
        logger.info("数据库迁移成功完成！")
        return True
        
    except Exception as e:
        logger.error(f"数据库迁移失败: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def update_service_data(db_path):
    """
    更新服务数据，将项目数量更新到total_sessions字段
    """
    logger.info(f"开始更新服务数据: {db_path}")
    
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取所有服务
        cursor.execute("SELECT service_id FROM services")
        services = cursor.fetchall()
        
        updated = 0
        for service in services:
            service_id = service[0]
            
            # 获取服务项目数量
            cursor.execute("SELECT COUNT(*) FROM service_items WHERE service_id = ?", (service_id,))
            item_count = cursor.fetchone()[0]
            
            # 更新服务的total_sessions
            cursor.execute("UPDATE services SET total_sessions = ? WHERE service_id = ?", 
                          (item_count, service_id))
            updated += 1
        
        # 提交更改
        conn.commit()
        logger.info(f"更新了 {updated} 条服务记录的总项目数")
        return True
        
    except Exception as e:
        logger.error(f"更新服务数据失败: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def remove_duplicate_services(db_path):
    """
    删除重复的服务记录
    """
    logger.info(f"开始清理重复的服务记录: {db_path}")
    
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 找出所有重复的服务记录（相同客户ID和日期的）
        cursor.execute("""
            SELECT customer_id, service_date, COUNT(*) as count
            FROM services
            GROUP BY customer_id, service_date
            HAVING count > 1
        """)
        
        duplicates = cursor.fetchall()
        logger.info(f"找到 {len(duplicates)} 组重复的服务记录")
        
        removed = 0
        for dup in duplicates:
            customer_id, service_date, count = dup
            
            # 获取重复的服务ID（保留第一个，删除其他）
            cursor.execute("""
                SELECT service_id FROM services 
                WHERE customer_id = ? AND service_date = ?
                ORDER BY created_at
            """, (customer_id, service_date))
            
            service_ids = [row[0] for row in cursor.fetchall()]
            keep_id = service_ids[0]
            delete_ids = service_ids[1:]
            
            logger.info(f"客户 {customer_id} 在 {service_date} 有 {count} 条重复记录，保留ID: {keep_id}")
            
            # 删除重复服务的项目
            for delete_id in delete_ids:
                cursor.execute("DELETE FROM service_items WHERE service_id = ?", (delete_id,))
                
                # 删除服务
                cursor.execute("DELETE FROM services WHERE service_id = ?", (delete_id,))
                removed += 1
        
        # 提交更改
        conn.commit()
        logger.info(f"成功删除 {removed} 条重复的服务记录")
        return True
        
    except Exception as e:
        logger.error(f"清理重复服务记录失败: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # 数据库路径
    db_path = "instance/database.db"
    
    # 执行迁移
    if migrate_database(db_path):
        # 更新服务数据
        update_service_data(db_path)
        # 清理重复数据
        remove_duplicate_services(db_path)
    else:
        logger.error("数据库迁移失败，后续步骤已跳过")