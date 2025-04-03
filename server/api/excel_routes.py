"""
Excel导入和导出API
"""
import os
import logging
import tempfile
import pandas as pd
import json
from flask import Blueprint, request, jsonify, send_file, current_app
from datetime import datetime
from werkzeug.utils import secure_filename
import uuid

from utils.excel_processor import ExcelProcessor
# 修复导入路径问题，直接从models模块导入
from models import Customer, HealthRecord, Consumption, Service, Communication, ServiceItem

# 设置日志
logger = logging.getLogger(__name__)

# 创建蓝图
excel_bp = Blueprint('excel', __name__, url_prefix='/api/excel')

@excel_bp.route('/import', methods=['POST'])
def import_excel():
    """
    导入Excel文件
    """
    logger.info("接收到Excel导入请求")
    
    # 检查是否为调试模式
    debug_mode = request.form.get('debug') == 'true'
    if debug_mode:
        logger.setLevel(logging.DEBUG)
        logger.debug("开启调试模式")
    
    # 检查请求是否包含文件
    if 'file' not in request.files:
        logger.warning("未找到上传的文件")
        return jsonify({'error': '未找到上传的文件'}), 400
    
    file = request.files['file']
    
    # 如果用户未选择文件
    if file.filename == '':
        logger.warning("文件名为空")
        return jsonify({'error': '未选择文件'}), 400
    
    # 检查文件类型
    allowed_extensions = {'xlsx', 'xls'}
    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        logger.warning(f"不支持的文件类型: {file.filename}")
        return jsonify({'error': '只支持.xlsx和.xls格式的Excel文件'}), 400
    
    # 检查是否是预检查请求
    if request.form.get('action') == 'precheck':
        return precheck_excel(file)
    
    # 保存文件
    filename = secure_filename(file.filename)
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'excel')
    
    if not os.path.exists(upload_folder):
        logger.info(f"创建上传目录: {upload_folder}")
        os.makedirs(upload_folder)
    
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    logger.info(f"文件已保存: {filepath}")
    
    try:
        # 处理Excel文件
        processor = ExcelProcessor()
        result = processor.process_file(filepath)
        
        # 导入数据到数据库
        import_result = import_to_database(result)
        
        return jsonify({
            'filename': filename,
            'message': '文件上传和处理成功',
            'stats': {
                'customers': len(result['customers']),
                'health_records': len(result['health_records']),
                'consumptions': len(result['consumptions']),
                'services': len(result['services']),
                'communications': len(result['communications']),
            }
        }), 200
    
    except Exception as e:
        logger.exception(f"Excel处理失败: {str(e)}")
        return jsonify({'error': f'Excel处理失败: {str(e)}'}), 500

