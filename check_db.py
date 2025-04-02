import sqlite3
import os

def check_db_file(db_path):
    print(f"检查数据库: {db_path}")
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    print(f"数据库文件存在: {db_path}")
    print(f"文件大小: {os.path.getsize(db_path)} 字节")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查询所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("数据库中的表:")
        for table in tables:
            print(f"- {table[0]}")
        
        # 如果services表存在，查询其结构
        if ('services',) in tables:
            cursor.execute("PRAGMA table_info(services);")
            columns = cursor.fetchall()
            print("\nservices表结构:")
            for col in columns:
                print(f"- {col[1]} ({col[2]})")
        else:
            print("\nservices表不存在")
        
        conn.close()
        return True
    except Exception as e:
        print(f"访问数据库时出错: {str(e)}")
        return False

def find_and_check_dbs():
    possible_paths = [
        "beauty_crm.db",
        "server/beauty_crm.db",
        "server/instance/beauty_crm.db",
        "instance/beauty_crm.db",
        "database.db",
        "server/database.db"
    ]
    
    found = False
    for path in possible_paths:
        full_path = os.path.abspath(path)
        if os.path.exists(full_path):
            found = check_db_file(full_path) or found
    
    if not found:
        print("\n未找到任何SQLite数据库文件")
        
        # 列出当前目录所有文件
        print("\n当前目录下的数据库文件:")
        for file in os.listdir("."):
            if os.path.isfile(file) and (file.endswith(".db") or file.endswith(".sqlite")):
                print(f" - {file} ({os.path.getsize(file)} 字节)")
        
        print("\nserver目录下的数据库文件:")
        if os.path.exists("server"):
            for file in os.listdir("server"):
                if os.path.isfile(os.path.join("server", file)) and (file.endswith(".db") or file.endswith(".sqlite")):
                    print(f" - server/{file} ({os.path.getsize(os.path.join('server', file))} 字节)")

if __name__ == "__main__":
    find_and_check_dbs()