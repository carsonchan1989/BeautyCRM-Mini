"""
插入测试服务记录，用于验证报告生成功能
"""
import sqlite3
import uuid
from datetime import datetime

# 数据库连接
conn = sqlite3.connect('instance/beauty_crm.db')
cursor = conn.cursor()

# 创建服务记录
def create_service(customer_id, service_date, departure_time, total_amount, total_sessions, satisfaction):
    service_id = f"S{uuid.uuid4().hex[:8].upper()}"
    
    # 插入服务记录
    cursor.execute("""
        INSERT INTO services 
        (service_id, customer_id, customer_name, service_date, departure_time, 
         total_amount, total_sessions, satisfaction, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        service_id,
        customer_id,
        f"客户{customer_id}",
        service_date,
        departure_time,
        total_amount,
        total_sessions,
        satisfaction,
        datetime.now(),
        datetime.now()
    ))
    
    print(f"创建服务记录: {service_id}")
    return service_id

# 创建服务项目
def create_service_item(service_id, project_name, beautician_name, unit_price, is_specified):
    cursor.execute("""
        INSERT INTO service_items
        (service_id, project_name, beautician_name, unit_price, is_specified, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        service_id,
        project_name,
        beautician_name,
        unit_price,
        is_specified,
        datetime.now(),
        datetime.now()
    ))
    
    print(f"创建服务项目: {project_name} - {beautician_name}")

# 测试数据
test_data = [
    {
        "customer_id": "C003",
        "service_date": "2023-12-01 19:00:00",
        "departure_time": "2023-12-01 21:30:00",
        "total_amount": 1840.0,
        "total_sessions": 2,
        "satisfaction": "4.9/5",
        "items": [
            {"project_name": "黄金射频紧致疗程", "beautician_name": "周杰", "unit_price": 1360.0, "is_specified": True},
            {"project_name": "帝王艾灸调理", "beautician_name": "王芳", "unit_price": 480.0, "is_specified": False}
        ]
    },
    {
        "customer_id": "C003",
        "service_date": "2023-11-18 18:45:00",
        "departure_time": "2023-11-18 20:15:00",
        "total_amount": 293.0,
        "total_sessions": 1,
        "satisfaction": "4.3/5",
        "items": [
            {"project_name": "极光净透泡泡", "beautician_name": "周杰", "unit_price": 293.0, "is_specified": False}
        ]
    },
    {
        "customer_id": "C003",
        "service_date": "2023-11-05 21:00:00",
        "departure_time": "2023-11-05 23:30:00",
        "total_amount": 730.5,
        "total_sessions": 2,
        "satisfaction": "4.7/5",
        "items": [
            {"project_name": "帝王艾灸调理", "beautician_name": "周杰", "unit_price": 533.0, "is_specified": True},
            {"project_name": "足部SPA", "beautician_name": "杨树", "unit_price": 197.5, "is_specified": True}
        ]
    }
]

try:
    # 清空现有服务记录
    cursor.execute("DELETE FROM service_items")
    cursor.execute("DELETE FROM services")
    conn.commit()
    print("清空现有服务记录")
    
    # 插入测试数据
    for service_data in test_data:
        # 创建服务记录
        service_id = create_service(
            service_data["customer_id"],
            service_data["service_date"],
            service_data["departure_time"],
            service_data["total_amount"],
            service_data["total_sessions"],
            service_data["satisfaction"]
        )
        
        # 创建服务项目
        for item in service_data["items"]:
            create_service_item(
                service_id,
                item["project_name"],
                item["beautician_name"],
                item["unit_price"],
                item["is_specified"]
            )
    
    # 提交事务
    conn.commit()
    print("测试数据导入成功")
    
except Exception as e:
    conn.rollback()
    print(f"导入失败: {e}")
    
finally:
    conn.close()