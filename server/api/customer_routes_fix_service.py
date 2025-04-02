"""
修复客户服务记录API接口，适配新数据库表结构
"""
import logging
from flask import Blueprint, request, jsonify, current_app
from models import db, Customer, Service, ServiceItem
from sqlalchemy import desc

# 配置日志
logger = logging.getLogger(__name__)

# 创建蓝图
customer_service_bp = Blueprint('customer_service', __name__)

@customer_service_bp.route('/<customer_id>/services', methods=['GET'])
def get_customer_services(customer_id):
    """
    获取客户服务记录 - 包含详细服务项目
    使用新的数据库表结构
    """
    try:
        # 验证客户是否存在
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({
                'success': False,
                'message': f'客户 {customer_id} 不存在'
            }), 404
            
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 查询服务记录
        query = Service.query.filter_by(customer_id=customer_id)
        
        # 获取总记录数
        total_count = query.count()
        
        # 分页并按时间降序排序
        paginated_services = query.order_by(desc(Service.service_date)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # 转换为包含服务项目详情的字典
        service_list = []
        for service in paginated_services.items:
            service_dict = service.to_dict()
            
            # 确保service_items包含详细信息
            service_items = ServiceItem.query.filter_by(service_id=service.service_id).all()
            service_dict['service_items'] = [item.to_dict() for item in service_items]
            
            # 添加项目名称和美容师汇总
            project_names = [item.project_name for item in service_items if item.project_name]
            service_dict['project_summary'] = "、".join(project_names) if project_names else ""
            
            beautician_names = set([item.beautician_name for item in service_items 
                                 if item.beautician_name and item.beautician_name.strip()])
            service_dict['beautician_summary'] = "、".join(beautician_names) if beautician_names else ""
            
            service_list.append(service_dict)
        
        # 构建响应
        return jsonify({
            'success': True,
            'data': {
                'total': total_count,
                'pages': paginated_services.pages,
                'page': page,
                'per_page': per_page,
                'items': service_list
            },
            'message': '获取服务记录成功'
        })
        
    except Exception as e:
        logger.error(f"获取客户服务记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取服务记录失败: {str(e)}'
        }), 500
        
@customer_service_bp.route('/<customer_id>/service/<service_id>', methods=['GET'])
def get_customer_service_detail(customer_id, service_id):
    """获取客户单条服务记录详情"""
    try:
        # 验证客户是否存在
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({
                'success': False,
                'message': f'客户 {customer_id} 不存在'
            }), 404
        
        # 查询服务记录
        service = Service.query.filter_by(
            service_id=service_id, 
            customer_id=customer_id
        ).first()
        
        if not service:
            return jsonify({
                'success': False,
                'message': f'服务记录 {service_id} 不存在'
            }), 404
        
        # 转换为字典
        service_dict = service.to_dict()
        
        # 查询服务项目详情
        service_items = ServiceItem.query.filter_by(service_id=service_id).all()
        service_dict['service_items'] = [item.to_dict() for item in service_items]
        
        # 添加项目名称和美容师汇总
        project_names = [item.project_name for item in service_items if item.project_name]
        service_dict['project_summary'] = "、".join(project_names) if project_names else ""
        
        beautician_names = set([item.beautician_name for item in service_items 
                             if item.beautician_name and item.beautician_name.strip()])
        service_dict['beautician_summary'] = "、".join(beautician_names) if beautician_names else ""
        
        return jsonify({
            'success': True,
            'data': service_dict,
            'message': '获取服务记录详情成功'
        })
        
    except Exception as e:
        logger.error(f"获取客户服务记录详情失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取服务记录详情失败: {str(e)}'
        }), 500