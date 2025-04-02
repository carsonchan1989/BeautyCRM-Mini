import requests
import json

BASE_URL = "http://localhost:5000/api"

def get_data(endpoint):
    response = requests.get(f"{BASE_URL}/{endpoint}")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching {endpoint}: {response.status_code}")
        return None

def check_customer_data():
    # 获取客户列表
    customers_data = get_data("customers")
    if not customers_data:
        return

    print(f"总客户数: {customers_data.get('total', 0)}")
    
    # 逐个检查客户详情
    for customer in customers_data.get("items", []):
        customer_id = customer.get("id")
        name = customer.get("name")
        print(f"\n客户: {name} (ID: {customer_id})")
        
        # 获取沟通记录
        communications = get_data(f"customers/{customer_id}/communication")
        if communications:
            print(f"沟通记录数: {len(communications)}")
            for comm in communications:
                print(f"  日期: {comm.get('communication_date')}, 类型: {comm.get('communication_type')}, 内容: {comm.get('communication_content')}")
        
        # 获取服务记录
        services = get_data(f"customers/{customer_id}/service")
        if services:
            print(f"服务记录数: {len(services)}")
            for service in services[:3]:  # 只显示前3条
                print(f"  日期: {service.get('service_date')}, 金额: {service.get('total_amount')}")
            if len(services) > 3:
                print(f"  ... 及其他 {len(services)-3} 条记录")

if __name__ == "__main__":
    print("===== 检查数据导入结果 =====")
    check_customer_data()
    print("\n===== 检查完成 =====")