def precheck_excel(file):
    """
    预检查Excel文件
    """
    logger.info("执行Excel预检查")
    
    try:
        # 创建临时文件
        temp_fd, temp_path = tempfile.mkstemp(suffix='.xlsx')
        os.close(temp_fd)
        
        # 保存上传的文件到临时文件
        file.save(temp_path)
        logger.info(f"文件已保存到临时路径: {temp_path}")
        
        # 读取Excel文件的sheet页
        excel_data = pd.read_excel(temp_path, sheet_name=None)
        sheet_names = list(excel_data.keys())
        
        logger.info(f"检测到的Sheet页: {sheet_names}")
        
        # 预期的Sheet页
        expected_sheets = {
            '客户': ['客户', '客户基础信息', '基础信息'],
            '健康档案': ['健康', '健康档案', '健康与皮肤数据'],
            '消费记录': ['消费', '消费行为记录', '消费记录'],
            '服务记录': ['消耗', '消耗行为记录', '服务记录'],
            '沟通记录': ['沟通', '客户沟通记录', '沟通记录']
        }
        
        # 检查是否有匹配的Sheet页
        matched_sheets = []
        for category, patterns in expected_sheets.items():
            for sheet in sheet_names:
                if any(pattern in sheet for pattern in patterns):
                    matched_sheets.append(category)
                    break
        
        # 检查必要的Sheet页是否存在
        required_sheets = ['客户']
        missing_required = [sheet for sheet in required_sheets if sheet not in matched_sheets]
        
        if missing_required:
            logger.warning(f"缺少必要的Sheet页: {', '.join(missing_required)}")
            return jsonify({
                'error': f'Excel文件缺少必要的Sheet页: {", ".join(missing_required)}，至少需要包含客户信息表',
                'sheets': sheet_names
            }), 400
        
        # 检查数据样本
        sample_data = {}
        if '客户' in matched_sheets:
            for sheet_name in sheet_names:
                if any(pattern in sheet_name for pattern in expected_sheets['客户']):
                    df = excel_data[sheet_name]
                    if df.shape[0] > 0:
                        # 检查是否是标题行
                        if isinstance(df.iloc[0, 0], str) and ('客户ID' in df.iloc[0, 0] or 'ID' in df.iloc[0, 0]):
                            sample_data['customer_headers'] = df.iloc[0].tolist()
                            sample_data['customer_data'] = df.iloc[1] if df.shape[0] > 1 else None
                        else:
                            sample_data['customer_headers'] = df.columns.tolist()
                            sample_data['customer_data'] = df.iloc[0] if df.shape[0] > 0 else None
                    break
        
        # 清理临时文件
        os.unlink(temp_path)
        
        return jsonify({
            'message': '文件检查通过',
            'sheets': matched_sheets,
            'all_sheets': sheet_names,
            'stats': {
                'totalSheets': len(sheet_names),
                'matchedSheets': len(matched_sheets)
            },
            'sample': sample_data
        }), 200
    
    except Exception as e:
        logger.exception(f"Excel预检查失败: {str(e)}")
        
        # 确保清理临时文件
        try:
            if 'temp_path' in locals():
                os.unlink(temp_path)
        except:
            pass
            
        return jsonify({'error': f'Excel预检查失败: {str(e)}'}), 500

@excel_bp.route('/export', methods=['POST'])
def export_excel():
    """
    导出Excel文件
    """
    logger.info("接收到Excel导出请求")
    
    # 获取客户ID列表
    data = request.get_json()
    
    if not data:
        logger.warning("请求体为空")
        return jsonify({'error': '请求数据缺失'}), 400
    
    customer_ids = data.get('customer_ids', [])
    sections = data.get('sections', ['customer', 'health', 'consumption', 'service', 'communication'])
    
    if not customer_ids:
        logger.warning("未提供客户ID")
        return jsonify({'error': '未提供客户ID'}), 400
    
    try:
        # 创建临时目录
        export_folder = os.path.join(current_app.config['EXPORT_FOLDER'])
        
        if not os.path.exists(export_folder):
            logger.info(f"创建导出目录: {export_folder}")
            os.makedirs(export_folder)
        
        # 生成导出文件名
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        export_filename = f"客户数据导出_{timestamp}.xlsx"
        export_filepath = os.path.join(export_folder, export_filename)
        
        # 创建Excel写入器
        writer = pd.ExcelWriter(export_filepath, engine='xlsxwriter')
        
        # 导出数据
        export_data = {}
        
        # 导出客户信息
        if 'customer' in sections:
            customers_df = export_customers(customer_ids)
            customers_df.to_excel(writer, sheet_name='客户基础信息', index=False)
            export_data['customers'] = len(customers_df)
        
        # 导出健康档案
        if 'health' in sections:
            health_df = export_health_records(customer_ids)
            health_df.to_excel(writer, sheet_name='健康与皮肤数据', index=False)
            export_data['health_records'] = len(health_df)
        
        # 导出消费记录
        if 'consumption' in sections:
            consumption_df = export_consumptions(customer_ids)
            consumption_df.to_excel(writer, sheet_name='消费行为记录', index=False)
            export_data['consumptions'] = len(consumption_df)
        
        # 导出服务记录
        if 'service' in sections:
            service_df = export_services(customer_ids)
            service_df.to_excel(writer, sheet_name='消耗行为记录', index=False)
            export_data['services'] = len(service_df)
        
        # 导出沟通记录
        if 'communication' in sections:
            communication_df = export_communications(customer_ids)
            communication_df.to_excel(writer, sheet_name='客户沟通记录', index=False)
            export_data['communications'] = len(communication_df)
        
        # 保存Excel文件
        writer.close()
        
        logger.info(f"Excel导出成功: {export_filepath}")
        
        # 返回文件
        return send_file(
            export_filepath,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=export_filename
        )
    
    except Exception as e:
        logger.exception(f"Excel导出失败: {str(e)}")
        return jsonify({'error': f'Excel导出失败: {str(e)}'}), 500

