def _process_services(self, df):
    """
    处理服务记录数据，按照一行基础信息配合多个服务项目组的模式处理
    """
    services = []
    
    try:
        # 记录DataFrame的形状和原始列名
        logger.info(f"DataFrame形状: {df.shape}")
        logger.info(f"原始列名: {list(df.columns)}")
        
        # 检查第一行是否包含标题信息
        first_row = df.iloc[0].tolist()
        logger.info(f"第一行内容样本: {first_row[:5]}")
        
        # 如果第一行包含"客户ID"等标题信息，则将其设为新的列名
        if '客户ID' in first_row:
            logger.info("第一行是标题行，将使用第一行作为列名")
            # 提取新的列名
            new_headers = []
            grouped_headers = []
            
            for col_idx, col_val in enumerate(first_row):
                if pd.notna(col_val):
                    col_name = str(col_val).strip()
                    new_headers.append(col_name)
                else:
                    # 对于空值，使用前一个值或默认值
                    if col_idx > 0 and pd.notna(first_row[col_idx-1]):
                        # 对于空列名，使用前一个列名+"_子列"
                        prev_name = str(first_row[col_idx-1]).strip()
                        new_headers.append(f"{prev_name}_子列_{col_idx}")
                    else:
                        new_headers.append(f"未命名列_{col_idx}")
            
            # The rest of the method is in the next file...