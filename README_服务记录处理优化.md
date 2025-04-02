# 服务记录处理优化报告

## 问题分析

在测试中发现，系统对Excel中"消耗"表的处理存在以下问题：

1. **格式识别问题**：无法正确识别和处理包含标题行的Excel表格
2. **列名匹配问题**：无法正确识别列名，导致数据解析错误
3. **项目组处理问题**：无法正确解析项目名称、美容师、金额和是否指定字段
4. **特殊值处理问题**：无法正确处理带有"次"字的总次数字段
5. **Series对象问题**：处理pandas Series对象时出现"The truth value of a Series is ambiguous"错误

## 优化方案

基于`test_service_import_fixed_v2.py`测试脚本的成功经验，我们对`excel_processor.py`中的`_process_services`函数进行了以下优化：

### 1. 改进Excel读取策略

从原始数据读取，而不依赖pandas的默认列名处理，更灵活地适应不同Excel结构：

```python
# 直接使用原始数据(不使用pandas默认的列名处理)
raw_df = pd.read_excel(df.attrs.get('filepath'), sheet_name="消耗", header=None)
```

### 2. 增强标题行检测

使用更健壮的方法检测标题行，即使没有找到客户ID也会尝试使用默认行处理：

```python
# 检查前三行，寻找包含"客户ID"的行作为标题行
for i in range(min(3, len(raw_df))):
    row_values = raw_df.iloc[i].tolist()
    # 检查是否包含客户ID列
    if any(["客户ID" in str(val) if not pd.isna(val) else False for val in row_values]):
        header_row = i
        data_start_row = i + 1
        logger.info(f"找到标题行: 第{header_row+1}行, 数据从第{data_start_row+1}行开始")
        break

if header_row is None:
    logger.warning("未能找到包含'客户ID'的标题行，尝试第1行作为标题行处理")
    header_row = 1
    data_start_row = 2
```

### 3. 增强日期解析功能

增加备选的日期解析方法，提高处理多种日期格式的能力：

```python
# 解析到店时间
try:
    # 使用更灵活的日期解析
    if isinstance(arrival_time, str):
        if '/' in arrival_time:
            arrival_dt = datetime.strptime(arrival_time, "%Y/%m/%d %H:%M")
        else:
            arrival_dt = datetime.strptime(arrival_time, "%Y-%m-%d %H:%M")
    else:
        arrival_dt = pd.to_datetime(arrival_time).to_pydatetime()
    
    service_date = arrival_dt
except Exception as e:
    logger.warning(f"解析到店时间出错 [{arrival_time}]: {str(e)}")
    # 尝试使用parse_date函数重新解析
    service_date = parse_date(arrival_time)
    if service_date is None:
        logger.error(f"无法解析到店时间，跳过记录: {arrival_time}")
        continue
```

### 4. 安全的项目组处理

增加索引检查，避免数组越界错误：

```python
# 处理项目组 - 使用更安全的索引检查方法
for group in project_groups:
    # 确保索引在有效范围内
    if group["name"] >= len(row):
        continue
        
    project_name_val = row[group["name"]]
    
    # 跳过空项目
    if pd.isna(project_name_val) or not str(project_name_val).strip():
        continue
    
    # 获取美容师
    beautician_name = ""
    if group["beautician"] < len(row):
        beautician_val = row[group["beautician"]]
        if not pd.isna(beautician_val):
            beautician_name = str(beautician_val).strip()
```

### 5. 统一数据结构

使用中间结构记录服务项目，然后统一添加到服务记录中：

```python
# 创建服务记录
service_record = {
    'customer_id': customer_id,
    'name': customer_name,
    'service_date': service_date,
    'departure_time': departure_time_obj,
    'total_amount': total_amount,
    'total_sessions': total_sessions,
    'satisfaction': satisfaction,
    'service_items': service_items
}

services.append(service_record)
```

## 验证结果

通过`test_export_services.py`，我们验证了优化后的清洗逻辑处理后的数据与数据库模型的兼容性：

1. **服务记录统计**：
   - 成功导入30条服务记录（每位客户10条）
   - 成功导入41个服务项目（比服务记录多，因为一次服务可包含多个项目）

2. **客户服务分布**：
   - C001客户：10条服务记录
   - C002客户：10条服务记录
   - C003客户：10条服务记录

3. **满意度评价**：
   - C001客户：平均4.72分
   - C002客户：平均4.84分（最高）
   - C003客户：平均4.30分（最低）

4. **美容师统计**：
   - 王芳：14次服务，总金额4978.50元，指定率50.0%
   - 周杰：9次服务，总金额6692.00元，指定率100.0%
   - 李婷：6次服务，总金额2933.00元，指定率83.3%
   - 张伟：6次服务，总金额5837.50元，指定率16.7%
   - 陈莉：4次服务，总金额1125.50元，指定率0.0%
   - 张莉：2次服务，总金额773.00元，指定率50.0%

5. **项目使用统计**：
   - 冰肌焕颜护理：使用9次，平均480.00元
   - 帝王艾灸调理：使用8次，平均533.00元
   - 黄金射频紧致疗程：使用7次，平均1360.00元
   - 草本熏蒸SPA：使用7次，平均197.50元
   - 经络排毒塑身：使用3次，平均198.00元
   - 极光净透泡泡：使用3次，平均293.00元
   - 颈部导入：使用2次，平均340.00元
   - 头皮护理：使用2次，平均350.00元

## 数据库字段匹配情况

**Service模型字段**:
- service_id: 服务ID，已正确导入
- customer_id: 客户ID，已正确导入
- customer_name: 客户姓名，已正确导入
- service_date: 服务日期，已正确导入
- departure_time: 离店时间，已正确导入
- total_amount: 总金额，已正确导入
- total_sessions: 总次数，已正确导入
- satisfaction: 满意度，已正确导入

**ServiceItem模型字段**:
- project_name: 项目名称，已正确导入
- beautician_name: 美容师，已正确导入
- unit_price: 单价，已正确导入
- is_specified: 是否指定，已正确导入

## 优化建议

1. 考虑使用UUID代替自增ID作为服务项目的主键，以便在多个导入间保持一致性
2. 考虑增加导入Excel文件校验和预览功能，让用户确认数据格式
3. 为美容师和项目建立标准化字典，以避免拼写差异导致的数据不一致
4. 考虑添加批量验证和修正工具，用于处理导入后的数据清洗

## 附件

1. 已导出的服务记录JSON文件：verified_services.json
2. 格式化的Excel导出文件：服务记录导出.xlsx