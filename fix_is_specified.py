"""
修复数据库中is_specified字段的值，从Excel中读取正确的值
"""
import os
import sys
import pandas as pd
from datetime import datetime
import sqlite3
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('IsSpecifiedFixer')

# 数据库路径
DB_PATH = "instance/beauty_crm.db"
EXCEL_PATH = "模拟-客户信息档案.xlsx"

def fix_is_specified():
    """
    从Excel中读取正确的"是否指定"值，并更新数据库
    """
    logger.info(f"开始从Excel中修复is_specified字段")
    
    # 检查数据库和Excel文件是否存在
    if not os.path.exists(DB_PATH):
        logger.error(f"数据库文件不存在: {DB_PATH}")
        return False
    
    if not os.path.exists(EXCEL_PATH):
        logger.error(f"Excel文件不存在: {EXCEL_PATH}")
        return False
    
    try:
        # 读取Excel文件
        df = pd.read_excel(EXCEL_PATH, sheet_name="消耗")
        logger.info(f"成功读取Excel文件: {EXCEL_PATH}, 表: 消耗")
        
        # 检查第一行是否为标题行
        first_row = df.iloc[0].tolist()
        if '客户ID' in str(first_row) or '进店时间' in str(first_row):
            logger.info("检测到第一行是标题行，将其作为列名")
            # 重命名列
            new_columns = []
            for col in df.columns:
                if pd.isna(col) or col == '':
                    new_columns.append("Unnamed")
                else:
                    new_columns.append(str(col))
            df.columns = new_columns
            # 删除第一行
            df = df.iloc[1:].reset_index(drop=True)
        
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 获取所有服务记录
        cursor.execute("SELECT service_id, customer_id, service_date FROM services")
        services = cursor.fetchall()
        
        updated_count = 0
        for service_id, customer_id, service_date in services:
            # 在Excel中查找匹配的记录
            service_date_dt = datetime.strptime(service_date, "%Y-%m-%d %H:%M:%S") if isinstance(service_date, str) else service_date
            excel_date_format = "%Y/%m/%d %H:%M:%S"
            
            # 尝试查找匹配的记录
            matched_rows = None
            
            # 使用客户ID和日期查找
            if '客户ID' in df.columns and '进店时间' in df.columns:
                try:
                    matched_rows = df[(df['客户ID'] == customer_id) & 
                                   (pd.to_datetime(df['进店时间']).dt.date == service_date_dt.date())]
                except:
                    pass
            
            # 如果没找到，尝试使用其他列名
            if matched_rows is None or len(matched_rows) == 0:
                for date_col in df.columns:
                    if '时间' in str(date_col) and '进' in str(date_col) or '到' in str(date_col):
                        try:
                            matched_rows = df[(df['客户ID'] == customer_id) & 
                                          (pd.to_datetime(df[date_col]).dt.date == service_date_dt.date())]
                            if len(matched_rows) > 0:
                                break
                        except:
                            pass
            
            if matched_rows is not None and len(matched_rows) > 0:
                # 找到匹配的行，查找"是否指定"列
                row = matched_rows.iloc[0]
                
                # 获取总消耗项目数
                total_sessions = int(row['总消耗项目数']) if '总消耗项目数' in row and not pd.isna(row['总消耗项目数']) else 0
                
                # 更新total_sessions字段
                cursor.execute("UPDATE services SET total_sessions = ? WHERE service_id = ?", 
                             (total_sessions, service_id))
                
                # 获取服务项目
                cursor.execute("SELECT id, project_name FROM service_items WHERE service_id = ?", (service_id,))
                items = cursor.fetchall()
                
                # 尝试匹配项目并更新is_specified
                for i, (item_id, project_name) in enumerate(items):
                    # 尝试不同格式的列名
                    specified_value = None
                    
                    # 首先尝试按项目匹配
                    for j in range(1, 6):  # 最多检查5个项目
                        project_col = f'项目{j}'
                        specified_col = f'是否指定{j}'
                        
                        if project_col in row and specified_col in row:
                            excel_project = row[project_col]
                            if not pd.isna(excel_project) and excel_project == project_name:
                                specified_value = row[specified_col]
                                break
                    
                    # 如果没有找到按项目匹配，则按顺序匹配
                    if specified_value is None and i < total_sessions:
                        specified_col = f'是否指定{i+1}'
                        if specified_col in row:
                            specified_value = row[specified_col]
                    
                    # 如果找到了指定值，更新数据库
                    if specified_value is not None:
                        is_specified = True if specified_value == '✓' or specified_value == '√' or specified_value == 'True' else False
                        cursor.execute("UPDATE service_items SET is_specified = ? WHERE id = ?", 
                                     (is_specified, item_id))
                        logger.info(f"更新项目 {item_id} (服务ID: {service_id}) 的is_specified为 {is_specified}")
                
                updated_count += 1
        
        # 提交更改
        conn.commit()
        logger.info(f"成功更新了 {updated_count} 条服务记录的is_specified值")
        
        # 关闭连接
        conn.close()
        return True
    
    except Exception as e:
        logger.error(f"修复is_specified时出错: {str(e)}")
        return False

if __name__ == "__main__":
    fix_is_specified()