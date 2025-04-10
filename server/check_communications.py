from app import create_app
app = create_app()
from models import Communication, Customer
import json

with app.app_context():
    # 获取所有客户
    customers = Customer.query.all()
    print(f"总客户数: {len(customers)}")
    
    # 查询每个客户的沟通记录
    results = {}
    for customer in customers:
        records = Communication.query.filter_by(customer_id=customer.id).all()
        print(f"\n客户: {customer.name} (ID: {customer.id})")
        print(f"沟通记录数: {len(records)}")
        
        if records:
            print("沟通记录详情:")
            for r in records:
                print(f"  日期: {r.communication_date}, 类型: {r.communication_type}, 内容: {r.communication_content}")
        
        results[customer.id] = {
            "name": customer.name,
            "records_count": len(records),
            "records": [
                {
                    "date": r.communication_date.strftime('%Y-%m-%d %H:%M:%S') if r.communication_date else None,
                    "type": r.communication_type,
                    "content": r.communication_content,
                    "staff": r.staff_name
                } 
                for r in records
            ]
        }
    
    # 将结果保存到文件
    with open("communication_check.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        print("\n结果已保存到 communication_check.json")