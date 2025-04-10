def import_consumption_records(df, cursor, conn):
    """导入消费记录数据"""
    logger.info("正在导入消费记录...")
    count = 0
    skipped = 0
    
    # 准备查询语句
    check_sql = "SELECT COUNT(*) FROM consumptions WHERE customer_id = ? AND date = ? AND project_name = ? AND amount = ?"
    insert_sql = """
    INSERT INTO consumptions (
        customer_id, date, project_name, amount, payment_method, 
        total_sessions, completion_date, satisfaction, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    for _, row in df.iterrows():
        try:
            # 提取数据
            customer_id = str(row.get('customer_id', '')).strip()
            if not customer_id or pd.isna(customer_id):
                continue
                
            # 处理日期格式
            date_str = row.get('date', None)
            if pd.isna(date_str) or not date_str:
                continue
                
            if isinstance(date_str, str):
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        date = datetime.strptime(date_str, '%Y-%m-%d')
                    except ValueError:
                        continue
            else:
                try:
                    date = pd.to_datetime(date_str)
                except:
                    continue
                
            date_formatted = date.strftime('%Y-%m-%d %H:%M:%S')
            
            # 其他字段
            project_name = str(row.get('project_name', '')).strip()
            amount = float(row.get('amount', 0)) if not pd.isna(row.get('amount')) else 0
            payment_method = str(row.get('payment_method', '')).strip() if not pd.isna(row.get('payment_method')) else None
            total_sessions = int(row.get('total_sessions', 0)) if not pd.isna(row.get('total_sessions')) else None
            
            # 处理完成日期
            completion_date = row.get('completion_date', None)
            if pd.isna(completion_date) or not completion_date:
                completion_date_formatted = None
            else:
                if isinstance(completion_date, str):
                    try:
                        completion_date = datetime.strptime(completion_date, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        try:
                            completion_date = datetime.strptime(completion_date, '%Y-%m-%d')
                        except ValueError:
                            completion_date_formatted = None
                else:
                    try:
                        completion_date = pd.to_datetime(completion_date)
                        completion_date_formatted = completion_date.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        completion_date_formatted = None
            
            satisfaction = str(row.get('satisfaction', '')).strip() if not pd.isna(row.get('satisfaction')) else None
            
            # 检查是否已存在相同记录
            cursor.execute(check_sql, (customer_id, date_formatted, project_name, amount))
            if cursor.fetchone()[0] > 0:
                logger.info(f"跳过重复消费记录: 客户{customer_id}, 日期{date_formatted}, 项目{project_name}, 金额{amount}")
                skipped += 1
                continue
            
            # 时间戳
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 插入数据
            cursor.execute(insert_sql, (
                customer_id, date_formatted, project_name, amount, payment_method,
                total_sessions, completion_date_formatted, satisfaction, now, now
            ))
            
            count += 1
            
        except Exception as e:
            logger.error(f"导入消费记录时出错: {str(e)}")
            logger.error(f"问题数据: {row}")
    
    conn.commit()
    logger.info(f"消费记录导入完成: 成功 {count} 条, 跳过重复 {skipped} 条")
    return count

def import_communication_records(df, cursor, conn):
    """导入沟通记录数据"""
    logger.info("正在导入沟通记录...")
    count = 0
    skipped = 0
    
    # 准备查询语句
    check_sql = "SELECT COUNT(*) FROM communications WHERE customer_id = ? AND communication_date = ? AND communication_content = ?"
    insert_sql = """
    INSERT INTO communications (
        customer_id, communication_date, communication_type, communication_location,
        staff_name, communication_content, customer_feedback, follow_up_action,
        created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    for _, row in df.iterrows():
        try:
            # 提取数据
            customer_id = str(row.get('customer_id', '')).strip()
            if not customer_id or pd.isna(customer_id):
                continue
                
            # 处理日期格式
            date_str = row.get('communication_date', None)
            if pd.isna(date_str) or not date_str:
                continue
                
            if isinstance(date_str, str):
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        date = datetime.strptime(date_str, '%Y-%m-%d')
                    except ValueError:
                        continue
            else:
                try:
                    date = pd.to_datetime(date_str)
                except:
                    continue
                
            date_formatted = date.strftime('%Y-%m-%d %H:%M:%S')
            
            # 其他字段
            communication_type = str(row.get('communication_type', '')).strip() if not pd.isna(row.get('communication_type')) else None
            communication_location = str(row.get('communication_location', '')).strip() if not pd.isna(row.get('communication_location')) else None
            staff_name = str(row.get('staff_name', '')).strip() if not pd.isna(row.get('staff_name')) else None
            communication_content = str(row.get('communication_content', '')).strip() if not pd.isna(row.get('communication_content')) else ''
            customer_feedback = str(row.get('customer_feedback', '')).strip() if not pd.isna(row.get('customer_feedback')) else None
            follow_up_action = str(row.get('follow_up_action', '')).strip() if not pd.isna(row.get('follow_up_action')) else None
            
            # 检查是否已存在相同记录
            cursor.execute(check_sql, (customer_id, date_formatted, communication_content))
            if cursor.fetchone()[0] > 0:
                logger.info(f"跳过重复沟通记录: 客户{customer_id}, 日期{date_formatted}, 内容摘要: {communication_content[:20]}...")
                skipped += 1
                continue
            
            # 时间戳
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 插入数据
            cursor.execute(insert_sql, (
                customer_id, date_formatted, communication_type, communication_location,
                staff_name, communication_content, customer_feedback, follow_up_action,
                now, now
            ))
            
            count += 1
            
        except Exception as e:
            logger.error(f"导入沟通记录时出错: {str(e)}")
            logger.error(f"问题数据: {row}")
    
    conn.commit()
    logger.info(f"沟通记录导入完成: 成功 {count} 条, 跳过重复 {skipped} 条")
    return count 