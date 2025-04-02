"""
应用Excel导入功能补丁
"""
import os
import shutil
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('PatchApplier')

def apply_patches():
    """应用所有补丁文件"""
    logger.info("开始应用Excel导入补丁...")
    
    # 1. 复制修复版Excel导入JS模块
    src_path = "excel_import_fixed.js"
    dest_path = os.path.join("utils", "excel_import_fixed.js")
    
    if os.path.exists(src_path):
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(src_path, dest_path)
        logger.info(f"复制 {src_path} 到 {dest_path} 成功")
    else:
        logger.error(f"文件不存在: {src_path}")
    
    # 2. 应用补丁到服务器端代码
    # 2.1 确保patches目录存在
    patch_dir = os.path.join("server", "api", "patches")
    os.makedirs(patch_dir, exist_ok=True)
    
    # 2.2 复制补丁文件
    patch_src = os.path.join("server", "api", "excel_import_patch.py")
    patch_dest = os.path.join(patch_dir, "excel_import_patch.py")
    
    if os.path.exists(patch_src):
        shutil.copy2(patch_src, patch_dest)
        logger.info(f"复制补丁文件 {patch_src} 到 {patch_dest} 成功")
    else:
        logger.error(f"补丁文件不存在: {patch_src}")
    
    # 3. 更新app.py以注册补丁
    update_app_py()
    
    # 4. 修改md_report_generator.py，移除对不存在字段的引用
    update_md_report_generator()
    
    logger.info("补丁应用完成")

def update_app_py():
    """更新app.py文件注册补丁"""
    app_py_path = os.path.join("server", "app.py")
    backup_path = os.path.join("server", "app.py.bak")
    
    # 先备份原文件
    if os.path.exists(app_py_path):
        shutil.copy2(app_py_path, backup_path)
        logger.info(f"备份app.py到 {backup_path}")
        
        with open(app_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经导入补丁
        if "from .api.patches.excel_import_patch import register_excel_patch" not in content:
            # 添加导入语句
            import_line = "from .api.patches.excel_import_patch import register_excel_patch"
            content = content.replace("from flask import Flask", "from flask import Flask\n" + import_line)
            
            # 添加注册语句
            register_line = "    register_excel_patch(app)"
            if "def create_app():" in content:
                # 在create_app函数中添加补丁注册
                content = content.replace("    return app", register_line + "\n    return app")
            
            # 写入更新后的内容
            with open(app_py_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("更新app.py成功")
        else:
            logger.info("app.py已包含补丁代码，无需更新")
    else:
        logger.error(f"文件不存在: {app_py_path}")

def update_md_report_generator():
    """更新md_report_generator.py移除不存在字段引用"""
    file_path = "md_report_generator.py"
    backup_path = "md_report_generator.py.bak"
    
    if os.path.exists(file_path):
        # 备份原文件
        shutil.copy2(file_path, backup_path)
        logger.info(f"备份 {file_path} 到 {backup_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换不正确的字段引用
        old_code = """# 使用服务记录中的总耗卡次数，而不是计算值
        total_sessions = service.get('total_sessions', 0)
        if total_sessions == 0 and 'total_project_count' in service:
            # 兼容旧字段
            total_sessions = service.get('total_project_count', len(filtered_items))
        elif total_sessions == 0:
            # 如果没有值，则使用过滤后的项目数
            total_sessions = len(filtered_items)"""
        
        new_code = """# 使用服务记录中的总耗卡次数，而不是计算值
        total_sessions = service.get('total_sessions', 0)
        if total_sessions == 0:
            # 如果数据库中没有值，则使用过滤后的项目数
            total_sessions = len(filtered_items)"""
        
        if old_code in content:
            content = content.replace(old_code, new_code)
            
            # 写入更新后的内容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("更新 md_report_generator.py 成功")
        else:
            logger.info("md_report_generator.py 已修复，无需更新")
    else:
        logger.error(f"文件不存在: {file_path}")

if __name__ == "__main__":
    apply_patches()