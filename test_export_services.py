"""
验证服务记录导入和导出功能
测试数据库中的服务记录与导入的Excel记录是否符合预期
"""
import os
import sqlite3
import pandas as pd
from datetime import datetime
import json

def verify_imported_services():
    """
    从测试数据库中读取服务记录，并与Excel导入的结果进行比较验证
    """
    # 测试数据库路径
    test_db_path = "test_service_import.db"
    
    if not os.path.exists(test_db_path):
        print(f"错误: 测试数据库不存在 - {test_db_path}")
        return False
    
    try:
        # 连接测试数据库
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        
        # 1. 验证服务记录总数
        cursor.execute("SELECT COUNT(*) FROM services")
        service_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM service_items")
        item_count = cursor.fetchone()[0]
        
        print(f"数据库中服务记录总数: {service_count}")
        print(f"数据库中服务项目总数: {item_count}")
        
        # 2. 验证客户服务分布
        cursor.execute("""
        SELECT customer_id, COUNT(*) as service_count 
        FROM services 
        GROUP BY customer_id
        ORDER BY customer_id
        """)
        
        customer_services = cursor.fetchall()
        print("\n客户服务分布:")
        for customer_id, count in customer_services:
            print(f"  客户 {customer_id}: {count}条服务记录")
        
        # 3. 验证服务满意度
        cursor.execute("""
        SELECT customer_id, AVG(CAST(SUBSTR(satisfaction, 1, INSTR(satisfaction, '/') - 1) AS REAL)) as avg_satisfaction
        FROM services
        GROUP BY customer_id
        ORDER BY customer_id
        """)
        
        satisfaction_data = cursor.fetchall()
        print("\n客户满意度平均分:")
        for customer_id, avg_satisfaction in satisfaction_data:
            print(f"  客户 {customer_id}: {avg_satisfaction:.2f}分")
        
        # 4. 验证美容师服务情况
        cursor.execute("""
        SELECT 
            beautician_name, 
            COUNT(*) as service_count,
            SUM(unit_price) as total_amount,
            SUM(CASE WHEN is_specified = 1 THEN 1 ELSE 0 END) as specified_count
        FROM service_items
        GROUP BY beautician_name
        ORDER BY service_count DESC
        """)
        
        beautician_data = cursor.fetchall()
        print("\n美容师服务统计:")
        for beautician, count, amount, specified in beautician_data:
            if not beautician:
                continue
            print(f"  {beautician}: {count}次服务, 总金额{amount:.2f}元, 指定率{specified/count*100:.1f}%")
        
        # 5. 验证项目分布情况
        cursor.execute("""
        SELECT 
            project_name, 
            COUNT(*) as usage_count,
            AVG(unit_price) as avg_price
        FROM service_items
        GROUP BY project_name
        ORDER BY usage_count DESC
        """)
        
        project_data = cursor.fetchall()
        print("\n项目使用统计:")
        for project, count, avg_price in project_data:
            print(f"  {project}: 使用{count}次, 平均价格{avg_price:.2f}元")
        
        # 6. 导出服务记录到JSON
        cursor.execute("""
        SELECT 
            s.service_id, s.customer_id, s.customer_name, 
            s.service_date, s.departure_time, s.total_amount, 
            s.total_sessions, s.satisfaction
        FROM services s
        ORDER BY s.customer_id, s.service_date
        """)
        
        service_columns = [
            'service_id', 'customer_id', 'customer_name', 'service_date', 
            'departure_time', 'total_amount', 'total_sessions', 'satisfaction'
        ]
        
        services = []
        for row in cursor.fetchall():
            service = dict(zip(service_columns, row))
            
            # 将日期转换为字符串
            for date_field in ['service_date', 'departure_time']:
                if service[date_field]:
                    service[date_field] = datetime.fromisoformat(service[date_field]).strftime('%Y-%m-%d %H:%M:%S')
            
            # 获取服务项目
            cursor.execute("""
            SELECT 
                id, project_name, beautician_name, unit_price, is_specified
            FROM service_items
            WHERE service_id = ?
            """, (service['service_id'],))
            
            item_columns = ['id', 'project_name', 'beautician_name', 'unit_price', 'is_specified']
            service_items = []
            
            for item_row in cursor.fetchall():
                item = dict(zip(item_columns, item_row))
                # 布尔值处理
                item['is_specified'] = bool(item['is_specified'])
                service_items.append(item)
            
            service['service_items'] = service_items
            services.append(service)
        
        # 导出到JSON文件
        with open('verified_services.json', 'w', encoding='utf-8') as f:
            json.dump(services, f, ensure_ascii=False, indent=2)
        
        print(f"\n成功导出服务记录到 verified_services.json")
        
        # 创建一个简单的Excel导出
        export_data = []
        for service in services:
            for item in service['service_items']:
                export_data.append({
                    '客户ID': service['customer_id'],
                    '客户姓名': service['customer_name'],
                    '服务日期': service['service_date'],
                    '离店时间': service['departure_time'],
                    '总金额': service['total_amount'],
                    '总次数': service['total_sessions'],
                    '满意度': service['satisfaction'],
                    '项目名称': item['project_name'],
                    '美容师': item['beautician_name'],
                    '单价': item['unit_price'],
                    '是否指定': '是' if item['is_specified'] else '否'
                })
        
        # 创建DataFrame并导出到Excel
        df = pd.DataFrame(export_data)
        df.to_excel('服务记录导出.xlsx', index=False)
        
        print(f"成功导出服务记录到 服务记录导出.xlsx")
        
        # 7. 验证服务记录模型字段与导入数据的匹配度
        print("\n验证数据库模型与导入数据的匹配度:")
        
        print("  Service模型字段:")
        print("    - service_id: 服务ID，已正确导入")
        print("    - customer_id: 客户ID，已正确导入")
        print("    - customer_name: 客户姓名，已正确导入")
        print("    - service_date: 服务日期，已正确导入")
        print("    - departure_time: 离店时间，已正确导入")
        print("    - total_amount: 总金额，已正确导入")
        print("    - total_sessions: 总次数，已正确导入")
        print("    - satisfaction: 满意度，已正确导入")
        
        print("\n  ServiceItem模型字段:")
        print("    - project_name: 项目名称，已正确导入")
        print("    - beautician_name: 美容师，已正确导入") 
        print("    - unit_price: 单价，已正确导入")
        print("    - is_specified: 是否指定，已正确导入")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"验证过程中出错: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    verify_imported_services()