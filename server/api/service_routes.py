"""
服务记录相关API路由 - 美容客户管理系统
"""

import logging
import os
import json
import pandas as pd
import traceback
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_file
from models import db, Service, ServiceItem, Customer, Project
from utils.consumption_excel_processor import ConsumptionExcelProcessor
from sqlalchemy import func, exc
from werkzeug.utils import secure_filename

# 创建蓝图
service_bp = Blueprint('service', __name__)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'xlsx', 'xls'}

def generate_service_report(customer_id, export_path=None):
    """生成客户服务记录报告"""
    try:
        # 获取客户信息
        customer = Customer.query.get(customer_id)
        if not customer:
            return {
                'success': False,
                'message': f'客户 {customer_id} 不存在'
            }
            
        # 获取客户所有服务记录
        services = Service.query.filter_by(customer_id=customer_id).order_by(Service.service_date.desc()).all()
        
        # 生成Markdown内容
        md_content = f"# {customer.name} 服务记录报告\n\n"
        md_content += f"**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md_content += f"**客户ID:** {customer.id}\n"
        md_content += f"**姓名:** {customer.name}\n"
        md_content += f"**性别:** {customer.gender}\n"
        md_content += f"**所属门店:** {customer.store or '未知'}\n\n"
        
        md_content += f"## 服务记录总览\n\n"
        md_content += f"- **服务记录总数:** {len(services)}\n"
        
        # 计算总消费金额
        total_amount = sum(service.total_amount for service in services if service.total_amount)
        md_content += f"- **累计消费金额:** ￥{total_amount:.2f}\n\n"
        
        if services:
            md_content += "## 详细服务记录\n\n"
            
            for idx, service in enumerate(services, 1):
                md_content += f"### {idx}. 服务记录 ({service.service_date.strftime('%Y-%m-%d')})\n\n"
                md_content += f"- **服务ID:** {service.service_id}\n"
                md_content += f"- **服务日期:** {service.service_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
                md_content += f"- **总金额:** ￥{service.total_amount:.2f}\n"
                md_content += f"- **支付方式:** {service.payment_method or '未记录'}\n"
                md_content += f"- **操作人员:** {service.operator or '未记录'}\n"
                
                if service.remark:
                    md_content += f"- **备注:** {service.remark}\n"
                    
                md_content += "\n**服务项目:**\n\n"
                
                if service.service_items:
                    md_content += "| 项目名称 | 单价 | 数量 | 扣卡金额 | 美容师 | 备注 |\n"
                    md_content += "|---------|------|------|----------|--------|------|\n"
                    
                    for item in service.service_items:
                        unit_price = f"￥{item.unit_price:.2f}" if item.unit_price is not None else "未记录"
                        card_deduction = f"￥{item.card_deduction:.2f}" if item.card_deduction is not None else "未记录"
                        md_content += f"| {item.project_name} | {unit_price} | {item.quantity or 1} | {card_deduction} | {item.beautician_name or '未记录'} | {item.remark or ''} |\n"
                else:
                    md_content += "_无服务项目记录_\n"
                    
                md_content += "\n---\n\n"
        else:
            md_content += "## 暂无服务记录\n\n"
            
        # 如果提供了导出路径，则写入文件
        if export_path:
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
                
            return {
                'success': True,
                'message': '服务记录报告生成成功',
                'path': export_path
            }
        
        # 否则直接返回内容
        return {
            'success': True,
            'message': '服务记录报告生成成功',
            'content': md_content
        }
            
    except Exception as e:
        logger.error(f"生成服务记录报告出错: {str(e)}")
        return {
            'success': False,
            'message': f'生成服务记录报告失败: {str(e)}'
        }

