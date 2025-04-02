"""
查看Excel文件内容
"""
import pandas as pd
import sys

def view_excel(file_path):
    try:
        # 读取sheet名称
        xls = pd.ExcelFile(file_path)
        sheets = xls.sheet_names
        print(f"Excel文件包含以下表: {sheets}")
        
        # 逐个读取sheet
        for sheet_name in sheets:
            print(f"\n=== {sheet_name} 表内容 ===")
            # 直接读取原始数据，不使用pandas的标题行处理
            df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            
            # 查看每行内容
            print("\n原始数据前3行:")
            for i in range(min(3, len(df_raw))):
                row_data = df_raw.iloc[i].tolist()
                print(f"行 {i}: {row_data[:10]}...")
            
            # 当前表的形状
            print(f"\n形状: {df_raw.shape}")
            
            # 尝试检查客户ID列
            id_found = False
            for row_idx in range(min(3, len(df_raw))):
                for col_idx in range(df_raw.shape[1]):
                    cell_value = df_raw.iloc[row_idx, col_idx]
                    if not pd.isna(cell_value) and '客户ID' in str(cell_value):
                        print(f"\n找到'客户ID'在行 {row_idx}, 列 {col_idx}")
                        id_found = True
            
            if not id_found and sheet_name == '消耗':
                print("\n注意: 没有在消耗表中找到'客户ID'字段！")
                
                # 检查第一行每个单元格
                print("\n消耗表第一行详细内容:")
                for col_idx in range(df_raw.shape[1]):
                    cell_value = df_raw.iloc[0, col_idx]
                    print(f"列 {col_idx}: {cell_value}")
            
            # 特别处理消耗表
            if sheet_name == '消耗':
                # 查看消耗表的具体结构
                print("\n消耗表结构分析:")
                # 尝试检测并重构消耗数据
                
                # 假设第1行是标题，找到关键列
                search_row = 0
                customer_id_col = -1
                arrival_time_col = -1
                departure_time_col = -1
                total_amount_col = -1
                project_cols = []
                
                # 遍历每一列寻找关键字段
                for col in range(df_raw.shape[1]):
                    cell = df_raw.iloc[search_row, col]
                    if not pd.isna(cell):
                        cell_str = str(cell)
                        if '客户ID' in cell_str or 'ID' in cell_str:
                            customer_id_col = col
                            print(f"  - 找到客户ID列: {col}")
                        elif '到店时间' in cell_str:
                            arrival_time_col = col
                            print(f"  - 找到到店时间列: {col}")
                        elif '离店时间' in cell_str:
                            departure_time_col = col
                            print(f"  - 找到离店时间列: {col}")
                        elif '总金额' in cell_str or ('总' in cell_str and '金额' in cell_str):
                            total_amount_col = col
                            print(f"  - 找到总金额列: {col}")
                        elif '项目' in cell_str or '消耗项目' in cell_str:
                            project_cols.append(col)
                            print(f"  - 找到项目相关列: {col} - {cell_str}")
                
                # 输出第一条客户ID数据样本
                if customer_id_col >= 0:
                    print("\n客户ID列数据样本:")
                    for row in range(1, min(5, df_raw.shape[0])):
                        if not pd.isna(df_raw.iloc[row, customer_id_col]):
                            print(f"  行 {row}: {df_raw.iloc[row, customer_id_col]}")
                
                # 输出第一个项目列数据样本
                if project_cols:
                    print("\n项目列数据样本:")
                    for row in range(1, min(5, df_raw.shape[0])):
                        if not pd.isna(df_raw.iloc[row, project_cols[0]]):
                            print(f"  行 {row}, 列 {project_cols[0]}: {df_raw.iloc[row, project_cols[0]]}")
                
                # 手动解析服务项目
                print("\n尝试手动解析服务项目:")
                # 先找到第一个有效的客户行
                for row_idx in range(1, min(10, df_raw.shape[0])):
                    if customer_id_col >= 0 and not pd.isna(df_raw.iloc[row_idx, customer_id_col]):
                        print(f"\n第 {row_idx} 行客户: {df_raw.iloc[row_idx, customer_id_col]}")
                        
                        # 基本信息
                        if arrival_time_col >= 0:
                            print(f"  - 到店时间: {df_raw.iloc[row_idx, arrival_time_col]}")
                        if departure_time_col >= 0:
                            print(f"  - 离店时间: {df_raw.iloc[row_idx, departure_time_col]}")
                        if total_amount_col >= 0:
                            print(f"  - 总金额: {df_raw.iloc[row_idx, total_amount_col]}")
                        
                        # 尝试解构项目组
                        print("  - 项目信息:")
                        for proj_col in project_cols:
                            # 项目列通常是4列一组，包括项目名称、美容师、金额、是否指定
                            project_name = df_raw.iloc[row_idx, proj_col] if proj_col < df_raw.shape[1] else None
                            beautician = df_raw.iloc[row_idx, proj_col+1] if proj_col+1 < df_raw.shape[1] else None
                            amount = df_raw.iloc[row_idx, proj_col+2] if proj_col+2 < df_raw.shape[1] else None
                            is_specified = df_raw.iloc[row_idx, proj_col+3] if proj_col+3 < df_raw.shape[1] else None
                            
                            if not pd.isna(project_name) and str(project_name).strip():
                                print(f"    项目: {project_name}, 美容师: {beautician}, 金额: {amount}, 是否指定: {is_specified}")
                        break
            
            # 正常读取带标题行的数据
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            print(f"\n带标题行列名: {list(df.columns)}")
            print("\n前3行数据:")
            print(df.head(3))
            
            # 检查是否有空白列(全部为NaN的列)
            null_columns = df.columns[df.isnull().all()].tolist()
            if null_columns:
                print(f"\n注意: 发现{len(null_columns)}个空白列: {null_columns}")
        
        return True
    except Exception as e:
        print(f"查看Excel文件出错: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    file_path = "模拟-客户信息档案.xlsx"
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    
    view_excel(file_path)