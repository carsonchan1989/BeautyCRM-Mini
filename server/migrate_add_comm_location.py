"""
为沟通记录表添加沟通地点字段的迁移脚本
"""
import sys
import os
import sqlite3
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_column_to_communications():
    """向communications表添加communication_location列"""
    try:
        # 获取数据库路径
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'beauty_crm.db')
        logger.info(f"连接数据库: {db_path}")
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查列是否已存在
        cursor.execute("PRAGMA table_info(communications)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'communication_location' not in column_names:
            logger.info("添加communication_location列")
            cursor.execute("ALTER TABLE communications ADD COLUMN communication_location TEXT")
            logger.info("列添加成功")
        else:
            logger.info("communication_location列已存在")
        
        # 提交更改并关闭连接
        conn.commit()
        conn.close()
        logger.info("数据库迁移完成")
        return True
    
    except Exception as e:
        logger.error(f"迁移失败: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("开始执行数据库迁移")
    success = add_column_to_communications()
    if success:
        logger.info("迁移成功完成")
    else:
        logger.error("迁移失败")
        sys.exit(1)