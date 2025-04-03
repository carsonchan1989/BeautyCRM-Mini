#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速修复数据库中的服务项目
"""

import sqlite3
import logging
import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据库文件路径
DB_FILE = 'D:\\BeautyCRM-Mini\\server\\app.db'

# 服务项目数据 - 根据Excel中的数据手动整理
SERVICE_ITEMS = {
    # 客户ID: 服务日期 -> [(项目, 美容师, 金额, 是否指定)]
    "C001": {
        "2023-07-12 14:00:00": [
            ("冰肌焕颜护理", "李婷", 480.0, True),
            ("颈部导入", "张伟", 200.0, False)
        ],
        "2023-07-19 15:20:00": [
            ("冰肌焕颜护理", "李婷", 450.0, True)
        ],
        "2023-08-05 10:00:00": [
            ("黄金射频紧致疗程", "张伟", 1360.0, False),
            ("冰肌焕颜护理", "张伟", 480.0, False)
        ],
        "2023-08-12 11:15:00": [
            ("黄金射频紧致疗程", "张伟", 1360.0, False)
        ],
        "2023-08-18 14:00:00": [
            ("帝王艾灸调理", "李婷", 533.0, True),
            ("草本熏蒸SPA", "王芳", 197.5, True)
        ],
        "2023-09-02 09:30:00": [
            ("帝王艾灸调理", "王芳", 533.0, False)
        ],
        "2023-09-09 15:00:00": [
            ("冰肌焕颜护理", "李婷", 480.0, True),
            ("头皮护理", "王芳", 350.0, False)
        ],
        "2023-09-20 14:20:00": [
            ("冰肌焕颜护理", "李婷", 480.0, True),
            ("草本熏蒸SPA", "张伟", 197.5, True)
        ],
        "2023-10-05 10:45:00": [
            ("黄金射频紧致疗程", "张伟", 1360.0, False),
            ("颈部导入", "王芳", 480.0, False)
        ],
        "2023-10-18 16:00:00": [
            ("帝王艾灸调理", "王芳", 533.0, False)
        ]
    },
    "C002": {
        "2023-07-05 09:30:00": [
            ("草本熏蒸SPA", "王芳", 197.5, False)
        ],
        "2023-07-19 10:15:00": [
            ("经络排毒塑身", "王芳", 198.0, True)
        ],
        "2023-08-10 09:45:00": [
            ("帝王艾灸调理", "陈莉", 533.0, False),
            ("草本熏蒸SPA", "王芳", 197.5, True)
        ],
        "2023-08-17 14:30:00": [
            ("帝王艾灸调理", "王芳", 533.0, True)
        ],
        "2023-09-05 14:00:00": [
            ("经络排毒塑身", "王芳", 198.0, True)
        ],
        "2023-09-20 10:30:00": [
            ("草本熏蒸SPA", "陈莉", 197.5, False)
        ],
        "2023-10-03 09:00:00": [
            ("黄金射频紧致疗程", "张伟", 1360.0, False)
        ],
        "2023-10-15 15:15:00": [
            ("帝王艾灸调理", "王芳", 533.0, True)
        ],
        "2023-10-25 13:00:00": [
            ("草本熏蒸SPA", "陈莉", 197.5, False),
            ("头皮护理", "王芳", 350.0, False)
        ],
        "2023-11-02 11:00:00": [
            ("经络排毒塑身", "王芳", 198.0, True)
        ]
    },
    "C003": {
        "2023-08-05 20:15:00": [
            ("极光净透泡泡", "张莉", 293.0, False)
        ],
        "2023-08-12 19:30:00": [
            ("冰肌焕颜护理", "周杰", 480.0, True)
        ],
        "2023-09-02 20:45:00": [
            ("黄金射频紧致疗程", "周杰", 1360.0, True),
            ("冰肌焕颜护理", "张莉", 480.0, True)
        ],
        "2023-09-16 21:00:00": [
            ("帝王艾灸调理", "周杰", 533.0, True)
        ],
        "2023-09-30 18:30:00": [
            ("极光净透泡泡", "周杰", 293.0, True)
        ],
        "2023-10-12 19:15:00": [
            ("黄金射频紧致疗程", "周杰", 1360.0, True)
        ],
        "2023-10-25 20:30:00": [
            ("冰肌焕颜护理", "周杰", 480.0, True)
        ],
        "2023-11-05 21:00:00": [
            ("帝王艾灸调理", "周杰", 533.0, True),
            ("草本熏蒸SPA", "陈莉", 197.5, False)
        ],
        "2023-11-18 18:45:00": [
            ("极光净透泡泡", "周杰", 293.0, True)
        ],
        "2023-12-01 19:00:00": [
            ("黄金射频紧致疗程", "周杰", 1360.0, True),
            ("冰肌焕颜护理", "王芳", 480.0, False)
        ]
    }
}

def dump_services():
    """打印数据库中的服务记录信息"""
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 打印服务记录表结构
        cursor.execute("PRAGMA table_info(services)")
        columns = cursor.fetchall()
        logger.info("服务记录表结构:")
        for col in columns:
            logger.info(f"  {col}")
        
        # 打印服务项目表结构
        cursor.execute("PRAGMA table_info(service_items)")
        columns = cursor.fetchall()
        logger.info("服务项目表结构:")
        for col in columns:
            logger.info(f"  {col}")
        
        # 查询方式1: 直接获取所有服务记录
        cursor.execute("SELECT service_id, customer_id, service_date, total_amount FROM services")
        services = cursor.fetchall()
        logger.info(f"服务记录数量: {len(services)}")
        
        # 查询方式2: 尝试按不同字段格式匹配服务日期
        logger.info("尝试按不同格式匹配服务日期:")
        for customer_id, services_by_date in SERVICE_ITEMS.items():
            for service_date_str in services_by_date.keys():
                # 尝试多种格式匹配
                try:
                    # 原始格式
                    cursor.execute(
                        "SELECT service_id, customer_id, service_date FROM services WHERE customer_id = ? AND service_date = ?", 
                        (customer_id, service_date_str)
                    )
                    result = cursor.fetchall()
                    if result:
                        logger.info(f"匹配成功(原始格式): {customer_id}, {service_date_str} -> {result}")
                        continue
                    
                    # 尝试解析为datetime并重新格式化
                    dt = datetime.datetime.strptime(service_date_str, "%Y-%m-%d %H:%M:%S")
                    
                    # 格式1: ISO格式
                    iso_format = dt.isoformat()
                    cursor.execute(
                        "SELECT service_id, customer_id, service_date FROM services WHERE customer_id = ? AND service_date = ?", 
                        (customer_id, iso_format)
                    )
                    result = cursor.fetchall()
                    if result:
                        logger.info(f"匹配成功(ISO格式): {customer_id}, {service_date_str} -> {result}")
                        continue
                    
                    # 格式2: 只有日期部分
                    date_only = dt.strftime("%Y-%m-%d")
                    cursor.execute(
                        "SELECT service_id, customer_id, service_date FROM services WHERE customer_id = ? AND date(service_date) = ?", 
                        (customer_id, date_only)
                    )
                    result = cursor.fetchall()
                    if result:
                        logger.info(f"匹配成功(仅日期): {customer_id}, {service_date_str} -> {result}")
                        continue
                    
                    # 格式3: 模糊匹配
                    like_pattern = f"{date_only}%"
                    cursor.execute(
                        "SELECT service_id, customer_id, service_date FROM services WHERE customer_id = ? AND service_date LIKE ?", 
                        (customer_id, like_pattern)
                    )
                    result = cursor.fetchall()
                    if result:
                        logger.info(f"匹配成功(模糊匹配): {customer_id}, {service_date_str} -> {result}")
                        continue
                    
                    logger.warning(f"未找到匹配记录: {customer_id}, {service_date_str}")
                    
                except Exception as e:
                    logger.error(f"尝试匹配服务日期时出错: {customer_id}, {service_date_str}, {str(e)}")
        
        # 查看service_items表的内容
        cursor.execute("SELECT id, service_id, project_name, beautician_name, card_deduction FROM service_items LIMIT 10")
        items = cursor.fetchall()
        logger.info(f"服务项目表中的前10条记录:")
        for item in items:
            logger.info(f"  项目: {item}")
        
        # 检查服务记录与项目的关系
        logger.info("检查服务记录与项目的关系:")
        cursor.execute("""
            SELECT s.service_id, s.customer_id, s.service_date, COUNT(si.id) as item_count
            FROM services s
            LEFT JOIN service_items si ON s.service_id = si.service_id
            GROUP BY s.service_id
        """)
        service_items_count = cursor.fetchall()
        for record in service_items_count:
            service_id, customer_id, service_date, item_count = record
            logger.info(f"服务ID: {service_id}, 客户: {customer_id}, 日期: {service_date}, 项目数: {item_count}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"打印服务记录时出错: {str(e)}")

def update_service_items():
    """更新数据库中的服务项目"""
    logger.info("开始更新服务项目数据")
    
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 清空现有的服务项目表
        cursor.execute("DELETE FROM service_items")
        logger.info("已清空服务项目表")
        
        # 创建映射: 通过组合客户ID和日期部分来匹配服务ID
        logger.info("创建日期匹配映射...")
        cursor.execute("SELECT service_id, customer_id, service_date FROM services")
        rows = cursor.fetchall()
        
        # 多种匹配方式的映射
        service_id_by_exact_match = {}  # 完全匹配
        service_id_by_date_only = {}    # 只匹配日期部分
        
        for service_id, customer_id, service_date_str in rows:
            # 可能有None值
            if not service_date_str:
                continue
                
            # 完全匹配
            key_exact = f"{customer_id}_{service_date_str}"
            service_id_by_exact_match[key_exact] = service_id
            
            # 尝试提取日期部分
            try:
                dt = datetime.datetime.fromisoformat(service_date_str.replace(' ', 'T'))
                date_only = dt.strftime("%Y-%m-%d")
                key_date = f"{customer_id}_{date_only}"
                service_id_by_date_only[key_date] = service_id
            except Exception as e:
                logger.warning(f"无法解析日期: {service_date_str}, 错误: {str(e)}")
        
        logger.info(f"获取到 {len(service_id_by_exact_match)} 条完全匹配映射")
        logger.info(f"获取到 {len(service_id_by_date_only)} 条日期匹配映射")
        
        # 更新服务项目
        total_items = 0
        for customer_id, services in SERVICE_ITEMS.items():
            for service_date_str, items in services.items():
                # 尝试多种匹配方式
                service_id = None
                
                # 1. 完全匹配
                key_exact = f"{customer_id}_{service_date_str}"
                if key_exact in service_id_by_exact_match:
                    service_id = service_id_by_exact_match[key_exact]
                    logger.info(f"完全匹配: {key_exact} -> {service_id}")
                else:
                    # 2. 提取日期部分匹配
                    try:
                        dt = datetime.datetime.strptime(service_date_str, "%Y-%m-%d %H:%M:%S")
                        date_only = dt.strftime("%Y-%m-%d")
                        key_date = f"{customer_id}_{date_only}"
                        
                        if key_date in service_id_by_date_only:
                            service_id = service_id_by_date_only[key_date]
                            logger.info(f"日期匹配: {key_date} -> {service_id}")
                        else:
                            # 3. 模糊匹配 - 查询数据库
                            like_pattern = f"{date_only}%"
                            cursor.execute("""
                                SELECT service_id FROM services 
                                WHERE customer_id = ? AND service_date LIKE ?
                            """, (customer_id, like_pattern))
                            result = cursor.fetchone()
                            if result:
                                service_id = result[0]
                                logger.info(f"模糊匹配: {customer_id} + {like_pattern} -> {service_id}")
                    except Exception as e:
                        logger.error(f"尝试匹配时出错: {str(e)}")
                
                # 如果找不到匹配的服务ID，记录警告并跳过
                if not service_id:
                    logger.warning(f"未找到服务记录: {customer_id}, {service_date_str}")
                    continue
                
                logger.info(f"找到服务ID: {service_id} -> {customer_id}, {service_date_str}")
                
                # 添加服务项目
                for item in items:
                    project_name, beautician_name, amount, is_specified = item
                    
                    try:
                        cursor.execute("""
                            INSERT INTO service_items 
                            (service_id, project_name, beautician_name, card_deduction, is_specified, is_satisfied, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                        """, (
                            service_id,
                            project_name,
                            beautician_name,
                            amount,
                            1 if is_specified else 0,
                            1  # 默认满意
                        ))
                        
                        total_items += 1
                        logger.info(f"添加项目: {service_id} - {project_name} - {beautician_name} - {amount}")
                    
                    except Exception as e:
                        logger.error(f"添加项目时出错: {str(e)}")
        
        # 提交更改
        conn.commit()
        logger.info(f"更新完成: 共添加 {total_items} 个服务项目")
        
        # 关闭连接
        cursor.close()
        conn.close()
    
    except Exception as e:
        logger.error(f"更新服务项目时出错: {str(e)}")

if __name__ == "__main__":
    dump_services()
    update_service_items()