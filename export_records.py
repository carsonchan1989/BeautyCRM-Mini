"""
数据验证脚本 - 导出数据库记录到Markdown文档
"""
import os
import sys
import logging
from datetime import datetime

# 设置日志级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('ExportRecords')

# 添加服务器目录到Python路径
server_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server')
sys.path.append(server_dir)

try:
    from server.app import create_app
    from server.models import Customer, HealthRecord, Consumption, Service, Communication, db
    
    # 创建Flask应用实例
    app = create_app()
    logger.info("成功导入数据库模型和创建应用实例")
except ImportError as e:
    logger.error(f"导入数据库模型失败: {e}")
    sys.exit(1)
    
def export_records():
    """导出数据库记录到Markdown文档"""
    try:
        # 在Flask应用上下文中执行数据库操作
        with app.app_context():
            # 创建markdown文档
            output_file = "database_records.md"
            with open(output_file, "w", encoding="utf-8") as f:
                # 写入标题
                f.write("# 数据库记录导出\n\n")
                f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # 导出客户记录
                customers = Customer.query.all()
                f.write(f"## 客户记录 ({len(customers)}条)\n\n")
                if customers:
                    f.write("| 客户ID | 姓名 | 性别 | 年龄 | 门店归属 |\n")
                    f.write("|--------|------|------|------|----------|\n")
                    for customer in customers:
                        f.write(f"| {customer.id} | {customer.name} | {customer.gender or ''} | {customer.age or ''} | {customer.store or ''} |\n")
                else:
                    f.write("*无客户记录*\n\n")
                
                # 导出健康档案
                health_records = HealthRecord.query.all()
                f.write(f"\n## 健康档案 ({len(health_records)}条)\n\n")
                if health_records:
                    f.write("| 客户ID | 肤质类型 | 水油平衡 | 毛孔与黑头 | 皱纹与纹理 | 色素沉着 | 中医体质类型 |\n")
                    f.write("|--------|----------|----------|------------|------------|----------|------------|\n")
                    for record in health_records:
                        # 获取客户名
                        customer = Customer.query.filter_by(id=record.customer_id).first()
                        customer_name = customer.name if customer else "未知"
                        f.write(f"| {record.customer_id} ({customer_name}) | {record.skin_type or ''} | {record.oil_water_balance or ''} | {record.pores_blackheads or ''} | {record.wrinkles_texture or ''} | {record.pigmentation or ''} | {record.tcm_constitution or ''} |\n")
                else:
                    f.write("*无健康档案记录*\n\n")
                
                # 导出消费记录
                consumptions = Consumption.query.all()
                f.write(f"\n## 消费记录 ({len(consumptions)}条)\n\n")
                if consumptions:
                    f.write("| 客户ID | 消费时间 | 项目名称 | 消费金额 | 支付方式 |\n")
                    f.write("|--------|----------|----------|----------|----------|\n")
                    for consumption in consumptions:
                        # 获取客户名
                        customer = Customer.query.filter_by(id=consumption.customer_id).first()
                        customer_name = customer.name if customer else "未知"
                        date_str = consumption.date.strftime('%Y-%m-%d %H:%M') if consumption.date else "未知"
                        f.write(f"| {consumption.customer_id} ({customer_name}) | {date_str} | {consumption.project_name or ''} | {consumption.amount or ''} | {consumption.payment_method or ''} |\n")
                else:
                    f.write("*无消费记录*\n\n")
                
                # 导出服务记录
                services = Service.query.all()
                f.write(f"\n## 服务记录 ({len(services)}条)\n\n")
                if services:
                    f.write("| 客户ID | 到店时间 | 项目内容 | 操作美容师 | 耗卡金额 |\n")
                    f.write("|--------|----------|----------|------------|----------|\n")
                    for service in services[:20]:  # 只显示前20条，避免文档过长
                        # 获取客户名
                        customer = Customer.query.filter_by(id=service.customer_id).first()
                        customer_name = customer.name if customer else "未知"
                        date_str = service.service_date.strftime('%Y-%m-%d %H:%M') if service.service_date else "未知"
                        f.write(f"| {service.customer_id} ({customer_name}) | {date_str} | {service.service_items or ''} | {service.beautician or ''} | {service.service_amount or ''} |\n")
                    if len(services) > 20:
                        f.write(f"*... 共{len(services)}条记录，仅显示前20条 ...*\n")
                else:
                    f.write("*无服务记录*\n\n")
                
                # 导出沟通记录
                communications = Communication.query.all()
                f.write(f"\n## 沟通记录 ({len(communications)}条)\n\n")
                if communications:
                    f.write("| 客户ID | 沟通时间 | 沟通地点 | 沟通内容 |\n")
                    f.write("|--------|----------|----------|----------|\n")
                    for communication in communications:
                        # 获取客户名
                        customer = Customer.query.filter_by(id=communication.customer_id).first()
                        customer_name = customer.name if customer else "未知"
                        date_str = communication.comm_time.strftime('%Y-%m-%d %H:%M') if communication.comm_time else "未知"
                        f.write(f"| {communication.customer_id} ({customer_name}) | {date_str} | {communication.comm_location or ''} | {(communication.comm_content[:30] + '...') if communication.comm_content and len(communication.comm_content) > 30 else (communication.comm_content or '')} |\n")
                else:
                    f.write("*无沟通记录*\n\n")
                    
            logger.info(f"数据库记录导出完成: {output_file}")
            print(f"数据库记录已导出到: {output_file}")
        
    except Exception as e:
        logger.exception(f"导出数据库记录失败: {e}")
        print(f"导出失败: {str(e)}")

if __name__ == "__main__":
    logger.info("开始导出数据库记录")
    export_records() 