"""
专门测试'模拟-客户信息档案.xlsx'的服务记录清洗功能
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
        
        # 读取消耗表
        consumption_df = pd.read_excel(excel_path, sheet_name="消耗")
        
        # 输出原始表结构，调试用
        print(f"原始消耗表形状: {consumption_df.shape}")
        print(f"原始列名: {list(consumption_df.columns)}")
        print(f"第一行数据: {consumption_df.iloc[0].tolist()}")
        
        # 检查是否第一行是标题行
        if '客户ID' in str(consumption_df.iloc[0][0]) or 'ID' in str(consumption_df.iloc[0][0]):
            print("检测到第一行为标题行，将其设置为列名")
            
            # 重新整理列名
            header_row = consumption_df.iloc[0]
            consumption_df = consumption_df.iloc[1:].reset_index(drop=True)
            
            # 处理标题行，替换NaN为有意义的名称
            new_columns = []
            for i, col in enumerate(header_row):
                if pd.isna(col):
                    # 寻找上一个非空列名
                    for j in range(i-1, -1, -1):
                        if not pd.isna(header_row[j]):
                            prefix = str(header_row[j]).strip()
                            # 检查是否是项目组的一部分
                            if '项目' in prefix or '消耗项目' in prefix:
                                # 根据位置判断是什么类型的列
                                pos = i - j
                                if pos == 1:
                                    new_columns.append(f"美容师{len(new_columns) // 4 + 1}")
                                elif pos == 2:
                                    new_columns.append(f"金额{len(new_columns) // 4 + 1}")
                                elif pos == 3:
                                    new_columns.append(f"是否指定{len(new_columns) // 4 + 1}")
                                else:
                                    new_columns.append(f"{prefix}_未知_{i}")
                            else:
                                new_columns.append(f"{prefix}_未知_{i}")
                            break
                    else:
                        new_columns.append(f"未知列_{i}")
                else:
                    # 直接使用原列名，但标准化处理
                    col_str = str(col).strip()
                    if '项目' in col_str and '名称' not in col_str and '满意' not in col_str:
                        # 这是项目组的开始
                        new_columns.append(f"项目名称{len(new_columns) // 4 + 1}")
                    else:
                        # 使用原始列名，但清理一下
                        col_str = col_str.replace("\n", "").strip()
                        new_columns.append(col_str)
            
            # 设置新列名
            consumption_df.columns = new_columns
            print(f"处理后的列名: {new_columns}")
        
        # 导入服务记录
        imported_services = 0
        imported_items = 0
        
        # 按客户ID和到店时间分组处理
        if any(['客户ID' in col for col in consumption_df.columns]) and any(['到店时间' in col for col in consumption_df.columns]):
            # 找出客户ID和到店时间列
            customer_id_col = [col for col in consumption_df.columns if '客户ID' in col][0]
            arrival_time_col = [col for col in consumption_df.columns if '到店时间' in col][0]
            
            print(f"使用列: 客户ID={customer_id_col}, 到店时间={arrival_time_col}")
            
            # 处理每一行服务记录
            for idx, row in consumption_df.iterrows():
                try:
                    # 获取客户ID，跳过空值
                    customer_id = row[customer_id_col]
                    if pd.isna(customer_id):
                        continue
                    customer_id = str(customer_id).strip()
                    
                    print(f"处理客户: {customer_id}")
                    
                    # 解析日期时间
                    arrival_time = row[arrival_time_col]
                    if pd.isna(arrival_time):
                        continue
                    
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
                    departure_time = None
                    departure_cols = [col for col in consumption_df.columns if '离店时间' in col]
                    if departure_cols:
                        departure_val = row[departure_cols[0]]
                        if not pd.isna(departure_val):
                            try:
                                if isinstance(departure_val, str):
                                    if '/' in departure_val:
                                        departure_dt = datetime.strptime(departure_val, "%Y/%m/%d %H:%M")
                                    else:
                                        departure_dt = datetime.strptime(departure_val, "%Y-%m-%d %H:%M")
                                else:
                                    departure_dt = pd.to_datetime(departure_val).to_pydatetime()
                                
                                departure_time = departure_dt.strftime('%Y-%m-%d %H:%M:%S')
                            except Exception as e:
                                print(f"离店时间解析错误: {departure_val} - {str(e)}")
                    
                    # 获取总金额
                    total_amount = 0.0
                    total_amount_cols = [col for col in consumption_df.columns if '总' in col and '金额' in col]
                    if total_amount_cols:
                        total_amount_val = row[total_amount_cols[0]]
                        if not pd.isna(total_amount_val):
                            try:
                                total_amount = float(total_amount_val)
                            except:
                                print(f"总金额转换错误: {total_amount_val}")
                    
                    # 获取总次数
                    total_sessions = 0
                    total_sessions_cols = [col for col in consumption_df.columns if '总次数' in col or ('总' in col and '次' in col)]
                    if total_sessions_cols:
                        total_sessions_val = row[total_sessions_cols[0]]
                        if not pd.isna(total_sessions_val):
                            try:
                                sessions_str = str(total_sessions_val)
                                if "次" in sessions_str:
                                    sessions_str = sessions_str.replace("次", "").strip()
                                total_sessions = int(sessions_str)
                                print(f"提取总次数: {total_sessions_val} -> {total_sessions}")
                            except Exception as e:
                                print(f"总次数解析错误: {total_sessions_val} - {str(e)}")
                    
                    # 获取满意度
                    satisfaction = None
                    satisfaction_cols = [col for col in consumption_df.columns if '满意度' in col]
                    if satisfaction_cols:
                        satisfaction_val = row[satisfaction_cols[0]]
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
                        f"客户{customer_id}",  # 简化处理，仅用ID代替名称
                        service_date,
                        departure_time,
                        total_amount,
                        total_sessions,
                        satisfaction,
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ))
                    
                    imported_services += 1
                    print(f"创建服务记录: {service_id}")
                    
                    # 处理项目列
                    project_name_cols = [col for col in consumption_df.columns if '项目名称' in col]
                    
                    # 如果没有找到明确的项目名称列，尝试按编号查找
                    if not project_name_cols:
                        project_name_cols = []
                        for i in range(1, 10):  # 假设最多9个项目
                            col_name = f"项目名称{i}"
                            if col_name in consumption_df.columns:
                                project_name_cols.append(col_name)
                    
                    print(f"找到项目名称列: {project_name_cols}")
                    
                    for project_col in project_name_cols:
                        project_val = row[project_col]
                        if pd.isna(project_val) or not str(project_val).strip():
                            continue
                        
                        project_name = str(project_val).strip()
                        print(f"处理项目: {project_name}")
                        
                        # 提取项目编号
                        proj_num = None
                        for c in project_col:
                            if c.isdigit():
                                proj_num = c
                                break
                        
                        # 查找对应的美容师、金额和是否指定列
                        beautician_name = ""
                        unit_price = 0.0
                        is_specified = 0
                        
                        # 尝试找美容师列
                        beautician_col = f"美容师{proj_num}" if proj_num else None
                        if beautician_col and beautician_col in consumption_df.columns:
                            beautician_val = row[beautician_col]
                            if not pd.isna(beautician_val):
                                beautician_name = str(beautician_val).strip()
                        
                        # 尝试找金额列
                        amount_col = f"金额{proj_num}" if proj_num else None
                        if amount_col and amount_col in consumption_df.columns:
                            amount_val = row[amount_col]
                            if not pd.isna(amount_val):
                                try:
                                    unit_price = float(amount_val)
                                except:
                                    print(f"金额转换错误: {amount_val}")
                        
                        # 尝试找是否指定列
                        specified_col = f"是否指定{proj_num}" if proj_num else None
                        if specified_col and specified_col in consumption_df.columns:
                            specified_val = row[specified_col]
                            if not pd.isna(specified_val):
                                # 检查值是否是"✓"或任何其他可能表示"是"的值
                                value = str(specified_val).strip()
                                is_specified = 1 if value in ['✓', '√', '是', 'Yes', 'yes', 'TRUE', 'true', 'True', '1', 'Y', 'y'] else 0
                        
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
                        print(f"创建服务项目: {project_name} - {beautician_name} - {unit_price}元 - {'✓指定' if is_specified else '未指定'}")
                    
                    # 如果没有找到项目，尝试使用备选策略
                    if imported_items == 0:
                        # 查找可能包含项目信息的列
                        project_cols = [col for col in consumption_df.columns if '项目' in col and not (
                            '总' in col or '满意度' in col)]
                        
                        for col in project_cols:
                            project_val = row[col]
                            if pd.isna(project_val) or not str(project_val).strip():
                                continue
                            
                            # 这可能是一个项目，创建一个简单的项目记录
                            cursor.execute('''
                            INSERT INTO service_items
                            (service_id, project_name, created_at, updated_at)
                            VALUES (?, ?, ?, ?)
                            ''', (
                                service_id,
                                str(project_val).strip(),
                                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            ))
                            
                            imported_items += 1
                            print(f"创建备选服务项目: {str(project_val).strip()}")
                
                except Exception as e:
                    print(f"处理行 {idx} 时出错: {str(e)}")
                    print(traceback.format_exc())
            
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
            print("错误: 消耗表中未找到客户ID或到店时间列")
    
    except Exception as e:
        print(f"导入过程中出错: {str(e)}")
        print(traceback.format_exc())
        conn.rollback()
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    test_service_import()