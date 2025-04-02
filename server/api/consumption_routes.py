"""
消耗记录API路由
"""

import os
import logging
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from sqlalchemy.exc import SQLAlchemyError

from models import db, Customer, Consumption, Service
from utils.consumption_excel_processor import ConsumptionExcelProcessor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建Blueprint
consumption_bp = Blueprint('consumption', __name__)

# 上传目录
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Excel处理器
excel_processor = ConsumptionExcelProcessor()

@consumption_bp.route('/', methods=['GET'])
def get_all_consumptions():
    """获取所有消耗记录"""
    try:
        # 支持分页
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 支持客户ID过滤
        customer_id = request.args.get('customer_id')
        query = Consumption.query
        
        if customer_id:
            query = query.filter_by(customer_id=customer_id)
            
        # 支持日期范围过滤
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            query = query.filter(Consumption.start_time >= start_date)
        if end_date:
            query = query.filter(Consumption.start_time <= end_date)
            
        # 执行分页查询
        paginated = query.order_by(Consumption.start_time.desc()).paginate(page=page, per_page=per_page)
        
        # 构建响应
        result = {
            'data': [consumption.to_dict() for consumption in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': paginated.page,
            'success': True
        }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取消耗记录时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取消耗记录时出错: {str(e)}"
        }), 500

@consumption_bp.route('/<int:consumption_id>', methods=['GET'])
def get_consumption(consumption_id):
    """获取单个消耗记录"""
    try:
        consumption = Consumption.query.get(consumption_id)
        if not consumption:
            return jsonify({
                'success': False,
                'message': f"找不到ID为 {consumption_id} 的消耗记录"
            }), 404
            
        return jsonify({
            'data': consumption.to_dict(),
            'success': True
        })
    except Exception as e:
        logger.error(f"获取消耗记录时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取消耗记录时出错: {str(e)}"
        }), 500

@consumption_bp.route('/', methods=['POST'])
def create_consumption():
    """创建新的消耗记录"""
    try:
        data = request.json
        
        # 验证必要字段
        if not data.get('customer_id'):
            return jsonify({
                'success': False,
                'message': "客户ID是必需的"
            }), 400
            
        if not data.get('start_time'):
            return jsonify({
                'success': False,
                'message': "开始时间是必需的"
            }), 400
            
        # 验证客户是否存在
        customer = Customer.query.get(data.get('customer_id'))
        if not customer:
            return jsonify({
                'success': False,
                'message': f"找不到ID为 {data.get('customer_id')} 的客户"
            }), 404
            
        # 创建消耗记录
        consumption = Consumption(
            customer_id=data.get('customer_id'),
            start_time=datetime.strptime(data.get('start_time'), '%Y-%m-%d %H:%M:%S'),
            end_time=datetime.strptime(data.get('end_time'), '%Y-%m-%d %H:%M:%S') if data.get('end_time') else None,
            project_name=data.get('project_name'),
            project_category=data.get('project_category'),
            amount=data.get('amount'),
            satisfaction=data.get('satisfaction'),
            beautician=data.get('beautician'),
            is_specified=data.get('is_specified', False),
            service_id=data.get('service_id'),
            project_id=data.get('project_id')
        )
        
        db.session.add(consumption)
        db.session.commit()
        
        return jsonify({
            'data': consumption.to_dict(),
            'success': True,
            'message': "消耗记录创建成功"
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建消耗记录时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"创建消耗记录时出错: {str(e)}"
        }), 500

