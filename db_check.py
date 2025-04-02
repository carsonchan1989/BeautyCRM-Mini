import sqlite3
import os

db_path = os.path.join('instance', 'beauty_crm.db')
print(f'数据库路径：{db_path}, 存在：{os.path.exists(db_path)}')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查询所有表
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print('数据库表：')
for table in tables:
    print(f'- {table[0]}')

# 查询 services 表中的记录数
try:
    cursor.execute('SELECT COUNT(*) FROM services')
    count = cursor.fetchone()[0]
    print(f'服务记录数：{count}')
    
    if count > 0:
        # 查询一些服务记录示例
        cursor.execute('SELECT * FROM services LIMIT 5')
        services = cursor.fetchall()
        print('服务记录示例：')
        for service in services:
            print(service)
except Exception as e:
    print(f'查询services表出错: {str(e)}')

# 查询service_items表中的记录数
try:
    cursor.execute('SELECT COUNT(*) FROM service_items')
    count = cursor.fetchone()[0]
    print(f'服务项目数：{count}')
    
    if count > 0:
        # 查询一些服务项目示例
        cursor.execute('SELECT * FROM service_items LIMIT 5')
        items = cursor.fetchall()
        print('服务项目示例：')
        for item in items:
            print(item)
except Exception as e:
    print(f'查询service_items表出错: {str(e)}')

conn.close()
print('数据库检查完成')