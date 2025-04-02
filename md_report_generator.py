"""
修正版服务记录报告生成工具
按照正确的格式生成客户服务记录的MD报告
"""
import os
import sys
import sqlite3
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('MDReportGenerator')

class DatabaseManager:
    def __init__(self, db_path="instance/beauty_crm.db"):
        self.db_path = db_path
        if not os.path.exists(db_path):
            logger.error(f"数据库文件不存在: {db_path}")
            raise FileNotFoundError(f"数据库文件不存在: {db_path}")
    
    def get_customer(self, customer_id):
        """获取客户信息"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        customer = cursor.fetchone()
        
        conn.close()
        return dict(customer) if customer else None
    
    def get_health_record(self, customer_id):
        """获取客户健康档案"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM health_records WHERE customer_id = ?", (customer_id,))
        record = cursor.fetchone()
        
        conn.close()
        return dict(record) if record else None
    
    def get_consumptions(self, customer_id):
        """获取客户消费记录"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM consumptions WHERE customer_id = ? ORDER BY date DESC", (customer_id,))
        consumptions = cursor.fetchall()
        
        conn.close()
        return [dict(c) for c in consumptions] if consumptions else []
    
    def get_services(self, customer_id):
        """获取客户服务记录及相关项目"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取服务记录
        logger.info(f"查询客户 {customer_id} 的服务记录")
        query = """
            SELECT * FROM services 
            WHERE customer_id = ? 
            ORDER BY service_date DESC
        """
        cursor.execute(query, (customer_id,))
        services = cursor.fetchall()
        logger.info(f"找到 {len(services)} 条服务记录")
        
        result = []
        for service in services:
            service_dict = dict(service)
            service_id = service_dict['service_id']
            logger.info(f"处理服务记录ID: {service_id}")
            
            # 获取服务项目
            cursor.execute("""
                SELECT * FROM service_items
                WHERE service_id = ?
            """, (service_id,))
            
            items = cursor.fetchall()
            logger.info(f"服务 {service_id} 有 {len(items)} 个项目")
            service_dict['items'] = [dict(item) for item in items] if items else []
            
            result.append(service_dict)
        
        conn.close()
        return result
    
    def get_communications(self, customer_id):
        """获取客户沟通记录"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM communications 
            WHERE customer_id = ? 
            ORDER BY communication_date DESC
        """, (customer_id,))
        communications = cursor.fetchall()
        
        conn.close()
        return [dict(c) for c in communications] if communications else []

def format_service_records(services):
    """
    按照正确格式处理服务记录，输出MD表格内容
    """
    if not services:
        return "无服务记录"
    
    # 表头
    md_table = [
        "| 到店时间 | 离店时间 | 总耗卡次数 | 总耗卡金额 | 服务满意度 | 项目详情1 | 项目详情2 | 项目详情3 | 项目详情4 | 项目详情5 |",
        "|----------|----------|------------|------------|------------|-----------|-----------|-----------|-----------|------------|"
    ]
    
    for service in services:
        # 获取服务项目
        items = service.get('items', [])
        
        # 移除重复项目，只保留唯一项目
        unique_items = []
        seen_projects = set()
        for item in items:
            project_name = item.get('project_name', '')
            # 过滤掉项目名称为数字的记录，这些可能是错误数据
            if not str(project_name).isdigit() and project_name.strip():
                # 使用项目名称作为唯一键，允许同一项目由不同美容师操作
                project_key = f"{project_name}-{item.get('beautician_name', '')}"
                if project_key not in seen_projects:
                    seen_projects.add(project_key)
                    unique_items.append(item)
        
        # 格式化日期时间
        service_date = service.get('service_date')
        arrival_time = ""
        if service_date:
            try:
                if isinstance(service_date, str):
                    dt = datetime.strptime(service_date, "%Y-%m-%d %H:%M:%S.%f")
                else:
                    dt = service_date
                arrival_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            except Exception as e:
                logger.warning(f"日期格式转换错误: {e}")
                arrival_time = str(service_date)
        
        departure_time = service.get('departure_time')
        departure_str = ""
        if departure_time:
            try:
                if isinstance(departure_time, str):
                    dt = datetime.strptime(departure_time, "%Y-%m-%d %H:%M:%S.%f")
                else:
                    dt = departure_time
                departure_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            except Exception as e:
                logger.warning(f"日期格式转换错误: {e}")
                departure_str = str(departure_time)
        
        # 获取总耗卡次数 - 优先使用Excel中的记录值
        total_sessions = service.get('total_sessions', 0)
        
        # 如果total_sessions为0或不存在，使用去重后的项目数
        if not total_sessions:
            total_sessions = len(unique_items)
        
        total_amount = service.get('total_amount', 0)
        satisfaction = service.get('satisfaction', '')
        
        # 按正确格式处理项目详情：项目内容\操作美容师\耗卡金额\是否指定
        project_details = []
        for item in unique_items:
            beautician = item.get('beautician_name', '')
            project_name = item.get('project_name', '')
            # 优先使用unit_price，如果为空则尝试使用card_deduction
            amount = item.get('unit_price', 0)
            if amount is None or amount == 0:
                amount = item.get('card_deduction', 0)
            if amount is None:
                amount = 0
            
            # 使用实际的is_specified值，不再默认为False
            is_specified = "✓指定" if item.get('is_specified', False) else "未指定"
            
            detail = f"{project_name} - {beautician} - {amount}元 - {is_specified}"
            project_details.append(detail)
        
        # 保证有5个项目详情字段
        while len(project_details) < 5:
            project_details.append("")
        
        # 限制为5个项目详情
        project_details = project_details[:5]
        
        # 构建表格行
        row = f"| {arrival_time} | {departure_str} | {total_sessions} | {total_amount} | {satisfaction} | {' | '.join(project_details)} |"
        md_table.append(row)
    
    return "\n".join(md_table)

