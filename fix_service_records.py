"""
服务记录全面修复工具
包含数据库结构修复、Excel导入逻辑修复和报告生成逻辑修复
"""
import os
import sys
import logging
import sqlite3
import pandas as pd
from datetime import datetime
import json

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ServiceRecordsFixer')

# 数据库路径
DB_PATH = "instance/beauty_crm.db"
EXCEL_PATH = "模拟-客户信息档案.xlsx"

def fix_database_structure():
    """
    修复数据库结构，添加缺失字段
    """
    logger.info("步骤1: 修复数据库结构")
    
    if not os.path.exists(DB_PATH):
        logger.error(f"数据库文件不存在: {DB_PATH}")
        return False
    
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查services表结构
        cursor.execute("PRAGMA table_info(services)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        logger.info(f"当前services表字段: {column_names}")
        
        # 检查是否需要添加total_sessions字段
        if 'total_sessions' not in column_names:
            logger.info("添加total_sessions字段到services表")
            cursor.execute("ALTER TABLE services ADD COLUMN total_sessions INTEGER DEFAULT 0")
        
        # 检查ServiceItem表是否有is_specified字段
        cursor.execute("PRAGMA table_info(service_items)")
        item_columns = cursor.fetchall()
        item_column_names = [col[1] for col in item_columns]
        
        logger.info(f"当前service_items表字段: {item_column_names}")
        
        if 'is_specified' not in item_column_names:
            logger.info("添加is_specified字段到service_items表")
            cursor.execute("ALTER TABLE service_items ADD COLUMN is_specified BOOLEAN DEFAULT 0")
        
        # 提交更改
        conn.commit()
        logger.info("数据库结构修复完成")
        return True
        
    except Exception as e:
        logger.error(f"数据库结构修复失败: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def remove_duplicate_services():
    """
    清理重复的服务记录
    """
    logger.info("步骤2: 清理重复的服务记录")
    
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 找出所有重复的服务记录（相同客户ID和日期的）
        cursor.execute("""
            SELECT customer_id, service_date, COUNT(*) as count
            FROM services
            GROUP BY customer_id, service_date
            HAVING count > 1
        """)
        
        duplicates = cursor.fetchall()
        logger.info(f"找到 {len(duplicates)} 组重复的服务记录")
        
        removed = 0
        for dup in duplicates:
            customer_id, service_date, count = dup
            
            # 获取重复的服务ID（保留第一个，删除其他）
            cursor.execute("""
                SELECT service_id FROM services 
                WHERE customer_id = ? AND service_date = ?
                ORDER BY created_at
            """, (customer_id, service_date))
            
            service_ids = [row[0] for row in cursor.fetchall()]
            keep_id = service_ids[0]
            delete_ids = service_ids[1:]
            
            logger.info(f"客户 {customer_id} 在 {service_date} 有 {count} 条重复记录，保留ID: {keep_id}")
            
            # 删除重复服务的项目
            for delete_id in delete_ids:
                cursor.execute("DELETE FROM service_items WHERE service_id = ?", (delete_id,))
                
                # 删除服务
                cursor.execute("DELETE FROM services WHERE service_id = ?", (delete_id,))
                removed += 1
        
        # 提交更改
        conn.commit()
        logger.info(f"成功删除 {removed} 条重复的服务记录")
        return True
        
    except Exception as e:
        logger.error(f"清理重复服务记录失败: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def update_service_data():
    """
    更新服务数据，将项目数量更新到total_sessions字段
    """
    logger.info("步骤3: 更新服务数据")
    
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 获取所有服务
        cursor.execute("SELECT service_id FROM services")
        services = cursor.fetchall()
        
        updated = 0
        for service in services:
            service_id = service[0]
            
            # 获取服务项目数量
            cursor.execute("SELECT COUNT(*) FROM service_items WHERE service_id = ?", (service_id,))
            item_count = cursor.fetchone()[0]
            
            # 更新服务的total_sessions
            cursor.execute("UPDATE services SET total_sessions = ? WHERE service_id = ?", 
                          (item_count, service_id))
            updated += 1
        
        # 提交更改
        conn.commit()
        logger.info(f"更新了 {updated} 条服务记录的总项目数")
        return True
        
    except Exception as e:
        logger.error(f"更新服务数据失败: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def process_excel_file():
    """
    处理Excel文件，生成正确的服务记录
    """
    logger.info("步骤4: 处理Excel文件")
    
    try:
        # 读取Excel文件中的消耗表
        df = pd.read_excel(EXCEL_PATH, sheet_name="消耗")
        logger.info(f"成功读取Excel文件: {EXCEL_PATH}, 表: 消耗")
        
        # 识别首行是否为标题行
        first_row = df.iloc[0].tolist()
        
        # 如果第一行是标题行，则将其作为列名，并删除这一行
        if '客户ID' in str(first_row) or '到店时间' in str(first_row):
            logger.info("检测到第一行是标题行，将其作为列名")
            # 将第一行设为列名
            new_columns = []
            for col in first_row:
                if pd.isna(col) or col == '':
                    new_columns.append("Unnamed")
                else:
                    new_columns.append(str(col))
            
            df.columns = new_columns
            # 删除第一行
            df = df.iloc[1:].reset_index(drop=True)
        
        # 识别列分组
        base_cols = {
            'customer_id': None,
            'name': None,
            'service_date': None,
            'departure_time': None,
            'total_sessions': None,
            'total_amount': None,
            'satisfaction': None
        }
        
        # 映射列名
        col_map = {
            '客户ID': 'customer_id',
            '姓名': 'name',
            '进店时间': 'service_date',
            '到店时间': 'service_date',
            '离店时间': 'departure_time',
            '总消耗项目数': 'total_sessions',
            '总耗卡次数': 'total_sessions',
            '总耗卡金额': 'total_amount',
            '服务满意度': 'satisfaction'
        }
        
        # 识别基础信息列
        for col in df.columns:
            if col in col_map:
                base_cols[col_map[col]] = col
        
        logger.info(f"识别到的基础信息列: {base_cols}")
        
        # 识别项目消耗分组
        project_groups = []
        for col_idx, col in enumerate(df.columns):
            if '项目' in str(col) or '消耗' in str(col):
                if col_idx + 3 < len(df.columns):
                    beautician_col = df.columns[col_idx + 1] if '美容师' in str(df.columns[col_idx + 1]) else None
                    amount_col = df.columns[col_idx + 2] if '金额' in str(df.columns[col_idx + 2]) or '耗卡' in str(df.columns[col_idx + 2]) else None
                    specified_col = df.columns[col_idx + 3] if '指定' in str(df.columns[col_idx + 3]) else None
                    
                    if beautician_col and amount_col:
                        group = {
                            'project': col,
                            'beautician': beautician_col,
                            'amount': amount_col,
                            'is_specified': specified_col
                        }
                        project_groups.append(group)
        
        logger.info(f"识别到的项目消耗分组: {project_groups}")
        
        # 处理每一行数据
        processed_services = []
        for _, row in df.iterrows():
            # 获取基本信息
            customer_id = row[base_cols['customer_id']] if base_cols['customer_id'] else None
            service_date = row[base_cols['service_date']] if base_cols['service_date'] else None
            
            if not customer_id or not service_date or pd.isna(customer_id) or pd.isna(service_date):
                logger.warning(f"跳过无效记录: 客户ID={customer_id}, 服务日期={service_date}")
                continue
            
            # 处理基本信息
            service = {
                'customer_id': str(customer_id),
                'service_date': service_date,
                'departure_time': row[base_cols['departure_time']] if base_cols['departure_time'] and not pd.isna(row[base_cols['departure_time']]) else None,
                'total_amount': float(row[base_cols['total_amount']]) if base_cols['total_amount'] and not pd.isna(row[base_cols['total_amount']]) else 0.0,
                'satisfaction': str(row[base_cols['satisfaction']]) if base_cols['satisfaction'] and not pd.isna(row[base_cols['satisfaction']]) else None,
                'items': []
            }
            
            # 处理项目消耗
            total_sessions = 0
            for group in project_groups:
                project_name = row[group['project']] if not pd.isna(row[group['project']]) else None
                if not project_name:
                    continue
                
                beautician_name = row[group['beautician']] if group['beautician'] and not pd.isna(row[group['beautician']]) else None
                amount = float(row[group['amount']]) if group['amount'] and not pd.isna(row[group['amount']]) else 0.0
                is_specified = row[group['is_specified']] == '✓' if group['is_specified'] and not pd.isna(row[group['is_specified']]) else False
                
                # 只有当项目名称存在时才添加项目
                if project_name and str(project_name).strip():
                    service_item = {
                        'project_name': str(project_name),
                        'beautician_name': str(beautician_name) if beautician_name else '',
                        'unit_price': amount,
                        'is_specified': is_specified
                    }
                    service['items'].append(service_item)
                    total_sessions += 1
            
            # 设置总耗卡次数
            if base_cols['total_sessions'] and not pd.isna(row[base_cols['total_sessions']]):
                try:
                    service['total_sessions'] = int(row[base_cols['total_sessions']])
                except (ValueError, TypeError):
                    # 如果转换失败，使用计算的值
                    service['total_sessions'] = total_sessions
            else:
                service['total_sessions'] = total_sessions
            
            # 添加到处理结果
            processed_services.append(service)
        
        logger.info(f"成功处理 {len(processed_services)} 条服务记录")
        
        # 保存处理结果
        with open("processed_services.json", "w", encoding="utf-8") as f:
            json.dump(processed_services, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info("处理结果已保存到 processed_services.json")
        return processed_services
    
    except Exception as e:
        logger.error(f"处理Excel文件失败: {str(e)}")
        return None

def import_services_to_db(services):
    """
    将处理后的服务记录导入数据库
    """
    logger.info("步骤5: 导入服务记录到数据库")
    
    if not services:
        logger.error("无服务记录可导入")
        return False
    
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 清除现有服务数据（可选）
        # cursor.execute("DELETE FROM service_items")
        # cursor.execute("DELETE FROM services")
        # logger.info("已清除现有服务数据")
        
        # 导入服务记录
        imported = 0
        for service in services:
            # 检查是否已存在相同记录（避免重复导入）
            cursor.execute("""
                SELECT service_id FROM services 
                WHERE customer_id = ? AND service_date = ? AND total_amount = ?
            """, (service['customer_id'], service['service_date'], service['total_amount']))
            
            existing = cursor.fetchone()
            if existing:
                logger.info(f"服务记录已存在，跳过: {service['customer_id']} - {service['service_date']}")
                continue
            
            # 生成服务ID
            import uuid
            service_id = f"S{uuid.uuid4().hex[:8].upper()}"
            
            # 插入服务记录
            cursor.execute("""
                INSERT INTO services 
                (service_id, customer_id, service_date, departure_time, total_amount, 
                 total_sessions, satisfaction, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                service_id,
                service['customer_id'],
                service['service_date'],
                service['departure_time'],
                service['total_amount'],
                service['total_sessions'],
                service['satisfaction'],
                datetime.now(),
                datetime.now()
            ))
            
            # 插入服务项目
            for item in service['items']:
                cursor.execute("""
                    INSERT INTO service_items
                    (service_id, project_name, beautician_name, unit_price, is_specified, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    service_id,
                    item['project_name'],
                    item['beautician_name'],
                    item['unit_price'],
                    item['is_specified'],
                    datetime.now(),
                    datetime.now()
                ))
            
            imported += 1
        
        # 提交更改
        conn.commit()
        logger.info(f"成功导入 {imported} 条服务记录到数据库")
        return True
        
    except Exception as e:
        logger.error(f"导入服务记录失败: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def generate_customer_report(customer_id):
    """
    生成客户报告
    """
    logger.info(f"步骤6: 生成客户 {customer_id} 的报告")
    
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取客户信息
        cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            logger.error(f"客户不存在: {customer_id}")
            return False
        
        customer_dict = dict(customer)
        
        # 获取健康档案
        cursor.execute("SELECT * FROM health_records WHERE customer_id = ?", (customer_id,))
        health_record = cursor.fetchone()
        health_record_dict = dict(health_record) if health_record else {}
        
        # 获取消费记录
        cursor.execute("SELECT * FROM consumptions WHERE customer_id = ? ORDER BY date DESC", (customer_id,))
        consumptions = cursor.fetchall()
        consumption_list = [dict(c) for c in consumptions]
        
        # 获取服务记录
        cursor.execute("SELECT * FROM services WHERE customer_id = ? ORDER BY service_date DESC", (customer_id,))
        services = cursor.fetchall()
        service_list = []
        
        for service in services:
            service_dict = dict(service)
            
            # 获取服务项目
            cursor.execute("SELECT * FROM service_items WHERE service_id = ?", (service_dict['service_id'],))
            items = cursor.fetchall()
            service_dict['items'] = [dict(item) for item in items]
            
            service_list.append(service_dict)
        
        # 获取沟通记录
        cursor.execute("SELECT * FROM communications WHERE customer_id = ? ORDER BY communication_date DESC", (customer_id,))
        communications = cursor.fetchall()
        communication_list = [dict(c) for c in communications]
        
        # 生成MD报告
        md_content = []
        
        # 客户基本信息
        md_content.append(f"## 客户: {customer_dict.get('name', '')} ({customer_id})\n")
        md_content.append("### 基本信息\n")
        md_content.append("| 字段 | 值 |")
        md_content.append("|------|----|")
        
        # 添加基本信息字段
        for field, value in [
            ('姓名', customer_dict.get('name', '')),
            ('性别', customer_dict.get('gender', '')),
            ('年龄', customer_dict.get('age', '')),
            ('门店归属', customer_dict.get('store', '')),
            ('籍贯', customer_dict.get('hometown', '')),
            ('现居地', customer_dict.get('residence', '')),
            ('居住时长', customer_dict.get('residence_years', '')),
            ('家庭成员构成', customer_dict.get('family_structure', '')),
            ('家庭人员年龄分布', customer_dict.get('family_age_distribution', '')),
            ('家庭居住情况', customer_dict.get('living_condition', '')),
            ('性格类型标签', customer_dict.get('personality_tags', '')),
            ('消费决策主导', customer_dict.get('consumption_decision', '')),
            ('兴趣爱好', customer_dict.get('hobbies', '')),
            ('作息规律', customer_dict.get('routine', '')),
            ('饮食偏好', customer_dict.get('diet_preference', '')),
            ('职业', customer_dict.get('occupation', '')),
            ('单位性质', customer_dict.get('work_unit_type', '')),
            ('年收入', customer_dict.get('annual_income', ''))
        ]:
            md_content.append(f"| {field} | {value} |")
        
        # 健康档案
        if health_record_dict:
            md_content.append("\n### 健康档案\n")
            md_content.append("| 类别 | 字段 | 值 |")
            md_content.append("|------|------|----|")
            
            # 皮肤状况
            for field, value in [
                ('皮肤状况', '肤质类型', health_record_dict.get('skin_type', '')),
                ('皮肤状况', '水油平衡', health_record_dict.get('oil_water_balance', '')),
                ('皮肤状况', '毛孔与黑头', health_record_dict.get('pores_blackheads', '')),
                ('皮肤状况', '皱纹与纹理', health_record_dict.get('wrinkles_texture', '')),
                ('皮肤状况', '色素沉着', health_record_dict.get('pigmentation', '')),
                ('皮肤状况', '光老化与炎症', health_record_dict.get('photoaging_inflammation', '')),
                ('中医体质', '体质类型', health_record_dict.get('tcm_constitution', '')),
                ('中医体质', '舌象特征', health_record_dict.get('tongue_features', '')),
                ('中医体质', '脉象数据', health_record_dict.get('pulse_data', '')),
                ('生活习惯', '作息规律', health_record_dict.get('sleep_routine', '')),
                ('生活习惯', '运动频率', health_record_dict.get('exercise_pattern', '')),
                ('生活习惯', '饮食禁忌', health_record_dict.get('diet_restrictions', '')),
                ('护理需求', '时间灵活度', health_record_dict.get('care_time_flexibility', '')),
                ('护理需求', '手法力度偏好', health_record_dict.get('massage_pressure_preference', '')),
                ('护理需求', '环境氛围', health_record_dict.get('environment_requirements', '')),
                ('美容健康目标', '短期美丽目标', health_record_dict.get('short_term_beauty_goal', '')),
                ('美容健康目标', '长期美丽目标', health_record_dict.get('long_term_beauty_goal', '')),
                ('美容健康目标', '短期健康目标', health_record_dict.get('short_term_health_goal', '')),
                ('美容健康目标', '长期健康目标', health_record_dict.get('long_term_health_goal', '')),
                ('健康记录', '医美操作史', health_record_dict.get('medical_cosmetic_history', '')),
                ('健康记录', '大健康服务史', health_record_dict.get('wellness_service_history', '')),
                ('健康记录', '过敏史', health_record_dict.get('allergies', '')),
                ('健康记录', '重大疾病历史', health_record_dict.get('major_disease_history', ''))
            ]:
                md_content.append(f"| {field[0]} | {field[1]} | {value} |")
        
        # 消费记录
        if consumption_list:
            md_content.append("\n### 消费记录\n")
            md_content.append("| 消费时间 | 项目名称 | 消费金额 | 支付方式 |")
            md_content.append("|----------|----------|----------|----------|")
            
            for consumption in consumption_list:
                date_str = consumption.get('date', '')
                if date_str:
                    try:
                        if isinstance(date_str, str):
                            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                        else:
                            dt = date_str
                        date_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass
                
                md_content.append(f"| {date_str} | {consumption.get('project_name', '')} | {consumption.get('amount', 0.0)} | {consumption.get('payment_method', '')} |")
        
        # 服务记录
        if service_list:
            md_content.append("\n### 服务记录\n")
            md_content.append("| 到店时间 | 离店时间 | 总耗卡次数 | 总耗卡金额 | 服务满意度 | 项目详情1 | 项目详情2 | 项目详情3 | 项目详情4 | 项目详情5 |")
            md_content.append("|----------|----------|------------|------------|------------|-----------|-----------|-----------|-----------|------------|")
            
            for service in service_list:
                # 格式化日期时间
                service_date = service.get('service_date', '')
                if service_date:
                    try:
                        if isinstance(service_date, str):
                            dt = datetime.strptime(service_date, "%Y-%m-%d %H:%M:%S")
                        else:
                            dt = service_date
                        service_date = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass
                
                departure_time = service.get('departure_time', '')
                if departure_time:
                    try:
                        if isinstance(departure_time, str):
                            dt = datetime.strptime(departure_time, "%Y-%m-%d %H:%M:%S")
                        else:
                            dt = departure_time
                        departure_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass
                
                # 项目详情：项目内容\操作美容师\耗卡金额\是否指定
                items = service.get('items', [])
                project_details = []
                
                for item in items:
                    project_name = item.get('project_name', '')
                    beautician_name = item.get('beautician_name', '')
                    unit_price = item.get('unit_price', 0)
                    is_specified = "✓指定" if item.get('is_specified', False) else "未指定"
                    
                    detail = f"{project_name} - {beautician_name} - {unit_price}元 - {is_specified}"
                    project_details.append(detail)
                
                # 确保有5个项目详情字段
                while len(project_details) < 5:
                    project_details.append("")
                
                # 限制为5个项目详情
                project_details = project_details[:5]
                
                # 添加行
                row = f"| {service_date} | {departure_time} | {service.get('total_sessions', len(items))} | {service.get('total_amount', 0)} | {service.get('satisfaction', '')} | {' | '.join(project_details)} |"
                md_content.append(row)
        
        # 沟通记录
        if communication_list:
            md_content.append("\n### 沟通记录\n")
            md_content.append("| 沟通时间 | 沟通地点 | 沟通内容 |")
            md_content.append("|----------|----------|----------|")
            
            for comm in communication_list:
                date_str = comm.get('communication_date', '')
                if date_str:
                    try:
                        if isinstance(date_str, str):
                            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                        else:
                            dt = date_str
                        date_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass
                
                md_content.append(f"| {date_str} | {comm.get('communication_location', '')} | {comm.get('communication_content', '')} |")
        
        # 保存到文件
        output_file = f"{customer_id}_customer_report_fixed.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(md_content))
        
        logger.info(f"客户报告已生成: {output_file}")
        return output_file
        
    except Exception as e:
        logger.error(f"生成客户报告失败: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # 执行全流程修复
    try:
        # 1. 修复数据库结构
        if fix_database_structure():
            # 2. 清理重复数据
            remove_duplicate_services()
            
            # 3. 更新服务数据
            update_service_data()
            
            # 4. 处理Excel文件
            services = process_excel_file()
            
            # 5. 导入服务记录到数据库
            if services:
                import_services_to_db(services)
            
            # 6. 生成客户报告
            customer_ids = ["C001", "C002", "C003"]
            for customer_id in customer_ids:
                generate_customer_report(customer_id)
            
            logger.info("全流程修复完成！")
        else:
            logger.error("数据库结构修复失败，后续步骤已跳过")
    except Exception as e:
        logger.error(f"修复过程出错: {str(e)}")