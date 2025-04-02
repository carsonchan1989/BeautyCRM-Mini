"""
数据库模型更新脚本 - 用于更新数据库表结构以适配最新的服务记录清洗逻辑
"""
import os
import sys
import sqlite3
import logging
from datetime import datetime
import uuid

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def update_service_models(db_path):
    """更新服务记录相关的数据库表结构
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        bool: 是否成功更新
    """
    try:
        # 确保数据库文件目录存在
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logging.info(f"创建数据库目录: {db_dir}")
        
        logging.info(f"连接数据库: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查是否已存在服务记录表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='services'")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            # 如果表已存在，检查结构
            logging.info("服务记录表已存在，检查结构...")
            
            # 检查是否需要更新表结构
            cursor.execute("PRAGMA table_info(services)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            update_needed = False
            
            # 检查是否缺少必要的列
            required_columns = ['service_id', 'customer_id', 'customer_name', 'service_date', 
                              'departure_time', 'total_amount', 'total_sessions', 'satisfaction']
            
            missing_columns = [col for col in required_columns if col not in column_names]
            
            if missing_columns:
                update_needed = True
                logging.info(f"需要添加的列: {missing_columns}")
            
            # 检查service_items表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='service_items'")
            items_table_exists = cursor.fetchone() is not None
            
            if not items_table_exists:
                update_needed = True
                logging.info("缺少service_items表")
            
            if update_needed:
                # 如果需要更新，备份原表
                logging.info("开始备份原表...")
                
                # 创建临时表保存旧数据
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS temp_services AS
                SELECT * FROM services
                """)
                
                # 获取原表中的记录数
                cursor.execute("SELECT COUNT(*) FROM temp_services")
                backup_count = cursor.fetchone()[0]
                logging.info(f"备份了 {backup_count} 条服务记录")
                
                # 删除原表
                cursor.execute("DROP TABLE services")
                
                # 检查service_items表是否存在，如果存在也备份
                if items_table_exists:
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS temp_service_items AS
                    SELECT * FROM service_items
                    """)
                    
                    cursor.execute("SELECT COUNT(*) FROM temp_service_items")
                    backup_items_count = cursor.fetchone()[0]
                    logging.info(f"备份了 {backup_items_count} 条服务项目")
                    
                    cursor.execute("DROP TABLE service_items")
            else:
                logging.info("服务记录表结构正确，无需更新")
                conn.close()
                return True
        
        # 创建服务记录表
        logging.info("创建服务记录表...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_id TEXT UNIQUE NOT NULL,
            customer_id TEXT NOT NULL,
            customer_name TEXT,
            service_date TEXT,
            departure_time TEXT,
            total_amount REAL,
            total_sessions INTEGER,
            satisfaction TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """)
        
        # 创建服务项目表
        logging.info("创建服务项目表...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS service_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_id TEXT NOT NULL,
            project_name TEXT,
            beautician_name TEXT,
            unit_price REAL,
            is_specified INTEGER,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE
        )
        """)
        
        # 创建索引
        logging.info("创建索引...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_services_customer_id ON services(customer_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_service_items_service_id ON service_items(service_id)")
        
        if table_exists:
            # 迁移旧数据
            logging.info("开始迁移旧数据...")
            
            # 先检查temp_services表的结构
            cursor.execute("PRAGMA table_info(temp_services)")
            old_columns = cursor.fetchall()
            old_column_names = [col[1] for col in old_columns]
            
            # 获取旧数据
            cursor.execute("SELECT * FROM temp_services")
            old_services = cursor.fetchall()
            
            # 准备迁移
            migrated_count = 0
            
            # 获取service_id索引(如果存在)
            service_id_idx = -1
            if "service_id" in old_column_names:
                service_id_idx = old_column_names.index("service_id")
            
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            for service in old_services:
                try:
                    # 如果旧表有service_id列，使用原来的service_id
                    if service_id_idx >= 0 and service[service_id_idx]:
                        service_id = service[service_id_idx]
                    else:
                        service_id = f"S{uuid.uuid4().hex[:8].upper()}"
                    
                    # 获取旧数据中的列值
                    customer_id = service[old_column_names.index("customer_id")] if "customer_id" in old_column_names else ""
                    service_date = service[old_column_names.index("service_date")] if "service_date" in old_column_names else None
                    
                    # 这些列可能不存在于旧表中
                    customer_name = service[old_column_names.index("customer_name")] if "customer_name" in old_column_names else f"客户{customer_id}"
                    departure_time = service[old_column_names.index("departure_time")] if "departure_time" in old_column_names else None
                    total_amount = service[old_column_names.index("total_amount")] if "total_amount" in old_column_names else 0
                    total_sessions = service[old_column_names.index("total_sessions")] if "total_sessions" in old_column_names else 0
                    satisfaction = service[old_column_names.index("satisfaction")] if "satisfaction" in old_column_names else None
                    
                    # 创建时间和更新时间
                    created_at = service[old_column_names.index("created_at")] if "created_at" in old_column_names else now
                    updated_at = service[old_column_names.index("updated_at")] if "updated_at" in old_column_names else now
                    
                    # 插入新表
                    cursor.execute("""
                    INSERT INTO services
                    (service_id, customer_id, customer_name, service_date, departure_time, 
                    total_amount, total_sessions, satisfaction, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        service_id,
                        customer_id,
                        customer_name,
                        service_date,
                        departure_time,
                        total_amount,
                        total_sessions,
                        satisfaction,
                        created_at,
                        updated_at
                    ))
                    
                    migrated_count += 1
                    
                    # 检查是否有服务项目表的旧数据
                    if items_table_exists:
                        cursor.execute("SELECT * FROM temp_service_items WHERE service_id = ?", (service_id,))
                        old_items = cursor.fetchall()
                        
                        for item in old_items:
                            # 获取旧项目数据
                            project_name = item["project_name"] if "project_name" in item.keys() else item["service_items"]
                            beautician_name = item["beautician_name"] if "beautician_name" in item.keys() else item["beautician"]
                            unit_price = item["unit_price"] if "unit_price" in item.keys() else item["service_amount"]
                            is_specified = item["is_specified"] if "is_specified" in item.keys() else 0
                            item_created_at = item["created_at"] if "created_at" in item.keys() else now
                            item_updated_at = item["updated_at"] if "updated_at" in item.keys() else now
                            
                            # 插入项目
                            cursor.execute("""
                            INSERT INTO service_items
                            (service_id, project_name, beautician_name, unit_price, is_specified, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                service_id,
                                project_name,
                                beautician_name,
                                unit_price,
                                is_specified,
                                item_created_at,
                                item_updated_at
                            ))
                    
                    # 如果旧表有服务项目数据但没有单独的service_items表
                    elif "service_items" in old_column_names and "beautician" in old_column_names:
                        project_name = service[old_column_names.index("service_items")]
                        beautician_name = service[old_column_names.index("beautician")]
                        unit_price = service[old_column_names.index("service_amount")] if "service_amount" in old_column_names else 0
                        is_specified = service[old_column_names.index("is_specified")] if "is_specified" in old_column_names else 0
                        
                        if project_name and project_name.strip():
                            cursor.execute("""
                            INSERT INTO service_items
                            (service_id, project_name, beautician_name, unit_price, is_specified, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                service_id,
                                project_name,
                                beautician_name,
                                unit_price,
                                1 if is_specified else 0,
                                now,
                                now
                            ))
                
                except Exception as e:
                    logging.warning(f"迁移服务记录 {service_id} 时出错: {str(e)}")
            
            logging.info(f"成功迁移 {migrated_count} 条服务记录")
            
            # 删除临时表
            cursor.execute("DROP TABLE temp_services")
            if items_table_exists:
                cursor.execute("DROP TABLE temp_service_items")
        
        # 提交事务
        conn.commit()
        conn.close()
        
        logging.info("数据库表结构更新成功")
        return True
        
    except Exception as e:
        logging.exception(f"更新数据库表结构时出错: {str(e)}")
        return False

if __name__ == "__main__":
    # 默认数据库路径
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           "instance", "beauty_crm.db")
    
    # 如果提供了命令行参数，使用指定的数据库路径
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    # 执行更新
    success = update_service_models(db_path)
    
    if success:
        print("数据库表结构更新成功!")
    else:
        print("数据库表结构更新失败!")
        sys.exit(1)