# 辅助函数：导入数据到数据库
def import_to_database(data):
    """将处理后的数据导入到数据库"""
    from models import db, Customer, HealthRecord, Consumption, Service, Communication, ServiceItem
    import inspect
    
    result = {
        'customers': 0,
        'health_records': 0,
        'consumptions': 0,
        'services': 0,
        'communications': 0
    }
    
    try:
        # 获取各个模型的字段名称
        customer_fields = [column.key for column in Customer.__table__.columns]
        health_record_fields = [column.key for column in HealthRecord.__table__.columns]
        consumption_fields = [column.key for column in Consumption.__table__.columns]
        service_fields = [column.key for column in Service.__table__.columns]
        communication_fields = [column.key for column in Communication.__table__.columns]
        
        logger.info(f"Customer字段: {customer_fields}")
        logger.info(f"HealthRecord字段: {health_record_fields}")
        logger.info(f"Consumption字段: {consumption_fields}")
        logger.info(f"Service字段: {service_fields}")
        logger.info(f"Communication字段: {communication_fields}")
        
        # 导入客户数据
        for customer_data in data['customers']:
            # 跳过标题行（如果存在）
            if isinstance(customer_data.get('id'), str) and customer_data.get('id') in ['客户ID', 'ID']:
                continue
                
            if not customer_data.get('id'):
                continue
            
            # 过滤字段 - 仅保留模型中存在的字段
            filtered_data = {k: v for k, v in customer_data.items() if k in customer_fields}
            logger.info(f"过滤后的客户数据: {filtered_data.keys()}")
                
            # 检查客户是否已存在
            customer = Customer.query.filter_by(id=filtered_data['id']).first()
            
            if customer:
                # 更新现有客户
                for key, value in filtered_data.items():
                    if hasattr(customer, key) and value is not None:
                        setattr(customer, key, value)
            else:
                # 创建新客户
                customer = Customer(**filtered_data)
                db.session.add(customer)
            
            result['customers'] += 1
        
        # 导入健康档案
        for health_data in data['health_records']:
            # 跳过标题行或无效数据
            if not health_data.get('customer_id') or health_data.get('customer_id') in ['客户ID', 'ID']:
                continue
            
            # 过滤字段 - 仅保留模型中存在的字段
            filtered_data = {k: v for k, v in health_data.items() if k in health_record_fields}
            logger.info(f"过滤后的健康档案数据: {filtered_data.keys()}")
                
            # 检查健康档案是否已存在
            health_record = HealthRecord.query.filter_by(customer_id=filtered_data['customer_id']).first()
            
            if health_record:
                # 更新现有健康档案
                for key, value in filtered_data.items():
                    if hasattr(health_record, key) and value is not None:
                        setattr(health_record, key, value)
            else:
                # 创建新健康档案
                health_record = HealthRecord(**filtered_data)
                db.session.add(health_record)
            
            result['health_records'] += 1
        
        # 导入消费记录
        for consumption_data in data['consumptions']:
            # 跳过标题行或无效数据
            if not consumption_data.get('customer_id') or consumption_data.get('customer_id') in ['客户ID', 'ID']:
                continue
            
            # 过滤字段 - 仅保留模型中存在的字段
            filtered_data = {k: v for k, v in consumption_data.items() if k in consumption_fields}
            logger.info(f"过滤后的消费记录数据: {filtered_data.keys()}")
            
            # 检查必填字段
            if not filtered_data.get('date'):
                logger.warning(f"跳过缺少date的消费记录: {filtered_data}")
                continue
            
            # 创建新消费记录（不检查重复）
            consumption = Consumption(**filtered_data)
            db.session.add(consumption)
            
            result['consumptions'] += 1
        
        # 导入服务记录
        for service_data in data['services']:
            # 跳过标题行或无效数据
            if not service_data.get('customer_id') or service_data.get('customer_id') in ['客户ID', 'ID']:
                continue
            
            # 提取服务项目列表
            service_items_list = service_data.pop('service_items', []) if isinstance(service_data.get('service_items'), list) else []
            
            # 记录服务项目数据
            logger.info(f"服务项目列表大小: {len(service_items_list)}")
            if service_items_list:
                logger.info(f"服务项目样例: {service_items_list[0]}")
            
            # 过滤服务记录主表字段
            filtered_data = {k: v for k, v in service_data.items() if k in service_fields}
            logger.info(f"过滤后的服务记录数据: {filtered_data.keys()}")
            
            # 如果service_date为空，使用当前时间作为替代
            if not filtered_data.get('service_date'):
                logger.warning(f"服务记录缺少service_date字段，使用当前时间: {filtered_data}")
                filtered_data['service_date'] = datetime.now()
            
            # 检查是否已存在相同服务记录（相同客户、相同日期、相同金额）
            existing_service = Service.query.filter_by(
                customer_id=filtered_data['customer_id'],
                service_date=filtered_data['service_date']
            ).first()
            
            if existing_service:
                logger.info(f"发现已存在的服务记录: {existing_service.service_id}")
                
                # 检查是否需要添加新的服务项目 - 比较项目内容是否已存在
                if service_items_list:
                    existing_items = {(item.project_name, item.beautician_name): item 
                                     for item in existing_service.service_items}
                    
                    for item_data in service_items_list:
                        try:
                            # 确保所有必要字段存在
                            if 'project_name' not in item_data or not item_data['project_name']:
                                logger.warning(f"服务项目数据缺少project_name字段，跳过: {item_data}")
                                continue
                            
                            # 创建查找键
                            item_key = (item_data['project_name'], item_data.get('beautician_name', ''))
                            
                            # 检查是否已存在相同服务项目
                            if item_key in existing_items:
                                logger.info(f"服务项目已存在，跳过: {item_data['project_name']} - {item_data.get('beautician_name', '')}")
                                continue
                            
                            # 创建新的服务项目
                            service_item_data = {
                                'service_id': existing_service.service_id,
                                'project_name': item_data['project_name'],
                                'beautician_name': item_data.get('beautician_name', ''),
                                'unit_price': item_data.get('unit_price', 0),
                                'is_specified': item_data.get('is_specified', False)
                            }
                            
                            service_item = ServiceItem(**service_item_data)
                            db.session.add(service_item)
                            logger.info(f"为现有服务记录添加新项目: {item_data['project_name']} - {item_data.get('beautician_name', '')}")
                            
                        except Exception as e:
                            logger.error(f"为现有记录添加服务项目时出错: {str(e)}")
                            logger.error(f"原始项目数据: {item_data}")
                
            else:
                # 添加总项目数
                if 'total_project_count' in service_data:
                    filtered_data['total_project_count'] = service_data['total_project_count']
                
                # 生成服务记录ID (如果没有提供)
                if 'service_id' not in filtered_data or not filtered_data['service_id']:
                    service_id = f"S{uuid.uuid4().hex[:10].upper()}"
                    filtered_data['service_id'] = service_id
                
                # 复制客户姓名到service记录
                if 'name' in service_data and not filtered_data.get('customer_name'):
                    filtered_data['customer_name'] = service_data['name']
                
                # 创建新服务记录
                service = Service(**filtered_data)
                db.session.add(service)
                db.session.flush()  # 确保获取到新ID
                
                # 添加关联的服务项目
                if service_items_list:
                    logger.info(f"为新服务记录添加 {len(service_items_list)} 个服务项目")
                    
                    for item_data in service_items_list:
                        try:
                            # 确保所有必要字段存在
                            if 'project_name' not in item_data or not item_data['project_name']:
                                logger.warning(f"服务项目数据缺少project_name字段，跳过: {item_data}")
                                continue
                            
                            logger.info(f"处理服务项目: {item_data}")
                            
                            # 创建新的服务项目
                            service_item_data = {
                                'service_id': service.service_id,
                                'project_name': item_data['project_name'],
                                'beautician_name': item_data.get('beautician_name', ''),
                                'unit_price': item_data.get('unit_price', 0),
                                'is_specified': item_data.get('is_specified', False)
                            }
                            
                            service_item = ServiceItem(**service_item_data)
                            db.session.add(service_item)
                            logger.info(f"创建新服务项目: {item_data['project_name']} - {item_data.get('beautician_name', '')}")
                            
                        except Exception as e:
                            logger.error(f"创建服务项目时出错: {str(e)}")
                            logger.error(f"原始项目数据: {item_data}")
                        
                    # 更新服务记录的总项目数
                    if not service.total_sessions and service_items_list:
                        service.total_sessions = len(service_items_list)
                
                result['services'] += 1
        
        # 导入沟通记录
        for communication_data in data['communications']:
            # 跳过标题行或无效数据
            if not communication_data.get('customer_id') or communication_data.get('customer_id') in ['客户ID', 'ID']:
                continue
            
            # 过滤字段 - 仅保留模型中存在的字段
            filtered_data = {k: v for k, v in communication_data.items() if k in communication_fields}
            logger.info(f"过滤后的沟通记录数据: {filtered_data.keys()}")
            
            # 检查必填字段
            if not filtered_data.get('communication_date'):
                logger.warning(f"跳过缺少communication_date的沟通记录: {filtered_data}")
                continue
            
            # 创建新沟通记录
            communication = Communication(**filtered_data)
            db.session.add(communication)
            
            result['communications'] += 1
        
        # 提交所有更改
        db.session.commit()
        
        logger.info(f"数据库导入完成: {json.dumps(result)}")
        return result
    
    except Exception as e:
        db.session.rollback()
        logger.exception(f"数据库导入失败: {str(e)}")
        raise e

