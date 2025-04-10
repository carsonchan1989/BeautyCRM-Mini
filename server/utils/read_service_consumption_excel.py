"""
读取服务消耗数据并处理 - 美容客户管理系统

此脚本专门处理Excel中的"消耗"表数据，清洗并结构化为服务记录。
"""

import os
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import re
from typing import Dict, List, Optional, Any, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_date(date_str: Any) -> Optional[datetime]:
    """解析多种格式的日期字符串为datetime对象"""
    if pd.isna(date_str):
        return None
        
    # 处理pandas Timestamp类型
    if isinstance(date_str, pd.Timestamp):
        return date_str.to_pydatetime()
        
    # 处理字符串类型
    if isinstance(date_str, str):
        date_str = date_str.strip()
        
        # 尝试多种日期格式
        formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%Y.%m.%d',
            '%Y年%m月%d日',
            '%m-%d-%Y',
            '%m/%d/%Y',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%Y-%m-%d %H:%M:%S',
            '%Y/%m/%d %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except (ValueError, TypeError):
                continue
                
    # 处理数值类型（Excel日期数字）
    if isinstance(date_str, (int, float)):
        try:
            # Excel日期从1900年1月1日开始计数
            # 但由于Excel的1900年2月28日和3月1日之间有一个bug，我们需要调整
            excel_epoch = datetime(1899, 12, 30)
            return excel_epoch + pd.Timedelta(days=int(date_str))
        except (ValueError, OverflowError):
            pass
            
    logger.warning(f"无法解析日期: {date_str} ({type(date_str)})")
    return None

def clean_number(value: Any) -> Optional[float]:
    """清洗数值字段为浮点数"""
    if pd.isna(value):
        return None
        
    if isinstance(value, (int, float)):
        return float(value)
        
    if isinstance(value, str):
        # 移除可能包含的货币符号和其他非数字字符
        value = re.sub(r'[^\d\.\-]', '', value)
        try:
            return float(value)
        except (ValueError, TypeError):
            pass
            
    return None

def read_consumption_excel(excel_path: str, sheet_name: str = '消耗') -> Tuple[pd.DataFrame, Dict]:
    """读取Excel消耗表并返回DataFrame和分析结果"""
    logger.info(f"开始读取Excel文件: {excel_path}, 表: {sheet_name}")
    
    try:
        # 尝试读取指定表格
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        
        # 检查是否为空DataFrame
        if df.empty:
            logger.error(f"Excel表 '{sheet_name}' 不包含数据")
            return pd.DataFrame(), {"error": f"表 '{sheet_name}' 不包含数据"}
            
        # 获取表格基本信息
        rows_count = len(df)
        columns_count = len(df.columns)
        
        logger.info(f"成功读取Excel表: {rows_count}行, {columns_count}列")
        
        # 确认表格包含客户消耗相关数据
        required_columns = ['客户ID', '顾客姓名', '消耗日期', '项目名称']
        found_required = [col for col in required_columns if any(col in c for c in df.columns)]
        
        if len(found_required) < 2:
            logger.error(f"表格缺少消耗记录必要字段: {required_columns}")
            return pd.DataFrame(), {"error": f"表格缺少消耗记录必要字段: {required_columns}"}
            
        # 返回DataFrame和基本信息
        return df, {
            "rows_count": rows_count,
            "columns_count": columns_count,
            "found_required_columns": found_required
        }
        
    except Exception as e:
        logger.error(f"读取Excel出错: {str(e)}")
        return pd.DataFrame(), {"error": str(e)}

