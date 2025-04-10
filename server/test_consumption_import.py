#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
消耗记录导入测试脚本
"""

import os
import sys
import json
import unittest
import tempfile
import pandas as pd
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目模块
from models import db, Customer, Service, ServiceItem, Project
from utils.consumption_excel_processor import ConsumptionExcelProcessor

class TestConsumptionImport(unittest.TestCase):
    """测试消耗记录导入功能"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试应用
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app.config['UPLOAD_FOLDER'] = self.temp_dir
        self.app.config['EXPORT_FOLDER'] = self.temp_dir
        
        # 初始化数据库
        db.init_app(self.app)
        
        # 创建应用上下文
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # 创建数据库表
        db.create_all()
        
        # 创建测试数据
        self._create_test_data()
        
        # 测试Excel文件路径
        self.excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                              'uploads', '模拟-客户信息档案.xlsx')
        
        # 确保Excel文件存在
        if not os.path.exists(self.excel_path):
            print(f"警告：测试Excel文件不存在：{self.excel_path}")
            print("请确保测试数据文件存在，否则测试将失败")
    
    def tearDown(self):
        """清理测试环境"""
        # 清理数据库
        db.session.remove()
        db.drop_all()
        
        # 清理上下文
        self.app_context.pop()
        
        # 移除临时目录
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def _create_test_data(self):
        """创建测试数据"""
        # 创建测试项目
        project1 = Project(
            id="PRJ-2023-001",
            name="美白嫩肤",
            category="面部护理",
            price=1000.0,
            duration=60,
            description="高效美白嫩肤项目",
            status="active"
        )
        
        project2 = Project(
            id="PRJ-2023-002",
            name="深层清洁",
            category="面部护理",
            price=800.0,
            duration=45,
            description="深层清洁毛孔项目",
            status="active"
        )
        
        # 创建测试客户
        customer = Customer(
            id="CST-2023-001",
            name="张三",
            gender="女",
            age=30,
            store="总店"
        )
        
        # 添加测试数据并提交到数据库
        db.session.add(project1)
        db.session.add(project2)
        db.session.add(customer)
        
        try:
            db.session.commit()
            print("测试数据创建成功")
        except Exception as e:
            db.session.rollback()
            print(f"测试数据创建失败：{str(e)}")
            raise
    
    def test_read_consumption_excel(self):
        """测试读取消耗记录Excel"""
        # 检查测试文件是否存在
        if not os.path.exists(self.excel_path):
            print(f"测试文件不存在: {self.excel_path}，跳过测试")
            return
            
        try:
            # 使用pandas读取Excel文件中的消耗子表
            df = pd.read_excel(self.excel_path, sheet_name='消耗')
            
            # 验证是否成功读取
            self.assertIsNotNone(df)
            self.assertTrue(len(df) > 0)
            
            # 打印读取的记录数和前两行数据作为示例
            print(f"成功读取消耗记录 {len(df)} 条")
            if len(df) > 0:
                print("第一条记录示例：")
                print(df.iloc[0])
            
            # 转换为记录列表
            records = df.to_dict('records')
            self.assertIsInstance(records, list)
            
            return records
        except Exception as e:
            self.fail(f"读取Excel文件失败: {str(e)}")
    
    def test_consumption_excel_processor(self):
        """测试ConsumptionExcelProcessor处理Excel"""
        # 检查测试文件是否存在
        if not os.path.exists(self.excel_path):
            print(f"测试文件不存在: {self.excel_path}，跳过测试")
            return
            
        try:
            processor = ConsumptionExcelProcessor()
            
            # 调用处理函数
            result = processor.process_file(self.excel_path)
            
            # 验证处理结果
            self.assertIsNotNone(result)
            self.assertIn('records', result)
            self.assertIn('stats', result)
            
            # 打印处理统计信息
            print(f"处理结果：{json.dumps(result['stats'], ensure_ascii=False, indent=2)}")
            
            # 返回处理的记录
            return result['records']
        except Exception as e:
            self.fail(f"消耗记录处理失败: {str(e)}")
    
    def test_api_import_excel(self):
        """测试API导入Excel功能"""
        # 检查测试文件是否存在
        if not os.path.exists(self.excel_path):
            print(f"测试文件不存在: {self.excel_path}，跳过测试")
            return
        
        # 导入API路由模块
        from api.service_routes import service_bp
        self.app.register_blueprint(service_bp, url_prefix='/api/services')
        
        # 创建测试客户端
        client = self.app.test_client()
        
        # 构建导入请求
        with open(self.excel_path, 'rb') as file:
            response = client.post(
                '/api/services/import-consumption',
                data={
                    'file': (file, '模拟-客户信息档案.xlsx'),
                    'import_mode': 'add'
                },
                content_type='multipart/form-data'
            )
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertTrue(data['success'])
        
        # 验证导入后的数据
        services_count = Service.query.count()
        service_items_count = ServiceItem.query.count()
        
        print(f"导入后服务记录数：{services_count}")
        print(f"导入后服务项目数：{service_items_count}")
        
        self.assertTrue(services_count > 0)
        self.assertTrue(service_items_count > 0)
    
    def test_generate_md_report(self):
        """测试生成消耗记录的Markdown报告"""
        # 先创建一些服务记录
        service = Service(
            service_id="SVC-2023-001",
            customer_id="CST-2023-001",
            customer_name="张三",
            service_date=datetime.now(),
            total_amount=1800.0,
            payment_method="卡扣",
            operator="王医师",
            remark="常规服务"
        )
        
        item1 = ServiceItem(
            service_id=service.service_id,
            project_id="PRJ-2023-001",
            project_name="美白嫩肤",
            card_deduction=1000.0,
            quantity=1,
            unit_price=1000.0,
            remark="客户反馈良好"
        )
        
        item2 = ServiceItem(
            service_id=service.service_id,
            project_id="PRJ-2023-002",
            project_name="深层清洁",
            card_deduction=800.0,
            quantity=1,
            unit_price=800.0,
            remark="需要后续跟进"
        )
        
        db.session.add(service)
        db.session.add(item1)
        db.session.add(item2)
        db.session.commit()
        
        # 从API路由导入生成报告函数
        from api.service_routes import generate_service_report
        
        # 生成报告
        customer_id = "CST-2023-001"
        report_path = os.path.join(self.temp_dir, f"{customer_id}_services.md")
        
        result = generate_service_report(customer_id, report_path)
        
        # 验证报告是否生成
        self.assertTrue(os.path.exists(report_path))
        self.assertTrue(result['success'])
        
        # 打印报告内容
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
            print("生成的服务记录报告示例：")
            print(report_content[:500] + "..." if len(report_content) > 500 else report_content)
        
        return report_path

if __name__ == '__main__':
    unittest.main()