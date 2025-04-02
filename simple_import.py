"""
简化版的Excel导入脚本 - 修复'total_project_count'错误
"""
import os
import sys
import pandas as pd
from datetime import datetime
import sqlite3
import uuid

def fix_import():
    """
    修复Excel导入功能，解决'total_project_count'错误
    """
    print("开始导入Excel数据...")
    
    # 数据库路径
    db_path = "instance/beauty_crm.db"
    excel_path = "模拟-客户信息档案.xlsx"
    
    # 确保目录存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    if not os.path.exists(excel_path):
        print(f"Excel文件不存在: {excel_path}")
        return
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 读取Excel数据
    try:
        # 读取客户表 - 使用header=1参数，因为第一行是空行，第二行才是标题
        customers_df = pd.read_excel(excel_path, sheet_name="客户", header=1)
        print(f"客户表列名: {list(customers_df.columns)}")
        
        # 确认客户表中的ID列
        if '客户ID' in customers_df.columns:
            customer_id_column = '客户ID'
        else:
            # 尝试查找包含"ID"的列
            for col in customers_df.columns:
                if 'ID' in str(col) or 'id' in str(col).lower():
                    customer_id_column = col
                    print(f"使用列名 '{col}' 作为客户ID")
                    break
            else:
                print("错误: 客户表中无法找到客户ID列")
                return False
        
        # 读取消费表
        consumption_df = pd.read_excel(excel_path, sheet_name="消费")
        print(f"消费表数据行数: {len(consumption_df)}")
        
        # 读取消耗表
        depletion_df = pd.read_excel(excel_path, sheet_name="消耗")
        print(f"消耗表数据行数: {len(depletion_df)}")
        
        # 清空旧数据（如果需要）
        cursor.execute("DELETE FROM service")
        cursor.execute("DELETE FROM service_item")
        
        # 存储处理过的客户ID
        customer_ids = set()
        for _, row in customers_df.iterrows():
            customer_id = row[customer_id_column]
            if pd.isna(customer_id):
                continue
            customer_ids.add(str(customer_id))
                
        # 处理消费数据（服务主表）
        imported_services = 0
        imported_items = 0
        
        for index, row in consumption_df.iterrows():
            try:
                # 获取客户ID
                customer_id = row[customer_id_column]
                if pd.isna(customer_id):
                    continue  # 跳过没有客户ID的行
                
                customer_id = str(customer_id)
                
                # 生成唯一的服务ID
                service_id = str(uuid.uuid4())[:8]
                
                # 尝试获取日期，如果不存在则使用当前日期
                service_date = row.get('服务日期', datetime.now())
                if pd.isna(service_date):
                    service_date = datetime.now()
                    
                # 尝试获取满意度，如果不存在则设为0
                satisfaction = row.get('满意度', 0)
                if pd.isna(satisfaction):
                    satisfaction = 0
                
                # 获取消费金额
                amount = row.get('消费金额', 0)
                if pd.isna(amount):
                    amount = 0
                
                # 插入服务记录
                cursor.execute(
                    "INSERT INTO service (SERVICE_ID, CUSTOMER_ID, SERVICE_DATE, SATISFACTION, AMOUNT) VALUES (?, ?, ?, ?, ?)",
                    (service_id, customer_id, service_date, satisfaction, amount)
                )
                imported_services += 1
                
                # 处理相关的消耗明细
                services_for_customer = depletion_df[depletion_df['客户ID'] == customer_id]
                
                if not services_for_customer.empty:
                    for _, item_row in services_for_customer.iterrows():
                        # 生成唯一的服务项目ID
                        item_id = str(uuid.uuid4())[:8]
                        
                        # 获取项目名称
                        item_name = item_row.get('服务项目', '未知项目')
                        if pd.isna(item_name):
                            item_name = '未知项目'
                            
                        # 获取项目状态
                        status = item_row.get('项目状态', '完成')
                        if pd.isna(status):
                            status = '完成'
                            
                        # 获取项目满意度
                        item_satisfaction = item_row.get('项目满意度', 0)
                        if pd.isna(item_satisfaction):
                            item_satisfaction = 0
                            
                        # 插入服务项目记录
                        cursor.execute(
                            "INSERT INTO service_item (ITEM_ID, SERVICE_ID, ITEM_NAME, STATUS, SATISFACTION) VALUES (?, ?, ?, ?, ?)",
                            (item_id, service_id, item_name, status, item_satisfaction)
                        )
                        imported_items += 1
            
            except Exception as e:
                print(f"导入失败: {str(e)}")
                conn.rollback()
                return False
        
        # 提交事务
        conn.commit()
        print(f"导入成功! 导入了 {imported_services} 条服务记录和 {imported_items} 条服务项目明细")
        return True
        
    except Exception as e:
        print(f"导入失败: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    fix_import()