"""
从Excel文件导入服务记录到数据库

使用方法：
python import_services_from_excel.py <excel文件路径>
"""
import os
import sys
import sqlite3
import pandas as pd
import logging
from datetime import datetime

# 设置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 添加服务器目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
server_dir = os.path.join(current_dir, 'server')
if server_dir not in sys.path:
    sys.path.append(server_dir)

# 导入Excel处理器
from server.utils.excel_processor import ExcelProcessor, import_services_to_db

# 主数据库路径
MAIN_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'beauty_crm.db')

def import_services_from_excel(excel_file_path):
    """从Excel文件导入服务记录到数据库"""
    
    # 检查Excel文件是否存在
    if not os.path.exists(excel_file_path):
        logging.error(f"Excel文件不存在: {excel_file_path}")
        return False
    
    try:
        # 连接数据库
        logging.info(f"连接数据库: {MAIN_DB_PATH}")
        conn = sqlite3.connect(MAIN_DB_PATH)
        conn.row_factory = sqlite3.Row
        
        # 创建Excel处理器
        processor = ExcelProcessor()
        
        # 读取Excel文件
        logging.info(f"读取Excel文件: {excel_file_path}")
        excel_data = pd.read_excel(excel_file_path, sheet_name=None)
        
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
        
        # 处理服务记录
        logging.info("开始处理服务记录...")
        services = processor._process_services(service_sheet)
        logging.info(f"处理完成，共 {len(services)} 条服务记录")
        
        # 导入服务记录到数据库
        logging.info("开始导入服务记录到数据库...")
        imported_services, imported_items = import_services_to_db(services, conn)
        logging.info(f"导入完成，共 {imported_services} 条服务记录和 {imported_items} 个服务项目")
        
        # 验证导入数据
        cursor = conn.cursor()
        
        # 检查服务记录数
        cursor.execute("SELECT COUNT(*) FROM services")
        total_services = cursor.fetchone()[0]
        logging.info(f"数据库中现有服务记录总数: {total_services}")
        
        # 检查服务项目数
        cursor.execute("SELECT COUNT(*) FROM service_items")
        total_items = cursor.fetchone()[0]
        logging.info(f"数据库中现有服务项目总数: {total_items}")
        
        # 列出导入的客户及其服务记录数
        cursor.execute("""
        SELECT customer_id, COUNT(*) as service_count 
        FROM services 
        GROUP BY customer_id 
        ORDER BY service_count DESC
        LIMIT 5
        """)
        customer_stats = cursor.fetchall()
        for row in customer_stats:
            logging.info(f"客户 {row['customer_id']} 的服务记录数: {row['service_count']}")
        
        # 列出最受欢迎的服务项目
        cursor.execute("""
        SELECT project_name, COUNT(*) as item_count, SUM(unit_price) as total_amount
        FROM service_items
        GROUP BY project_name
        ORDER BY item_count DESC
        LIMIT 5
        """)
        popular_items = cursor.fetchall()
        logging.info("最受欢迎的服务项目:")
        for row in popular_items:
            logging.info(f"  - {row['project_name']}: 数量 {row['item_count']}, 总金额 {row['total_amount']:.2f}元")
        
        # 关闭数据库连接
        conn.close()
        
        return True
    
    except Exception as e:
        logging.exception(f"导入服务记录时出错: {str(e)}")
        return False

if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 2:
        print("用法: python import_services_from_excel.py <excel文件路径>")
        excel_path = "模拟-客户信息档案.xlsx"  # 默认值
        print(f"使用默认文件: {excel_path}")
    else:
        excel_path = sys.argv[1]
    
    # 执行导入
    success = import_services_from_excel(excel_path)
    
    if success:
        print("服务记录导入成功!")
    else:
        print("服务记录导入失败!")
        sys.exit(1)