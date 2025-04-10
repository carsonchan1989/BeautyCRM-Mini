# BeautyCRM 美容客户管理系统

## 项目概述

BeautyCRM是一套专为美容院设计的客户关系管理系统，主要功能包括：

- 客户信息管理 - 全面记录客户基础信息
- 健康与皮肤档案管理 - 跟踪客户肤质状况和健康信息
- 消费记录跟踪 - 记录消费项目、金额和满意度
- 服务记录管理 - 详细记录每次服务的内容和效果
- 客户沟通记录 - 持续跟进客户反馈和需求
- Excel数据导入导出 - 支持批量处理客户数据
- 客户数据统计分析 - 了解客户分布和消费趋势

## 开发进度

当前版本: v0.2.0 (2025-03-28)

### 已完成功能

#### 后端部分

- ✅ 数据库模型设计与实现 - Customer, HealthRecord, Consumption, Service, Communication
- ✅ RESTful API实现 - 所有核心功能的API端点
- ✅ Excel导入导出功能 - 支持多表联动和数据校验
- ✅ 客户基础统计分析 - 按性别、门店、会员等级分布
- ✅ 自动生成客户ID - 使用UUID确保唯一性
- ✅ 完整API测试 - 验证了所有API端点的正常工作

#### 微信小程序部分

- ✅ Excel导入页面 - 支持上传Excel文件
- ✅ Excel预览页面 - 显示解析后的数据预览
- ✅ 基础UI组件 - 表单、列表、导航等组件

### 进行中功能

- 🔄 微信小程序客户管理模块
- 🔄 客户详情页面开发
- 🔄 健康档案管理页面
- 🔄 数据可视化报表

### 计划中功能

- ⏳ 用户权限管理系统
- ⏳ 多门店数据隔离
- ⏳ 客户画像AI分析
- ⏳ 客户关怀提醒功能
- ⏳ 会员卡管理功能
- ⏳ 数据备份与恢复

## 项目结构

```
server/
├── app.py               # 应用主入口
├── models.py            # 数据库模型
├── requirements.txt     # 项目依赖
├── test_api.py          # API测试脚本
├── api/                 # API路由
│   ├── __init__.py
│   ├── customer_routes.py  # 客户相关API
│   └── excel_routes.py     # Excel处理API
├── utils/               # 工具函数
│   ├── __init__.py
│   └── excel_processor.py  # Excel处理器
├── uploads/             # 上传文件目录
└── exports/             # 导出文件目录
```

## 安装与运行

1. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 运行开发服务器

```bash
python app.py
```

默认情况下，服务器将在 http://localhost:5000 上运行。

## API 端点

### 客户管理

- `GET /api/customers` - 获取客户列表
- `GET /api/customers/<id>` - 获取单个客户详情
- `POST /api/customers` - 创建新客户
- `PUT /api/customers/<id>` - 更新客户信息
- `DELETE /api/customers/<id>` - 删除客户
- `POST /api/customers/<id>/health` - 添加健康档案
- `POST /api/customers/<id>/consumption` - 添加消费记录
- `POST /api/customers/<id>/service` - 添加服务记录
- `POST /api/customers/<id>/communication` - 添加沟通记录
- `GET /api/customers/stats` - 获取客户统计信息

### Excel 处理

- `POST /api/excel/import` - 导入Excel文件
- `POST /api/excel/export` - 导出客户数据到Excel

## Excel处理功能

系统能够处理以下五张子表的Excel数据:

1. 客户基础信息表
2. 健康与皮肤数据档案表
3. 消费行为记录表
4. 消耗行为记录表
5. 客户沟通记录表

Excel处理模块使用pandas进行数据清洗，具有以下功能：

- 自动识别工作表类型
- 标准化列名映射
- 自动清理和转换数据类型
- 处理日期格式
- 去除重复数据
- 填充缺失值
- 验证手机号格式
- 生成唯一客户ID
- 确保表之间的关系完整性

## 环境变量

可以通过环境变量或.env文件配置以下选项：

- `SECRET_KEY` - 应用密钥
- `DATABASE_URI` - 数据库连接URI
- `PORT` - 服务器端口（默认5000）

## 数据库模型

系统包含以下主要数据模型：

1. `Customer` - 客户基础信息
2. `HealthRecord` - 健康与皮肤档案
3. `Consumption` - 消费记录
4. `Service` - 服务记录
5. `Communication` - 沟通记录

## 测试

项目包含一个完整的API测试脚本 `test_api.py`，可以通过以下方式运行：

```bash
python test_api.py
```

该脚本会测试所有主要API功能，包括：
- 健康检查
- 创建客户
- 获取客户列表和详情
- 更新客户信息
- 添加健康记录
- 添加消费记录
- 添加服务记录
- 添加沟通记录
- 获取统计信息
- 导出Excel数据

## 技术栈

- 后端框架: Flask
- 数据库: SQLite (开发), MySQL (生产)
- ORM: SQLAlchemy
- 数据处理: Pandas
- Excel处理: XlsxWriter
- 前端: 微信小程序

## 下一步计划

1. 完成微信小程序客户管理模块
2. 实现客户健康档案的可视化展示
3. 添加用户认证与权限管理
4. 开发AI客户画像分析功能
5. 实现数据备份与恢复功能

## 贡献

如有问题或建议，请提交issue或pull request。