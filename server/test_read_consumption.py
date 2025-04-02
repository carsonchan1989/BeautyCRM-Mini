"""
测试从Excel中读取消费记录数据
"""
import os
import sys
import json
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path

# 确保可以导入当前目录模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from utils.consumption_excel_processor import ConsumptionExcelProcessor

def main():
    # Excel文件路径
    excel_path = Path("D:/BeautyCRM-Mini/模拟-客户信息档案.xlsx")
    
    if not excel_path.exists():
        logger.error(f"Excel文件不存在: {excel_path}")
        return
    
    logger.info(f"开始处理Excel文件: {excel_path}")
    
    # 实例化Excel处理器
    processor = ConsumptionExcelProcessor()
    
    try:
        # 读取消费子表
        consumption_data, errors = processor.read_excel(excel_path, "消耗")
        
        # 输出错误信息
        if errors:
            logger.warning(f"处理过程中出现以下错误: {errors}")
        
        # 输出基本信息
        logger.info(f"共读取到 {len(consumption_data)} 条消费记录")
        
        # 输出前5条记录
        if consumption_data:
            logger.info("前5条记录:")
            for i, record in enumerate(consumption_data[:5]):
                logger.info(f"记录 {i+1}: {record}")
        else:
            logger.warning("未读取到任何消费记录")
        
        # 保存为JSON文件以便查看
        output_path = Path("consumption_data.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(consumption_data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"数据已保存到: {output_path}")
        
        # 测试导入到数据库
        from app import create_app
        from models import db, Consumption, Customer
        
        app = create_app()
        with app.app_context():
            # 检查已有客户
            customers = Customer.query.count()
            logger.info(f"数据库中有 {customers} 位客户")
            
            # 如果没有客户，先添加一个测试客户
            if customers == 0:
                test_customer = Customer(
                    id="C20250001",
                    name="测试客户",
                    gender="女",
                    age=30,
                    store="总店"
                )
                db.session.add(test_customer)
                db.session.commit()
                logger.info(f"已添加测试客户: {test_customer.id}")
            
            # 导入消费记录
            for record in consumption_data:
                # 检查客户ID是否存在
                customer_id = record.get("customer_id")
                if not customer_id:
                    logger.warning(f"跳过无客户ID的记录: {record}")
                    continue
                
                # 检查客户是否存在
                customer = Customer.query.filter_by(id=customer_id).first()
                if not customer:
                    logger.warning(f"客户不存在，无法导入记录: {customer_id}")
                    continue
                
                # 创建消费记录
                try:
                    # 处理日期格式
                    if 'start_time' in record and record['start_time']:
                        start_time = datetime.strptime(record['start_time'], '%Y-%m-%d %H:%M:%S')
                        record['start_time'] = start_time
                    
                    if 'end_time' in record and record['end_time']:
                        end_time = datetime.strptime(record['end_time'], '%Y-%m-%d %H:%M:%S')
                        record['end_time'] = end_time
                    
                    consumption = Consumption(**record)
                    db.session.add(consumption)
                    logger.info(f"成功创建消费记录: {record}")
                except Exception as e:
                    logger.error(f"创建消费记录失败: {str(e)}")
                    logger.error(f"记录数据: {record}")
                
            # 提交事务
            db.session.commit()
            logger.info("消费记录已成功导入数据库")
            
            # 验证导入结果
            count = Consumption.query.count()
            logger.info(f"数据库中现有 {count} 条消费记录")
            
    except Exception as e:
        logger.exception(f"处理Excel文件时出错: {e}")

if __name__ == "__main__":
    main()