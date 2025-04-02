#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pandas as pd
import numpy as np
from datetime import datetime
import json

def read_consumption_sheet(excel_path, sheet_name='消耗'):
    """
    读取Excel文档中的消耗记录子表
    
    Args:
        excel_path: Excel文件路径
        sheet_name: 子表名称，默认为'消耗'
    
    Returns:
        consumption_records: 消耗记录字典列表
    """
    try:
        # 读取Excel文件
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        
        # 清理数据 - 删除全空行
        df = df.replace('', np.nan)
        df = df.dropna(how='all')
        
        # 映射列名 - 根据Excel表头进行调整
        column_mapping = {
            '客户ID': 'customer_id',
            '姓名': 'customer_name',
            '到店时间': 'arrival_time',
            '离店时间': 'departure_time',
            '总共卡金': 'total_card_amount',
            '服务满意度': 'satisfaction_rating',
            '项目内容': 'project_content',
            '操作美容师': 'beautician_name',
            '扣卡金额': 'card_deduction',
            '总消耗': 'total_consumption',
            '项目内容2': 'project_content2',
            '操作美容师2': 'beautician_name2',
            '扣卡金额2': 'card_deduction2',
            '总消耗2': 'total_consumption2',
            # 可以添加更多的项目列映射
        }
        
        # 重命名列名
        df = df.rename(columns={col: column_mapping.get(col, col) for col in df.columns})
        
        # 转换日期时间格式
        for date_col in ['arrival_time', 'departure_time']:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                df[date_col] = df[date_col].dt.strftime('%Y/%m/%d %H:%M')
        
        # 处理数值列，确保是浮点数
        for num_col in ['total_card_amount', 'satisfaction_rating', 'card_deduction', 'total_consumption',
                      'card_deduction2', 'total_consumption2']:
            if num_col in df.columns:
                df[num_col] = pd.to_numeric(df[num_col], errors='coerce')
        
        # 转换为字典列表
        records = df.to_dict(orient='records')
        
        # 进一步处理数据 - 拆分为基础记录和项目明细
        consumption_records = []
        
        for record in records:
            # 创建基础消费记录
            base_record = {
                'customer_id': record.get('customer_id'),
                'customer_name': record.get('customer_name'),
                'arrival_time': record.get('arrival_time'),
                'departure_time': record.get('departure_time'),
                'total_card_amount': record.get('total_card_amount'),
                'satisfaction_rating': record.get('satisfaction_rating'),
                'projects': []
            }
            
            # 添加项目1
            if record.get('project_content'):
                project1 = {
                    'project_name': record.get('project_content'),
                    'beautician_name': record.get('beautician_name'),
                    'card_deduction': record.get('card_deduction'),
                    'consumption': record.get('total_consumption')
                }
                base_record['projects'].append(project1)
            
            # 添加项目2
            if record.get('project_content2'):
                project2 = {
                    'project_name': record.get('project_content2'),
                    'beautician_name': record.get('beautician_name2'),
                    'card_deduction': record.get('card_deduction2'),
                    'consumption': record.get('total_consumption2')
                }
                base_record['projects'].append(project2)
            
            # 添加额外项目（如果存在）
            # 这里可以扩展添加更多的项目列
            
            consumption_records.append(base_record)
        
        return consumption_records
    
    except Exception as e:
        print(f"读取Excel消耗表格出错: {str(e)}")
        return []

def main():
    """测试函数"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(current_dir, "模拟-客户信息档案.xlsx")
    
    if not os.path.exists(excel_path):
        print(f"Excel文件不存在: {excel_path}")
        return
    
    consumption_records = read_consumption_sheet(excel_path)
    print(f"读取到 {len(consumption_records)} 条消耗记录")
    
    # 打印前3条记录示例
    for i, record in enumerate(consumption_records[:3]):
        print(f"\n记录 {i+1}:")
        print(json.dumps(record, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()