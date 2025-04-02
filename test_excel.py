"""
测试Excel处理模块的脚本
"""
import os
import sys
import logging
import json
from datetime import datetime

# 设置日志级别
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('excel_test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('ExcelTest')

# 添加服务器目录到Python路径
server_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server')
sys.path.append(server_dir)

try:
    from utils.excel_processor import ExcelProcessor
    logger.info("成功导入ExcelProcessor模块")
except ImportError as e:
    logger.error(f"导入ExcelProcessor失败: {e}")
    server_utils_dir = os.path.join(server_dir, 'utils')
    if os.path.exists(server_utils_dir):
        logger.info(f"服务器utils目录存在: {server_utils_dir}")
        logger.info(f"目录内容: {os.listdir(server_utils_dir)}")
    else:
        logger.error(f"服务器utils目录不存在: {server_utils_dir}")
    sys.exit(1)

def test_excel_processor():
    """测试Excel处理器"""
    try:
        # 获取Excel文件路径
        excel_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '模拟-客户信息档案.xlsx')
        
        if not os.path.exists(excel_file):
            logger.error(f"Excel文件不存在: {excel_file}")
            return
        
        logger.info(f"开始处理Excel文件: {excel_file}")
        
        # 初始化Excel处理器
        processor = ExcelProcessor()
        logger.info("成功创建ExcelProcessor实例")
        
        # 处理Excel文件
        logger.info("开始调用process_file方法")
        result = processor.process_file(excel_file)
        
        # 记录结果
        logger.info("Excel处理完成，写入结果到json文件")
        
        # 将结果写入文件以便查看
        result_file = 'excel_result.json'
        with open(result_file, 'w', encoding='utf-8') as f:
            # 将datetime对象转换为字符串
            def datetime_converter(o):
                if isinstance(o, datetime):
                    return o.isoformat()
                
            json.dump(result, f, ensure_ascii=False, indent=2, default=datetime_converter)
            
        logger.info(f"结果已保存至: {result_file}")
        
        # 输出统计信息
        logger.info("处理结果统计:")
        for key, items in result.items():
            logger.info(f"  {key}: {len(items)}项")
            
        # 检查客户数据
        if 'customers' in result and len(result['customers']) > 0:
            logger.info("客户数据示例:")
            sample = result['customers'][0]
            for key, value in sample.items():
                logger.info(f"  {key}: {value}")
        else:
            logger.warning("未找到客户数据")
            
    except Exception as e:
        logger.exception(f"Excel处理过程中出错: {e}")

if __name__ == "__main__":
    logger.info("==== 开始Excel处理测试 ====")
    test_excel_processor()
    logger.info("==== Excel处理测试完成 ====")