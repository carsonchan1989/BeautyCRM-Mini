import pandas as pd
import os
import json

def read_project_excel(file_path):
    """读取项目Excel文件内容并输出"""
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        # 打印基本信息
        print("Excel文件基本信息:")
        print(f"行数: {len(df)}")
        print(f"列数: {len(df.columns)}")
        print(f"列名: {list(df.columns)}")
        
        # 打印前5行数据
        print("\n前5行数据:")
        print(df.head())
        
        # 检查空值
        print("\n各列空值数量:")
        print(df.isnull().sum())
        
        # 将数据转换为JSON格式
        json_data = df.to_dict(orient='records')
        
        # 保存为JSON文件以便查看
        with open('project_data.json', 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
            
        print("\nJSON数据已保存到project_data.json")
        
        return df
    except Exception as e:
        print(f"读取Excel文件出错: {str(e)}")
        return None

if __name__ == "__main__":
    # Excel文件路径
    file_path = "../模拟-店内项目介绍.xlsx"
    
    if os.path.exists(file_path):
        read_project_excel(file_path)
    else:
        print(f"文件 {file_path} 不存在") 