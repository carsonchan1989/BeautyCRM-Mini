"""
导出Excel文档"模拟-客户信息档案.xlsx"的"消耗"子表内容
"""
import pandas as pd
import os

def export_consumption_sheet():
    # 假设Excel文件在当前目录
    excel_path = "模拟-客户信息档案.xlsx"
    
    if not os.path.exists(excel_path):
        print(f"错误：找不到文件 {excel_path}")
        return
    
    try:
        # 读取"消耗"子表
        df = pd.read_excel(excel_path, sheet_name="消耗")
        
        # 导出为CSV以便检查
        csv_path = "消耗表导出.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        print(f"成功导出消耗表到 {csv_path}")
        
        # 打印前几行以验证
        print("\n数据预览：")
        print(df.head())
        
        return df
    except Exception as e:
        print(f"导出失败：{str(e)}")
        return None

if __name__ == "__main__":
    export_consumption_sheet()