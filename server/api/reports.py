"""
报告生成API路由
"""
from flask import Blueprint, request, jsonify, current_app
import os
import sys
import subprocess
from pathlib import Path
from server.models import db, Customer

bp = Blueprint('reports', __name__)

@bp.route('/generate/<customer_id>', methods=['GET'])
def generate_report(customer_id):
    """生成客户报告"""
    # 检查客户是否存在
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({
            'code': 1,
            'message': f'客户 {customer_id} 不存在'
        }), 404
    
    try:
        # 项目根目录
        root_dir = Path(current_app.root_path).parent
        
        # 报告生成脚本路径
        report_script = os.path.join(root_dir, 'md_report_generator.py')
        
        # 运行报告生成脚本
        result = subprocess.run(
            [sys.executable, report_script, customer_id],
            capture_output=True,
            text=True,
            cwd=root_dir
        )
        
        if result.returncode != 0:
            return jsonify({
                'code': 1,
                'message': f'报告生成失败: {result.stderr}'
            }), 500
        
        # 报告文件路径
        report_file = os.path.join(root_dir, f"{customer_id}_customer_report.md")
        
        # 检查报告是否已生成
        if not os.path.exists(report_file):
            return jsonify({
                'code': 1,
                'message': f'报告文件未生成'
            }), 500
        
        # 返回报告文件路径或内容
        with open(report_file, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        return jsonify({
            'code': 0,
            'data': {
                'customer_id': customer_id,
                'customer_name': customer.name,
                'report_content': report_content,
                'report_file': f"{customer_id}_customer_report.md"
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 1,
            'message': f'报告生成出错: {str(e)}'
        }), 500