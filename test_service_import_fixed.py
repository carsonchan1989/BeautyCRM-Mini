"""
修复后的测试脚本，用于从'模拟-客户信息档案.xlsx'读取服务记录
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
        
        # 读取消耗表 - 不使用pandas默认列名
        raw_df = pd.read_excel(excel_path, sheet_name="消耗", header=None)
        
        # 输出原始表结构，调试用
        print(f"原始消耗表形状: {raw_df.shape}")
        first_row = raw_df.iloc[0].tolist()
        print(f"第一行数据样本: {first_row[:10]}...")
        print(f"包含'客户ID'?: {any(['客户ID' in str(val) if not pd.isna(val) else False for val in first_row])}")
        
        # 处理标题行
        if any(["客户ID" in str(val) if not pd.isna(val) else False for val in raw_df.iloc[0]]):
            print("检测到第一行为标题行，开始处理")
            
            # 构建更清晰的表结构
            structured_data = []
            
            # 遍历每一行
            for idx in range(1, len(raw_df)):  # 跳过标题行
                row = raw_df.iloc[idx]
                
                # 基本信息
                customer_id = row[0] if not pd.isna(row[0]) else None
                if not customer_id:
                    continue
                    
                customer_name = row[1] if not pd.isna(row[1]) else None
                arrival_time = row[2] if not pd.isna(row[2]) else None
                departure_time = row[3] if not pd.isna(row[3]) else None
                total_sessions = row[4] if not pd.isna(row[4]) else None
                total_amount = row[5] if not pd.isna(row[5]) else None
                satisfaction = row[6] if not pd.isna(row[6]) else None
                
                # 项目组 - 这里假设每4列为一组(项目名称、美容师、金额、是否指定)
                projects = []
                for i in range(7, min(raw_df.shape[1], 27), 4):
                    project_name = row[i] if i < len(row) and not pd.isna(row[i]) else None
                    beautician = row[i+1] if i+1 < len(row) and not pd.isna(row[i+1]) else None
                    amount = row[i+2] if i+2 < len(row) and not pd.isna(row[i+2]) else None
                    is_specified = row[i+3] if i+3 < len(row) and not pd.isna(row[i+3]) else None
                    
                    if project_name and str(project_name).strip():
                        projects.append({
                            'project_name': str(project_name).strip(),
                            'beautician': str(beautician).strip() if beautician else "",
                            'amount': float(amount) if amount and not pd.isna(amount) else 0.0,
                            'is_specified': is_specified
                        })
                
                # 创建记录
                service_record = {
                    'customer_id': str(customer_id).strip(),
                    'customer_name': str(customer_name).strip() if customer_name else f"客户{customer_id}",
                    'arrival_time': arrival_time,
                    'departure_time': departure_time,
                    'total_sessions': total_sessions,
                    'total_amount': float(total_amount) if total_amount and not pd.isna(total_amount) else 0.0,
                    'satisfaction': str(satisfaction).strip() if satisfaction else None,
                    'projects': projects
                }
                
                structured_data.append(service_record)
            
            # 导入服务记录
            imported_services = 0
            imported_items = 0
            
            # 处理每条记录
            for record in structured_data:
                customer_id = record['customer_id']
                
                # 解析到店时间
                service_date = None
                arrival_time = record['arrival_time']
                if arrival_time:
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
                        print(f"到店时间解析错误: {arrival_time} - {str(e)}")
                        continue
                
                # 解析离店时间
                departure_time_str = None
                if record['departure_time']:
                    try:
                        departure_val = record['departure_time']
                        if isinstance(departure_val, str):
                            if '/' in departure_val:
                                departure_dt = datetime.strptime(departure_val, "%Y/%m/%d %H:%M")
                            else:
                                departure_dt = datetime.strptime(departure_val, "%Y-%m-%d %H:%M")
                        else:
                            departure_dt = pd.to_datetime(departure_val).to_pydatetime()
                        
                        departure_time_str = departure_dt.strftime('%Y-%m-%d %H:%M:%S')
                    except Exception as e:
                        print(f"离店时间解析错误: {record['departure_time']} - {str(e)}")
                
                # 获取总次数
                total_sessions = 0
                if record['total_sessions']:
                    try:
                        sessions_str = str(record['total_sessions'])
                        if "次" in sessions_str:
                            sessions_str = sessions_str.replace("次", "").strip()
                        total_sessions = int(float(sessions_str))
                        print(f"提取总次数: {record['total_sessions']} -> {total_sessions}")
                    except Exception as e:
                        print(f"总次数解析错误: {record['total_sessions']} - {str(e)}")
                        # 如果无法解析，使用项目数量作为总次数
                        total_sessions = len(record['projects'])
                
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
                    record['customer_name'],
                    service_date,
                    departure_time_str,
                    record['total_amount'],
                    total_sessions,
                    record['satisfaction'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
                
                imported_services += 1
                print(f"创建服务记录: {service_id}, 客户: {customer_id}, 总次数: {total_sessions}")
                
                # 插入项目
                for project in record['projects']:
                    project_name = project['project_name']
                    beautician_name = project['beautician']
                    unit_price = project['amount']
                    
                    # 处理是否指定
                    is_specified = 0
                    if project['is_specified'] is not None:
                        specified_val = project['is_specified']
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
            
            # 提交事务
            conn.commit()
            
            # 输出导入结果
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
        else:
            print("错误: 找不到标题行，Excel文件可能格式不正确")
    
    except Exception as e:
        print(f"导入过程中出错: {str(e)}")
        print(traceback.format_exc())
        conn.rollback()
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    test_service_import()