import pandas as pd
import json

def read_service_excel():
    try:
        # 读取Excel文件
        df = pd.read_excel('模拟-店内项目介绍.xlsx')
        
        # 将DataFrame转换为字典列表
        records = df.to_dict('records')
        
        # 打印JSON格式的数据
        print(json.dumps(records, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"Error reading Excel file: {str(e)}")

if __name__ == "__main__":
    read_service_excel()