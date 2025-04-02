"""
检查数据库状态和表结构
"""
import os
import sqlite3
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database():
    """检查数据库文件和表结构"""
    # 获取数据库路径
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'beauty_crm.db')
    
    # 检查文件是否存在
    if not os.path.exists(db_path):
        logger.error(f"数据库文件不存在: {db_path}")
        return False
    
    logger.info(f"数据库文件存在: {db_path}")
    logger.info(f"文件大小: {os.path.getsize(db_path)} bytes")
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 列出所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            logger.error("数据库中没有表")
            return False
        
        logger.info(f"数据库中的表: {[table[0] for table in tables]}")
        
        # 对每个表检查结构
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            logger.info(f"表 {table_name} 的列: {[column[1] for column in columns]}")
        
        # 关闭连接
        conn.close()
        return True
    
    except Exception as e:
        logger.error(f"检查数据库时出错: {str(e)}")
        return False

if __name__ == "__main__":
    check_database()