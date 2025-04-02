# 修复Python导入错误

## 问题描述

运行服务器时出现以下错误：
```
ImportError: attempted relative import with no known parent package
(base) PS D:\BeautyCRM-Mini> cd D:\BeautyCRM-Mini && set RESET_DB=true && python server/app.py
Traceback (most recent call last):
  File "D:\BeautyCRM-Mini\server\app.py", line 19, in <module>
    from .models import db
ImportError: attempted relative import with no known parent package
```

## 原因

这个错误是因为在Python中，当直接运行脚本文件时（如`python server/app.py`），相对导入（以点`.`开头的导入语句）无法正常工作。相对导入只能在作为包的一部分导入时使用，而不能在直接作为脚本运行时使用。

## 解决方案

### 方案1：修改导入语句

将`server/app.py`中的相对导入改为绝对导入：

```python
# 修改前
from .models import db

# 修改后
from server.models import db
```

### 方案2：使用Python模块运行方式

不要直接运行Python文件，而是使用`-m`参数以模块形式运行：

```bash
cd D:\BeautyCRM-Mini
set RESET_DB=true
python -m server.app
```

### 方案3：修改项目结构（推荐）

1. 创建一个启动脚本`run_server.py`，放在项目根目录：

```python
# D:\BeautyCRM-Mini\run_server.py
import os
import sys

# 将当前目录添加到Python路径
sys.path.insert(0, os.path.abspath('.'))

# 导入并运行服务器
from server.app import app

if __name__ == '__main__':
    # 检查是否需要重置数据库
    reset_db = os.environ.get('RESET_DB', 'false').lower() == 'true'
    if reset_db:
        print("将重置数据库...")
        
    # 启动服务器
    app.run(host='0.0.0.0', port=5000, debug=True)
```

2. 然后修改`server/app.py`，删除直接运行的部分：

```python
# server/app.py
from flask import Flask
from server.models import db  # 使用绝对导入

# 创建Flask应用
app = Flask(__name__)
# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/beauty_crm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db.init_app(app)

# 注册蓝图
# 例如: from server.api.customers import customer_bp
# app.register_blueprint(customer_bp, url_prefix='/api/customers')

# 不要在这里运行app，而是在run_server.py中运行
```

3. 使用新的启动方式：

```bash
cd D:\BeautyCRM-Mini
set RESET_DB=true
python run_server.py
```

## 为什么会出现这个问题？

Python的导入系统基于包的概念。当你使用相对导入（如`from .models import db`）时，Python需要知道当前文件位于哪个包中。

当你直接运行一个Python文件（如`python server/app.py`）时，Python将该文件作为独立的`__main__`模块运行，而不是作为`server`包的一部分。因此，Python不知道`.models`指的是什么。

使用上述任何一种解决方案都可以确保Python正确理解包的上下文，从而解决导入错误。