def generate_customer_report(customer_id, db_manager=None):
    """
    生成客户报告
    """
    if not db_manager:
        db_manager = DatabaseManager()
    
    logger.info(f"开始生成客户 {customer_id} 的报告")
    
    # 获取客户信息
    customer = db_manager.get_customer(customer_id)
    if not customer:
        logger.error(f"客户不存在: {customer_id}")
        return False
    
    # 获取健康档案
    health_record = db_manager.get_health_record(customer_id)
    
    # 获取消费记录
    consumptions = db_manager.get_consumptions(customer_id)
    
    # 获取服务记录
    services = db_manager.get_services(customer_id)
    
    # 获取沟通记录
    communications = db_manager.get_communications(customer_id)
    
    # 生成MD报告
    md_content = []
    
    # 客户基本信息
    md_content.append(f"## 客户: {customer.get('name', '')} ({customer_id})\n")
    md_content.append("### 基本信息\n")
    md_content.append("| 字段 | 值 |")
    md_content.append("|------|----|")
    md_content.append(f"| 姓名 | {customer.get('name', '')} |")
    md_content.append(f"| 性别 | {customer.get('gender', '')} |")
    md_content.append(f"| 年龄 | {customer.get('age', '')} |")
    md_content.append(f"| 门店归属 | {customer.get('store', '')} |")
    md_content.append(f"| 籍贯 | {customer.get('hometown', '')} |")
    md_content.append(f"| 现居地 | {customer.get('residence', '')} |")
    md_content.append(f"| 居住时长 | {customer.get('residence_years', '')} |")
    md_content.append(f"| 家庭成员构成 | {customer.get('family_structure', '')} |")
    md_content.append(f"| 家庭人员年龄分布 | {customer.get('family_age_distribution', '')} |")
    md_content.append(f"| 家庭居住情况 | {customer.get('living_condition', '')} |")
    md_content.append(f"| 性格类型标签 | {customer.get('personality_tags', '')} |")
    md_content.append(f"| 消费决策主导 | {customer.get('consumption_decision', '')} |")
    md_content.append(f"| 兴趣爱好 | {customer.get('hobbies', '')} |")
    md_content.append(f"| 作息规律 | {customer.get('routine', '')} |")
    md_content.append(f"| 饮食偏好 | {customer.get('diet_preference', '')} |")
    md_content.append(f"| 职业 | {customer.get('occupation', '')} |")
    md_content.append(f"| 单位性质 | {customer.get('work_unit_type', '')} |")
    md_content.append(f"| 年收入 | {customer.get('annual_income', '')} |")
    
    # 健康档案
    if health_record:
        md_content.append("\n### 健康档案\n")
        md_content.append("| 类别 | 字段 | 值 |")
        md_content.append("|------|------|----|")
        md_content.append(f"| 皮肤状况 | 肤质类型 | {health_record.get('skin_type', '')} |")
        md_content.append(f"| 皮肤状况 | 水油平衡 | {health_record.get('oil_water_balance', '')} |")
        md_content.append(f"| 皮肤状况 | 毛孔与黑头 | {health_record.get('pores_blackheads', '')} |")
        md_content.append(f"| 皮肤状况 | 皱纹与纹理 | {health_record.get('wrinkles_texture', '')} |")
        md_content.append(f"| 皮肤状况 | 色素沉着 | {health_record.get('pigmentation', '')} |")
        md_content.append(f"| 皮肤状况 | 光老化与炎症 | {health_record.get('photoaging_inflammation', '')} |")
        md_content.append(f"| 中医体质 | 体质类型 | {health_record.get('tcm_constitution', '')} |")
        md_content.append(f"| 中医体质 | 舌象特征 | {health_record.get('tongue_features', '')} |")
        md_content.append(f"| 中医体质 | 脉象数据 | {health_record.get('pulse_data', '')} |")
        md_content.append(f"| 生活习惯 | 作息规律 | {health_record.get('sleep_routine', '')} |")
        md_content.append(f"| 生活习惯 | 运动频率 | {health_record.get('exercise_pattern', '')} |")
        md_content.append(f"| 生活习惯 | 饮食禁忌 | {health_record.get('diet_restrictions', '')} |")
        md_content.append(f"| 护理需求 | 时间灵活度 | {health_record.get('care_time_flexibility', '')} |")
        md_content.append(f"| 护理需求 | 手法力度偏好 | {health_record.get('massage_pressure_preference', '')} |")
        md_content.append(f"| 护理需求 | 环境氛围 | {health_record.get('environment_requirements', '')} |")
        md_content.append(f"| 美容健康目标 | 短期美丽目标 | {health_record.get('short_term_beauty_goal', '')} |")
        md_content.append(f"| 美容健康目标 | 长期美丽目标 | {health_record.get('long_term_beauty_goal', '')} |")
        md_content.append(f"| 美容健康目标 | 短期健康目标 | {health_record.get('short_term_health_goal', '')} |")
        md_content.append(f"| 美容健康目标 | 长期健康目标 | {health_record.get('long_term_health_goal', '')} |")
        md_content.append(f"| 健康记录 | 医美操作史 | {health_record.get('medical_cosmetic_history', '')} |")
        md_content.append(f"| 健康记录 | 大健康服务史 | {health_record.get('wellness_service_history', '')} |")
        md_content.append(f"| 健康记录 | 过敏史 | {health_record.get('allergies', '')} |")
        md_content.append(f"| 健康记录 | 重大疾病历史 | {health_record.get('major_disease_history', '')} |")
    
    # 消费记录
    if consumptions:
        md_content.append("\n### 消费记录\n")
        md_content.append("| 消费时间 | 项目名称 | 消费金额 | 支付方式 |")
        md_content.append("|----------|----------|----------|----------|")
        
        for consumption in consumptions:
            # 格式化日期
            date_str = consumption.get('date', '')
            if date_str:
                try:
                    if isinstance(date_str, str):
                        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f")
                    else:
                        dt = date_str
                    date_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    date_str = str(date_str)
            
            md_content.append(f"| {date_str} | {consumption.get('project_name', '')} | {consumption.get('amount', 0.0)} | {consumption.get('payment_method', '')} |")
    
    # 服务记录
    md_content.append("\n### 服务记录\n")
    service_table = format_service_records(services)
    md_content.append(service_table)
    
    # 沟通记录
    if communications:
        md_content.append("\n### 沟通记录\n")
        md_content.append("| 沟通时间 | 沟通地点 | 沟通内容 |")
        md_content.append("|----------|----------|----------|")
        
        for comm in communications:
            # 格式化日期
            date_str = comm.get('communication_date', '')
            if date_str:
                try:
                    if isinstance(date_str, str):
                        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f")
                    else:
                        dt = date_str
                    date_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    date_str = str(date_str)
            
            md_content.append(f"| {date_str} | {comm.get('communication_location', '')} | {comm.get('communication_content', '')} |")
    
    # 保存到文件
    output_file = f"{customer_id}_customer_report.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md_content))
    
    logger.info(f"客户报告已生成: {output_file}")
    return output_file

if __name__ == "__main__":
    # 默认客户ID
    customer_id = "C003"
    
    # 如果有命令行参数，使用命令行参数
    if len(sys.argv) > 1:
        customer_id = sys.argv[1]
    
    # 生成报告
    generate_customer_report(customer_id)