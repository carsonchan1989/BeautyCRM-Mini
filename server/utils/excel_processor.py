"""
Excel文件处理器 - 用于处理导入的Excel文件，提取数据并按照模型结构整理
专门针对"模拟-客户信息档案.xlsx"标准模板格式优化
"""
import os
import pandas as pd
import logging
import re
from datetime import datetime
import traceback

# 配置日志
logger = logging.getLogger(__name__)

def parse_date(date_str):
    """
    解析日期字符串为datetime对象
    支持多种格式的日期字符串
    """
    if not date_str or pd.isna(date_str):
        return None
    
    if isinstance(date_str, datetime):
        return date_str
    
    date_str = str(date_str).strip()
    
    # 尝试多种常见的日期格式
    formats = [
        '%Y-%m-%d %H:%M:%S',  # 2023-01-01 12:30:45
        '%Y-%m-%d %H:%M',     # 2023-01-01 12:30
        '%Y/%m/%d %H:%M:%S',  # 2023/01/01 12:30:45
        '%Y/%m/%d %H:%M',     # 2023/01/01 12:30
        '%Y-%m-%d',           # 2023-01-01
        '%Y/%m/%d',           # 2023/01/01
        '%Y年%m月%d日 %H:%M',  # 2023年01月01日 12:30
        '%Y年%m月%d日',        # 2023年01月01日
        '%m/%d/%Y',           # 01/01/2023
        '%d/%m/%Y',           # 01/01/2023
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    logger.warning(f"无法解析日期字符串: {date_str}")
    return None

class ExcelProcessor:
    """Excel文件处理器类"""
    
    def __init__(self):
        # 客户表模板字段映射 - 根据"模拟-客户信息档案.xlsx"中的客户表格式
        self.customer_fields = {
            '客户ID': 'id',  # 直接使用Excel中的客户ID
            '姓名': 'name',
            '性别': 'gender',
            '年龄': 'age',
            '门店归属': 'store',
            '籍贯': 'hometown',
            '现居地': 'residence',
            '居住时长': 'residence_years',
            '家庭成员构成': 'family_structure',
            '家庭人员年龄分布': 'family_age_distribution',
            '家庭居住情况': 'living_condition',
            '性格类型标签': 'personality_tags',
            '消费决策主导': 'consumption_decision',
            '风险敏感度': 'risk_sensitivity',
            '兴趣爱好': 'hobbies',
            '作息规律': 'routine',
            '饮食偏好': 'diet_preference',
            '生理期': 'menstrual_record',
            '家族遗传病史': 'family_medical_history',
            '职业': 'occupation',
            '单位性质': 'work_unit_type',
            '年收入': 'annual_income'
        }

        # 健康档案表模板字段映射 - 根据"模拟-客户信息档案.xlsx"中的健康档案表格式
        self.health_fields = {
            '客户ID': 'customer_id',  # 关联到客户表的ID
            '姓名': 'name',  # 增加姓名字段用于交叉验证
            '肤质类型': 'skin_type',
            '水油情况': 'oil_water_balance',  # 更新为与数据库模型匹配的字段名
            '毛孔与黑头': 'pores_blackheads',  # 更新为与数据库模型匹配的字段名
            '皱纹与纹理': 'wrinkles_texture',  # 更新为与数据库模型匹配的字段名
            '色素沉着': 'pigmentation',  # 更新为与数据库模型匹配的字段名
            '光老化与炎症': 'photoaging_inflammation',  # 更新为与数据库模型匹配的字段名
            '中医体质类型': 'tcm_constitution',
            '舌象特征': 'tongue_features',  # 更新为与数据库模型匹配的字段名
            '脉象数据': 'pulse_data',  # 更新为与数据库模型匹配的字段名
            '作息规律': 'sleep_routine',
            '运动频率及类型': 'exercise_pattern',
            '饮食禁忌/偏好': 'diet_restrictions',  # 更新为与数据库模型匹配的字段名
            '护理时间灵活度': 'care_time_flexibility',  # 更新为与数据库模型匹配的字段名
            '手法力度偏好': 'massage_pressure_preference',  # 更新为与数据库模型匹配的字段名
            '环境氛围要求': 'environment_requirements',
            '短期美丽目标': 'short_term_beauty_goal',
            '长期美丽目标': 'long_term_beauty_goal',
            '短期健康目标': 'short_term_health_goal',
            '长期健康目标': 'long_term_health_goal',
            '医美操作史': 'medical_cosmetic_history',  # 更新为与数据库模型匹配的字段名
            '大健康服务史': 'wellness_service_history',  # 更新为与数据库模型匹配的字段名
            '重大疾病历史': 'major_disease_history',
            '过敏史': 'allergies'  # 更新为与数据库模型匹配的字段名
        }

        # 消费记录表模板字段映射 - 根据"模拟-客户信息档案.xlsx"中的消费表格式
        self.consumption_fields = {
            '客户ID': 'customer_id',  # 关联到客户表的ID
            '姓名': 'name',  # 增加姓名字段用于交叉验证
            '消费时间': 'date',
            '日期': 'date',  # 增加日期字段别名匹配
            '项目名称': 'project_name',  # 更新为与数据库模型匹配的字段名
            '消费金额': 'amount',
            '支付方式': 'payment_method',
            '总次数': 'total_sessions',  # 更新为与数据库模型匹配的字段名
            '耗卡完成时间': 'completion_date',
            '项目满意度': 'satisfaction'
        }

        # 服务记录表模板字段映射 - 根据"模拟-客户信息档案.xlsx"中的消耗表格式
        self.service_fields = {
            '客户ID': 'customer_id',  # 关联到客户表的ID
            '姓名': 'name',  # 增加姓名字段用于交叉验证
            '到店时间': 'service_date',  # 更新为与数据库模型匹配的字段名
            '离店时间': 'departure_time',
            '总耗卡金额': 'total_amount',  # 更新为与数据库模型匹配的字段名
            '服务满意度': 'satisfaction_rating',  # 更新为与数据库模型匹配的字段名
            '项目内容': 'project_name',  # 更新为与数据库模型匹配的字段名
            '操作美容师': 'beautician_name',  # 更新为与数据库模型匹配的字段名
            '耗卡金额': 'unit_price',  # 更新为与数据库模型匹配的字段名
            '是否指定': 'is_specified',
            '总次数': 'total_sessions'  # 添加总次数字段
        }

        # 沟通记录表模板字段映射 - 根据"模拟-客户信息档案.xlsx"中的沟通记录表格式
        self.communication_fields = {
            '客户ID': 'customer_id',  # 关联到客户表的ID
            '姓名': 'name',  # 增加姓名字段用于交叉验证
            '沟通时间': 'comm_time',
            '沟通地点': 'comm_location',
            '沟通主要内容': 'comm_content',
            '是否需要跟进': 'follow_up_needed',
            '沟通人员': 'staff'
        }

    def process_file(self, filepath):
        """处理Excel文件

        Args:
            filepath: Excel文件路径

        Returns:
            dict: 包含处理后数据的字典
        """
        logger.info(f"开始处理Excel文件: {filepath}")

        if not os.path.exists(filepath):
            logger.error(f"文件不存在: {filepath}")
            raise FileNotFoundError(f"文件不存在: {filepath}")

        try:
            # 读取Excel文件的所有sheet
            logger.info(f"使用pandas读取Excel文件: {filepath}")
            excel_data = pd.read_excel(filepath, sheet_name=None)

            # 输出读取到的sheet名称
            sheet_names = list(excel_data.keys())
            logger.info(f"读取到的Sheet页: {sheet_names}")

            processed_data = {
                'customers': [],
                'health_records': [],
                'consumptions': [],
                'services': [],
                'communications': []
            }

            # 检查并处理客户信息sheet - 根据Excel中的表名调整
            for sheet_name in sheet_names:
                if '客户' in sheet_name and ('基本' in sheet_name or '基础' in sheet_name):
                    logger.info(f"开始处理'{sheet_name}'Sheet页")
                    df = excel_data[sheet_name]
                    logger.info(f"'{sheet_name}'列名: {list(df.columns)}")
                    customers = self._process_customers(df)
                    processed_data['customers'] = customers
                    logger.info(f"处理客户信息完成，共{len(customers)}条记录")
                    break
            else:
                # 如果没有找到包含"基本"或"基础"的客户表，尝试直接使用"客户"表
                for sheet_name in sheet_names:
                    if sheet_name == '客户':
                        logger.info(f"尝试使用'{sheet_name}'Sheet页作为客户信息表")
                        df = excel_data[sheet_name]
                        logger.info(f"'{sheet_name}'列名: {list(df.columns)}")
                        customers = self._process_customers(df)
                        processed_data['customers'] = customers
                        logger.info(f"处理客户信息完成，共{len(customers)}条记录")
                        break
                else:
                    logger.warning("没有找到包含客户基本信息的Sheet页")

            # 处理健康档案sheet - 根据Excel中的表名调整
            for sheet_name in sheet_names:
                if '健康' in sheet_name or '档案' in sheet_name:
                    logger.info(f"开始处理'{sheet_name}'Sheet页")
                    df = excel_data[sheet_name]
                    health_records = self._process_health_records(df)
                    processed_data['health_records'] = health_records
                    logger.info(f"处理健康档案完成，共{len(health_records)}条记录")
                    break
            else:
                logger.warning("没有找到包含健康档案的Sheet页")

            # 处理消费记录sheet - 根据Excel中的表名调整
            for sheet_name in sheet_names:
                if '消费' in sheet_name and '记录' in sheet_name:
                    logger.info(f"开始处理'{sheet_name}'Sheet页")
                    df = excel_data[sheet_name]
                    consumptions = self._process_consumptions(df)
                    processed_data['consumptions'] = consumptions
                    logger.info(f"处理消费记录完成，共{len(consumptions)}条记录")
                    break
            else:
                # 如果没有找到包含"消费记录"的Sheet页，尝试直接使用"消费"表
                for sheet_name in sheet_names:
                    if sheet_name == '消费' or '消费' in sheet_name:
                        logger.info(f"尝试使用'{sheet_name}'Sheet页作为消费记录表")
                        df = excel_data[sheet_name]
                        consumptions = self._process_consumptions(df)
                        processed_data['consumptions'] = consumptions
                        logger.info(f"处理消费记录完成，共{len(consumptions)}条记录")
                        break
                else:
                    logger.warning("没有找到包含消费记录的Sheet页")

            # 处理服务记录sheet - 根据Excel中的表名调整
            for sheet_name in sheet_names:
                if '消耗' in sheet_name or ('服务' in sheet_name and '记录' in sheet_name):
                    logger.info(f"开始处理'{sheet_name}'Sheet页")
                    df = excel_data[sheet_name]
                    services = self._process_services(df)
                    processed_data['services'] = services
                    logger.info(f"处理服务记录完成，共{len(services)}条记录")
                    break
            else:
                logger.warning("没有找到包含服务记录的Sheet页")

            # 处理沟通记录sheet - 根据Excel中的表名调整
            for sheet_name in sheet_names:
                if '沟通' in sheet_name and '记录' in sheet_name:
                    logger.info(f"开始处理'{sheet_name}'Sheet页")
                    df = excel_data[sheet_name]
                    communications = self._process_communications(df)
                    processed_data['communications'] = communications
                    logger.info(f"处理沟通记录完成，共{len(communications)}条记录")
                    break
            else:
                logger.warning("没有找到包含沟通记录的Sheet页")

            # 输出处理统计信息
            counts = {
                '客户数量': len(processed_data['customers']),
                '健康档案数量': len(processed_data['health_records']),
                '消费记录数量': len(processed_data['consumptions']),
                '服务记录数量': len(processed_data['services']),
                '沟通记录数量': len(processed_data['communications']),
            }
            logger.info(f"Excel文件处理统计: {counts}")

            logger.info(f"Excel文件处理完成: {filepath}")
            return processed_data

        except Exception as e:
            logger.error(f"Excel文件处理错误: {str(e)}", exc_info=True)
            raise e

    def _process_customers(self, df):
        """
        处理客户数据 DataFrame
        """
        logger.info("开始处理客户数据")
        logger.info(f"DataFrame形状: {df.shape}")
        
        # 打印前几行数据的信息，帮助调试
        logger.info(f"DataFrame前2行数据类型: {df.dtypes}")
        logger.info(f"DataFrame前2行数据: \n{df.head(2)}")
        
        # 检查第一行是否为标题行
        first_row = df.iloc[0].astype(str).tolist()
        logger.info(f"第一行内容: {first_row}")
        
        if any('客户ID' in str(val) or '姓名' in str(val) for val in first_row):
            logger.info("第一行是标题行，将作为新的列名")
            columns = df.iloc[0].astype(str).tolist()
            df = df[1:]  # 删除旧标题行
            df.columns = columns  # 设置新标题行
            df = df.reset_index(drop=True)  # 重置索引
            logger.info(f"新列名: {list(df.columns)}")
        
        customers = []
        skipped_count = 0
        
        for i, row in df.iterrows():
            customer = {}
            
            # 检查客户ID
            customer_id = row.get('客户ID')
            if customer_id is None or pd.isna(customer_id) or (isinstance(customer_id, str) and customer_id.strip() in ['客户ID', 'ID', '']):
                logger.warning(f"跳过第{i+1}行：客户ID为空或无效")
                skipped_count += 1
                continue
            
            # 确保ID是字符串
            customer_id = str(customer_id).strip()
            logger.info(f"处理客户ID: {customer_id}")
            
            # 映射字段
            for excel_field, db_field in self.customer_fields.items():
                for col in df.columns:
                    if excel_field in str(col):
                        value = row.get(col)
                        
                        # 处理常见的空值情况
                        if value is None or pd.isna(value):
                            customer[db_field] = None
                            continue
                            
                        # 处理数值型字段
                        if db_field == 'age' and not pd.isna(value):
                            try:
                                customer[db_field] = int(value) if pd.notna(value) else None
                            except (ValueError, TypeError):
                                logger.warning(f"无法将年龄值转换为整数: {value}")
                                customer[db_field] = None
                        else:
                            customer[db_field] = str(value).strip() if pd.notna(value) else None
                        
                        break  # 找到匹配的列后不再继续查找
            
            # 添加客户记录
            customers.append(customer)
        
        logger.info(f"处理完成: 共处理{len(customers)}条客户记录，跳过{skipped_count}条无效记录")
        
        # 记录一些处理后的客户ID信息以便调试
        if customers:
            sample_ids = [customer.get('id') for customer in customers[:min(3, len(customers))]]
            logger.info(f"处理后的客户ID样本: {sample_ids}")
        
        return customers

    def _process_health_records(self, df):
        """处理健康档案记录"""
        logger.info("开始处理健康档案记录")
        
        # 检查头部行是否是标题
        if df.shape[0] > 0 and isinstance(df.iloc[0, 0], str) and ('客户ID' in df.iloc[0, 0] or 'ID' in df.iloc[0, 0]):
            logger.info("检测到第一行是标题行，将其作为新的列名")
            # 将首行设为表头
            new_header = df.iloc[0]
            df = df[1:]  # 删除旧标题行
            df.columns = new_header  # 设置新标题行
            df = df.reset_index(drop=True)  # 重置索引
            logger.info(f"新的列名: {list(df.columns)}")

        # 反向映射中文列名到英文字段
        df = self._rename_columns(df, self.health_fields)

        # 转换为字典列表
        health_records = []
        for _, row in df.iterrows():
            # 验证是否有客户ID
            if pd.isna(row.get('customer_id')):
                logger.warning(f"跳过没有客户ID的健康记录行: {row.to_dict()}")
                continue
                
            # 转换并清洗数据
            record = {}
            for field, value in row.items():
                # 跳过不在字段映射中的列，但保留customer_id和name
                if field not in self.health_fields.values() and field not in ['customer_id', 'name']:
                    continue
                
                # 处理空值
                if pd.isna(value):
                    record[field] = None
                    continue
                
                # 清洗数据
                if field == 'customer_id':
                    # 确保客户ID是字符串格式
                    record[field] = str(value).strip()
                else:
                    # 其他字段保持原样，但确保字符串类型
                    record[field] = str(value) if isinstance(value, (str, int, float)) else None
            
            health_records.append(record)
            
        logger.info(f"处理健康档案记录完成，共{len(health_records)}条记录")
        return health_records

    def _process_consumptions(self, df):
        """处理消费记录"""
        logger.info("开始处理消费记录")
        
        # 检查头部行是否是标题
        if df.shape[0] > 0 and isinstance(df.iloc[0, 0], str) and ('客户ID' in df.iloc[0, 0] or 'ID' in df.iloc[0, 0]):
            logger.info("检测到第一行是标题行，将其作为新的列名")
            # 将首行设为表头
            new_header = df.iloc[0]
            df = df[1:]  # 删除旧标题行
            df.columns = new_header  # 设置新标题行
            df = df.reset_index(drop=True)  # 重置索引
            logger.info(f"新的列名: {list(df.columns)}")

        # 反向映射中文列名到英文字段
        df = self._rename_columns(df, self.consumption_fields)

        # 转换为字典列表
        consumptions = []
        for _, row in df.iterrows():
            # 验证是否有客户ID和消费时间
            if pd.isna(row.get('customer_id')) or pd.isna(row.get('date')):
                logger.warning(f"跳过没有客户ID或消费时间的消费记录行: {row.to_dict()}")
                continue
                
            # 转换并清洗数据
            consumption = {}
            for field, value in row.items():
                # 跳过不在字段映射中的列
                if field not in self.consumption_fields.values():
                    continue
                
                # 处理空值
                if pd.isna(value):
                    consumption[field] = None
                    continue
                
                # 数据处理
                if field == 'customer_id':
                    # 确保客户ID是字符串格式
                    consumption[field] = str(value).strip()
                elif field == 'date':
                    # 日期格式处理
                    try:
                        if isinstance(value, str):
                            # 尝试从字符串解析日期
                            date_formats = ['%Y/%m/%d %H:%M', '%Y-%m-%d %H:%M', '%Y/%m/%d', '%Y-%m-%d']
                            for fmt in date_formats:
                                try:
                                    consumption[field] = datetime.strptime(value, fmt)
                                    break
                                except ValueError:
                                    continue
                            else:
                                # 如果尝试所有格式失败, 记录警告并使用当前日期
                                logger.warning(f"无法解析消费时间: {value}，使用当前日期")
                                consumption[field] = datetime.now()
                        else:
                            # 尝试直接使用pandas日期类型
                            consumption[field] = pd.to_datetime(value).to_pydatetime()
                    except Exception as e:
                        logger.warning(f"处理消费时间异常: {str(e)}，使用当前日期")
                        consumption[field] = datetime.now()
                elif field == 'amount':
                    # 金额格式处理
                    try:
                        consumption[field] = float(value) if not pd.isna(value) else None
                    except (ValueError, TypeError):
                        logger.warning(f"金额值无法转换为浮点数: {value}，设为None")
                        consumption[field] = None
                elif field == 'total_sessions':
                    # 总次数格式处理 - 改进此处逻辑
                    try:
                        # 尝试从字符串中提取数字部分（如"6次"中的"6"）
                        if isinstance(value, str) and "次" in value:
                            sessions_str = value.replace("次", "").strip()
                            consumption[field] = int(sessions_str)
                        elif isinstance(value, (int, float)):
                            consumption[field] = int(value)
                        else:
                            consumption[field] = int(value) if not pd.isna(value) else None
                        logger.info(f"提取总次数: 原始值 {value} -> {consumption[field]}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"总次数值无法转换为整数: {value}, 错误: {str(e)}，设为None")
                        consumption[field] = None
                elif field == 'completion_date':
                    # 日期格式处理
                    try:
                        if isinstance(value, str):
                            # 尝试从字符串解析日期
                            date_formats = ['%Y/%m/%d %H:%M', '%Y-%m-%d %H:%M', '%Y/%m/%d', '%Y-%m-%d']
                            for fmt in date_formats:
                                try:
                                    consumption[field] = datetime.strptime(value, fmt)
                                    break
                                except ValueError:
                                    continue
                            else:
                                logger.warning(f"无法解析耗卡完成时间: {value}，设为None")
                                consumption[field] = None
                        else:
                            # 尝试直接使用pandas日期类型
                            consumption[field] = pd.to_datetime(value).to_pydatetime()
                    except Exception as e:
                        logger.warning(f"处理耗卡完成时间异常: {str(e)}，设为None")
                        consumption[field] = None
                else:
                    # 其他字段保持原样，但确保字符串类型
                    consumption[field] = str(value) if isinstance(value, (str, int, float)) else None
            
            consumptions.append(consumption)
            
        logger.info(f"处理消费记录完成，共{len(consumptions)}条记录")
        return consumptions

    def _process_services(self, df):
        """
        处理服务记录数据，按照一行基础信息配合多个服务项目组的模式处理
        优化处理逻辑，使用更直接的索引方式，提高对Excel特殊结构的兼容性
        完全重构的服务记录清洗逻辑，基于测试脚本的成功导入经验
        """
        services = []
        
        try:
            # 记录DataFrame的形状和原始列名
            logger.info(f"DataFrame形状: {df.shape}")
            logger.info(f"原始列名: {list(df.columns)}")
            logger.info(f"服务记录字段映射: {self.service_fields}")
            
            # 直接使用原始数据(不使用pandas默认的列名处理)
            # 创建一个没有预设标题行的数据框
            raw_df = pd.DataFrame(df.values, columns=range(df.shape[1]))
            
            # 根据观察到的数据结构，直接使用第1行作为标题行，从第2行开始作为数据
            header_row = None
            data_start_row = 0
            
            # 检查前三行，寻找包含"客户ID"的行作为标题行
            for i in range(min(3, len(raw_df))):
                row_values = raw_df.iloc[i].tolist()
                # 检查是否包含客户ID列
                if any(["客户ID" in str(val) if not pd.isna(val) else False for val in row_values]):
                    header_row = i
                    data_start_row = i + 1
                    logger.info(f"找到标题行: 第{header_row+1}行, 数据从第{data_start_row+1}行开始")
                    logger.info(f"标题行内容: {row_values}")
                    break
            
            if header_row is None:
                logger.warning("未能找到包含'客户ID'的标题行，将使用默认处理方式")
                return services
            
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
            
            logger.info(f"使用第{data_start_row+1}行开始作为数据，第{header_row+1}行作为标题")
            
            # 导入服务记录
            imported_services = 0
            imported_items = 0
            
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
                    
                    # 解析到店时间
                    arrival_time = row[arrival_time_col]
                    if pd.isna(arrival_time):
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
                        
                        service_date = arrival_dt
                    except Exception as e:
                        logger.warning(f"解析到店时间出错 [{arrival_time}]: {str(e)}")
                        continue
                    
                    # 解析离店时间
                    departure_time = row[departure_time_col]
                    departure_time_obj = None
                    if not pd.isna(departure_time):
                        try:
                            if isinstance(departure_time, str):
                                if '/' in departure_time:
                                    departure_dt = datetime.strptime(departure_time, "%Y/%m/%d %H:%M")
                                else:
                                    departure_dt = datetime.strptime(departure_time, "%Y-%m-%d %H:%M")
                            else:
                                departure_dt = pd.to_datetime(departure_time).to_pydatetime()
                            
                            departure_time_obj = departure_dt
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
                    
                    # 创建服务项目列表
                    service_items = []
                    
                    # 记录所有项目栏位的值
                    logger.info(f"项目组数据: 项目1={row[7] if 7 < len(row) else 'N/A'}, 项目2={row[11] if 11 < len(row) else 'N/A'}, 项目3={row[15] if 15 < len(row) else 'N/A'}")
                    
                    # 处理项目组
                    for group in project_groups:
                        try:
                            # 确保索引在有效范围内
                            if group["name"] >= len(row):
                                logger.warning(f"项目名称索引 {group['name']} 超出行长度 {len(row)}")
                                continue
                            
                            project_name_val = row[group["name"]]
                            
                            # 跳过空项目
                            if pd.isna(project_name_val) or not str(project_name_val).strip():
                                continue
                            
                            project_name = str(project_name_val).strip()
                            logger.info(f"发现项目名称: {project_name}")
                            
                            # 获取美容师
                            beautician_name = ""
                            if group["beautician"] < len(row):
                                beautician_val = row[group["beautician"]]
                                if not pd.isna(beautician_val):
                                    beautician_name = str(beautician_val).strip()
                            
                            # 获取金额
                            unit_price = 0.0
                            if group["amount"] < len(row):
                                price_val = row[group["amount"]]
                                if not pd.isna(price_val):
                                    try:
                                        unit_price = float(price_val)
                                    except:
                                        logger.warning(f"解析项目金额出错 [{price_val}]")
                            
                            # 获取是否指定
                            is_specified = False
                            if group["specified"] < len(row):
                                specified_val = row[group["specified"]]
                                if not pd.isna(specified_val):
                                    if isinstance(specified_val, str):
                                        is_specified = specified_val.strip() in ['✓', '√', '是', 'Yes', 'yes', 'TRUE', 'true', 'True', '1', 'Y', 'y']
                                    else:
                                        is_specified = bool(specified_val)
                            
                            # 使用有意义的字段名存储项目数据
                            service_item = {
                                'project_name': project_name,  # 明确使用project_name作为项目名称字段
                                'beautician_name': beautician_name,
                                'unit_price': unit_price,
                                'is_specified': is_specified
                            }
                            
                            # 记录详细的项目数据转换过程
                            logger.info(f"项目数据转换: Excel项目 -> 数据库模型")
                            logger.info(f"  - 项目名称: '{project_name_val}' -> 'project_name': '{project_name}'")
                            logger.info(f"  - 美容师: '{beautician_val if not pd.isna(beautician_val) else 'N/A'}' -> 'beautician_name': '{beautician_name}'")
                            logger.info(f"  - 金额: '{price_val if not pd.isna(price_val) else 'N/A'}' -> 'unit_price': {unit_price}")
                            logger.info(f"  - 是否指定: '{specified_val if not pd.isna(specified_val) else 'N/A'}' -> 'is_specified': {is_specified}")

                            service_items.append(service_item)
                            
                            imported_items += 1
                            logger.info(f"创建服务项目: {project_name} - {beautician_name} - {unit_price}元 - {'指定' if is_specified else '未指定'}")
                        except Exception as e:
                            logger.warning(f"处理项目组时出错: {str(e)}")
                            logger.warning(f"行内容: {row}")
                            continue
                    
                    # 记录服务项目总数
                    logger.info(f"解析出服务项目数: {len(service_items)}")
                    
                    # 如果没有找到有效的项目数，则使用实际项目数
                    if total_sessions == 0 and service_items:
                        total_sessions = len(service_items)
                        logger.info(f"使用实际项目数 {total_sessions} 代替总次数")
                    
                    # 创建服务记录
                    service_record = {
                        'customer_id': customer_id,
                        'name': customer_name,
                        'service_date': service_date,
                        'departure_time': departure_time_obj,
                        'total_amount': total_amount,
                        'total_sessions': total_sessions,
                        'satisfaction_rating': satisfaction,
                        'service_items': service_items
                    }
                    
                    # 记录服务记录的字段和值
                    logger.info(f"服务记录字段映射结果:")
                    logger.info(f"  - customer_id: {customer_id}")
                    logger.info(f"  - name: {customer_name}")
                    logger.info(f"  - service_date: {service_date}")
                    logger.info(f"  - departure_time: {departure_time_obj}")
                    logger.info(f"  - total_amount: {total_amount}")
                    logger.info(f"  - total_sessions: {total_sessions}")
                    logger.info(f"  - satisfaction_rating: {satisfaction}")
                    logger.info(f"  - service_items: {len(service_items)} 项")

                    services.append(service_record)
                    
                    imported_services += 1
                    logger.info(f"创建服务记录: 客户ID={customer_id}, 项目数={len(service_items)}")
                
                except Exception as e:
                    logger.error(f"处理行 {row_idx} 时出错: {str(e)}")
                    logger.error(traceback.format_exc())
            
            logger.info(f"服务记录处理完成: 共处理 {imported_services} 条记录, {imported_items} 个服务项目")
            
        except Exception as e:
            logger.error(f"处理服务记录时出错: {str(e)}")
            logger.error(traceback.format_exc())
        
        return services

    def _get_value_safe(self, row, column):
        """安全获取DataFrame中的值，处理Series对象"""
        if column not in row.index:
            return None
        
        value = row[column]
        
        if isinstance(value, pd.Series):
            if value.empty or value.isna().all():
                return None
            # 使用第一个非空值
            for val in value:
                if not pd.isna(val):
                    return val
            return None
        
        return value if pd.notna(value) else None

    def _convert_to_boolean(self, value):
        """将值转换为布尔类型"""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        return True if str(value).strip() == "是" else False

    def _process_communications(self, df):
        """
        处理沟通记录表的数据
        """
        logger.info("开始处理沟通记录")
        communications = []
        
        try:
            # 记录DataFrame的形状和原始列名
            logger.info(f"DataFrame形状: {df.shape}")
            logger.info(f"原始列名: {list(df.columns)}")
            
            # 检查第一行是否包含标题信息
            if df.shape[0] > 0:
                first_row = df.iloc[0].tolist()
                if '客户ID' in first_row or any('沟通' in str(val) for val in first_row):
                    logger.info(f"第一行内容: {first_row}")
                    logger.info("第一行是标题行，将使用第一行作为新的列名")
                    
                    # 使用第一行作为新的列名
                    df.columns = first_row
                    # 删除第一行，因为它已经成为列名
                    df = df.iloc[1:].reset_index(drop=True)
            
            logger.info(f"处理后的列名: {list(df.columns)}")
            
            # 字段映射 - 按照Excel表格原有结构和数据库模型进行映射
            field_mapping = {
                '客户ID': 'customer_id',
                '沟通时间': 'communication_date',  # 修改：直接映射到数据库字段
                '沟通方式': 'communication_type',   # 添加：沟通方式字段
                '沟通地点': 'communication_location',  # 添加：沟通地点字段
                '员工': 'staff_name',              # 添加：员工名称对应staff_name
                '沟通内容': 'communication_content', # 添加：沟通内容字段
                '客户反馈': 'customer_feedback',     # 添加：客户反馈字段
                '后续跟进': 'follow_up_action'       # 添加：后续跟进字段
            }
            
            logger.info(f"沟通记录字段映射: {field_mapping}")
            
            # 处理每一行
            for idx, row in df.iterrows():
                try:
                    # 获取客户ID
                    customer_id = None
                    for col in df.columns:
                        if '客户ID' in col or col.lower() == 'id':
                            customer_id = str(row[col]).strip() if pd.notna(row[col]) else None
                            break
                    
                    if not customer_id:
                        logger.warning(f"行 {idx}: 缺少客户ID，跳过")
                        continue
                    
                    # 创建记录
                    record = {'customer_id': customer_id}
                    
                    # 添加其他字段
                    for orig_field, mapped_field in field_mapping.items():
                        if orig_field == '客户ID':  # 客户ID已处理
                            continue
                        
                        # 查找包含字段名的列
                        matching_cols = [col for col in df.columns if orig_field in col]
                        if matching_cols:
                            field_value = row[matching_cols[0]]
                            
                            # 特殊处理日期时间字段
                            if mapped_field == 'communication_date' and pd.notna(field_value):
                                try:
                                    # 尝试解析日期时间
                                    if isinstance(field_value, (datetime, pd.Timestamp)):
                                        record[mapped_field] = field_value
                                    else:
                                        record[mapped_field] = self._parse_datetime(field_value)
                                except Exception as e:
                                    logger.warning(f"行 {idx}: 沟通时间解析失败 '{field_value}', 使用当前时间")
                                    record[mapped_field] = datetime.now()
                            elif pd.notna(field_value):
                                record[mapped_field] = str(field_value).strip()
                    
                    # 检查沟通方式字段（从列名中获取）
                    if 'communication_type' not in record:
                        for col in df.columns:
                            if any(type_name in col for type_name in ['电话', '门店', '微信', '短信', '其他']):
                                if pd.notna(row[col]) and row[col]:
                                    record['communication_type'] = col
                                    break
                    
                    # 确保必要字段存在
                    if 'communication_date' not in record:
                        logger.warning(f"行 {idx}: 缺少沟通时间，使用当前时间")
                        record['communication_date'] = datetime.now()
                                
                    # 处理员工字段
                    if 'staff_name' not in record:
                        for col in df.columns:
                            if any(name in col for name in ['员工', '接待人', '负责人']):
                                if pd.notna(row[col]):
                                    record['staff_name'] = str(row[col]).strip()
                                    break
                    
                    # 处理沟通内容
                    if 'communication_content' not in record:
                        for col in df.columns:
                            if any(content in col for content in ['内容', '沟通记录', '交流']):
                                if pd.notna(row[col]):
                                    record['communication_content'] = str(row[col]).strip()
                                    break
                    
                    communications.append(record)
                    logger.debug(f"行 {idx}: 成功处理客户 {customer_id} 的沟通记录")
                
                except Exception as e:
                    logger.error(f"处理行 {idx} 时出错: {str(e)}")
            
            logger.info(f"沟通记录处理完成，共 {len(communications)} 条记录")
        
        except Exception as e:
            logger.error(f"处理沟通记录时出错: {str(e)}")
        
        return communications

    def _parse_datetime(self, value):
        """解析日期时间值"""
        # 处理Series对象
        if isinstance(value, pd.Series):
            if value.empty or value.isna().all():
                return None
            # 使用第一个非空值
            for val in value:
                if not pd.isna(val):
                    return self._parse_datetime(val)
            return None
            
        if pd.isna(value):
            return None
            
        try:
            if isinstance(value, str):
                # 尝试从字符串解析日期
                date_formats = ['%Y/%m/%d %H:%M', '%Y-%m-%d %H:%M', '%Y/%m/%d', '%Y-%m-%d']
                for fmt in date_formats:
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
                # 如果标准格式都失败，尝试更灵活的格式
                try:
                    return pd.to_datetime(value).to_pydatetime()
                except:
                    logger.warning(f"无法解析日期时间: {value}")
                    return None
            elif isinstance(value, (datetime, pd.Timestamp)):
                return pd.to_datetime(value).to_pydatetime()
            else:
                return None
        except Exception as e:
            logger.warning(f"处理日期时间异常: {str(e)}")
            return None
            
    def _parse_float(self, value):
        """解析浮点数值"""
        # 处理Series对象
        if isinstance(value, pd.Series):
            if value.empty or value.isna().all():
                return None
            # 使用第一个非空值
            for val in value:
                if not pd.isna(val):
                    return self._parse_float(val)
            return None
            
        if pd.isna(value):
            return None
            
        try:
            return float(value)
        except (ValueError, TypeError):
            # 尝试处理字符串中的数字
            if isinstance(value, str):
                # 删除非数字字符（保留小数点）
                cleaned = ''.join(c for c in value if c.isdigit() or c == '.')
                try:
                    return float(cleaned) if cleaned else None
                except:
                    return None
            return None
            
    def _convert_amount(self, value):
        """
        从字符串或数值转换为金额浮点数
        """
        if pd.isna(value):
            return None
        
        try:
            if isinstance(value, (int, float)):
                return float(value)
            
            # 字符串处理
            if isinstance(value, str):
                # 移除货币符号和千位分隔符
                amount_str = value.replace('¥', '').replace('元', '').replace(',', '').strip()
                # 尝试转换为浮点数
                return float(amount_str)
            
            return None
        except (ValueError, TypeError):
            logger.warning(f"金额转换失败: {value}")
            return None
            
    def _parse_boolean(self, value):
        """解析布尔值，识别各种表示"是"的方式"""
        if pd.isna(value):
            return False
            
        if isinstance(value, bool):
            return value
            
        if isinstance(value, (int, float)):
            return value == 1
            
        if isinstance(value, str):
            true_values = ['1', 'true', 'yes', '是', 't', 'y', '√', '✓', '指定']
            return value.lower() in true_values
            
        return False

    def _rename_columns(self, df, field_mapping):
        """将DataFrame的列名从中文映射到英文字段名"""
        logger.info(f"原始列名: {list(df.columns)}")
        
        # 创建反向映射字典
        reverse_mapping = {}
        for zh_field, en_field in field_mapping.items():
            # 添加中文字段名的精确匹配
            reverse_mapping[zh_field] = en_field
            
            # 为了提高匹配率，增加一些近似匹配
            if zh_field == '客户ID':
                reverse_mapping['ID'] = en_field
                reverse_mapping['客户id'] = en_field
                reverse_mapping['顾客ID'] = en_field
                
        # 映射列名
        new_columns = []
        for col in df.columns:
            # 如果列名是数字索引，则跳过
            if isinstance(col, int):
                new_columns.append(col)
                continue
                
            # 去除可能的空格
            col_clean = col.strip() if isinstance(col, str) else col
            
            # 尝试精确匹配
            if col_clean in reverse_mapping:
                new_columns.append(reverse_mapping[col_clean])
            else:
                # 尝试部分匹配
                matched = False
                for zh_field in field_mapping.keys():
                    if isinstance(col_clean, str) and isinstance(zh_field, str) and (zh_field in col_clean or col_clean in zh_field):
                        new_columns.append(field_mapping[zh_field])
                        matched = True
                        logger.info(f"列名部分匹配: '{col_clean}' -> '{zh_field}' -> '{field_mapping[zh_field]}'")
                        break
                
                if not matched:
                    # 如果无法匹配，保留原列名
                    new_columns.append(col)
                    logger.warning(f"无法匹配列名: '{col_clean}'")
        
        # 更新DataFrame列名
        rename_dict = {old: new for old, new in zip(df.columns, new_columns)}
        df = df.rename(columns=rename_dict)
        
        logger.info(f"映射后列名: {list(df.columns)}")
        return df