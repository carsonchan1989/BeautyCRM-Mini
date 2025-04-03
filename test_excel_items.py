#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试Excel处理器对服务项目的处理
确保Excel清洗器能准确清洗服务项目内容
"""

import logging
import sys
import json
import os
from datetime import datetime
import pandas as pd
from server.utils.excel_processor import ExcelProcessor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ExcelItemsTest')

def test_excel_service_items():
    """测试Excel处理器对服务项目的处理"""
    logger.info("==== 开始服务项目处理测试 ====")
    
    # Excel文件路径
    excel_file = "模拟-客户信息档案.xlsx"
    
    # 检查文件是否存在
    if not os.path.exists(excel_file):
        logger.error(f"Excel文件不存在: {excel_file}")
        return False
    
    # 创建Excel处理器
    processor = ExcelProcessor()
    
    # 读取Excel文件的消耗sheet
    excel_data = pd.read_excel(excel_file, sheet_name=None)
    
    # 查找消耗表
    service_sheet = None
    for sheet_name in excel_data:
        if "消耗" in sheet_name:
            service_sheet = excel_data[sheet_name]
            logger.info(f"找到服务记录表: {sheet_name}")
            break
    
    if service_sheet is None:
        logger.error("未找到消耗表")
        return False
    
    # 处理服务记录
    logger.info("开始处理服务记录...")
    services = processor._process_services(service_sheet)
    logger.info(f"处理完成，共 {len(services)} 条服务记录")
    
    # 验证服务项目
    total_items = 0
    for i, service in enumerate(services):
        logger.info(f"服务记录 {i+1}: 客户ID={service['customer_id']}, 服务日期={service['service_date']}")
        
        service_items = service.get('service_items', [])
        if not service_items:
            logger.warning(f"服务记录 {i+1} 没有服务项目")
            continue
        
        logger.info(f"服务记录 {i+1} 包含 {len(service_items)} 个服务项目:")
        for j, item in enumerate(service_items):
            logger.info(f"  项目 {j+1}: 名称={item.get('project_name', '未知')}, "
                        f"美容师={item.get('beautician_name', '未知')}, "
                        f"金额={item.get('unit_price', 0)}, "
                        f"是否指定={item.get('is_specified', False)}")
            
            # 验证必要字段
            if not item.get('project_name'):
                logger.error(f"  项目 {j+1} 缺少项目名称")
            
            total_items += 1
    
    # 将服务记录保存到JSON文件
    with open('service_items_test.json', 'w', encoding='utf-8') as f:
        json.dump(services, f, ensure_ascii=False, indent=2, default=str)
    
    logger.info(f"服务记录已保存到 service_items_test.json")
    logger.info(f"共处理 {len(services)} 条服务记录，{total_items} 个服务项目")
    logger.info("==== 服务项目处理测试完成 ====")
    
    return True

if __name__ == "__main__":
    test_excel_service_items() 