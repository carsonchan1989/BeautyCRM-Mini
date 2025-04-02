import requests
import os
import logging
import json

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def upload_excel(file_path):
    """上传Excel文件到服务器"""
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return
    
    url = 'http://localhost:5000/api/excel/import'
    
    try:
        logger.info(f"准备上传文件: {file_path}")
        
        # 准备文件对象
        files = {'file': (os.path.basename(file_path), open(file_path, 'rb'), 
                          'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        
        # 发送请求
        logger.info(f"发送请求到: {url}")
        response = requests.post(url, files=files)
        
        # 检查响应
        if response.status_code == 200:
            result = response.json()
            logger.info(f"上传成功! 响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return result
        else:
            logger.error(f"上传失败，状态码: {response.status_code}, 响应: {response.text}")
            return None
    
    except Exception as e:
        logger.exception(f"上传过程中发生错误: {str(e)}")
        return None
    
    finally:
        # 确保文件已关闭
        if 'files' in locals():
            for f in files.values():
                if hasattr(f[1], 'close'):
                    f[1].close()

if __name__ == "__main__":
    # 指定Excel文件路径
    excel_file = "模拟-客户信息档案.xlsx"
    
    # 上传文件
    upload_excel(excel_file) 