@consumption_bp.route('/<int:consumption_id>', methods=['PUT'])
def update_consumption(consumption_id):
    """更新消耗记录"""
    try:
        consumption = Consumption.query.get(consumption_id)
        if not consumption:
            return jsonify({
                'success': False,
                'message': f"找不到ID为 {consumption_id} 的消耗记录"
            }), 404
            
        data = request.json
        
        # 更新字段
        if 'start_time' in data:
            consumption.start_time = datetime.strptime(data.get('start_time'), '%Y-%m-%d %H:%M:%S')
        if 'end_time' in data and data.get('end_time'):
            consumption.end_time = datetime.strptime(data.get('end_time'), '%Y-%m-%d %H:%M:%S')
        if 'project_name' in data:
            consumption.project_name = data.get('project_name')
        if 'project_category' in data:
            consumption.project_category = data.get('project_category')
        if 'amount' in data:
            consumption.amount = data.get('amount')
        if 'satisfaction' in data:
            consumption.satisfaction = data.get('satisfaction')
        if 'beautician' in data:
            consumption.beautician = data.get('beautician')
        if 'is_specified' in data:
            consumption.is_specified = data.get('is_specified')
        if 'service_id' in data:
            consumption.service_id = data.get('service_id')
        if 'project_id' in data:
            consumption.project_id = data.get('project_id')
            
        db.session.commit()
        
        return jsonify({
            'data': consumption.to_dict(),
            'success': True,
            'message': "消耗记录更新成功"
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新消耗记录时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"更新消耗记录时出错: {str(e)}"
        }), 500

@consumption_bp.route('/<int:consumption_id>', methods=['DELETE'])
def delete_consumption(consumption_id):
    """删除消耗记录"""
    try:
        consumption = Consumption.query.get(consumption_id)
        if not consumption:
            return jsonify({
                'success': False,
                'message': f"找不到ID为 {consumption_id} 的消耗记录"
            }), 404
            
        db.session.delete(consumption)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': "消耗记录删除成功"
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除消耗记录时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"删除消耗记录时出错: {str(e)}"
        }), 500

