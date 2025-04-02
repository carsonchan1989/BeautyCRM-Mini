"""
修复客户服务记录API - 适配最新数据库表结构
"""
from flask import Blueprint, jsonify, current_app
from sqlalchemy import func
from models import db, Service, ServiceItem, Customer
import logging

# 配置日志
logger = logging.getLogger(__name__)

def get_customer_services_with_items(customer_id):
    """
    获取客户服务记录，包含服务项目详情
    适配新的数据库表结构
    
    Args:
        customer_id: 客户ID
    
    Returns:
        list: 包含详细服务项目的服务记录列表
    """
    try:
        # 检查客户是否存在
        customer = Customer.query.get(customer_id)
        if not customer:
            return None, "客户不存在"
            
        # 获取所有服务记录
        services = Service.query.filter_by(customer_id=customer_id).order_by(Service.service_date.desc()).all()
        
        result = []
        for service in services:
            # 获取服务基础数据
            service_data = service.to_dict()
            
            # 确保service_items已完整加载
            if not service_data.get('service_items') and service.service_items:
                service_data['service_items'] = [item.to_dict() for item in service.service_items]
                
            # 增加服务项目名称汇总
            if service.service_items:
                projects = [item.project_name for item in service.service_items if item.project_name]
                service_data['project_summary'] = "、".join(projects)
            else:
                service_data['project_summary'] = ""
                
            # 增加美容师汇总
            if service.service_items:
                beauticians = set([item.beautician_name for item in service.service_items 
                                if item.beautician_name and item.beautician_name.strip()])
                service_data['beautician_summary'] = "、".join(beauticians) if beauticians else ""
            else:
                service_data['beautician_summary'] = ""
                
            result.append(service_data)
            
        return result, None
            
    except Exception as e:
        logger.error(f"获取客户服务记录出错: {str(e)}")
        return None, f"获取服务记录失败: {str(e)}"

def update_customer_api_routes(app, customer_bp):
    """
    更新客户API路由，添加修复后的服务记录获取路由
    
    Args:
        app: Flask应用实例
        customer_bp: 客户API蓝图
    """
    @customer_bp.route('/<customer_id>/service/detail', methods=['GET'])
    def get_customer_services_detail(customer_id):
        """获取客户服务记录详情 - 包含服务项目详情"""
        # 获取详细服务记录
        services, error = get_customer_services_with_items(customer_id)
        
        if error:
            return jsonify({'success': False, 'message': error}), 404 if "不存在" in error else 500
            
        return jsonify({
            'success': True, 
            'data': services, 
            'message': '获取服务记录成功'
        })
        
    @app.template_filter('get_service_details')
    def get_service_details_filter(service):
        """
        Jinja2模板过滤器 - 获取服务记录详情
        可用于模板中渲染服务记录详情
        """
        if not service:
            return {"project_summary": "", "beautician_summary": ""}
            
        service_data = {}
        
        # 如果传入的是字典
        if isinstance(service, dict):
            service_data = service
            
            # 如果没有汇总信息，尝试生成
            if 'project_summary' not in service_data and 'service_items' in service_data:
                items = service_data.get('service_items', [])
                projects = [item.get('project_name', '') for item in items if item.get('project_name')]
                service_data['project_summary'] = "、".join(projects)
                
                beauticians = set([item.get('beautician_name', '') for item in items 
                               if item.get('beautician_name') and item.get('beautician_name').strip()])
                service_data['beautician_summary'] = "、".join(beauticians) if beauticians else ""
        
        # 如果传入的是Service模型实例
        elif hasattr(service, 'to_dict'):
            service_data = service.to_dict()
            
            # 获取服务项目和美容师汇总
            if hasattr(service, 'service_items') and service.service_items:
                projects = [item.project_name for item in service.service_items if item.project_name]
                service_data['project_summary'] = "、".join(projects)
                
                beauticians = set([item.beautician_name for item in service.service_items 
                               if item.beautician_name and item.beautician_name.strip()])
                service_data['beautician_summary'] = "、".join(beauticians) if beauticians else ""
            else:
                service_data['project_summary'] = ""
                service_data['beautician_summary'] = ""
        
        return service_data
        
    logger.info("客户服务记录API路由更新完成")
    return customer_bp