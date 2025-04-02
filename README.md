# BeautyCRM-Mini 微信小程序

## 项目概述

BeautyCRM-Mini是一款专为美容院设计的微信小程序，帮助美容院管理客户信息、服务记录和消费数据。主要功能包括：

- Excel数据导入 - 批量导入客户、服务记录等数据
- 客户管理 - 查看和管理客户基本信息
- 服务记录 - 记录客户每次服务的详细信息
- 数据分析 - 生成客户数据分析报告

## 开发进度

当前版本: v0.2.5 (2025-04-01)

### 最新更新

- ✅ 修复了服务记录导入Excel的解析问题
- ✅ 优化了Excel处理器，解决了Pandas Series对象处理问题
- ✅ 改进服务记录导入/导出功能，支持Excel和Markdown格式
- ✅ 修复了后端启动失败问题，清理了代码中的语法错误
- ✅ 解决了服务记录在小程序上显示为0条的问题

## 主要功能

### Excel数据处理

- ✅ 支持多种格式的Excel文件导入
- ✅ 智能识别Excel表头和数据格式
- ✅ 自动清洗和标准化数据
- ✅ 导入前数据预览和确认
- ✅ 支持导出数据为Excel和Markdown格式

### 客户管理

- ✅ 客户列表浏览和搜索
- ✅ 客户详情查看
- ✅ 客户服务记录查看
- 🔄 客户编辑功能
- 🔄 客户筛选和分类

### 服务记录

- ✅ 查看服务记录列表
- ✅ 服务记录详情展示
- ✅ 服务项目详情查看
- 🔄 服务记录搜索和筛选
- 🔄 服务记录统计分析

### 数据分析

- 🔄 客户消费统计
- 🔄 服务项目热度分析
- ⏳ 美容师业绩分析
- ⏳ 客户画像生成

## 后端技术栈

- Flask - Web框架
- SQLite - 开发环境数据库
- SQLAlchemy - ORM框架
- Pandas - 数据处理
- XlsxWriter/openpyxl - Excel文件处理

## 小程序技术栈

- 原生微信小程序开发
- WXML/WXSS/JS
- 微信云存储
- Charts组件 - 数据可视化

## 安装运行

### 后端

1. 进入server目录
2. 安装依赖：`pip install -r requirements.txt`
3. 运行服务器：`python app.py`

### 小程序

1. 使用微信开发者工具打开mini-program目录
2. 在project.config.json中配置自己的AppID
3. 在app.js中配置API地址为本地服务器地址
4. 编译运行

## 常见问题

### Excel导入问题

如果在导入Excel文件时遇到"连接被拒绝"错误，请确保：

1. 小程序中配置的API地址指向正确的服务器IP（不能使用localhost）
2. 手机和服务器在同一网络环境中
3. 服务器防火墙允许5000端口的访问

具体解决方案可参考：`README_网络连接问题修复.md`

### 服务记录显示问题

如果服务记录导入后在小程序中显示为0条，原因可能是：

1. Excel处理器未能正确解析服务记录数据
2. Series对象处理时出现"The truth value of a Series is ambiguous"错误

最新版本已修复此问题，请确保使用最新代码。

## 项目规划

### 近期计划（1-2周）

- 完善服务记录筛选和搜索功能
- 优化Excel导入用户体验
- 添加服务记录导出为PDF功能

### 中期计划（1-2个月）

- 实现客户画像分析
- 开发会员卡管理功能
- 添加数据备份和恢复功能

### 长期计划

- 多门店数据管理
- 客户关怀提醒系统
- 员工绩效分析系统

## 联系与支持

如有问题或建议，请提交issue或联系项目维护者。