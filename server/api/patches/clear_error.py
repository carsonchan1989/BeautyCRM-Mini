"""
修复API错误的补丁，添加错误处理和异常捕获
"""
from flask import jsonify
import traceback

def apply_error_handling_patch(app):
    """
    为Flask应用添加全局错误处理
    
    Args:
        app: Flask应用实例
    """
    # 注册全局错误处理
    @app.errorhandler(400)
    def handle_bad_request(e):
        app.logger.warning(f"400错误: {str(e)}")
        return jsonify({
            'code': 1,
            'message': f'请求错误: {str(e)}'
        }), 400
    
    @app.errorhandler(404)
    def handle_not_found(e):
        app.logger.warning(f"404错误: {str(e)}")
        return jsonify({
            'code': 1,
            'message': '请求的资源不存在'
        }), 404
    
    @app.errorhandler(500)
    def handle_server_error(e):
        app.logger.error(f"500服务器错误: {str(e)}")
        # 获取详细的错误堆栈
        error_traceback = traceback.format_exc()
        app.logger.error(error_traceback)
        
        return jsonify({
            'code': 1,
            'message': '服务器内部错误，请稍后重试'
        }), 500
    
    # 注册全局异常处理
    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f"未处理的异常: {str(e)}")
        # 获取详细的错误堆栈
        error_traceback = traceback.format_exc()
        app.logger.error(error_traceback)
        
        return jsonify({
            'code': 1,
            'message': f'服务器异常: {str(e)}'
        }), 500