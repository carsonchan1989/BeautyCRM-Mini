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

当前版本: v0.3.0 (2025-04-16)

### 最新更新

- 🔧 修复数据库文件权限问题，解决客户删除失败的bug
- 🔧 修复Excel导入时的JSON序列化错误
- 🆕 添加服务器自动启动/停止脚本，简化部署
- 🆕 增强数据库权限管理，确保写入操作正常
- 🆕 优化错误处理和日志记录

### 已完成功能

#### 后端部分

- ✅ 数据库模型设计与实现 - Customer, HealthRecord, Consumption, Service, Communication
- ✅ RESTful API实现 - 所有核心功能的API端点
- ✅ Excel导入导出功能 - 支持多表联动和数据校验
- ✅ 客户基础统计分析 - 按性别、门店、会员等级分布
- ✅ 自动生成客户ID - 使用UUID确保唯一性
- ✅ 完整API测试 - 验证了所有API端点的正常工作
- ✅ 自动检查和修复数据库权限 - 解决写入操作失败问题
- ✅ 服务管理脚本 - 安全启动和停止服务

#### 微信小程序部分

- ✅ Excel导入页面 - 支持上传Excel文件
- ✅ Excel预览页面 - 显示解析后的数据预览
- ✅ 基础UI组件 - 表单、列表、导航等组件
- ✅ 客户列表和删除功能 - 完整的客户管理基础功能

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
├── start_server.sh      # 服务启动脚本
├── stop_server.sh       # 服务停止脚本
├── server.pid           # 服务进程ID文件
├── server.log           # 服务日志文件
├── test_api.py          # API测试脚本
├── api/                 # API路由
│   ├── __init__.py
│   ├── customer_routes.py  # 客户相关API
│   └── excel_routes.py     # Excel处理API
├── utils/               # 工具函数
│   ├── __init__.py
│   └── excel_processor.py  # Excel处理器
├── instance/            # 数据库文件目录
│   └── beauty_crm.db    # SQLite数据库文件
├── uploads/             # 上传文件目录
└── exports/             # 导出文件目录
```

## 安装与运行

### 推荐方式（使用服务管理脚本）

1. 导航到服务器目录

```bash
cd /var/www/BeautyCRM-Mini/server
```

2. 启动服务

```bash
./start_server.sh
```

3. 停止服务

```bash
./stop_server.sh
```

### 手动方式

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

3. 确保数据库文件权限正确

```bash
mkdir -p instance
chmod 777 instance
touch instance/beauty_crm.db
chmod 777 instance/beauty_crm.db
```

4. 运行开发服务器

```bash
python app.py
```

默认情况下，服务器将在 http://localhost:5000 上运行。

## 服务器管理

### 数据库权限问题

BeautyCRM 使用 SQLite 数据库存储数据。在某些情况下，数据库文件可能会遇到权限问题，导致无法执行写操作（如删除客户记录）。我们通过以下方式解决这个问题：

1. 在应用启动时自动检查数据库文件权限
2. 如果权限不正确，自动设置为可读写权限 (777)
3. 提供专用启动脚本确保每次启动时权限正确

### 启动服务

使用以下命令启动服务：

```bash
cd /var/www/BeautyCRM-Mini/server
./start_server.sh
```

启动脚本会自动：
- 检查并创建必要的目录
- 设置正确的数据库文件权限
- 检查并释放被占用的端口
- 启动 Flask 应用并记录 PID
- 提供启动状态反馈

### 停止服务

使用以下命令停止服务：

```bash
cd /var/www/BeautyCRM-Mini/server
./stop_server.sh
```

停止脚本会自动：
- 尝试优雅地停止服务
- 如果服务无法正常停止，强制终止
- 清理 PID 文件
- 提供停止状态反馈

### 日志查看

服务日志存储在 `/var/www/BeautyCRM-Mini/server/server.log` 文件中，可以通过以下命令查看：

```bash
tail -f /var/www/BeautyCRM-Mini/server/server.log
```

### 常见问题解决

#### 无法删除客户

如果遇到无法删除客户等写操作问题，通常是数据库权限问题导致的。运行以下命令修复：

```bash
sudo chmod 777 /var/www/BeautyCRM-Mini/server/instance/beauty_crm.db
```

#### 端口被占用

如果 5000 端口被占用，可以使用以下命令查找占用进程：

```bash
sudo lsof -i :5000
```

然后使用以下命令停止占用进程：

```bash
sudo kill -9 <PID>
```

或者直接使用停止脚本：

```bash
./stop_server.sh
```

#### 数据库损坏

如果数据库文件损坏，可以尝试使用备份文件恢复：

```bash
cp /var/www/BeautyCRM-Mini/server/instance/beauty_crm.db.bak /var/www/BeautyCRM-Mini/server/instance/beauty_crm.db
chmod 777 /var/www/BeautyCRM-Mini/server/instance/beauty_crm.db
```

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
- `POST /api/excel/precheck` - 检查Excel文件格式

## 修复日志

### 2025-04-16 版本更新

1. 修复了Excel文件预检查失败的问题
   - 解决了pandas Series对象无法JSON序列化的错误
   - 增强了数据类型处理和空值处理
   
2. 修复了SQLite数据库权限问题
   - 在应用启动时自动检查和修复数据库文件权限
   - 添加了`check_and_fix_db_permissions`函数确保文件可写
   - 修改了数据库文件默认路径，确保路径正确
   
3. 实现了服务管理脚本
   - 添加`start_server.sh`脚本，安全启动服务
   - 添加`stop_server.sh`脚本，安全停止服务
   - 脚本自动处理端口占用和进程管理
   
4. 优化了系统稳定性
   - 增强了错误处理和日志记录
   - 改进了数据库连接管理
   - 使用绝对路径确保资源文件定位正确

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