@service_bp.route('/list', methods=['GET'])
def get_services():
    """获取服务记录列表"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('limit', 10))
        customer_id = request.args.get('customer_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 构建查询
        query = Service.query
        
        # 应用筛选条件
        if customer_id:
            query = query.filter(Service.customer_id == customer_id)
            
        if start_date:
            try:
                start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(Service.service_date >= start_datetime)
            except ValueError:
                logger.warning(f"无效的开始日期格式: {start_date}")
                
        if end_date:
            try:
                end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
                query = query.filter(Service.service_date <= end_datetime)
            except ValueError:
                logger.warning(f"无效的结束日期格式: {end_date}")
        
        # 获取总记录数
        total = query.count()
        
        # 获取分页数据
        services = query.order_by(Service.service_date.desc()).paginate(page=page, per_page=per_page)
        
        # 格式化返回数据
        result = []
        for service in services.items:
            service_dict = service.to_dict()
            result.append(service_dict)
            
        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'items': result,
                'page': page,
                'limit': per_page
            },
            'message': '获取服务记录成功'
        })
        
    except Exception as e:
        logger.error(f"获取服务记录列表出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取服务记录列表失败: {str(e)}'
        })

@service_bp.route('/<service_id>', methods=['GET'])
def get_service(service_id):
    """获取单个服务记录详情"""
    try:
        service = Service.query.get(service_id)
        
        if not service:
            return jsonify({
                'success': False,
                'message': f'服务记录 {service_id} 不存在'
            })
            
        service_dict = service.to_dict()
            
        return jsonify({
            'success': True,
            'data': service_dict,
            'message': '获取服务记录成功'
        })
        
    except Exception as e:
        logger.error(f"获取服务记录详情出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取服务记录详情失败: {str(e)}'
        })

@service_bp.route('/create', methods=['POST'])
def create_service():
    """创建新的服务记录"""
    try:
        data = request.json
        
        # 验证必需字段
        if not data.get('customer_id'):
            return jsonify({
                'success': False,
                'message': '客户ID不能为空'
            })
            
        # 检查客户是否存在
        customer = Customer.query.get(data.get('customer_id'))
        if not customer:
            return jsonify({
                'success': False,
                'message': f'客户 {data.get("customer_id")} 不存在'
            })
            
        # 解析服务日期
        service_date = datetime.now()
        if data.get('service_date'):
            try:
                service_date = datetime.strptime(data.get('service_date'), '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    service_date = datetime.strptime(data.get('service_date'), '%Y-%m-%d')
                except ValueError:
                    return jsonify({
                        'success': False,
                        'message': '服务日期格式无效，请使用YYYY-MM-DD或YYYY-MM-DD HH:MM:SS格式'
                    })
                
        # 创建新服务记录
        service = Service(
            customer_id=data.get('customer_id'),
            customer_name=customer.name,
            service_date=service_date,
            total_amount=data.get('total_amount', 0),
            payment_method=data.get('payment_method'),
            operator=data.get('operator'),
            remark=data.get('remark')
        )
        
        db.session.add(service)
        db.session.flush()  # 生成ID但不提交事务
        
        # 处理服务项目
        service_items_data = data.get('service_items', [])
        for item_data in service_items_data:
            project_name = item_data.get('project_name')
            if not project_name:
                continue
            
            # 查找项目ID
            project_id = item_data.get('project_id')
            if not project_id and item_data.get('project_name'):
                # 尝试通过名称查找项目
                project = Project.query.filter_by(name=item_data.get('project_name')).first()
                if project:
                    project_id = project.id
                
            # 创建服务项目记录
            service_item = ServiceItem(
                service_id=service.service_id,
                project_id=project_id,
                project_name=project_name,
                beautician_name=item_data.get('beautician_name'),
                card_deduction=item_data.get('card_deduction', 0),
                quantity=item_data.get('quantity', 1),
                unit_price=item_data.get('unit_price'),
                remark=item_data.get('remark'),
                is_satisfied=item_data.get('is_satisfied', True)
            )
            
            db.session.add(service_item)
                
        # 提交事务
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'service_id': service.service_id,
                'service': service.to_dict()
            },
            'message': '创建服务记录成功'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建服务记录出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'创建服务记录失败: {str(e)}'
        })

@service_bp.route('/<service_id>', methods=['PUT'])
def update_service(service_id):
    """更新服务记录"""
    try:
        service = Service.query.get(service_id)
        
        if not service:
            return jsonify({
                'success': False,
                'message': f'服务记录 {service_id} 不存在'
            })
            
        data = request.json
        
        # 更新服务日期
        if data.get('service_date'):
            try:
                service_date = datetime.strptime(data.get('service_date'), '%Y-%m-%d %H:%M:%S')
                service.service_date = service_date
            except ValueError:
                try:
                    service_date = datetime.strptime(data.get('service_date'), '%Y-%m-%d')
                    service.service_date = service_date
                except ValueError:
                    return jsonify({
                        'success': False,
                        'message': '服务日期格式无效，请使用YYYY-MM-DD或YYYY-MM-DD HH:MM:SS格式'
                    })
                    
        # 更新其他字段
        if 'total_amount' in data:
            service.total_amount = data.get('total_amount')
            
        if 'payment_method' in data:
            service.payment_method = data.get('payment_method')
            
        if 'operator' in data:
            service.operator = data.get('operator')
            
        if 'remark' in data:
            service.remark = data.get('remark')
            
        # 处理服务项目更新
        if 'service_items' in data:
            # 删除现有服务项目
            ServiceItem.query.filter_by(service_id=service_id).delete()
            
            # 添加新的服务项目
            for item_data in data.get('service_items', []):
                project_name = item_data.get('project_name')
                if not project_name:
                    continue
                    
                # 查找项目ID
                project_id = item_data.get('project_id')
                if not project_id and item_data.get('project_name'):
                    # 尝试通过名称查找项目
                    project = Project.query.filter_by(name=item_data.get('project_name')).first()
                    if project:
                        project_id = project.id
                    
                # 创建服务项目记录
                service_item = ServiceItem(
                    service_id=service.service_id,
                    project_id=project_id,
                    project_name=project_name,
                    beautician_name=item_data.get('beautician_name'),
                    card_deduction=item_data.get('card_deduction', 0),
                    quantity=item_data.get('quantity', 1),
                    unit_price=item_data.get('unit_price'),
                    remark=item_data.get('remark'),
                    is_satisfied=item_data.get('is_satisfied', True)
                )
                
                db.session.add(service_item)
                
        # 提交事务
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': service.to_dict(),
            'message': '更新服务记录成功'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新服务记录出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新服务记录失败: {str(e)}'
        })

@service_bp.route('/<service_id>', methods=['DELETE'])
def delete_service(service_id):
    """删除服务记录"""
    try:
        service = Service.query.get(service_id)
        
        if not service:
            return jsonify({
                'success': False,
                'message': f'服务记录 {service_id} 不存在'
            })
            
        # 删除关联的服务项目
        ServiceItem.query.filter_by(service_id=service_id).delete()
        
        # 删除服务记录
        db.session.delete(service)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '删除服务记录成功'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除服务记录出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除服务记录失败: {str(e)}'
        })

@service_bp.route('/import-consumption', methods=['POST'])
def import_consumption_excel():
    """从Excel导入消耗记录"""
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '未上传任何文件'
            })
            
        file = request.files['file']
        
        # 检查文件名是否为空
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '文件名为空'
            })
            
        # 检查文件类型
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': '仅支持Excel文件(.xlsx, .xls)'
            })
            
        # 获取导入模式
        import_mode = request.form.get('import_mode', 'add')
        if import_mode not in ['add', 'update', 'replace']:
            import_mode = 'add'
            
        # 安全保存文件
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        logger.info(f"成功上传文件: {file_path}")
        
        # 创建Excel处理器并处理文件
        processor = ConsumptionExcelProcessor()
        result = processor.process_file(file_path, import_mode=import_mode)
        
        if not result['success']:
            return jsonify(result)
            
        # 处理数据导入
        records = result['records']
        stats = result['stats']
        
        # 根据导入模式处理数据
        if import_mode == 'replace':
            # 先清空所有服务记录
            ServiceItem.query.delete()
            Service.query.delete()
            db.session.commit()
            
        # 添加新记录
        success_count = 0
        error_count = 0
        
        for record in records:
            try:
                # 检查客户是否存在
                customer_id = record.get('customer_id')
                if not customer_id:
                    logger.warning(f"记录缺少客户ID，跳过: {record}")
                    error_count += 1
                    continue
                    
                customer = Customer.query.get(customer_id)
                if not customer:
                    logger.warning(f"客户 {customer_id} 不存在，跳过记录")
                    error_count += 1
                    continue
                
                # 解析服务日期
                service_date = None
                if record.get('service_date'):
                    try:
                        service_date = pd.to_datetime(record.get('service_date')).to_pydatetime()
                    except Exception as e:
                        logger.warning(f"解析服务日期出错，使用当前时间: {e}")
                        service_date = datetime.now()
                else:
                    service_date = datetime.now()
                
                # 如果是更新模式，检查是否有相同日期的记录
                existing_service = None
                if import_mode == 'update':
                    # 查找相同客户、相同日期的记录
                    existing_service = Service.query.filter_by(
                        customer_id=customer_id,
                        service_date=service_date
                    ).first()
                
                if existing_service and import_mode == 'update':
                    # 更新现有记录
                    existing_service.total_amount = record.get('total_amount', 0)
                    existing_service.payment_method = record.get('payment_method')
                    existing_service.operator = record.get('operator')
                    existing_service.remark = record.get('remark')
                    
                    # 删除现有项目
                    ServiceItem.query.filter_by(service_id=existing_service.service_id).delete()
                    
                    # 添加新项目
                    service_id = existing_service.service_id
                else:
                    # 创建新服务记录
                    new_service = Service(
                        customer_id=customer_id,
                        customer_name=customer.name,
                        service_date=service_date,
                        total_amount=record.get('total_amount', 0),
                        payment_method=record.get('payment_method'),
                        operator=record.get('operator'),
                        remark=record.get('remark')
                    )
                    
                    db.session.add(new_service)
                    db.session.flush()  # 生成ID但不提交事务
                    service_id = new_service.service_id
                
                # 处理服务项目
                items = record.get('items', [])
                for item_data in items:
                    project_name = item_data.get('project_name')
                    if not project_name:
                        continue
                    
                    # 查找项目ID
                    project_id = None
                    project = Project.query.filter_by(name=project_name).first()
                    if project:
                        project_id = project.id
                    
                    # 创建服务项目记录
                    service_item = ServiceItem(
                        service_id=service_id,
                        project_id=project_id,
                        project_name=project_name,
                        beautician_name=item_data.get('beautician_name'),
                        card_deduction=item_data.get('card_deduction', 0),
                        quantity=item_data.get('quantity', 1),
                        unit_price=item_data.get('unit_price'),
                        remark=item_data.get('remark'),
                        is_satisfied=item_data.get('is_satisfied', True)
                    )
                    
                    db.session.add(service_item)
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"处理记录时出错: {str(e)}\n{traceback.format_exc()}")
                error_count += 1
        
        # 提交事务
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'processed_count': len(records),
                'success_count': success_count,
                'error_count': error_count,
                'stats': stats
            },
            'message': f'成功导入 {success_count} 条消耗记录，失败 {error_count} 条'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"导入消耗记录出错: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'导入消耗记录失败: {str(e)}'
        })

@service_bp.route('/report/<customer_id>', methods=['GET'])
def get_service_report(customer_id):
    """生成客户服务记录报告"""
    try:
        format_type = request.args.get('format', 'json')
        
        if format_type == 'md':
            # 生成Markdown报告并下载
            export_folder = current_app.config['EXPORT_FOLDER']
            file_name = f"{customer_id}_services_{datetime.now().strftime('%Y%m%d%H%M%S')}.md"
            export_path = os.path.join(export_folder, file_name)
            
            result = generate_service_report(customer_id, export_path)
            
            if not result['success']:
                return jsonify(result)
                
            return send_file(
                export_path,
                mimetype='text/markdown',
                as_attachment=True,
                download_name=file_name
            )
        else:
            # 返回JSON格式的报告内容
            result = generate_service_report(customer_id)
            return jsonify(result)
        
    except Exception as e:
        logger.error(f"生成服务记录报告出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'生成服务记录报告失败: {str(e)}'
        })

@service_bp.route('/stats', methods=['GET'])
def get_service_stats():
    """获取服务统计信息"""
    try:
        # 获取时间范围
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 构建查询
        query = db.session.query(
            Service.customer_id,
            func.count(Service.service_id).label('service_count'),
            func.sum(Service.total_amount).label('total_amount')
        ).group_by(Service.customer_id)
        
        # 应用时间筛选
        if start_date:
            try:
                start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(Service.service_date >= start_datetime)
            except ValueError:
                logger.warning(f"无效的开始日期格式: {start_date}")
                
        if end_date:
            try:
                end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
                query = query.filter(Service.service_date <= end_datetime)
            except ValueError:
                logger.warning(f"无效的结束日期格式: {end_date}")
        
        # 执行查询
        results = query.all()
        
        # 格式化结果
        stats = []
        for customer_id, service_count, total_amount in results:
            # 获取客户信息
            customer = Customer.query.get(customer_id)
            if customer:
                stats.append({
                    'customer_id': customer_id,
                    'customer_name': customer.name,
                    'service_count': service_count,
                    'total_amount': float(total_amount) if total_amount else 0
                })
                
        # 获取服务记录总数
        total_services = Service.query.count()
        
        # 获取项目分布
        project_stats = db.session.query(
            ServiceItem.project_name,
            func.count(ServiceItem.id).label('count')
        ).group_by(ServiceItem.project_name).order_by(func.count(ServiceItem.id).desc()).limit(10).all()
        
        project_distribution = [
            {'project_name': project_name, 'count': count}
            for project_name, count in project_stats
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'total_services': total_services,
                'customer_stats': stats,
                'project_distribution': project_distribution
            },
            'message': '获取服务统计成功'
        })
        
    except Exception as e:
        logger.error(f"获取服务统计出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取服务统计失败: {str(e)}'
        })