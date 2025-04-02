"""
将数据库中的客户数据导出为Markdown文档
"""
import os
import sys
from datetime import datetime
from models import db, Customer, HealthRecord, Consumption, Service, Communication
from flask import Flask

def export_customers_to_markdown():
    """将所有客户数据导出为Markdown格式"""
    try:
        # 获取所有客户
        customers = Customer.query.all()
        if not customers:
            print("数据库中没有客户数据")
            return
        
        # 创建导出目录
        export_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports')
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        
        # 创建导出文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = os.path.join(export_dir, f'customer_data_export_{timestamp}.md')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('# 客户数据导出\n\n')
            f.write(f'生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
            f.write(f'总客户数: {len(customers)}\n\n')
            
            # 客户汇总表
            f.write('## 客户基本信息汇总\n\n')
            f.write('| ID | 姓名 | 性别 | 年龄 | 门店 | 家乡 | 居住地 | 职业 | 风险敏感度 |\n')
            f.write('|----|----|----|----|----|----|----|----|----|\n')
            
            for customer in customers:
                c = customer.to_dict()
                f.write(f"| {c.get('id', 'N/A')} | {c.get('name', 'N/A')} | {c.get('gender', 'N/A')} | " +
                        f"{c.get('age', 'N/A')} | {c.get('store', 'N/A')} | {c.get('hometown', 'N/A')} | " +
                        f"{c.get('residence', 'N/A')} | {c.get('occupation', 'N/A')} | " +
                        f"{c.get('risk_sensitivity', 'N/A')} |\n")
            
            f.write('\n\n')
            
            # 详细客户信息
            f.write('## 客户详细信息\n\n')
            
            for customer in customers:
                c = customer.to_dict()
                f.write(f"### 客户 ID: {c.get('id', 'N/A')} - {c.get('name', 'N/A')}\n\n")
                
                # 基本信息
                f.write('#### 基本信息\n\n')
                f.write('| 字段 | 值 |\n')
                f.write('|----|----|\n')
                for key, value in c.items():
                    if key not in ['id', 'created_at', 'updated_at', 'health_records', 
                                   'consumption_records', 'service_records', 'communication_records']:
                        f.write(f"| {key} | {value if value not in [None, ''] else 'N/A'} |\n")
                
                f.write('\n')
                
                # 健康记录
                health_records = HealthRecord.query.filter_by(customer_id=customer.id).all()
                if health_records:
                    f.write('#### 健康记录\n\n')
                    f.write('| ID | 检测项目 | 检测结果 | 检测时间 | 备注 |\n')
                    f.write('|----|----|----|----|----|----|\n')
                    
                    for record in health_records:
                        r = record.to_dict()
                        test_time = r.get('test_time')
                        if isinstance(test_time, datetime):
                            test_time = test_time.strftime('%Y-%m-%d %H:%M:%S')
                        
                        f.write(f"| {r.get('id', 'N/A')} | {r.get('test_item', 'N/A')} | " +
                                f"{r.get('test_result', 'N/A')} | {test_time or 'N/A'} | " +
                                f"{r.get('remarks', 'N/A')} |\n")
                    
                    f.write('\n')
                
                # 消费记录
                consumption_records = Consumption.query.filter_by(customer_id=customer.id).all()
                if consumption_records:
                    f.write('#### 消费记录\n\n')
                    f.write('| ID | 项目名称 | 金额 | 消费日期 | 消费类型 | 支付方式 | 备注 |\n')
                    f.write('|----|----|----|----|----|----|----|\n')
                    
                    for record in consumption_records:
                        r = record.to_dict()
                        date = r.get('date')
                        if isinstance(date, datetime):
                            date = date.strftime('%Y-%m-%d %H:%M:%S')
                        
                        f.write(f"| {r.get('id', 'N/A')} | {r.get('item_name', 'N/A')} | " +
                                f"{r.get('amount', 'N/A')} | {date or 'N/A'} | " +
                                f"{r.get('consumption_type', 'N/A')} | {r.get('payment_method', 'N/A')} | " +
                                f"{r.get('remarks', 'N/A')} |\n")
                    
                    f.write('\n')
                
                # 服务记录
                service_records = Service.query.filter_by(customer_id=customer.id).all()
                if service_records:
                    f.write('#### 服务记录\n\n')
                    f.write('| ID | 服务项目 | 服务日期 | 技师 | 到店时间 | 离店时间 | 备注 |\n')
                    f.write('|----|----|----|----|----|----|----|\n')
                    
                    for record in service_records:
                        r = record.to_dict()
                        service_date = r.get('service_date')
                        if isinstance(service_date, datetime):
                            service_date = service_date.strftime('%Y-%m-%d %H:%M:%S')
                        
                        arrival_time = r.get('arrival_time')
                        if isinstance(arrival_time, datetime):
                            arrival_time = arrival_time.strftime('%Y-%m-%d %H:%M:%S')
                        
                        departure_time = r.get('departure_time')
                        if isinstance(departure_time, datetime):
                            departure_time = departure_time.strftime('%Y-%m-%d %H:%M:%S')
                        
                        f.write(f"| {r.get('id', 'N/A')} | {r.get('service_item', 'N/A')} | " +
                                f"{service_date or 'N/A'} | {r.get('technician', 'N/A')} | " +
                                f"{arrival_time or 'N/A'} | {departure_time or 'N/A'} | " +
                                f"{r.get('remarks', 'N/A')} |\n")
                    
                    f.write('\n')
                
                # 沟通记录
                communication_records = Communication.query.filter_by(customer_id=customer.id).all()
                if communication_records:
                    f.write('#### 沟通记录\n\n')
                    f.write('| ID | 沟通方式 | 沟通时间 | 沟通内容 | 跟进需求 | 负责人 |\n')
                    f.write('|----|----|----|----|----|----|\n')
                    
                    for record in communication_records:
                        r = record.to_dict()
                        comm_time = r.get('comm_time')
                        if isinstance(comm_time, datetime):
                            comm_time = comm_time.strftime('%Y-%m-%d %H:%M:%S')
                        
                        f.write(f"| {r.get('id', 'N/A')} | {r.get('comm_method', 'N/A')} | " +
                                f"{comm_time or 'N/A'} | {r.get('content', 'N/A')} | " +
                                f"{r.get('follow_up_needed', 'N/A')} | {r.get('staff', 'N/A')} |\n")
                    
                    f.write('\n')
                
                f.write('\n---\n\n')
        
        print(f"导出完成，文件保存在: {file_path}")
        return file_path
    
    except Exception as e:
        print(f"导出失败: {str(e)}")
        return None

if __name__ == '__main__':
    # 创建Flask应用并初始化数据库连接
    app = Flask(__name__)
    
    # 直接设置配置
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///beauty_crm.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your-secret-key'
    
    # 初始化数据库
    db.init_app(app)
    
    with app.app_context():
        export_customers_to_markdown()