@consumption_bp.route('/import/excel', methods=['POST'])
def import_excel_preview():
    """导入Excel文件并获取预览数据"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': "请上传Excel文件"
            }), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': "未选择文件"
            }), 400
            
        # 检查文件类型
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({
                'success': False,
                'message': "请上传Excel文件(.xlsx或.xls)"
            }), 400
            
        # 保存文件
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        saved_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, saved_filename)
        file.save(filepath)
        
        # 获取工作表名
        sheet_name = request.form.get('sheet_name')
        
        # 预览数据
        preview_result = excel_processor.preview_data(filepath, sheet_name)
        
        return jsonify({
            'success': True,
            'data': {
                'preview': preview_result['preview'],
                'total_rows': preview_result['total_rows'],
                'errors': preview_result['errors']
            },
            'file_path': filepath
        })
    except Exception as e:
        logger.error(f"预览Excel数据时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"预览Excel数据时出错: {str(e)}"
        }), 500

@consumption_bp.route('/import/confirm', methods=['POST'])
def import_excel_confirm():
    """确认导入Excel数据"""
    try:
        data = request.json
        
        if not data.get('file_path'):
            return jsonify({
                'success': False,
                'message': "文件路径是必需的"
            }), 400
            
        file_path = data.get('file_path')
        sheet_name = data.get('sheet_name')
        import_mode = data.get('mode', 'add_only')  # 导入模式: add_only, update_existing, replace_all
        
        # 读取Excel数据
        consumption_data, errors = excel_processor.read_excel(file_path, sheet_name)
        
        if not consumption_data:
            return jsonify({
                'success': False,
                'message': "没有可导入的数据",
                'errors': errors
            }), 400
            
        # 准备导入统计
        import_stats = {
            'total': len(consumption_data),
            'success': 0,
            'failed': 0,
            'services_created': 0
        }
        
        # 处理导入模式
        if import_mode == 'replace_all':
            # 清空所有消耗记录和服务记录
            Consumption.query.delete()
            Service.query.delete()
            db.session.commit()
            logger.info("已清空所有消耗记录和服务记录")
            
        # 按照服务分组组织消耗记录
        services = excel_processor.group_into_services(consumption_data)
        logger.info(f"识别到 {len(services)} 个服务记录")
        
        # 导入服务记录和消耗记录
        for service_data in services:
            try:
                # 创建服务记录
                service = Service(
                    customer_id=service_data['customer_id'],
                    service_date=datetime.strptime(service_data['service_date'], '%Y-%m-%d %H:%M:%S'),
                    departure_time=datetime.strptime(service_data['departure_time'], '%Y-%m-%d %H:%M:%S') if service_data.get('departure_time') else None,
                    total_amount=service_data['total_amount'],
                    total_duration=service_data['total_duration'],
                    satisfaction=service_data['satisfaction']
                )
                
                db.session.add(service)
                db.session.flush()  # 获取service_id
                
                # 添加消耗记录
                for record_data in service_data['consumption_records']:
                    try:
                        # 创建消耗记录
                        consumption = Consumption(
                            customer_id=record_data['customer_id'],
                            start_time=datetime.strptime(record_data['start_time'], '%Y-%m-%d %H:%M:%S'),
                            end_time=datetime.strptime(record_data['end_time'], '%Y-%m-%d %H:%M:%S') if record_data.get('end_time') else None,
                            project_name=record_data.get('project_name'),
                            project_category=record_data.get('project_category'),
                            amount=record_data.get('amount'),
                            satisfaction=record_data.get('satisfaction'),
                            beautician=record_data.get('beautician'),
                            is_specified=record_data.get('is_specified', False),
                            service_id=service.id
                        )
                        
                        db.session.add(consumption)
                        import_stats['success'] += 1
                    except Exception as e:
                        logger.error(f"导入消耗记录时出错: {str(e)}")
                        import_stats['failed'] += 1
                        errors.append(f"导入消耗记录时出错: {str(e)}")
                        
                db.session.commit()
                import_stats['services_created'] += 1
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"导入服务记录时出错: {str(e)}")
                import_stats['failed'] += len(service_data['consumption_records'])
                errors.append(f"导入服务记录时出错: {str(e)}")
                
        # 删除临时文件
        try:
            os.remove(file_path)
            logger.info(f"已删除临时文件: {file_path}")
        except:
            logger.warning(f"删除临时文件失败: {file_path}")
            
        return jsonify({
            'success': True,
            'message': f"成功导入 {import_stats['success']} 条消耗记录，创建 {import_stats['services_created']} 个服务记录，失败 {import_stats['failed']} 条",
            'stats': import_stats,
            'errors': errors
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"确认导入Excel数据时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"确认导入Excel数据时出错: {str(e)}"
        }), 500

@consumption_bp.route('/stats', methods=['GET'])
def get_consumption_stats():
    """获取消耗统计数据"""
    try:
        # 获取客户ID（可选）
        customer_id = request.args.get('customer_id')
        
        # 基本查询
        query = Consumption.query
        
        if customer_id:
            query = query.filter_by(customer_id=customer_id)
            
        # 统计总消耗金额
        total_amount = db.session.query(db.func.sum(Consumption.amount)).filter(query.whereclause).scalar() or 0
        
        # 统计总消耗次数
        total_count = query.count()
        
        # 按项目分类统计
        category_stats = []
        categories = db.session.query(Consumption.project_category, db.func.count(Consumption.id).label('count'), db.func.sum(Consumption.amount).label('amount')) \
            .filter(query.whereclause) \
            .group_by(Consumption.project_category) \
            .all()
            
        for category, count, amount in categories:
            if category:  # 忽略没有分类的记录
                category_stats.append({
                    'category': category,
                    'count': count,
                    'amount': amount or 0
                })
                
        # 按美容师统计
        beautician_stats = []
        beauticians = db.session.query(Consumption.beautician, db.func.count(Consumption.id).label('count'), db.func.sum(Consumption.amount).label('amount')) \
            .filter(query.whereclause) \
            .group_by(Consumption.beautician) \
            .all()
            
        for beautician, count, amount in beauticians:
            if beautician:  # 忽略没有美容师的记录
                beautician_stats.append({
                    'beautician': beautician,
                    'count': count,
                    'amount': amount or 0
                })
                
        # 按月份统计
        month_stats = []
        months = db.session.query(db.func.date_format(Consumption.start_time, '%Y-%m').label('month'), db.func.count(Consumption.id).label('count'), db.func.sum(Consumption.amount).label('amount')) \
            .filter(query.whereclause) \
            .group_by('month') \
            .order_by('month') \
            .all()
            
        for month, count, amount in months:
            month_stats.append({
                'month': month,
                'count': count,
                'amount': amount or 0
            })
                
        return jsonify({
            'success': True,
            'data': {
                'total_amount': total_amount,
                'total_count': total_count,
                'category_stats': category_stats,
                'beautician_stats': beautician_stats,
                'month_stats': month_stats
            }
        })
    except Exception as e:
        logger.error(f"获取消耗统计数据时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取消耗统计数据时出错: {str(e)}"
        }), 500