# 辅助函数：导出客户数据
def export_customers(customer_ids):
    """导出客户数据"""
    customers = Customer.query.filter(Customer.id.in_(customer_ids)).all()
    
    # 将客户数据转换为DataFrame
    data = []
    for customer in customers:
        data.append(customer.to_dict())
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 重命名列（英文列名转为中文）
    column_mapping = {
        'id': '客户ID',
        'name': '姓名',
        'gender': '性别',
        'age': '年龄',
        'store': '门店归属',
        'hometown': '籍贯',
        'residence': '现居地',
        'residence_years': '居住时长',
        'family_structure': '家庭成员构成',
        'family_age_distribution': '家庭人员年龄分布',
        'living_condition': '家庭居住情况',
        'personality_tags': '性格类型标签',
        'consumption_decision': '消费决策主导',
        'risk_sensitivity': '风险敏感度',
        'hobbies': '兴趣爱好',
        'routine': '作息规律',
        'diet_preference': '饮食偏好',
        'menstrual_record': '生理期记录',
        'family_medical_history': '家族遗传病史',
        'occupation': '职业',
        'work_unit_type': '单位性质',
        'annual_income': '年收入'
    }
    
    df = df.rename(columns=column_mapping)
    
    return df

# 辅助函数：导出健康档案
def export_health_records(customer_ids):
    """导出健康档案"""
    health_records = HealthRecord.query.filter(HealthRecord.customer_id.in_(customer_ids)).all()
    
    # 获取相关客户信息
    customer_dict = {}
    customers = Customer.query.filter(Customer.id.in_(customer_ids)).all()
    for customer in customers:
        customer_dict[customer.id] = customer.name
    
    # 将健康档案数据转换为DataFrame
    data = []
    for record in health_records:
        record_dict = record.to_dict()
        record_dict['姓名'] = customer_dict.get(record.customer_id, '')
        data.append(record_dict)
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 重命名列（英文列名转为中文）
    column_mapping = {
        'customer_id': '客户ID',
        'skin_type': '肤质类型',
        'oil_water_balance': '水油情况',
        'pores_blackheads': '毛孔与黑头',
        'wrinkles_texture': '皱纹与纹理',
        'pigmentation': '色素沉着',
        'photoaging_inflammation': '光老化与炎症',
        'tcm_constitution': '中医体质类型',
        'tongue_features': '舌象特征',
        'pulse_data': '脉象数据',
        'sleep_routine': '作息规律',
        'exercise_pattern': '运动频率及类型',
        'diet_restrictions': '饮食禁忌/偏好',
        'care_time_flexibility': '护理时间灵活度',
        'massage_pressure_preference': '手法力度偏好',
        'environment_requirements': '环境氛围要求',
        'short_term_beauty_goal': '短期美丽目标',
        'long_term_beauty_goal': '长期美丽目标',
        'short_term_health_goal': '短期健康目标',
        'long_term_health_goal': '长期健康目标',
        'medical_cosmetic_history': '医美操作史',
        'wellness_service_history': '大健康服务史',
        'major_disease_history': '重大疾病历史',
        'allergies': '过敏史'
    }
    
    df = df.rename(columns=column_mapping)
    
    # 调整列顺序，将客户ID和姓名放在最前面
    cols = ['客户ID', '姓名'] + [col for col in df.columns if col not in ['客户ID', '姓名']]
    df = df[cols]
    
    return df

