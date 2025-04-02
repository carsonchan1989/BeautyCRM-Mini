"""
客户信息相关的API接口
"""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from models import db, Customer, HealthRecord, Consumption, Service, ServiceItem, Communication, Project
# from flask_login import current_user  # 暂时注释掉，未安装flask_login
from functools import wraps

# 定义权限装饰器
def require_role(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 简单实现，实际项目中可以根据用户角色做权限验证
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# 创建蓝图
customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/', methods=['GET'])
def get_customers():
    """获取客户列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        name = request.args.get('name', '')
        store = request.args.get('store', '')
        gender = request.args.get('gender', '')

        # 构建查询
        query = Customer.query

        # 应用过滤条件
        if name:
            query = query.filter(Customer.name.like(f'%{name}%'))
        if store:
            query = query.filter(Customer.store == store)
        if gender:
            query = query.filter(Customer.gender == gender)

        # 分页查询
        paginated_customers = query.order_by(Customer.created_at.desc()).paginate(page=page, per_page=per_page)

        # 准备返回数据
        data = {
            'items': [customer.to_dict() for customer in paginated_customers.items],
            'total': paginated_customers.total,
            'pages': paginated_customers.pages,
            'page': page,
            'per_page': per_page
        }

        return jsonify(data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/<string:customer_id>', methods=['GET'])
def get_customer(customer_id):
    """获取单个客户详情"""
    try:
        # 查询客户信息
        customer = Customer.query.get_or_404(customer_id)
        customer_data = customer.to_dict()

        # 查询关联的健康档案
        health_records = HealthRecord.query.filter_by(customer_id=customer_id).all()
        customer_data['health_records'] = [record.to_dict() for record in health_records]

        # 查询关联的消费记录
        consumptions = Consumption.query.filter_by(customer_id=customer_id).all()
        customer_data['consumption_records'] = [record.to_dict() for record in consumptions]

        # 查询关联的服务记录
        services = Service.query.filter_by(customer_id=customer_id).all()
        customer_data['service_records'] = [record.to_dict() for record in services]

        # 查询关联的沟通记录
        communications = Communication.query.filter_by(customer_id=customer_id).all()
        customer_data['communication_records'] = [record.to_dict() for record in communications]

        return jsonify(customer_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/', methods=['POST'])
def create_customer():
    """创建新客户"""
    try:
        # 获取请求数据
        data = request.json

        # 检查必要字段
        if not data.get('name'):
            return jsonify({'error': '姓名不能为空'}), 400

        # 创建客户 - ID将通过models.py中的default函数自动生成
        customer = Customer(**data)
        db.session.add(customer)
        db.session.commit()

        return jsonify(customer.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/<string:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """更新客户信息"""
    try:
        # 获取请求数据
        data = request.json

        # 查询客户
        customer = Customer.query.get_or_404(customer_id)

        # 客户存在检查已在前面完成

        # 更新客户信息
        for key, value in data.items():
            if hasattr(customer, key):
                setattr(customer, key, value)

        db.session.commit()

        return jsonify(customer.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/<string:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """删除客户"""
    try:
        # 查询客户
        customer = Customer.query.get_or_404(customer_id)
        
        # 查询所有关联的服务记录
        services = Service.query.filter_by(customer_id=customer_id).all()
        
        # 先删除关联的服务项目记录
        for service in services:
            ServiceItem.query.filter_by(service_id=service.service_id).delete()
        
        # 删除关联的服务记录
        Service.query.filter_by(customer_id=customer_id).delete()
        
        # 删除关联的健康档案
        HealthRecord.query.filter_by(customer_id=customer_id).delete()

        # 删除关联的消费记录
        Consumption.query.filter_by(customer_id=customer_id).delete()

        # 删除关联的沟通记录
        Communication.query.filter_by(customer_id=customer_id).delete()

        # 删除客户
        db.session.delete(customer)
        db.session.commit()

        return jsonify({'message': '客户删除成功'}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除客户失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/<string:customer_id>/health', methods=['POST', 'GET'])
def manage_health_record(customer_id):
    """添加或获取健康档案"""
    # 先检查客户是否存在
    customer = Customer.query.get_or_404(customer_id)

    if request.method == 'GET':
        # 获取健康档案
        health_records = HealthRecord.query.filter_by(customer_id=customer_id).all()
        return jsonify([record.to_dict() for record in health_records]), 200
    else:
        # 添加健康档案
        try:
            data = request.json
            data['customer_id'] = customer_id
            health_record = HealthRecord(**data)
            db.session.add(health_record)
            db.session.commit()
            return jsonify(health_record.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@customer_bp.route('/<string:customer_id>/consumption', methods=['POST', 'GET'])
def manage_consumption(customer_id):
    """添加或获取消费记录"""
    # 先检查客户是否存在
    customer = Customer.query.get_or_404(customer_id)

    if request.method == 'GET':
        # 获取消费记录
        consumptions = Consumption.query.filter_by(customer_id=customer_id).all()
        return jsonify([record.to_dict() for record in consumptions]), 200
    else:
        # 添加消费记录
        try:
            data = request.json
            data['customer_id'] = customer_id
            
            # 处理日期字段
            if 'date' in data and isinstance(data['date'], str):
                data['date'] = datetime.strptime(data['date'], '%Y-%m-%d %H:%M:%S')
            
            if 'completion_date' in data and isinstance(data['completion_date'], str) and data['completion_date']:
                data['completion_date'] = datetime.strptime(data['completion_date'], '%Y-%m-%d %H:%M:%S')

            consumption = Consumption(**data)
            db.session.add(consumption)
            db.session.commit()
            return jsonify(consumption.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@customer_bp.route('/<customer_id>/service', methods=['GET'])
@require_role(['admin', 'staff'])
def get_customer_services(customer_id):
    """获取客户服务记录"""
    try:
        # 先获取客户信息，确保客户存在
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'success': False, 'message': '客户不存在'}), 404
        
        # 获取客户的所有服务记录，按日期倒序排列
        services = Service.query.filter_by(customer_id=customer_id).order_by(Service.service_date.desc()).all()
        
        # 去重逻辑 - 根据服务日期和金额
        seen_keys = set()
        unique_services = []
        
        for service in services:
            # 创建唯一键
            key = f"{service.service_date}_{service.total_amount}"
            if key not in seen_keys:
                seen_keys.add(key)
                unique_services.append(service)
        
        # 转换为字典
        services_json = [service.to_dict() for service in unique_services]
        
        return jsonify(services_json)
    
    except Exception as e:
        current_app.logger.error(f"获取客户服务记录失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取服务记录失败: {str(e)}'}), 500

@customer_bp.route('/<customer_id>/service', methods=['POST'])
@require_role(['admin', 'staff'])
def create_customer_service(customer_id):
    """创建客户服务记录"""
    try:
        # 先获取客户信息，确保客户存在
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'success': False, 'message': '客户不存在'}), 404
        
        # 获取请求数据
        data = request.json
        data['customer_id'] = customer_id
        
        # 处理日期字段
        if 'service_date' in data and isinstance(data['service_date'], str):
            data['service_date'] = datetime.strptime(data['service_date'], '%Y-%m-%d %H:%M:%S')
        
        if 'departure_time' in data and isinstance(data['departure_time'], str) and data['departure_time']:
            data['departure_time'] = datetime.strptime(data['departure_time'], '%Y-%m-%d %H:%M:%S')
        
        # 提取服务项目数据
        service_items_data = data.pop('service_items', [])
        
        # 创建服务记录
        service = Service(**data)
        db.session.add(service)
        db.session.flush()  # 获取服务ID
        
        # 添加服务项目
        for item_data in service_items_data:
            service_item = ServiceItem(service_id=service.service_id, **item_data)
            db.session.add(service_item)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': '服务记录创建成功', 'data': service.to_dict()}), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建客户服务记录失败: {str(e)}")
        return jsonify({'success': False, 'message': f'创建服务记录失败: {str(e)}'}), 500

@customer_bp.route('/<string:customer_id>/communication', methods=['POST', 'GET'])
def manage_communication(customer_id):
    """添加或获取沟通记录"""
    # 先检查客户是否存在
    customer = Customer.query.get_or_404(customer_id)

    if request.method == 'GET':
        # 获取沟通记录
        communications = Communication.query.filter_by(customer_id=customer_id).all()
        return jsonify([record.to_dict() for record in communications]), 200
    else:
        # 添加沟通记录
        try:
            data = request.json
            data['customer_id'] = customer_id
            
            # 处理日期字段
            if 'communication_date' in data and isinstance(data['communication_date'], str):
                data['communication_date'] = datetime.strptime(data['communication_date'], '%Y-%m-%d %H:%M:%S')
            elif 'comm_time' in data and isinstance(data['comm_time'], str):
                # 兼容处理，将comm_time转换为communication_date
                data['communication_date'] = datetime.strptime(data['comm_time'], '%Y-%m-%d %H:%M:%S')
                del data['comm_time']

            communication = Communication(**data)
            db.session.add(communication)
            db.session.commit()
            return jsonify(communication.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"添加沟通记录失败: {str(e)}")
            return jsonify({'error': str(e)}), 500

@customer_bp.route('/communications/<int:comm_id>', methods=['GET', 'DELETE'])
def manage_single_communication(comm_id):
    """获取或删除单个沟通记录"""
    communication = Communication.query.get_or_404(comm_id)
    
    if request.method == 'GET':
        # 获取沟通记录详情
        return jsonify(communication.to_dict()), 200
    
    else:  # DELETE
        try:
            db.session.delete(communication)
            db.session.commit()
            return jsonify({"message": "沟通记录删除成功"}), 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"删除沟通记录失败: {str(e)}")
            return jsonify({'error': str(e)}), 500

@customer_bp.route('/stats', methods=['GET'])
def get_stats():
    """获取客户统计信息"""
    try:
        # 获取客户总数
        customer_count = Customer.query.count()
        
        # 获取项目总数
        project_count = Project.query.count()
        
        # 构建性别分布统计数据
        gender_query = db.session.query(
            Customer.gender, 
            db.func.count(Customer.id)
        ).group_by(Customer.gender).all()
        
        gender_distribution = {gender: count for gender, count in gender_query}
        
        # 构建门店分布统计数据
        store_query = db.session.query(
            Customer.store, 
            db.func.count(Customer.id)
        ).filter(Customer.store != None).filter(Customer.store != '').group_by(Customer.store).all()
        
        store_distribution = {store: count for store, count in store_query}
        
        # 计算消费总额
        consumption_sum = db.session.query(
            db.func.sum(Consumption.amount)
        ).scalar() or 0
        
        # 构建响应数据
        response = {
            'success': True,
            'data': {
                'total_customers': customer_count,
                'project_count': project_count,
                'gender_distribution': gender_distribution,
                'store_distribution': store_distribution,
                'total_consumption': consumption_sum
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f"获取统计信息失败: {str(e)}")
        return jsonify({'success': False, 'message': f"获取统计信息失败: {str(e)}"}), 500