"""
清理服务记录数据
"""
import os
import sqlite3

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'beauty_crm.db')

# 连接数据库
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 清理数据
try:
    cursor.execute('DELETE FROM service_items')
    print('服务项目表数据已清理')
except Exception as e:
    print(f'清理服务项目表失败: {str(e)}')

try:
    cursor.execute('DELETE FROM services')
    print('服务记录表数据已清理')
except Exception as e:
    print(f'清理服务记录表失败: {str(e)}')

# 尝试重置自增ID
try:
    cursor.execute('DELETE FROM sqlite_sequence WHERE name="services" OR name="service_items"')
    print('自增ID已重置')
except Exception as e:
    print(f'重置自增ID失败: {str(e)}')

# 提交更改
conn.commit()

# 关闭连接
cursor.close()
conn.close()

print('清理操作已完成')