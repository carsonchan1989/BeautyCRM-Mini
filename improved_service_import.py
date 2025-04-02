"""
改进版Excel服务记录导入脚本 - 基于测试脚本的成功逻辑
"""
import os
import sys
import pandas as pd
import sqlite3
import uuid
from datetime import datetime
import traceback
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("improved_service_import.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("service_import")

def import_excel_services(excel_path, db_path="instance/beauty_crm.db", sheet_name="消耗"):
    """
    从Excel文件导入服务记录
    
    Args:
        excel_path: Excel文件路径
        db_path: 数据库文件路径
        sheet_name: 表名
        
    Returns:
        dict: 导入结果统计
    """
    logger.info(f"开始导入Excel服务记录: {excel_path}")
    
    # 数据库连接
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 统计结果
    stats = {
        'services': 0,
        'service_items': 0,
        'errors': []
    }
    
    try:
        # 读取Excel数据 - 不使用pandas默认列名，直接读取原始数据
        raw_df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
        logger.info(f"原始消耗表形状: {raw_df.shape}")
        
        # 检查Excel结构
        if raw_df.shape[0] < 2:
            error_msg = "Excel文件格式不正确，行数过少"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
            return stats
        
        # 根据观察的数据结构，第1行为标题行，从第2行开始为数据
        header_row = raw_df.iloc[1]  # 标题行
        data_start_row = 2           # 数据起始行
        
        logger.info(f"使用第{data_start_row}行开始作为数据，第{data_start_row-1}行作为标题")
        
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
                
                logger.info(f"处理客户: {customer_id} - {customer_name}")
                
                # 检查客户是否存在
                cursor.execute("SELECT id FROM customers WHERE id = ?", (customer_id,))
                if not cursor.fetchone():
                    logger.warning(f"客户不存在，自动创建: {customer_id}")
                    # 插入基本客户信息
                    cursor.execute("""
                    INSERT INTO customers 
                    (id, name, created_at, updated_at) 
                    VALUES (?, ?, ?, ?)
                    """, (
                        customer_id, 
                        customer_name, 
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ))
                
                # 解析到店时间
                arrival_time = row[arrival_time_col]
                if pd.isna(arrival_time):
                    logger.warning(f"跳过行 {row_idx}: 缺少到店时间")
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
                    logger.error(f"解析到店时间出错 [{arrival_time}]: {str(e)}")
                    stats['errors'].append(f"行 {row_idx} 到店时间解析错误: {str(e)}")
                    continue
                
                # 检查是否已存在相同的服务记录
                cursor.execute("""
                SELECT service_id FROM services 
                WHERE customer_id = ? AND service_date = ?
                """, (customer_id, service_date))
                
                existing_service = cursor.fetchone()
                if existing_service:
                    logger.warning(f"跳过已存在的服务记录: {customer_id} - {service_date}")
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
                        logger.warning(f"解析离店时间出错 [{departure_time}]: {str(e)}")
                
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
                        logger.warning(f"解析总项目数出错 [{total_projects}]: {str(e)}")
                
                # 获取总金额
                total_amount = 0.0
                amount_val = row[total_amount_col]
                if not pd.isna(amount_val):
                    try:
                        total_amount = float(amount_val)
                    except Exception as e:
                        logger.warning(f"解析总金额出错 [{amount_val}]: {str(e)}")
                
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
                
                stats['services'] += 1
                logger.info(f"创建服务记录: {service_id}")
                
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
                            logger.warning(f"解析项目金额出错 [{price_val}]")
                    
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
                    
                    stats['service_items'] += 1
                    logger.info(f"创建服务项目: {project_name} - {beautician_name} - {unit_price}元 - {'✓指定' if is_specified == 1 else '未指定'}")
                
                # 每20条提交一次事务
                if stats['services'] % 20 == 0:
                    conn.commit()
                    logger.info(f"已导入 {stats['services']} 条服务记录，{stats['service_items']} 个服务项目")
            
            except Exception as e:
                logger.error(f"处理行 {row_idx} 时出错: {str(e)}")
                logger.error(traceback.format_exc())
                stats['errors'].append(f"行 {row_idx} 处理错误: {str(e)}")
        
        # 提交事务
        conn.commit()
        
        # 显示导入结果
        logger.info(f"导入结果汇总:")
        logger.info(f"成功导入服务记录: {stats['services']}条")
        logger.info(f"成功导入服务项目: {stats['service_items']}条")
        logger.info(f"错误数量: {len(stats['errors'])}")
        
        return stats
    
    except Exception as e:
        logger.error(f"导入过程中出错: {str(e)}")
        logger.error(traceback.format_exc())
        stats['errors'].append(f"导入过程出错: {str(e)}")
        conn.rollback()
        return stats
    finally:
        conn.close()

def export_service_to_markdown(customer_id=None, output_file=None):
    """
    导出服务记录到Markdown文件
    
    Args:
        customer_id: 客户ID（可选，如不提供则导出所有客户的服务记录）
        output_file: 输出文件路径（可选，如不提供则返回Markdown内容）
    
    Returns:
        str: Markdown内容或文件路径
    """
    db_path = "instance/beauty_crm.db"
    
    if not os.path.exists(db_path):
        return f"数据库文件不存在: {db_path}"
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # 使结果以字典形式返回
    cursor = conn.cursor()
    
    try:
        md_content = "# 服务记录导出\n\n"
        md_content += f"**导出时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 构建查询
        query = "SELECT * FROM services"
        params = []
        
        if customer_id:
            query += " WHERE customer_id = ?"
            params.append(customer_id)
            
            # 获取客户名称
            cursor.execute("SELECT name FROM customers WHERE id = ?", (customer_id,))
            customer = cursor.fetchone()
            if customer:
                md_content += f"**客户:** {customer_id} - {customer['name']}\n\n"
            else:
                md_content += f"**客户ID:** {customer_id}\n\n"
        
        # 获取服务记录
        cursor.execute(query, params)
        services = cursor.fetchall()
        
        md_content += f"## 服务记录 ({len(services)}条)\n\n"
        
        if services:
            md_content += "| 客户ID | 姓名 | 到店时间 | 离店时间 | 总耗卡金额 | 总次数 | 满意度 |\n"
            md_content += "|--------|------|----------|----------|------------|--------|--------|\n"
            
            for service in services:
                # 格式化日期
                service_date = service['service_date']
                departure_time = service['departure_time'] or "未记录"
                
                md_content += f"| {service['customer_id']} | {service['customer_name']} | {service_date} | {departure_time} | "
                md_content += f"{service['total_amount']} | {service['total_sessions']} | {service['satisfaction'] or '未记录'} |\n"
            
            # 添加服务项目详情
            md_content += "\n## 服务项目详情\n\n"
            
            for service in services:
                service_id = service['service_id']
                cursor.execute("SELECT * FROM service_items WHERE service_id = ?", (service_id,))
                items = cursor.fetchall()
                
                md_content += f"### 服务 {service_id} ({service['service_date']})\n\n"
                md_content += f"**客户:** {service['customer_id']} - {service['customer_name']}\n\n"
                
                if items:
                    md_content += "| 项目名称 | 美容师 | 金额 | 是否指定 |\n"
                    md_content += "|----------|--------|------|----------|\n"
                    
                    for item in items:
                        md_content += f"| {item['project_name']} | {item['beautician_name']} | {item['unit_price']} | "
                        md_content += f"{'是' if item['is_specified'] == 1 else '否'} |\n"
                else:
                    md_content += "*无服务项目记录*\n"
                
                md_content += "\n---\n\n"
        else:
            md_content += "*无服务记录*\n\n"
        
        # 写入文件或返回内容
        if output_file:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(md_content)
            return f"服务记录已导出到 {output_file}"
        else:
            return md_content
    
    except Exception as e:
        return f"导出服务记录出错: {str(e)}"
    finally:
        conn.close()

if __name__ == "__main__":
    # 解析命令行参数
    import argparse
    
    parser = argparse.ArgumentParser(description='改进版Excel服务记录导入/导出工具')
    parser.add_argument('--import', dest='import_file', help='导入Excel文件路径')
    parser.add_argument('--export', dest='export_file', help='导出Markdown文件路径')
    parser.add_argument('--customer', help='客户ID，用于导出特定客户的服务记录')
    
    args = parser.parse_args()
    
    if args.import_file:
        # 导入Excel文件
        result = import_excel_services(args.import_file)
        
        # 显示结果
        print(f"\n导入结果汇总:")
        print(f"成功导入服务记录: {result['services']}条")
        print(f"成功导入服务项目: {result['service_items']}条")
        
        if result['errors']:
            print(f"发生 {len(result['errors'])} 个错误:")
            for i, error in enumerate(result['errors'][:5], 1):
                print(f"  {i}. {error}")
            if len(result['errors']) > 5:
                print(f"  ... 还有 {len(result['errors']) - 5} 个错误未显示")
    
    elif args.export_file or args.customer:
        # 导出服务记录
        output_file = args.export_file
        customer_id = args.customer
        
        result = export_service_to_markdown(customer_id, output_file)
        print(result)
    
    else:
        print("请指定操作参数，使用 --help 查看帮助信息")