"""
客户API路由
"""
from flask import Blueprint, request, jsonify
from server.models import db, Customer

bp = Blueprint('customers', __name__)

@bp.route('/', methods=['GET'])
def get_customers():
    """获取所有客户"""
    customers = Customer.query.all()
    return jsonify({
        'code': 0,
        'data': [customer.to_dict() for customer in customers]
    })

@bp.route('/<customer_id>', methods=['GET'])
def get_customer(customer_id):
    """获取特定客户信息"""
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({
            'code': 1,
            'message': f'客户 {customer_id} 不存在'
        }), 404
        
    return jsonify({
        'code': 0,
        'data': customer.to_dict()
    })