from flask import Blueprint, request, jsonify
from models.service import Service
from utils.excel_processor import process_service_excel
from . import db

bp = Blueprint('service', __name__)

@bp.route('/services', methods=['GET'])
def get_services():
    """获取所有项目列表"""
    services = Service.query.all()
    return jsonify([service.to_dict() for service in services])

@bp.route('/services', methods=['POST'])
def create_service():
    """创建新项目"""
    data = request.json
    service = Service(
        name=data['name'],
        category=data['category'],
        sub_category=data.get('sub_category'),
        treatment_method=data.get('treatment_method'),
        description=data.get('description'),
        price=data.get('price'),
        duration=data.get('duration')
    )
    db.session.add(service)
    db.session.commit()
    return jsonify(service.to_dict()), 201

@bp.route('/services/import', methods=['POST'])
def import_services():
    """从Excel导入项目"""
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
        
    if not file.filename.endswith('.xlsx'):
        return jsonify({'error': '请上传Excel文件'}), 400
        
    try:
        services = process_service_excel(file)
        for service_data in services:
            service = Service(**service_data)
            db.session.add(service)
        db.session.commit()
        return jsonify({'message': f'成功导入{len(services)}个项目'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/services/<int:id>', methods=['GET'])
def get_service(id):
    """获取单个项目详情"""
    service = Service.query.get_or_404(id)
    return jsonify(service.to_dict())

@bp.route('/services/<int:id>', methods=['PUT'])
def update_service(id):
    """更新项目信息"""
    service = Service.query.get_or_404(id)
    data = request.json
    
    service.name = data.get('name', service.name)
    service.category = data.get('category', service.category)
    service.sub_category = data.get('sub_category', service.sub_category)
    service.treatment_method = data.get('treatment_method', service.treatment_method)
    service.description = data.get('description', service.description)
    service.price = data.get('price', service.price)
    service.duration = data.get('duration', service.duration)
    
    db.session.commit()
    return jsonify(service.to_dict())

@bp.route('/services/<int:id>', methods=['DELETE'])
def delete_service(id):
    """删除项目"""
    service = Service.query.get_or_404(id)
    db.session.delete(service)
    db.session.commit()
    return '', 204