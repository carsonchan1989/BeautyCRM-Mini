"""
修复后的测试脚本，用于从'模拟-客户信息档案.xlsx'读取服务记录 - 版本2
这个版本直接处理原始Excel数据中的第2行作为标题，第3行起作为数据
"""
import pandas as pd
import sqlite3
import uuid
import os
from datetime import datetime
import traceback

def test_service_import():
    # Excel文件路径
    excel_path = "模拟-客户信息档案.xlsx"
    
    if not os.path.exists(excel_path):
        print(f"错误: 文件不存在 - {excel_path}")
        return False
    
    # 创建测试数据库
    test_db_path = "test_service_import.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    
    # 创建服务和服务项目表
    cursor.execute('''
    CREATE TABLE services (
        service_id TEXT PRIMARY KEY,
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
    ''')
    
    cursor.execute('''
    CREATE TABLE service_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id TEXT NOT NULL,
        project_name TEXT,
        beautician_name TEXT,
        unit_price REAL,
        is_specified INTEGER,
        created_at TEXT,
        updated_at TEXT
    )
    ''')
    
    # 读取Excel数据
    try:
        print(f"开始读取Excel文件: {excel_path}")
        
        # 读取消耗表 - 不使用pandas默认列名，直接读取原始数据
        raw_df = pd.read_excel(excel_path, sheet_name="消耗", header=None)
        
        print(f"原始消耗表形状: {raw_df.shape}")
        
        # 根据观察到的数据结构，直接使用第1行作为标题行，从第2行开始作为数据
        header_row = raw_df.iloc[1]
        data_start_row = 2
        
        print(f"使用第{data_start_row}行开始作为数据，第{data_start_row-1}行作为标题")
        
        # 将关键列索引映射到易于理解的变量名
        customer_id_col = 0      # 客户ID
        customer_name_col = 1    # 姓名
        arrival_time_col = 2     # 到店时间
        departure_time_col = 3   # 离店时间
        total_projects_col = 4   # 总消耗项目数
        total_amount_col = 5     # 总耗卡金额
        satisfaction_col = 6     # 服务满意度
        
        # 服务项目组，每组4列(项目内容、操作美容师、耗卡金额、是否指定)
        project_groups = [
            {"name": 7, "beautician": 8, "amount": 9, "specified": 10},
            {"name": 11, "beautician": 12, "amount": 13, "specified": 14},
            {"name": 15, "beautician": 16, "amount": 17, "specified": 18},
            {"name": 19, "beautician": 20, "amount": 21, "specified": 22},
            {"name": 23, "beautician": 24, "amount": 25, "specified": 26}
        ]
        
        # 导入服务记录
        imported_services = 0
        imported_items = 0
        
        # 处理每一行数据
        for row_idx in range(data_start_row, raw_df.shape[0]):
            try:
                row = raw_df.iloc[row_idx]
                
                # 获取客户ID
                customer_id = row[customer_id_col]
                if pd.isna(customer_id):
                    continue  # 跳过没有客户ID的行
                
                customer_id = str(customer_id).strip()
                customer_name = str(row[customer_name_col]).strip() if not pd.isna(row[customer_name_col]) else f"客户{customer_id}"
                
                print(f"处理客户: {customer_id} - {customer_name}")
                
                # 解析到店时间
                arrival_time = row[arrival_time_col]
                if pd.isna(arrival_time):
                    continue  # 无到店时间，跳过
                
                # 解析日期时间
                try:
                    if isinstance(arrival_time, str):
                        if '/' in arrival_time:
                            arrival_dt = datetime.strptime(arrival_time, "%Y/%m/%d %H:%M")
                        else:
                            arrival_dt = datetime.strptime(arrival_time, "%Y-%m-%d %H:%M")
                    else:
                        arrival_dt = pd.to_datetime(arrival_time).to_pydatetime()
                    
                    service_date = arrival_dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    print(f"解析到店时间出错 [{arrival_time}]: {str(e)}")
                    continue
                
                # 解析离店时间
                departure_time = row[departure_time_col]
                departure_time_str = None
                if not pd.isna(departure_time):
                    try:
                        if isinstance(departure_time, str):
                            if '/' in departure_time:
                                departure_dt = datetime.strptime(departure_time, "%Y/%m/%d %H:%M")
                            else:
                                departure_dt = datetime.strptime(departure_time, "%Y-%m-%d %H:%M")
                        else:
                            departure_dt = pd.to_datetime(departure_time).to_pydatetime()
                        
                        departure_time_str = departure_dt.strftime('%Y-%m-%d %H:%M:%S')
                    except Exception as e:
                        print(f"解析离店时间出错 [{departure_time}]: {str(e)}")
                
                # 获取总项目数
                total_sessions = 0
                total_projects = row[total_projects_col]
                if not pd.isna(total_projects):
                    try:
                        if isinstance(total_projects, str):
                            # 处理可能的"次"字符
                            total_projects_str = total_projects.replace("次", "").strip()
                            total_sessions = int(float(total_projects_str))
                        else:
                            total_sessions = int(total_projects)
                    except Exception as e:
                        print(f"解析总项目数出错 [{total_projects}]: {str(e)}")
                
                # 获取总金额
                total_amount = 0.0
                amount_val = row[total_amount_col]
                if not pd.isna(amount_val):
                    try:
                        total_amount = float(amount_val)
                    except Exception as e:
                        print(f"解析总金额出错 [{amount_val}]: {str(e)}")
                
                # 获取满意度
                satisfaction = None
                satisfaction_val = row[satisfaction_col]
                if not pd.isna(satisfaction_val):
                    satisfaction = str(satisfaction_val)
                
                # 创建服务记录
                service_id = f"S{uuid.uuid4().hex[:8].upper()}"
                
                cursor.execute('''
                INSERT INTO services 
                (service_id, customer_id, customer_name, service_date, departure_time, 
                total_amount, total_sessions, satisfaction, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    service_id,
                    customer_id,
                    customer_name,
                    service_date,
                    departure_time_str,
                    total_amount,
                    total_sessions,
                    satisfaction,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
                
                imported_services += 1
                print(f"创建服务记录: {service_id}")
                
                # 处理项目组
                for group in project_groups:
                    project_name_val = row[group["name"]]
                    
                    # 跳过空项目
                    if pd.isna(project_name_val) or not str(project_name_val).strip():
                        continue
                    
                    project_name = str(project_name_val).strip()
                    
                    # 获取美容师
                    beautician_name = ""
                    beautician_val = row[group["beautician"]]
                    if not pd.isna(beautician_val):
                        beautician_name = str(beautician_val).strip()
                    
                    # 获取金额
                    unit_price = 0.0
                    price_val = row[group["amount"]]
                    if not pd.isna(price_val):
                        try:
                            unit_price = float(price_val)
                        except:
                            print(f"解析项目金额出错 [{price_val}]")
                    
                    # 获取是否指定
                    is_specified = 0
                    specified_val = row[group["specified"]]
                    if not pd.isna(specified_val):
                        if isinstance(specified_val, str):
                            is_specified = 1 if specified_val.strip() in ['✓', '√', '是', 'Yes', 'yes', 'TRUE', 'true', 'True', '1', 'Y', 'y'] else 0
                        else:
                            is_specified = 1 if specified_val else 0
                    
                    # 插入服务项目
                    cursor.execute('''
                    INSERT INTO service_items
                    (service_id, project_name, beautician_name, unit_price, is_specified, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        service_id,
                        project_name,
                        beautician_name,
                        unit_price,
                        is_specified,
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ))
                    
                    imported_items += 1
                    print(f"创建服务项目: {project_name} - {beautician_name} - {unit_price}元 - {'✓指定' if is_specified == 1 else '未指定'}")
            
            except Exception as e:
                print(f"处理行 {row_idx} 时出错: {str(e)}")
                print(traceback.format_exc())
        
        # 提交事务
        conn.commit()
        
        # 显示导入结果
        print(f"\n导入结果汇总:")
        print(f"成功导入服务记录: {imported_services}条")
        print(f"成功导入服务项目: {imported_items}条\n")
        
        # 显示导入的数据
        cursor.execute("SELECT * FROM services")
        services = cursor.fetchall()
        
        for service in services:
            print(f"服务ID: {service[0]}, 客户ID: {service[1]}, 总次数: {service[6]}, 满意度: {service[7]}")
            
            cursor.execute("SELECT * FROM service_items WHERE service_id = ?", (service[0],))
            service_items = cursor.fetchall()
            for item in service_items:
                print(f"  - 项目: {item[2]}, 美容师: {item[3]}, 金额: {item[4]}, 是否指定: {'是' if item[5] == 1 else '否'}")
        
        return True
    
    except Exception as e:
        print(f"导入过程中出错: {str(e)}")
        print(traceback.format_exc())
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    test_service_import()