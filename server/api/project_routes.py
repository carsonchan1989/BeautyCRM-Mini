"""
项目管理API路由
"""

import os
import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
from models import db, Project
from utils.project_excel_processor import ProjectExcelProcessor

# 创建蓝图
project_bp = Blueprint('project', __name__)

# 获取所有项目
@project_bp.route('/', methods=['GET'])
def get_all_projects():
    """获取所有项目"""
    try:
        # 查询过滤
        category = request.args.get('category')
        status = request.args.get('status', 'active')
        search = request.args.get('search')
        
        query = Project.query
        
        # 应用过滤条件
        if category:
            query = query.filter(Project.category == category)
        if status:
            query = query.filter(Project.status == status)
        if search:
            query = query.filter(Project.name.like(f'%{search}%'))
        
        # 获取分页参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        # 执行查询
        paginated = query.order_by(Project.created_at.desc()).paginate(page=page, per_page=page_size)
        
        # 构建响应
        response = {
            'success': True,
            'data': [project.to_dict() for project in paginated.items],
            'pagination': {
                'total': paginated.total,
                'pages': paginated.pages,
                'current': page,
                'per_page': page_size
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        current_app.logger.error(f"获取项目列表失败: {str(e)}")
        return jsonify({'success': False, 'message': f"获取项目列表失败: {str(e)}"}), 500

# 获取项目类别列表
@project_bp.route('/categories', methods=['GET'])
def get_project_categories():
    """获取所有项目类别"""
    try:
        # 查询所有不同的项目类别
        categories = db.session.query(Project.category).distinct().all()
        
        # 提取类别名称
        category_list = [category[0] for category in categories if category[0]]
        
        return jsonify({
            'success': True,
            'data': category_list
        })
    
    except Exception as e:
        current_app.logger.error(f"获取项目类别失败: {str(e)}")
        return jsonify({'success': False, 'message': f"获取项目类别失败: {str(e)}"}), 500

# 获取单个项目
@project_bp.route('/<project_id>', methods=['GET'])
def get_project(project_id):
    """获取单个项目详情"""
    try:
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'success': False, 'message': '项目不存在'}), 404
        
        return jsonify({
            'success': True,
            'data': project.to_dict()
        })
    
    except Exception as e:
        current_app.logger.error(f"获取项目详情失败: {str(e)}")
        return jsonify({'success': False, 'message': f"获取项目详情失败: {str(e)}"}), 500

# 创建项目
@project_bp.route('/', methods=['POST'])
def create_project():
    """创建新项目"""
    try:
        data = request.json
        
        # 检查必填字段
        required_fields = ['name', 'category', 'price', 'sessions']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'缺少必填字段: {field}'}), 400
        
        # 创建新项目
        project = Project(
            name=data['name'],
            category=data['category'],
            effects=data.get('effects'),
            description=data.get('description'),
            price=float(data['price']),
            sessions=int(data['sessions']),
            duration=data.get('duration'),
            materials=data.get('materials'),
            notes=data.get('notes'),
            status=data.get('status', 'active')
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '项目创建成功',
            'data': project.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建项目失败: {str(e)}")
        return jsonify({'success': False, 'message': f"创建项目失败: {str(e)}"}), 500

# 更新项目
@project_bp.route('/<project_id>', methods=['PUT'])
def update_project(project_id):
    """更新项目信息"""
    try:
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'success': False, 'message': '项目不存在'}), 404
        
        data = request.json
        
        # 更新项目字段
        if 'name' in data:
            project.name = data['name']
        if 'category' in data:
            project.category = data['category']
        if 'effects' in data:
            project.effects = data['effects']
        if 'description' in data:
            project.description = data['description']
        if 'price' in data:
            project.price = float(data['price'])
        if 'sessions' in data:
            project.sessions = int(data['sessions'])
        if 'duration' in data:
            project.duration = data['duration']
        if 'materials' in data:
            project.materials = data['materials']
        if 'notes' in data:
            project.notes = data['notes']
        if 'status' in data:
            project.status = data['status']
        
        project.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '项目更新成功',
            'data': project.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新项目失败: {str(e)}")
        return jsonify({'success': False, 'message': f"更新项目失败: {str(e)}"}), 500

# 删除项目
@project_bp.route('/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """删除项目"""
    try:
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'success': False, 'message': '项目不存在'}), 404
        
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '项目删除成功'
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除项目失败: {str(e)}")
        return jsonify({'success': False, 'message': f"删除项目失败: {str(e)}"}), 500