def process_consumption_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """处理消耗表数据，返回清洗后的DataFrame和处理结果"""
    logger.info("开始处理消耗表数据")
    
    # 保存原始行数
    original_row_count = len(df)
    results = {"original_row_count": original_row_count}
    
    # 尝试标准化列名
    column_mapping = {}
    for col in df.columns:
        if '客户ID' in col or '顾客ID' in col:
            column_mapping[col] = 'customer_id'
        elif '姓名' in col or '顾客姓名' in col:
            column_mapping[col] = 'customer_name'
        elif '消耗日期' in col or '服务日期' in col or '日期' in col:
            column_mapping[col] = 'service_date'
        elif '项目名称' in col or '服务项目' in col:
            column_mapping[col] = 'service_name'
        elif '美容师' in col or '操作人员' in col or '服务人员' in col:
            column_mapping[col] = 'beautician'
        elif '耗卡金额' in col or '金额' in col:
            column_mapping[col] = 'amount'
            
    # 应用列名映射
    if column_mapping:
        df = df.rename(columns=column_mapping)
        results["column_mapping"] = column_mapping
        
    # 检查是否有必要的列
    required_cols = ['customer_id', 'service_date', 'service_name']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        logger.warning(f"缺少必要列: {missing_cols}")
        results["missing_columns"] = missing_cols
        
    # 清洗和处理数据
    clean_df = df.copy()
    
    # 1. 处理客户ID - 确保格式一致
    if 'customer_id' in clean_df.columns:
        # 确保客户ID为字符串格式
        clean_df['customer_id'] = clean_df['customer_id'].astype(str)
        # 移除可能的空格
        clean_df['customer_id'] = clean_df['customer_id'].str.strip()
        
    # 2. 处理日期
    if 'service_date' in clean_df.columns:
        clean_df['service_date'] = clean_df['service_date'].apply(parse_date)
        
    # 3. 处理金额
    if 'amount' in clean_df.columns:
        clean_df['amount'] = clean_df['amount'].apply(clean_number)
        
    # 4. 移除空行
    clean_df = clean_df.dropna(subset=['customer_id', 'service_date'], how='all')
    
    # 记录处理后的行数
    clean_row_count = len(clean_df)
    results["clean_row_count"] = clean_row_count
    results["removed_rows"] = original_row_count - clean_row_count
    
    logger.info(f"处理后: {clean_row_count}行 (移除了{original_row_count - clean_row_count}行)")
    
    return clean_df, results

def generate_service_records(df: pd.DataFrame) -> Tuple[List[Dict], List[Dict]]:
    """将消耗表数据转换为服务记录和服务项目记录"""
    logger.info("生成服务记录和服务项目数据")
    
    # 按客户ID和服务日期分组
    grouped_df = df.groupby(['customer_id', 'service_date'])
    
    service_records = []
    service_items = []
    
    for (customer_id, service_date), group in grouped_df:
        if pd.isna(customer_id) or pd.isna(service_date):
            continue
            
        # 创建服务主记录
        service_record = {
            'customer_id': customer_id,
            'service_date': service_date,
            'total_amount': group['amount'].sum() if 'amount' in group.columns else 0,
        }
        
        service_records.append(service_record)
        
        # 为每次服务创建服务项目记录
        for _, row in group.iterrows():
            service_item = {
                'customer_id': customer_id,
                'service_date': service_date,
                'service_name': row.get('service_name', '未知项目'),
                'beautician': row.get('beautician', None),
                'amount': row.get('amount', 0),
            }
            
            service_items.append(service_item)
            
    logger.info(f"生成了 {len(service_records)} 条服务记录和 {len(service_items)} 条服务项目记录")
    
    return service_records, service_items

def process_and_import_consumption_data(excel_path: str, sheet_name: str = '消耗') -> Dict:
    """处理Excel消耗表并准备导入数据"""
    # 1. 读取Excel数据
    df, read_results = read_consumption_excel(excel_path, sheet_name)
    
    if 'error' in read_results:
        return read_results
        
    # 2. 清洗和处理数据
    clean_df, process_results = process_consumption_data(df)
    
    if clean_df.empty:
        return {**read_results, **process_results, "error": "清洗后无有效数据"}
        
    # 3. 生成服务记录
    service_records, service_items = generate_service_records(clean_df)
    
    # 4. 返回处理结果和准备好的数据
    return {
        **read_results,
        **process_results,
        "service_records_count": len(service_records),
        "service_items_count": len(service_items),
        "service_records": service_records,
        "service_items": service_items
    }

def main():
    """主函数"""
    # 搜索当前目录下的Excel文件
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    excel_files = []
    
    for root, _, files in os.walk(current_dir):
        for file in files:
            if file.endswith('.xlsx') and '客户' in file and '信息' in file:
                excel_files.append(os.path.join(root, file))
                
    if not excel_files:
        logger.error("未找到客户信息相关的Excel文件")
        return
        
    excel_path = excel_files[0]
    logger.info(f"找到Excel文件: {excel_path}")
    
    # 处理消耗数据
    results = process_and_import_consumption_data(excel_path)
    
    # 打印处理结果
    if 'error' in results:
        logger.error(f"处理消耗数据出错: {results['error']}")
    else:
        logger.info(f"成功处理消耗数据:")
        logger.info(f"- 原始数据: {results.get('original_row_count', 0)}行")
        logger.info(f"- 清洗后: {results.get('clean_row_count', 0)}行")
        logger.info(f"- 生成服务记录: {results.get('service_records_count', 0)}条")
        logger.info(f"- 生成服务项目: {results.get('service_items_count', 0)}条")

if __name__ == "__main__":
    main()