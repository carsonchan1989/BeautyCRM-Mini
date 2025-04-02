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
                
                # 确保列名数量与DataFrame列数匹配
                if len(new_headers) < len(df.columns):
                    new_headers.extend([f"Column_{i}" for i in range(len(new_headers), len(df.columns))])
                    
                df.columns = new_headers
                logger.info(f"处理后的列名: {list(df.columns)}")
                
                # 删除第一行，因为它已经成为列名
                df = df.iloc[1:].reset_index(drop=True)
                
                # 定义基础信息字段映射
                base_fields = {
                    'customer_id': None,
                    'service_date': None,
                    'departure_time': None,
                    'total_amount': None,
                    'total_sessions': None,
                    'satisfaction': None
                }
                
                # 查找基础信息列
                for col in df.columns:
                    if '客户ID' in col:
                        base_fields['customer_id'] = col
                    elif '到店时间' in col:
                        base_fields['service_date'] = col
                    elif '离店时间' in col:
                        base_fields['departure_time'] = col
                    elif '总耗卡金额' in col:
                        base_fields['total_amount'] = col
                    elif '总次数' in col or '耗卡次数' in col:
                        base_fields['total_sessions'] = col
                    elif '服务满意度' in col or '满意度' in col or '项目满意度' in col:
                        base_fields['satisfaction'] = col
                
                logger.info(f"识别到的基础信息列: {base_fields}")
                
                # 识别服务项目分组
                project_groups = []
                current_group = {}
                
                # 查找所有可能的项目组列
                for i, col in enumerate(df.columns):
                    if ('项目' in col or '服务项目' in col) and not current_group.get('project'):
                        current_group['project'] = col
                    elif ('美容师' in col) and current_group.get('project') and not current_group.get('beautician'):
                        current_group['beautician'] = col
                    elif ('金额' in col) and current_group.get('project') and current_group.get('beautician') and not current_group.get('amount'):
                        current_group['amount'] = col
                    elif ('指定' in col) and current_group.get('project') and current_group.get('beautician') and current_group.get('amount'):
                        current_group['is_specified'] = col
                        project_groups.append(current_group.copy())
                        current_group = {}
                
                logger.info(f"识别到的项目消耗分组: {project_groups}")
                
                # 处理每一行数据
                for index, row in df.iterrows():
                    try:
                        # 获取客户ID
                        customer_id_val = row[base_fields['customer_id']] if pd.notna(row[base_fields['customer_id']]) else None
                        
                        # 处理customer_id可能是Series的情况
                        if isinstance(customer_id_val, pd.Series):
                            if customer_id_val.empty or customer_id_val.isna().all():
                                continue
                            # 使用第一个非空值
                            for val in customer_id_val:
                                if pd.notna(val):
                                    customer_id = str(val).strip()
                                    break
                        else:
                            if pd.isna(customer_id_val):
                                continue
                            customer_id = str(customer_id_val).strip()
                        
                        if not customer_id:
                            logger.warning(f"行 {index} 缺少客户ID，跳过")
                            continue
                        
                        # 处理日期时间
                        service_date = self._parse_datetime(row[base_fields['service_date']]) if pd.notna(row[base_fields['service_date']]) else None
                        departure_time = self._parse_datetime(row[base_fields['departure_time']]) if pd.notna(row[base_fields['departure_time']]) else None
                        
                        # 处理金额和满意度
                        total_amount = self._convert_amount(row[base_fields['total_amount']]) if pd.notna(row[base_fields['total_amount']]) else None
                        satisfaction = str(row[base_fields['satisfaction']]) if pd.notna(row[base_fields['satisfaction']]) else None
                        
                        # 处理总次数 - 改进此处逻辑
                        total_sessions = None
                        if base_fields['total_sessions'] and pd.notna(row[base_fields['total_sessions']]):
                            try:
                                # 尝试从字符串中提取数字部分
                                sessions_value = row[base_fields['total_sessions']]
                                if isinstance(sessions_value, str) and "次" in sessions_value:
                                    sessions_str = sessions_value.replace("次", "").strip()
                                    total_sessions = int(sessions_str)
                                elif isinstance(sessions_value, (int, float)):
                                    total_sessions = int(sessions_value)
                                else:
                                    total_sessions = int(sessions_value)
                                logger.info(f"提取总次数: 原始值 {sessions_value} -> {total_sessions}")
                            except (ValueError, TypeError) as e:
                                logger.warning(f"总次数值无法转换为整数: {row[base_fields['total_sessions']]}, 错误: {str(e)}")
                                # 如果转换失败，保持None值
                        
                        # 创建服务项目列表
                        service_items = []
                        
                        # 处理服务项目组
                        for group in project_groups:
                            try:
                                # 获取项目名称，处理Series对象的情况
                                project_value = row[group['project']]
                                
                                # 判断项目名称是否为空
                                if isinstance(project_value, pd.Series):
                                    # 对Series对象，检查是否所有值都是na
                                    if project_value.isna().all():
                                        continue
                                    # 取第一个非空值
                                    project_name = None
                                    for val in project_value:
                                        if pd.notna(val):
                                            project_name = str(val).strip()
                                            break
                                    if not project_name:
                                        continue
                                else:
                                    # 直接判断标量值
                                    if pd.isna(project_value):
                                        continue
                                    project_name = str(project_value).strip()
                                    if not project_name:
                                        continue
                                
                                # 创建项目消耗记录
                                item = {
                                    'project_name': project_name,
                                    'beautician_name': '',
                                    'unit_price': 0.0,
                                    'is_specified': False
                                }
                                
                                # 处理美容师
                                if group['beautician'] and not pd.isna(row[group['beautician']]):
                                    beautician_value = row[group['beautician']]
                                    if isinstance(beautician_value, pd.Series):
                                        for val in beautician_value:
                                            if pd.notna(val):
                                                item['beautician_name'] = str(val).strip()
                                                break
                                    else:
                                        item['beautician_name'] = str(beautician_value).strip()
                                
                                # 处理金额
                                if group['amount'] and not pd.isna(row[group['amount']]):
                                    amount_value = row[group['amount']]
                                    if isinstance(amount_value, pd.Series):
                                        for val in amount_value:
                                            if pd.notna(val):
                                                try:
                                                    item['unit_price'] = float(val)
                                                except (ValueError, TypeError):
                                                    logger.warning(f"第{index+1}行项目金额格式错误: {val}")
                                                break
                                    else:
                                        try:
                                            item['unit_price'] = float(amount_value)
                                        except (ValueError, TypeError):
                                            logger.warning(f"第{index+1}行项目金额格式错误: {amount_value}")
                                
                                # 处理是否指定
                                if group['is_specified'] and not pd.isna(row[group['is_specified']]):
                                    specified_value = row[group['is_specified']]
                                    if isinstance(specified_value, pd.Series):
                                        for val in specified_value:
                                            if pd.notna(val):
                                                value = str(val).strip()
                                                item['is_specified'] = value in ['✓', '√', '是', 'Yes', 'yes', 'TRUE', 'true', 'True', '1', 'Y', 'y']
                                                break
                                    else:
                                        value = str(specified_value).strip()
                                        item['is_specified'] = value in ['✓', '√', '是', 'Yes', 'yes', 'TRUE', 'true', 'True', '1', 'Y', 'y']
                                    logger.info(f"是否指定原始值: {specified_value}, 解析结果: {item['is_specified']}")
                                
                                service_items.append(item)
                            except Exception as e:
                                logger.error(f"处理项目组时出错: {str(e)}")
                                continue
                        
                        # 如果没有找到有效的total_sessions，则使用服务项目数
                        if total_sessions is None and service_items:
                            total_sessions = len(service_items)
                            logger.info(f"未找到总次数，使用服务项目数量: {total_sessions}")
                        
                        # 创建单条服务记录，包含所有项目
                        services.append({
                            'customer_id': customer_id,
                            'service_date': service_date,
                            'departure_time': departure_time,
                            'total_amount': total_amount,
                            'satisfaction': satisfaction,
                            'total_sessions': total_sessions,  # 使用解析后的总次数
                            'service_items': service_items
                        })
                    
                    except Exception as e:
                        logger.error(f"处理第 {index} 行时出错: {str(e)}")
                        logger.error(traceback.format_exc())
                
                logger.info(f"服务记录处理完成: 共处理 {len(services)} 条记录")
            else:
                logger.warning("未找到标题行，无法处理服务记录")
        
        except Exception as e:
            logger.error(f"处理服务记录时出错: {str(e)}")
            logger.error(traceback.format_exc())
        
        return services