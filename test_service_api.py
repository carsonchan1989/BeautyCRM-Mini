"""
测试服务记录API是否正常工作
"""
import os
import sys
import json
import unittest
import tempfile
import requests
from datetime import datetime

# 服务器URL
BASE_URL = "http://localhost:5000/api"

def test_get_customer_services():
    """测试获取客户服务记录"""
    # 使用示例客户ID
    customer_id = "C001"
    
    # 测试修复前的API
    url = f"{BASE_URL}/customer/{customer_id}/service"
    print(f"\n测试旧API: {url}")
    try:
        response = requests.get(url)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"获取到 {len(data)} 条服务记录")
            if len(data) > 0:
                # 打印第一条记录的关键字段
                first_record = data[0]
                print(f"第一条记录:")
                print(f"  服务ID: {first_record.get('service_id')}")
                print(f"  服务日期: {first_record.get('service_date')}")
                print(f"  总金额: {first_record.get('total_amount')}")
                
                # 检查服务项目
                service_items = first_record.get('service_items', [])
                print(f"  服务项目数量: {len(service_items)}")
                if len(service_items) > 0:
                    print(f"  第一个项目: {service_items[0].get('project_name')}")
                    print(f"  美容师: {service_items[0].get('beautician_name')}")
        else:
            print(f"API请求失败: {response.text}")
    except Exception as e:
        print(f"请求出错: {str(e)}")
    
    # 测试修复后的API
    url = f"{BASE_URL}/customer/{customer_id}/services"
    print(f"\n测试新API: {url}")
    try:
        response = requests.get(url)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success', False):
                items = data.get('data', {}).get('items', [])
                print(f"获取到 {len(items)} 条服务记录")
                if len(items) > 0:
                    # 打印第一条记录的关键字段
                    first_record = items[0]
                    print(f"第一条记录:")
                    print(f"  服务ID: {first_record.get('service_id')}")
                    print(f"  服务日期: {first_record.get('service_date')}")
                    print(f"  总金额: {first_record.get('total_amount')}")
                    print(f"  项目汇总: {first_record.get('project_summary')}")
                    print(f"  美容师汇总: {first_record.get('beautician_summary')}")
                    
                    # 检查服务项目
                    service_items = first_record.get('service_items', [])
                    print(f"  服务项目数量: {len(service_items)}")
                    if len(service_items) > 0:
                        print(f"  第一个项目: {service_items[0].get('project_name')}")
                        print(f"  美容师: {service_items[0].get('beautician_name')}")
            else:
                print(f"API响应错误: {data.get('message')}")
        else:
            print(f"API请求失败: {response.text}")
    except Exception as e:
        print(f"请求出错: {str(e)}")

def test_get_service_detail():
    """测试获取服务记录详情"""
    # 使用示例客户ID和服务ID
    customer_id = "C001"
    
    # 先获取一个服务ID
    try:
        response = requests.get(f"{BASE_URL}/customer/{customer_id}/services")
        if response.status_code == 200:
            data = response.json()
            if data.get('success', False):
                items = data.get('data', {}).get('items', [])
                if len(items) > 0:
                    service_id = items[0].get('service_id')
                    print(f"\n测试服务详情API，服务ID: {service_id}")
                    
                    # 获取服务详情
                    detail_url = f"{BASE_URL}/customer/{customer_id}/service/{service_id}"
                    detail_response = requests.get(detail_url)
                    print(f"状态码: {detail_response.status_code}")
                    
                    if detail_response.status_code == 200:
                        detail_data = detail_response.json()
                        if detail_data.get('success', False):
                            service = detail_data.get('data', {})
                            print(f"服务详情:")
                            print(f"  服务ID: {service.get('service_id')}")
                            print(f"  服务日期: {service.get('service_date')}")
                            print(f"  总金额: {service.get('total_amount')}")
                            print(f"  项目汇总: {service.get('project_summary')}")
                            print(f"  美容师汇总: {service.get('beautician_summary')}")
                            
                            # 检查服务项目
                            service_items = service.get('service_items', [])
                            print(f"  服务项目数量: {len(service_items)}")
                            for idx, item in enumerate(service_items, 1):
                                print(f"  项目 {idx}: {item.get('project_name')} - ¥{item.get('unit_price')} - 美容师: {item.get('beautician_name')}")
                        else:
                            print(f"API响应错误: {detail_data.get('message')}")
                    else:
                        print(f"API请求失败: {detail_response.text}")
                else:
                    print("没有找到服务记录")
            else:
                print(f"API响应错误: {data.get('message')}")
        else:
            print(f"API请求失败: {response.text}")
    except Exception as e:
        print(f"请求出错: {str(e)}")

if __name__ == "__main__":
    print("===== 开始测试服务记录API =====")
    test_get_customer_services()
    test_get_service_detail()
    print("\n===== 测试完成 =====")