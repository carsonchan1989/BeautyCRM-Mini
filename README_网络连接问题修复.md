# BeautyCRM-Mini 导入Excel连接问题修复说明

## 问题描述

微信小程序上传Excel文件时出现以下错误：
```
uploadFile:fail Error: connect ECONNREFUSED 127.0.0.1:5000
```

此错误表明小程序无法连接到本地服务器（127.0.0.1:5000）。在移动设备上运行的微信小程序无法直接连接到开发者电脑上的localhost地址。

## 解决方案

### 1. 修改API地址配置

在小程序的`app.js`文件中，将API基础URL从localhost改为您电脑的局域网IP地址：

```javascript
globalData: {
  apiBaseUrl: 'http://192.168.x.x:5000/api' // 将127.0.0.1替换为您电脑的IP地址
}
```

您可以通过以下步骤找到您电脑的IP地址：
- Windows: 打开命令提示符并输入`ipconfig`
- Mac/Linux: 打开终端并输入`ifconfig`

### 2. 使用独立的Excel导入服务器

为了快速解决问题，我们提供了一个独立的Excel导入服务器脚本`excel_import_fix.py`。

#### 启动方法：

1. 确保已安装所需的Python库：
```
pip install flask flask-cors werkzeug pandas
```

2. 运行独立服务器：
```
python excel_import_fix.py
```

3. 服务器将在`0.0.0.0:5000`上启动，支持来自局域网的连接

### 3. 确保网络环境正确

1. 确保手机和电脑在同一个WiFi网络下
2. 临时关闭电脑防火墙，或添加5000端口到防火墙例外
3. 如果使用公司网络，可能需要检查网络策略是否允许设备间通信

### 4. 测试连接

启动服务器后，可以在手机浏览器中访问以下地址测试连接：
```
http://192.168.x.x:5000/api/excel/import
```

如果能看到错误提示"未找到上传的文件"，说明连接成功。

## 进一步优化

1. 在实际部署中，建议将后端服务部署到公网服务器
2. 使用HTTPS协议确保数据传输安全
3. 添加适当的用户认证和授权机制

## 临时解决方案

如果以上方法不起作用，可以暂时使用模拟数据：

1. 在模拟模式下，小程序不会实际发送网络请求
2. 编辑`pages/excel/import.js`，添加一个模拟模式标志
3. 使用本地模拟数据来测试其他功能