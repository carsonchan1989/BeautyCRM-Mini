"""
服务记录导入主脚本 - 用于从Excel导入服务记录到数据库
"""
import os
import sys
import logging
import pandas as pd
import sqlite3
from datetime import datetime

# 服务记录处理模块路径设置
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from server.utils.excel_processor import ExcelProcessor
from utils.db_model_update import update_service_models

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main(excel_path=None, db_path=None):
    """主函数，负责导入服务记录
    
    Args:
        excel_path: Excel文件路径，默认为"模拟-客户信息档案.xlsx"
        db_path: 数据库文件路径，默认为"instance/beauty_crm.db"
    
    Returns:
        bool: 是否成功导入
    """
    try:
        # 默认Excel文件路径
        if not excel_path:
            excel_path = "模拟-客户信息档案.xlsx"
        
        # 默认数据库路径
        if not db_path:
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                 "instance", "beauty_crm.db")
        
        logging.info(f"开始导入服务记录 从Excel: {excel_path} 到数据库: {db_path}")
        
        # 检查Excel文件是否存在
        if not os.path.exists(excel_path):
            logging.error(f"Excel文件不存在: {excel_path}")
            return False
        
        # 更新数据库表结构
        if not update_service_models(db_path):
            logging.error("更新数据库表结构失败，导入终止")
            return False
        
        # 创建Excel处理器
        processor = ExcelProcessor(db_path)
        
        # 读取Excel文件
        logging.info(f"读取Excel文件: {excel_path}")
        if excel_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(excel_path, sheet_name=0)  # 读取第一个工作表
        else:
            logging.error(f"不支持的文件格式: {excel_path}")
            return False
        
        logging.info(f"Excel文件读取成功，行数: {len(df)}, 列数: {len(df.columns)}")
        
        # 处理服务记录
        service_records, service_items = processor.process_services(df)
        
        if not service_records:
            logging.warning("没有找到有效的服务记录，导入终止")
            return False
        
        # 导入服务记录到数据库
        logging.info(f"开始导入服务记录到数据库...")
        import_count, item_count = processor.import_services_to_db(service_records, service_items)
        
        logging.info(f"导入完成，成功导入 {import_count} 条服务记录，{item_count} 个服务项目")
        
        # 连接数据库查询导入结果
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询各客户的服务次数
        cursor.execute("""
        SELECT customer_id, customer_name, COUNT(*) as service_count 
        FROM services 
        GROUP BY customer_id
        ORDER BY service_count DESC
        """)
        
        customer_stats = cursor.fetchall()
        
        if customer_stats:
            logging.info("各客户服务记录统计:")
            for stat in customer_stats:
                logging.info(f"客户: {stat['customer_name']}({stat['customer_id']}) - 服务次数: {stat['service_count']}")
        
        # 查询热门服务项目
        cursor.execute("""
        SELECT project_name, COUNT(*) as item_count, SUM(unit_price) as total_amount
        FROM service_items
        GROUP BY project_name
        ORDER BY item_count DESC
        LIMIT 5
        """)
        
        popular_items = cursor.fetchall()
        
        if popular_items:
            logging.info("热门服务项目统计:")
            for item in popular_items:
                logging.info(f"项目: {item['project_name']} - 次数: {item['item_count']} - 总金额: {item['total_amount']}")
        
        conn.close()
        
        return True
        
    except Exception as e:
        logging.exception(f"导入服务记录时出错: {str(e)}")
        return False

if __name__ == "__main__":
    # 命令行参数处理
    excel_path = None
    db_path = None
    
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    
    if len(sys.argv) > 2:
        db_path = sys.argv[2]
    
    # 执行导入
    success = main(excel_path, db_path)
    
    if success:
        print("服务记录导入成功!")
    else:
        print("服务记录导入失败!")
        sys.exit(1)