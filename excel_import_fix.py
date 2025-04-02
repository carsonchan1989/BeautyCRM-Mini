"""
修复微信小程序Excel导入功能 - 解决服务器连接问题
"""
import sys
import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pandas as pd
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('excel_import_fix')

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 配置上传文件目录
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB

@app.route('/api/excel/import', methods=['POST'])
def import_excel():
    """处理Excel文件上传"""
    logger.info("收到Excel上传请求")
    
    # 检查是否有文件上传
    if 'file' not in request.files:
        logger.error("没有找到上传的文件")
        return jsonify({'code': 1, 'message': '未找到上传的文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        logger.error("未选择文件")
        return jsonify({'code': 1, 'message': '未选择文件'}), 400
    
    if file:
        # 保存上传的文件
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        logger.info(f"保存文件到: {file_path}")
        file.save(file_path)
        
        # 创建响应数据
        response_data = {
            'code': 0, 
            'message': '文件上传成功',
            'data': {
                'fileUrl': f'/uploads/{filename}',
                'fileName': filename,
                'fileSize': os.path.getsize(file_path)
            }
        }
        
        logger.info("文件上传成功")
        return jsonify(response_data)
    
    logger.error("上传失败")
    return jsonify({'code': 1, 'message': '上传失败'}), 500

@app.route('/api/excel/preview', methods=['POST'])
def preview_excel():
    """预览Excel文件内容"""
    logger.info("收到Excel预览请求")
    
    # 检查是否有文件上传
    if 'file' not in request.files:
        logger.error("没有找到上传的文件")
        return jsonify({'code': 1, 'message': '未找到上传的文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        logger.error("未选择文件")
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
        
        logger.info(f"Excel预览成功，共 {len(preview_data)} 个工作表")
        return jsonify({
            'code': 0,
            'message': '预览成功',
            'data': preview_data
        })
        
    except Exception as e:
        logger.error(f"预览失败: {str(e)}")
        return jsonify({'code': 1, 'message': f'预览失败: {str(e)}'}), 500

# 启动服务器
if __name__ == '__main__':
    host = '0.0.0.0'  # 监听所有网络接口，使小程序可以访问
    port = 5000
    
    logger.info(f"启动Excel导入服务器，监听地址: {host}:{port}")
    print(f"* 服务已启动于 http://{host}:{port}/")
    print(f"* 在手机上请使用当前电脑的IP地址代替localhost")
    print(f"* 确保手机和电脑在同一网络环境下")
    
    app.run(host=host, port=port, debug=True)