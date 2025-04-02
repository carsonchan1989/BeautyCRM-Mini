"""
测试API功能的简单脚本
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = 'http://localhost:5000'

def test_health():
    """测试健康检查API"""
    print("\n测试健康检查API...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"响应: {response.json()}")

def test_create_customer():
    """测试创建客户API"""
    print("\n测试创建客户API...")
    customer_data = {
        "name": "李妟绮",
        "gender": "女",
        "age": 28,
        "store": "南区店",
        "hometown": "江苏苏州",
        "residence": "上海市静安区",
        "residence_years": "3年",
        "family_structure": "二口之家",
        "personality_tags": "内向,文艺,注重健康",
        "hobbies": "画画,读书,户外运动",
        "occupation": "平面设计师"
    }

    response = requests.post(
        f"{BASE_URL}/api/customers/",
        json=customer_data
    )

    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

    # 返回客户ID，用于后续测试
    if response.status_code == 201:
        return response.json().get('id')
    return None

def test_get_customers():
    """测试获取客户列表API"""
    print("\n测试获取客户列表API...")
    response = requests.get(f"{BASE_URL}/api/customers/")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

def test_get_customer(customer_id):
    """测试获取单个客户API"""
    print(f"\n测试获取客户详情API (ID: {customer_id})...")
    response = requests.get(f"{BASE_URL}/api/customers/{customer_id}")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

def test_update_customer(customer_id):
    """测试更新客户API"""
    print(f"\n测试更新客户API (ID: {customer_id})...")
    update_data = {
        "annual_income": "50万+"
    }

    response = requests.put(
        f"{BASE_URL}/api/customers/{customer_id}",
        json=update_data
    )

    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

def test_add_health_record(customer_id):
    """测试添加健康档案API"""
    print(f"\n测试添加健康档案API (客户ID: {customer_id})...")
    health_data = {
        "skin_type": "混合性偏油",
        "oil_water_balance": "T区油性明显，U区中性",
        "pores_blackheads": "鼻翼周围毛孔粗大，有轻微黑头",
        "wrinkles_texture": "眼部细纹，皮肤纹理较为粗糙",
        "pigmentation": "颧骨部位有轻微色斑",
        "tcm_constitution": "气虚质",
        "sleep_routine": "经常熬夜，睡眠质量一般",
        "short_term_beauty_goal": "改善肤色不均，控油祛痘",
        "long_term_beauty_goal": "延缓衰老，保持年轻状态"
    }

    response = requests.post(
        f"{BASE_URL}/api/customers/{customer_id}/health",
        json=health_data
    )

    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

def test_add_consumption(customer_id):
    """测试添加消费记录API"""
    print(f"\n测试添加消费记录API (客户ID: {customer_id})...")
    consumption_data = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "project_name": "逆龄焕肤套餐",
        "amount": 1888.00,
        "payment_method": "微信支付",
        "total_sessions": 10,
        "satisfaction": "非常满意"
    }

    response = requests.post(
        f"{BASE_URL}/api/customers/{customer_id}/consumption",
        json=consumption_data
    )

    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

def test_add_service(customer_id):
    """测试添加服务记录API"""
    print(f"\n测试添加服务记录API (客户ID: {customer_id})...")
    service_data = {
        "service_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "departure_time": (datetime.now().replace(hour=datetime.now().hour+2)).strftime("%Y-%m-%d %H:%M:%S"),
        "service_items": "基础护理,特殊护理",
        "beautician": "王美师",
        "total_amount": 300.00,
        "service_amount": 300.00,
        "satisfaction": "满意",
        "is_specified": True
    }

    response = requests.post(
        f"{BASE_URL}/api/customers/{customer_id}/service",
        json=service_data
    )

    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

def test_add_communication(customer_id):
    """测试添加沟通记录API"""
    print(f"\n测试添加沟通记录API (客户ID: {customer_id})...")
    communication_data = {
        "comm_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "comm_location": "电话",
        "comm_content": "客户反馈对上次服务很满意，询问了最新活动，预约了下周二的项目。"
    }

    response = requests.post(
        f"{BASE_URL}/api/customers/{customer_id}/communication",
        json=communication_data
    )

    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

def test_stats():
    """测试客户统计API"""
    print("\n测试客户统计API...")
    response = requests.get(f"{BASE_URL}/api/customers/stats")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

def test_export_excel():
    """测试导出Excel API"""
    print("\n测试导出Excel API...")
    export_data = {
        "include_sections": ["basic", "health", "consumption", "service", "communication"]
    }

    response = requests.post(
        f"{BASE_URL}/api/excel/export",
        json=export_data
    )

    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

def run_all_tests():
    """运行所有测试"""
    test_health()

    # 创建客户
    customer_id = test_create_customer()

    if customer_id:
        # 等待1秒，确保数据已写入
        time.sleep(1)

        # 测试获取客户列表
        test_get_customers()

        # 测试获取单个客户
        test_get_customer(customer_id)

        # 测试更新客户
        test_update_customer(customer_id)

        # 测试添加健康档案
        test_add_health_record(customer_id)

        # 测试添加消费记录
        test_add_consumption(customer_id)
        
        # 测试添加服务记录
        test_add_service(customer_id)
        
        # 测试添加沟通记录
        test_add_communication(customer_id)

        # 测试统计API
        test_stats()

        # 测试导出Excel
        test_export_excel()
    else:
        print("创建客户失败，无法继续后续测试")

if __name__ == "__main__":
    run_all_tests()