# Excel文件上传与导入
@project_bp.route('/import/excel', methods=['POST'])
def import_excel():
    """上传Excel并导入项目数据"""
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有上传文件'}), 400
        
        file = request.files['file']
        
        # 检查文件名是否为空
        if file.filename == '':
            return jsonify({'success': False, 'message': '没有选择文件'}), 400
        
        # 检查文件扩展名
        allowed_extensions = {'xlsx', 'xls'}
        if not file.filename.lower().endswith(tuple('.' + ext for ext in allowed_extensions)):
            return jsonify({'success': False, 'message': '不支持的文件类型，请上传Excel文件'}), 400
        
        # 保存文件
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"project_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}")
        file.save(file_path)
        
        # 处理Excel文件
        processor = ProjectExcelProcessor(file_path)
        if not processor.load_excel():
            return jsonify({'success': False, 'message': '无法加载Excel文件', 'errors': processor.get_errors()}), 400
        
        # 验证表头
        valid, missing_fields = processor.validate_headers()
        if not valid:
            return jsonify({
                'success': False, 
                'message': f'Excel格式验证失败', 
                'errors': processor.get_errors()
            }), 400
        
        # 获取预览数据
        preview_data = processor.get_preview_data()
        
        return jsonify({
            'success': True,
            'message': '文件上传成功，已解析数据',
            'data': preview_data,
            'file_path': file_path
        })
    
    except Exception as e:
        current_app.logger.error(f"项目Excel导入失败: {str(e)}")
        return jsonify({'success': False, 'message': f"项目Excel导入失败: {str(e)}"}), 500

# 确认导入Excel数据
@project_bp.route('/import/confirm', methods=['POST'])
def confirm_import():
    """确认导入Excel数据到数据库"""
    try:
        data = request.json
        file_path = data.get('file_path')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'success': False, 'message': '文件不存在或已被删除'}), 400
        
        # 处理Excel文件
        processor = ProjectExcelProcessor(file_path)
        if not processor.load_excel():
            return jsonify({'success': False, 'message': '无法加载Excel文件', 'errors': processor.get_errors()}), 400
        
        # 清洗数据
        cleaned_data = processor.clean_data()
        if not cleaned_data:
            return jsonify({'success': False, 'message': '没有有效数据可导入', 'errors': processor.get_errors()}), 400
        
        # 导入模式
        import_mode = data.get('mode', 'add_only')  # add_only, update_existing, replace_all
        
        # 如果是替换全部模式，先删除所有项目
        if import_mode == 'replace_all':
            Project.query.delete()
        
        # 导入数据
        imported_count = 0
        updated_count = 0
        error_count = 0
        
        for project_data in cleaned_data:
            try:
                # 检查项目是否已存在 (按名称匹配)
                existing_project = Project.query.filter_by(name=project_data['name']).first()
                
                if existing_project and import_mode in ['update_existing', 'replace_all']:
                    # 更新已存在的项目
                    for key, value in project_data.items():
                        setattr(existing_project, key, value)
                    
                    existing_project.updated_at = datetime.now()
                    updated_count += 1
                elif not existing_project:
                    # 创建新项目
                    new_project = Project(**project_data)
                    db.session.add(new_project)
                    imported_count += 1
            
            except Exception as e:
                error_count += 1
                current_app.logger.error(f"导入项目数据出错: {str(e)}")
                processor.errors.append(f"导入数据出错: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'数据导入完成，新增: {imported_count}，更新: {updated_count}，失败: {error_count}',
            'data': {
                'imported': imported_count,
                'updated': updated_count,
                'errors': error_count,
                'error_messages': processor.get_errors()
            }
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"确认导入项目数据失败: {str(e)}")
        return jsonify({'success': False, 'message': f"确认导入项目数据失败: {str(e)}"}), 500

# 获取项目统计信息
@project_bp.route('/stats', methods=['GET'])
def get_project_stats():
    """获取项目统计信息"""
    try:
        # 获取项目总数
        total_projects = Project.query.count()
        
        # 获取各类别项目数量
        category_stats = db.session.query(
            Project.category, db.func.count(Project.id)
        ).group_by(Project.category).all()
        
        category_distribution = {category: count for category, count in category_stats}
        
        # 获取价格区间分布
        price_ranges = [
            ('0-1000', db.func.count(Project.id.distinct())),
            ('1000-2000', db.func.count(Project.id.distinct())),
            ('2000-3000', db.func.count(Project.id.distinct())),
            ('3000-5000', db.func.count(Project.id.distinct())),
            ('5000+', db.func.count(Project.id.distinct()))
        ]
        
        price_stats = {}
        for range_name, _ in price_ranges:
            min_price, max_price = 0, float('inf')
            if range_name != '5000+':
                min_price, max_price = map(int, range_name.split('-'))
            else:
                min_price = 5000
            
            count = Project.query.filter(
                Project.price >= min_price,
                Project.price < max_price if max_price != float('inf') else True
            ).count()
            
            price_stats[range_name] = count
        
        return jsonify({
            'success': True,
            'data': {
                'total_projects': total_projects,
                'category_distribution': category_distribution,
                'price_distribution': price_stats
            }
        })
    
    except Exception as e:
        current_app.logger.error(f"获取项目统计失败: {str(e)}")
        return jsonify({'success': False, 'message': f"获取项目统计失败: {str(e)}"}), 500 