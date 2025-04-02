"""
更新app.py文件，添加项目管理API路由
"""

import os
import re

# 读取当前app.py内容
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 添加项目路由导入
import_pattern = r'from api\.excel_routes import excel_bp'
new_import = 'from api.excel_routes import excel_bp\nfrom api.project_routes import project_bp'
content = content.replace(import_pattern, new_import)

# 添加项目路由注册
blueprint_pattern = r'app\.register_blueprint\(excel_bp, url_prefix=\'\/api\/excel\'\)'
new_blueprint = 'app.register_blueprint(excel_bp, url_prefix=\'/api/excel\')\n    app.register_blueprint(project_bp, url_prefix=\'/api/projects\')'
content = content.replace(blueprint_pattern, new_blueprint)

# 写回文件
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("app.py文件已更新，添加了项目管理API路由") 