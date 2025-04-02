#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
消耗记录Excel处理器
- 用于从Excel文件中读取、清洗和导入客户消耗记录数据
"""

import os
import pandas as pd
import numpy as np
import logging
import re
from datetime import datetime
from collections import defaultdict

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConsumptionExcelProcessor:
    """
    消耗记录Excel处理器类
    - 提供从Excel文件读取、清洗和处理消耗记录的功能
    """
    
    def __init__(self):
        """初始化处理器"""
        # 字段映射配置 - 用于标准化列名
        self.column_mappings = {
            # 关键字映射
            'customer_id': ['客户编号', '顾客编号', '会员编号', '客户ID', '顾客ID', '会员ID', '编号', 'ID'],
            'customer_name': ['客户姓名', '顾客姓名', '会员姓名', '姓名', '客户名称', '顾客名称'],
            'service_date': ['服务日期', '消耗日期', '到店日期', '消费日期', '时间', '日期'],
            'project_name': ['项目名称', '消耗项目', '服务项目', '项目', '产品名称'],
            'unit_price': ['单价', '项目单价', '产品单价', '价格'],
            'quantity': ['数量', '项目数量', '产品数量', '次数'],
            'card_deduction': ['卡扣金额', '扣卡金额', '消费金额', '金额', '消耗金额'],
            'beautician_name': ['服务美容师', '操作美容师', '美容师', '技师', '服务人员'],
            'operator': ['操作人员', '经手人', '录入人', '前台'],
            'payment_method': ['支付方式', '付款方式', '支付类型'],
            'remark': ['备注', '备注信息', '记录', '说明']
        }
        
        # 消耗表名可能的变体
        self.consumption_sheet_names = ['消耗', '消耗记录', '消耗明细', '服务记录', '服务明细']
    
    def find_consumption_sheet(self, excel_file):
        """
        查找消耗记录表
        """
        try:
            # 获取所有工作表
            excel = pd.ExcelFile(excel_file)
            sheets = excel.sheet_names
            
            # 尝试找到消耗记录表
            for name in self.consumption_sheet_names:
                if name in sheets:
                    return name
            
            # 如果没有找到，尝试模糊匹配
            for sheet in sheets:
                for name in self.consumption_sheet_names:
                    if name in sheet:
                        return sheet
            
            # 如果仍未找到，返回第一个表
            if sheets:
                logger.warning(f"未找到消耗记录表，将使用第一个表: {sheets[0]}")
                return sheets[0]
            
            return None
        except Exception as e:
            logger.error(f"查找消耗记录表出错: {str(e)}")
            return None
    
    def standardize_column_names(self, df):
        """
        标准化列名 - 将原始列名映射到标准列名
        """
        # 创建原始列到标准列的映射
        column_map = {}
        for standard_name, possible_names in self.column_mappings.items():
            for original_name in df.columns:
                original_name_clean = str(original_name).strip()
                # 检查原始列名是否包含可能的标准列名变体
                for possible_name in possible_names:
                    if possible_name in original_name_clean:
                        column_map[original_name] = standard_name
                        break
        
        # 如果有可以映射的列，则重命名
        if column_map:
            df = df.rename(columns=column_map)
            logger.info(f"已将以下列标准化: {column_map}")
        
        return df
    
    def clean_data(self, df):
        """
        清洗数据
        - 处理空值、格式化日期、数字等
        """
        try:
            # 复制DataFrame避免修改原始数据
            df_clean = df.copy()
            
            # 删除全空行
            df_clean = df_clean.dropna(how='all')
            
            # 处理客户ID - 确保格式一致
            if 'customer_id' in df_clean.columns:
                # 移除非字母数字字符，确保ID格式一致
                df_clean['customer_id'] = df_clean['customer_id'].astype(str).apply(
                    lambda x: re.sub(r'[^a-zA-Z0-9-]', '', x) if pd.notna(x) else x
                )
            
            # 处理服务日期 - 转换为标准日期格式
            if 'service_date' in df_clean.columns:
                # 尝试将各种日期格式转换为标准日期
                try:
                    df_clean['service_date'] = pd.to_datetime(df_clean['service_date'], errors='coerce')
                except Exception as e:
                    logger.warning(f"日期转换错误: {str(e)}")
            
            # 处理数字字段
            numeric_fields = ['unit_price', 'quantity', 'card_deduction']
            for field in numeric_fields:
                if field in df_clean.columns:
                    # 处理金额字段中的货币符号和非数字字符
                    if field in ['unit_price', 'card_deduction']:
                        df_clean[field] = df_clean[field].astype(str).apply(
                            lambda x: re.sub(r'[^\d.]', '', x) if pd.notna(x) else x
                        )
                    
                    # 转换为数值类型
                    try:
                        df_clean[field] = pd.to_numeric(df_clean[field], errors='coerce')
                        # 填充空值
                        if field == 'quantity':
                            df_clean[field] = df_clean[field].fillna(1)  # 默认数量为1
                        else:
                            df_clean[field] = df_clean[field].fillna(0)  # 默认金额为0
                    except Exception as e:
                        logger.warning(f"{field}字段转换错误: {str(e)}")
            
            # 处理其他可能的列
            text_fields = ['customer_name', 'project_name', 'beautician_name', 'operator', 'payment_method', 'remark']
            for field in text_fields:
                if field in df_clean.columns:
                    # 去除文本字段中的前后空格
                    df_clean[field] = df_clean[field].astype(str).apply(
                        lambda x: x.strip() if pd.notna(x) and x != 'nan' else None
                    )
                    
                    # 将'nan'字符串转换为None
                    df_clean[field] = df_clean[field].replace('nan', None)
            
            return df_clean
            
        except Exception as e:
            logger.error(f"数据清洗过程出错: {str(e)}")
            # 返回原始数据，以便进一步处理
            return df
    
    def process_file(self, excel_file, import_mode='add'):
        """
        处理Excel文件
        - 查找消耗表、标准化列名、清洗数据、处理记录
        
        Args:
            excel_file (str): Excel文件路径
            import_mode (str): 导入模式，可为'add'(新增)、'update'(更新)、'replace'(替换)
            
        Returns:
            dict: 处理结果，包括成功标志、记录数据和统计信息
        """
        try:
            # 确保文件存在
            if not os.path.exists(excel_file):
                return {
                    'success': False,
                    'message': f'文件不存在: {excel_file}'
                }
            
            # 查找消耗记录表
            sheet_name = self.find_consumption_sheet(excel_file)
            if not sheet_name:
                return {
                    'success': False,
                    'message': '未找到消耗记录表'
                }
            
            # 读取Excel文件
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            # 标准化列名
            df = self.standardize_column_names(df)
            
            # 清洗数据
            df = self.clean_data(df)
            
            # 统计信息
            stats = {
                'total_rows': len(df),
                'invalid_rows': 0,
                'processed_rows': 0,
                'total_amount': 0.0
            }
            
            # 验证必要的列是否存在
            required_columns = ['customer_id', 'project_name']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return {
                    'success': False,
                    'message': f'缺少必要的列: {", ".join(missing_columns)}',
                    'data': {
                        'found_columns': list(df.columns)
                    }
                }
            
            # 处理数据，合并同一客户同一天的记录
            customer_services = defaultdict(list)
            
            for _, row in df.iterrows():
                # 跳过没有客户ID或项目名称的行
                if pd.isna(row.get('customer_id')) or pd.isna(row.get('project_name')):
                    stats['invalid_rows'] += 1
                    continue
                
                # 准备记录
                customer_id = str(row.get('customer_id')).strip()
                service_date = row.get('service_date') if pd.notna(row.get('service_date')) else datetime.now()
                
                # 生成服务记录键 - 用客户ID和服务日期(精确到天)
                if isinstance(service_date, datetime):
                    date_key = service_date.strftime('%Y-%m-%d')
                else:
                    date_key = str(service_date).split(' ')[0]  # 只保留日期部分
                
                service_key = f"{customer_id}_{date_key}"
                
                # 处理项目信息
                project_item = {
                    'project_name': str(row.get('project_name')).strip(),
                    'beautician_name': row.get('beautician_name') if pd.notna(row.get('beautician_name')) else None,
                    'unit_price': float(row.get('unit_price')) if pd.notna(row.get('unit_price')) else None,
                    'quantity': int(row.get('quantity')) if pd.notna(row.get('quantity')) else 1,
                    'card_deduction': float(row.get('card_deduction')) if pd.notna(row.get('card_deduction')) else 0,
                    'remark': row.get('remark') if pd.notna(row.get('remark')) else None
                }
                
                # 添加到对应客户的服务记录中
                if service_key not in customer_services:
                    customer_services[service_key] = {
                        'customer_id': customer_id,
                        'customer_name': row.get('customer_name') if pd.notna(row.get('customer_name')) else None,
                        'service_date': service_date,
                        'operator': row.get('operator') if pd.notna(row.get('operator')) else None,
                        'payment_method': row.get('payment_method') if pd.notna(row.get('payment_method')) else None,
                        'remark': row.get('remark') if pd.notna(row.get('remark')) else None,
                        'items': []
                    }
                
                # 添加项目
                customer_services[service_key]['items'].append(project_item)
                
                # 更新统计
                stats['processed_rows'] += 1
                stats['total_amount'] += float(project_item['card_deduction']) if project_item['card_deduction'] else 0
            
            # 整理结果列表
            records = []
            for service_data in customer_services.values():
                # 计算总金额
                total_amount = sum(item['card_deduction'] for item in service_data['items'] if item['card_deduction'])
                service_data['total_amount'] = total_amount
                records.append(service_data)
            
            # 更新统计
            stats['valid_services'] = len(records)
            
            return {
                'success': True,
                'records': records,
                'stats': stats,
                'message': f'成功处理 {stats["processed_rows"]} 条记录，合并为 {len(records)} 条服务记录'
            }
            
        except Exception as e:
            logger.error(f"处理Excel文件出错: {str(e)}")
            return {
                'success': False,
                'message': f'处理Excel文件失败: {str(e)}'
            }
    
    def validate_record(self, record):
        """
        验证记录是否有效
        
        Args:
            record (dict): 记录数据
            
        Returns:
            tuple: (是否有效, 错误消息)
        """
        # 必需字段验证
        required_fields = ['customer_id', 'items']
        for field in required_fields:
            if field not in record or not record[field]:
                return False, f"缺少必需字段: {field}"
        
        # 验证项目列表
        if not isinstance(record['items'], list) or len(record['items']) == 0:
            return False, "项目列表为空或格式错误"
        
        # 验证项目中的必需字段
        for item in record['items']:
            if 'project_name' not in item or not item['project_name']:
                return False, "项目名称不能为空"
        
        return True, ""

if __name__ == "__main__":
    # 测试代码
    processor = ConsumptionExcelProcessor()
    test_file = "模拟-客户信息档案.xlsx"
    
    if os.path.exists(test_file):
        result = processor.process_file(test_file)
        if result['success']:
            print(f"成功处理文件，共 {len(result['records'])} 条记录")
            print(f"统计信息: {result['stats']}")
        else:
            print(f"处理失败: {result['message']}")
    else:
        print(f"测试文件不存在: {test_file}")