# 辅助函数：导出消费记录
def export_consumptions(customer_ids):
    """导出消费记录"""
    consumptions = Consumption.query.filter(Consumption.customer_id.in_(customer_ids)).all()
    
    # 获取相关客户信息
    customer_dict = {}
    customers = Customer.query.filter(Customer.id.in_(customer_ids)).all()
    for customer in customers:
        customer_dict[customer.id] = customer.name
    
    # 将消费记录数据转换为DataFrame
    data = []
    for consumption in consumptions:
        consumption_dict = consumption.to_dict()
        consumption_dict['姓名'] = customer_dict.get(consumption.customer_id, '')
        data.append(consumption_dict)
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 重命名列（英文列名转为中文）
    column_mapping = {
        'customer_id': '客户ID',
        'date': '消费时间',
        'project_name': '项目名称',
        'amount': '消费金额',
        'payment_method': '支付方式',
        'total_sessions': '总次数',
        'completion_date': '耗卡完成时间',
        'satisfaction': '项目满意度'
    }
    
    df = df.rename(columns=column_mapping)
    
    # 调整列顺序，将客户ID和姓名放在最前面
    cols = ['客户ID', '姓名'] + [col for col in df.columns if col not in ['客户ID', '姓名']]
    df = df[cols]
    
    return df

