"""
测试Excel处理器的服务记录清洗功能
"""
import os
import sys
import sqlite3
import logging
import pandas as pd
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 添加当前目录和server目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
server_dir = os.path.join(current_dir, 'server')
if server_dir not in sys.path:
    sys.path.append(server_dir)

# 导入Excel处理器模块
from server.utils.excel_processor import ExcelProcessor, import_services_to_db

def test_excel_processor():
    """测试Excel处理器的服务记录清洗功能"""
    try:
        # 1. 创建Excel处理器实例
        excel_processor = ExcelProcessor()
        
        # 2. Excel文件路径 - 使用模拟客户信息档案
        excel_path = os.path.join(current_dir, "模拟-客户信息档案.xlsx")
        
        if not os.path.exists(excel_path):
            logging.error(f"Excel文件不存在: {excel_path}")
            return False
        
        # 3. 创建临时数据库
        test_db_path = os.path.join(current_dir, "test_excel_processor.db")
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        # 4. 连接数据库
        conn = sqlite3.connect(test_db_path)
        conn.row_factory = sqlite3.Row
        
        # 5. 读取Excel文件
        excel_data = pd.read_excel(excel_path, sheet_name=None)
        
        # 找到消耗表
        service_sheet = None
        for sheet_name in excel_data:
            if "消耗" in sheet_name:
                service_sheet = excel_data[sheet_name]
                logging.info(f"找到服务记录表: {sheet_name}")
                break
        
        if service_sheet is None:
            logging.error("未找到消耗表")
            return False
        
        # 6. 处理服务记录
        logging.info("开始处理服务记录...")
        services = excel_processor._process_services(service_sheet)
        logging.info(f"处理完成，共 {len(services)} 条服务记录")
        
        # 7. 导入到数据库
        logging.info("开始导入服务记录到数据库...")
        imported_services, imported_items = import_services_to_db(services, conn)
        logging.info(f"导入完成，共 {imported_services} 条服务记录和 {imported_items} 个服务项目")
        
        # 8. 验证导入数据
        cursor = conn.cursor()
        
        # 检查服务记录数
        cursor.execute("SELECT COUNT(*) FROM services")
        service_count = cursor.fetchone()[0]
        logging.info(f"数据库中服务记录数: {service_count}")
        
        # 检查服务项目数
        cursor.execute("SELECT COUNT(*) FROM service_items")
        item_count = cursor.fetchone()[0]
        logging.info(f"数据库中服务项目数: {item_count}")
        
        # 按客户ID分组检查记录数
        cursor.execute("SELECT customer_id, COUNT(*) as record_count FROM services GROUP BY customer_id")
        customer_counts = cursor.fetchall()
        for row in customer_counts:
            logging.info(f"客户 {row['customer_id']} 的服务记录数: {row['record_count']}")
        
        # 检查没有项目的服务记录
        cursor.execute("""
        SELECT s.service_id, s.customer_id 
        FROM services s 
        LEFT JOIN service_items i ON s.service_id = i.service_id 
        WHERE i.id IS NULL
        """)
        empty_services = cursor.fetchall()
        if empty_services:
            logging.warning(f"发现 {len(empty_services)} 条没有项目的服务记录")
            for row in empty_services:
                logging.warning(f"空记录: {row['service_id']} - 客户: {row['customer_id']}")
        
        # 9. 关闭数据库连接
        conn.close()
        
        return True
        
    except Exception as e:
        logging.exception(f"测试Excel处理器时出错: {str(e)}")
        return False

if __name__ == "__main__":
    test_excel_processor()