"""
Excel导入补丁脚本 - 修复Excel导入功能
"""
import os
import pandas as pd
from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from server.models import db, Customer, Service, ServiceItem

excel_patch = Blueprint('excel_patch', __name__)

# 配置上传文件保存路径
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@excel_patch.route('/import', methods=['POST'])
def import_excel():
    """处理上传的Excel文件"""
    if 'excel_file' not in request.files:
        return jsonify({'code': 1, 'message': '未找到上传的文件'}), 400
    
    file = request.files['excel_file']
    if file.filename == '':
        return jsonify({'code': 1, 'message': '未选择文件'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # 返回文件URL，用于后续处理
        file_url = f'/uploads/{filename}'
        
        return jsonify({
            'code': 0, 
            'message': '文件上传成功',
            'data': {'fileUrl': file_url}
        })

@excel_patch.route('/process', methods=['POST'])
def process_excel():
    """处理Excel文件中的数据"""
    try:
        data = request.get_json()
        file_url = data.get('fileUrl')
        mapping_options = data.get('mappingOptions', {})
        
        if not file_url:
            return jsonify({'code': 1, 'message': '文件URL不能为空'}), 400
        
        # 构建完整的文件路径
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', file_url.lstrip('/'))
        
        if not os.path.exists(file_path):
            return jsonify({'code': 1, 'message': '文件不存在'}), 404
        
        # 读取Excel文件
        try:
            excel_data = pd.read_excel(file_path, sheet_name=None)
        except Exception as e:
            return jsonify({'code': 1, 'message': f'Excel文件读取失败: {str(e)}'}), 400
        
        # 处理消耗数据
        result = process_consumption_data(excel_data, mapping_options)
        
        return jsonify({
            'code': 0,
            'message': '数据处理成功',
            'data': result
        })
            
    except Exception as e:
        return jsonify({'code': 1, 'message': f'数据处理失败: {str(e)}'}), 500

def process_consumption_data(excel_data, mapping_options):
    """处理Excel中的消耗数据"""
    # 获取消耗数据表
    sheet_name = '消耗'
    if sheet_name not in excel_data:
        return {'error': f'找不到名为"{sheet_name}"的表格'}
    
    df = excel_data[sheet_name]
    
    # 检查表格结构
    if len(df) == 0:
        return {'error': '表格没有数据'}
    
    # 获取映射配置
    service_mapping = mapping_options.get('serviceMapping', {})
    service_item_mapping = mapping_options.get('serviceItemMapping', {})
    
    # 提取映射字段
    customer_id_field = service_mapping.get('customer_id', '客户ID')
    service_date_field = service_mapping.get('service_date', '进店时间')
    departure_time_field = service_mapping.get('departure_time', '离店时间')
    total_amount_field = service_mapping.get('total_amount', '总耗卡金额')
    total_sessions_field = service_mapping.get('total_sessions', '总消耗项目数')  # 修复: 使用正确的字段名
    satisfaction_field = service_mapping.get('satisfaction', '服务满意度')
    
    project_name_field = service_item_mapping.get('project_name', '项目名称')
    beautician_field = service_item_mapping.get('beautician_name', '美容师')
    unit_price_field = service_item_mapping.get('unit_price', '金额')
    is_specified_field = service_item_mapping.get('is_specified', '是否指定')
    
    # 标准化列名
    df.columns = [str(col).strip() for col in df.columns]
    
    # 按客户和到店时间分组，避免重复导入
    grouped = df.groupby([customer_id_field, service_date_field])
    
    imported_services = 0
    imported_items = 0
    skipped_services = 0
    errors = []
    
    for (customer_id, service_time), group in grouped:
        try:
            # 检查客户是否存在
            customer = Customer.query.filter_by(id=customer_id).first()
            if not customer:
                errors.append(f"客户不存在: {customer_id}，跳过相关记录")
                continue
            
            # 解析日期时间
            try:
                if isinstance(service_time, str):
                    service_date = datetime.strptime(service_time, "%Y/%m/%d %H:%M:%S")
                else:
                    service_date = service_time
                    
                # 解析离店时间
                departure_time_str = group[departure_time_field].iloc[0]
                if isinstance(departure_time_str, str):
                    departure_time = datetime.strptime(departure_time_str, "%Y/%m/%d %H:%M:%S")
                else:
                    departure_time = departure_time_str
            except Exception as e:
                errors.append(f"日期解析错误: {str(e)}，跳过记录")
                continue
            
            # 检查该客户在该时间是否已有服务记录
            existing_service = Service.query.filter_by(
                customer_id=customer_id,
                service_date=service_date
            ).first()
            
            if existing_service:
                skipped_services += 1
                continue
            
            # 获取总耗卡次数 - 修复: 使用正确的字段
            total_sessions = 0
            if total_sessions_field in group.columns and not pd.isna(group[total_sessions_field].iloc[0]):
                try:
                    total_sessions = int(group[total_sessions_field].iloc[0])
                except:
                    # 如果转换失败，设置为默认值0
                    pass
            
            # 创建新服务记录
            service = Service(
                customer_id=customer_id,
                customer_name=customer.name,
                service_date=service_date,
                departure_time=departure_time,
                total_amount=float(group[total_amount_field].iloc[0]) if total_amount_field in group and not pd.isna(group[total_amount_field].iloc[0]) else 0,
                total_sessions=total_sessions,  # 使用解析后的值
                satisfaction=group[satisfaction_field].iloc[0] if satisfaction_field in group.columns and not pd.isna(group[satisfaction_field].iloc[0]) else None
            )
            
            db.session.add(service)
            db.session.flush()  # 获取服务ID
            
            # 添加服务项目
            added_items = 0
            
            # 查找所有包含项目名称的列
            for i in range(1, total_sessions + 1):
                # 构建可能的列名
                possible_project_cols = [
                    f"项目{i}", 
                    f"项目内容{i}", 
                    f"项目名称{i}"
                ]
                
                # 尝试找到存在的列名
                project_col = None
                for col in possible_project_cols:
                    if col in group.columns:
                        project_col = col
                        break
                
                # 如果找到项目列
                if project_col and not pd.isna(group[project_col].iloc[0]):
                    project_name = group[project_col].iloc[0]
                    
                    # 查找对应的美容师列
                    beautician_col = f"美容师{i}"
                    beautician_name = group[beautician_col].iloc[0] if beautician_col in group.columns and not pd.isna(group[beautician_col].iloc[0]) else ""
                    
                    # 查找对应的金额列
                    amount_col = f"金额{i}"
                    amount = float(group[amount_col].iloc[0]) if amount_col in group.columns and not pd.isna(group[amount_col].iloc[0]) else 0.0
                    
                    # 查找对应的指定列
                    specified_col = f"是否指定{i}"
                    is_specified = False
                    if specified_col in group.columns and not pd.isna(group[specified_col].iloc[0]):
                        specified_value = group[specified_col].iloc[0]
                        is_specified = specified_value in ['✓', '√', 'True', True, 1, '1']
                    
                    # 创建服务项目
                    service_item = ServiceItem(
                        service_id=service.service_id,
                        project_name=str(project_name),
                        beautician_name=str(beautician_name),
                        unit_price=amount,
                        is_specified=is_specified
                    )
                    
                    db.session.add(service_item)
                    added_items += 1
            
            imported_items += added_items
            imported_services += 1
            
        except Exception as e:
            errors.append(f"处理记录时出错: {str(e)}")
    
    # 提交事务
    db.session.commit()
    
    return {
        'imported_services': imported_services,
        'imported_items': imported_items,
        'skipped_services': skipped_services,
        'errors': errors
    }

@excel_patch.route('/preview', methods=['POST'])
def preview_excel():
    """预览Excel文件内容"""
    if 'excel_file' not in request.files:
        return jsonify({'code': 1, 'message': '未找到上传的文件'}), 400
    
    file = request.files['excel_file']
    if file.filename == '':
        return jsonify({'code': 1, 'message': '未选择文件'}), 400
    
    try:
        # 读取Excel文件的前几行用于预览
        df = pd.read_excel(file, sheet_name=None, nrows=10)
        
        preview_data = {}
        for sheet_name, sheet_df in df.items():
            # 将DataFrame转换为列表，便于JSON序列化
            preview_data[sheet_name] = {
                'columns': sheet_df.columns.tolist(),
                'data': sheet_df.fillna('').to_dict('records')
            }
        
        return jsonify({
            'code': 0,
            'message': '预览成功',
            'data': preview_data
        })
        
    except Exception as e:
        return jsonify({'code': 1, 'message': f'预览失败: {str(e)}'}), 500

# 注册蓝图函数
def register_excel_patch(app):
    app.register_blueprint(excel_patch, url_prefix='/api/excel')