# 辅助函数：导出服务记录
def export_services(customer_ids):
    """导出服务记录"""
    services = Service.query.filter(Service.customer_id.in_(customer_ids)).all()
    
    # 获取相关客户信息
    customer_dict = {}
    customers = Customer.query.filter(Customer.id.in_(customer_ids)).all()
    for customer in customers:
        customer_dict[customer.id] = customer.name
    
    # 将服务记录数据转换为DataFrame
    data = []
    for service in services:
        service_dict = service.to_dict()
        service_dict['姓名'] = customer_dict.get(service.customer_id, '')
        data.append(service_dict)
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 重命名列（英文列名转为中文）
    column_mapping = {
        'customer_id': '客户ID',
        'service_date': '到店时间',
        'departure_time': '离店时间',
        'total_amount': '总耗卡金额',
        'satisfaction': '服务满意度',
        'service_items': '消耗项目',
        'item_content': '项目内容',
        'beautician': '操作美容师',
        'service_amount': '耗卡金额',
        'is_specified': '是否指定'
    }
    
    df = df.rename(columns=column_mapping)
    
    # 调整列顺序，将客户ID和姓名放在最前面
    cols = ['客户ID', '姓名'] + [col for col in df.columns if col not in ['客户ID', '姓名']]
    df = df[cols]
    
    return df

# 辅助函数：导出沟通记录
def export_communications(customer_ids):
    """导出沟通记录"""
    communications = Communication.query.filter(Communication.customer_id.in_(customer_ids)).all()
    
    # 获取相关客户信息
    customer_dict = {}
    customers = Customer.query.filter(Customer.id.in_(customer_ids)).all()
    for customer in customers:
        customer_dict[customer.id] = customer.name
    
    # 将沟通记录数据转换为DataFrame
    data = []
    for communication in communications:
        communication_dict = communication.to_dict()
        communication_dict['姓名'] = customer_dict.get(communication.customer_id, '')
        data.append(communication_dict)
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 重命名列（英文列名转为中文）
    column_mapping = {
        'customer_id': '客户ID',
        'communication_date': '沟通时间',
        'communication_type': '沟通方式',
        'communication_location': '沟通地点',
        'staff_name': '员工',
        'communication_content': '沟通内容',
        'customer_feedback': '客户反馈',
        'follow_up_action': '后续跟进'
    }
    
    df = df.rename(columns=column_mapping)
    
    # 调整列顺序，将客户ID和姓名放在最前面
    cols = ['客户ID', '姓名'] + [col for col in df.columns if col not in ['客户ID', '姓名']]
    df = df[cols]
    
    return df