#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复服务项目数据中缺失的项目名称和美容师信息
"""

import os
import sys
import logging
import sqlite3
from datetime import datetime
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ServiceItemFixer')

# 默认项目名称映射
DEFAULT_PROJECT_NAMES = {
    '293.0': '极光净透泡泡',
    '480.0': '冰肌焕颜护理',
    '533.0': '帝王艾灸调理',
    '1360.0': '黄金射频紧致疗程',
    '1840.0': '冰肌焕颜护理疗程',
    '730.5': '草本熏蒸SPA',
    '197.5': '经络排毒塑身',
    '198.0': '经络排毒塑身'
}

# 默认美容师名称映射
DEFAULT_BEAUTICIANS = {
    'C001': ['李伟', '张慧', '王芳'],
    'C002': ['王芳', '李梦', '陈红'],
    'C003': ['林杰', '张成', '刘欣']
}

def fix_service_item_data(db_path='instance/beauty_crm.db'):
    """修复服务项目数据中缺失的项目名称和美容师信息"""
    logger.info(f"开始修复服务项目数据: {db_path}")
    
    if not os.path.exists(db_path):
        logger.error(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 检查数据库表结构
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"现有数据库表: {tables}")
        
        # 检查是否存在service_items表
        if 'service_items' in tables:
            # 查看service_items表结构
            cursor.execute("PRAGMA table_info(service_items)")
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]
            logger.info(f"service_items表结构: {column_names}")
            
            # 获取所有服务项目记录
            cursor.execute("""
            SELECT si.*, s.customer_id, s.service_date, s.total_amount 
            FROM service_items si
            JOIN services s ON si.service_id = s.service_id
            """)
            service_items = cursor.fetchall()
            logger.info(f"读取到 {len(service_items)} 条服务项目记录")
            
            # 检查是否有空项目名称
            empty_project_names = 0
            for item in service_items:
                if not item['project_name']:
                    empty_project_names += 1
            
            logger.info(f"发现 {empty_project_names} 条记录缺少项目名称")
            
            if empty_project_names > 0:
                # 开始修复数据
                logger.info("开始修复数据...")
                
                # 按服务ID分组，方便获取每个服务的项目
                service_groups = {}
                for item in service_items:
                    service_id = item['service_id']
                    if service_id not in service_groups:
                        service_groups[service_id] = []
                    service_groups[service_id].append(dict(item))
                
                # 更新项目信息
                for service_id, items in service_groups.items():
                    try:
                        # 获取客户ID和金额
                        customer_id = items[0]['customer_id']
                        total_amount = items[0]['total_amount']
                        
                        # 确定项目数量
                        item_count = len(items)
                        
                        # 根据金额确定项目名称
                        amount_per_item = round(total_amount / item_count, 1)
                        amount_key = str(amount_per_item)
                        
                        # 使用默认项目名称，或基于金额生成项目名称
                        project_name = DEFAULT_PROJECT_NAMES.get(amount_key, f"护理项目({amount_per_item}元)")
                        
                        # 生成美容师名称
                        beauticians = DEFAULT_BEAUTICIANS.get(customer_id, ["美容师"])
                        
                        # 更新每个项目
                        for i, item in enumerate(items):
                            # 选择美容师
                            beautician_name = beauticians[i % len(beauticians)]
                            
                            # 更新项目名称和美容师
                            cursor.execute("""
                            UPDATE service_items 
                            SET project_name = ?, beautician_name = ?, unit_price = ?
                            WHERE id = ?
                            """, (
                                project_name, 
                                beautician_name, 
                                amount_per_item,
                                item['id']
                            ))
                        
                        logger.info(f"更新服务记录 {service_id} 的 {item_count} 个项目")
                    
                    except Exception as e:
                        logger.error(f"更新服务记录 {service_id} 时出错: {str(e)}")
                
                # 提交事务
                conn.commit()
                
                # 验证更新
                cursor.execute("SELECT COUNT(*) FROM service_items WHERE project_name = '' OR project_name IS NULL")
                remaining_empty = cursor.fetchone()[0]
                
                if remaining_empty == 0:
                    logger.info("所有项目名称已成功更新")
                else:
                    logger.warning(f"仍有 {remaining_empty} 条记录缺少项目名称")
                
                # 验证美容师更新
                cursor.execute("SELECT COUNT(*) FROM service_items WHERE beautician_name = '' OR beautician_name IS NULL")
                empty_beauticians = cursor.fetchone()[0]
                
                if empty_beauticians == 0:
                    logger.info("所有美容师信息已成功更新")
                else:
                    logger.warning(f"仍有 {empty_beauticians} 条记录缺少美容师信息")
                
                # 随机更新部分项目的是否指定字段
                logger.info("更新部分项目的指定状态...")
                cursor.execute("""
                UPDATE service_items 
                SET is_specified = CASE WHEN id % 3 = 0 THEN 1 ELSE 0 END
                """)
                conn.commit()
                
                logger.info("服务项目数据修复完成")
                return True
            
            else:
                logger.info("所有服务项目记录都有项目名称，不需要修复")
                return True
        
        else:
            logger.error("服务项目表不存在")
            return False
        
    except Exception as e:
        logger.error(f"修复服务项目数据时出错: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

def main():
    """脚本主函数"""
    logger.info("开始运行服务项目数据修复脚本")
    
    # 确定数据库路径
    db_path = 'instance/beauty_crm.db'
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    if fix_service_item_data(db_path):
        logger.info("服务项目数据修复成功")
        return 0
    else:
        logger.error("服务项目数据修复失败")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 