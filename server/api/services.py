"""
服务记录API路由
"""
from flask import Blueprint, request, jsonify
from server.models import db, Service, ServiceItem

bp = Blueprint('services', __name__)

@bp.route('/', methods=['GET'])
def get_services():
    """获取所有服务记录"""
    services = Service.query.all()
    return jsonify({
        'code': 0,
        'data': [service.to_dict() for service in services]
    })

@bp.route('/<service_id>', methods=['GET'])
def get_service(service_id):
    """获取特定服务记录"""
    service = Service.query.get(service_id)
    if not service:
        return jsonify({
            'code': 1,
            'message': f'服务记录 {service_id} 不存在'
        }), 404
        
    return jsonify({
        'code': 0,
        'data': service.to_dict()
    })

@bp.route('/customer/<customer_id>', methods=['GET'])
def get_customer_services(customer_id):
    """获取指定客户的所有服务记录"""
    services = Service.query.filter_by(customer_id=customer_id).all()
    return jsonify({
        'code': 0,
        'data': [service.to_dict() for service in services]
    })