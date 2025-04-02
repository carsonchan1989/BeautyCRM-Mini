# 服务器启动错误解决指南

## 问题

当运行服务器时，您遇到了以下错误：
```
ImportError: cannot import name 'customer_bp' from 'server.api.customers'
```

这个错误表明在尝试导入蓝图对象时，名称不匹配。问题在于API蓝图文件中使用的名称是`bp`，而不是`customer_bp`。

## 已完成的修复

我们已经对服务器代码进行了以下修复：

1. 修改了导入语句，使用正确的蓝图名称：
   ```python
   from server.api.customers import bp as customer_bp
   from server.api.services import bp as service_bp
   from server.api.reports import bp as report_bp
   ```

2. 添加了Excel导入功能的API蓝图

3. 配置了上传文件夹，确保Excel导入功能正常工作

## 如何启动服务器

现在您可以通过以下方式启动服务器：

```bash
cd D:\BeautyCRM-Mini
python run_server.py
```

如果需要重置数据库：
```bash
cd D:\BeautyCRM-Mini
set RESET_DB=true
python run_server.py
```

## 服务器功能

修复后的服务器现在包含以下功能：

1. 客户管理API (`/api/customers`)
2. 服务记录API (`/api/services`)
3. 报告生成API (`/api/reports`)
4. Excel导入API (`/api/excel/import`)

## Excel导入功能说明

Excel导入API已经实现，主要功能包括：

1. 文件上传与保存
2. Excel文件格式验证
3. 工作表内容预览功能
4. 完整数据导入功能

## 微信小程序配置

为了让微信小程序能够成功连接到服务器，您需要在微信小程序的`app.js`文件中将API基础URL从localhost改为您的电脑IP地址：

```javascript
globalData: {
  apiBaseUrl: 'http://192.168.x.x:5000/api' // 将127.0.0.1替换为实际IP地址
}
```

您可以打开命令提示符并输入`ipconfig`查看电脑的IP地址。

## 常见问题

1. **找不到模块**：确保在项目根目录下运行服务器

2. **数据库错误**：可以尝试使用`set RESET_DB=true`重置数据库

3. **权限问题**：确保有足够权限创建文件和目录

4. **端口被占用**：如果5000端口被占用，可以修改`run_server.py`中的端口号