"""
生成模拟的客户服务记录报告
"""
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('MockReportGenerator')

def generate_mock_report():
    """
    生成模拟的C003客户报告
    """
    logger.info("开始生成模拟客户报告")
    
    # 模拟客户信息
    customer = {
        'id': 'C003',
        'name': '王思媛',
        'gender': '女',
        'age': 32,
        'store': '分店C',
        'hometown': '四川成都',
        'residence': '北京朝阳',
        'residence_years': '8年',
        'family_structure': '新婚无孩',
        'family_age_distribution': '32-35岁',
        'living_condition': '租房',
        'personality_tags': '冲动体验型',
        'consumption_decision': '本人主导',
        'hobbies': '网红探店、SPA',
        'routine': '01:00-9:00',
        'diet_preference': '火锅重辣',
        'occupation': '自媒体博主',
        'work_unit_type': '自由职业',
        'annual_income': '50万'
    }
    
    # 模拟健康档案
    health_record = {
        'skin_type': '油痘肌',
        'oil_water_balance': '全脸油光',
        'pores_blackheads': '粗大毛孔',
        'wrinkles_texture': '无皱纹',
        'pigmentation': '痘印',
        'photoaging_inflammation': '炎症活跃',
        'tcm_constitution': '痰湿质',
        'tongue_features': '舌胖齿痕',
        'pulse_data': '濡缓',
        'sleep_routine': '01:00-9:00',
        'exercise_pattern': '无规律',
        'diet_restrictions': '嗜辣、冷饮',
        'care_time_flexibility': '夜间优先',
        'massage_pressure_preference': '强效',
        'environment_requirements': '网红打卡风',
        'short_term_beauty_goal': '控油祛痘',
        'long_term_beauty_goal': '肤质维稳',
        'short_term_health_goal': '减肥5kg',
        'long_term_health_goal': '改善宫寒',
        'medical_cosmetic_history': '水光针',
        'wellness_service_history': '无',
        'allergies': '青霉素过敏',
        'major_disease_history': '糖尿病'
    }
    
    # 模拟消费记录
    consumptions = [
        {'date': '2023-10-05 00:00:00', 'project_name': '黄金射频紧致疗程', 'amount': 6800.0, 'payment_method': '花呗分期'},
        {'date': '2023-09-20 00:00:00', 'project_name': '冰肌焕颜护理', 'amount': 2880.0, 'payment_method': '信用卡'},
        {'date': '2023-08-01 00:00:00', 'project_name': '极光净透泡泡', 'amount': 880.0, 'payment_method': '支付宝'}
    ]
    
    # 模拟服务记录，根据Excel截图数据
    services = [
        {
            'service_id': 'S001',
            'service_date': '2023-12-01 19:00:00',
            'departure_time': '2023-12-01 21:30:00',
            'total_sessions': 2,  # 根据Excel
            'total_amount': 1840.0,
            'satisfaction': '4.9/5',
            'items': [
                {'project_name': '冰肌焕颜护理', 'beautician_name': '周杰', 'unit_price': 480.0, 'is_specified': False},
                {'project_name': '黄金射频紧致疗程', 'beautician_name': '周杰', 'unit_price': 1360.0, 'is_specified': False}
            ]
        },
        {
            'service_id': 'S002',
            'service_date': '2023-11-18 18:45:00',
            'departure_time': '2023-11-18 20:15:00',
            'total_sessions': 1,
            'total_amount': 293.0,
            'satisfaction': '4.3/5',
            'items': [
                {'project_name': '极光净透泡泡', 'beautician_name': '周杰', 'unit_price': 293.0, 'is_specified': False}
            ]
        },
        {
            'service_id': 'S003',
            'service_date': '2023-11-05 21:00:00',
            'departure_time': '2023-11-05 23:30:00',
            'total_sessions': 2,
            'total_amount': 730.5,
            'satisfaction': '4.7/5',
            'items': [
                {'project_name': '帝王艾灸调理', 'beautician_name': '周杰', 'unit_price': 533.0, 'is_specified': False},
                {'project_name': '芦荟修复SPA', 'beautician_name': '摩莉', 'unit_price': 197.5, 'is_specified': True}
            ]
        },
        {
            'service_id': 'S004',
            'service_date': '2023-10-25 20:30:00',
            'departure_time': '2023-10-25 22:00:00',
            'total_sessions': 1,
            'total_amount': 480.0,
            'satisfaction': '4.6/5',
            'items': [
                {'project_name': '冰肌焕颜护理', 'beautician_name': '周杰', 'unit_price': 480.0, 'is_specified': False}
            ]
        },
        {
            'service_id': 'S005',
            'service_date': '2023-10-12 19:15:00',
            'departure_time': '2023-10-12 21:45:00',
            'total_sessions': 1,
            'total_amount': 1360.0,
            'satisfaction': '4.2/5',
            'items': [
                {'project_name': '黄金射频紧致疗程', 'beautician_name': '周杰', 'unit_price': 1360.0, 'is_specified': False}
            ]
        },
        {
            'service_id': 'S006',
            'service_date': '2023-09-30 18:30:00',
            'departure_time': '2023-09-30 20:00:00',
            'total_sessions': 1,
            'total_amount': 293.0,
            'satisfaction': '4.8/5',
            'items': [
                {'project_name': '极光净透泡泡', 'beautician_name': '周杰', 'unit_price': 293.0, 'is_specified': False}
            ]
        },
        {
            'service_id': 'S007',
            'service_date': '2023-09-16 21:00:00',
            'departure_time': '2023-09-16 23:00:00',
            'total_sessions': 1,
            'total_amount': 533.0,
            'satisfaction': '4.5/5',
            'items': [
                {'project_name': '帝王艾灸调理', 'beautician_name': '周杰', 'unit_price': 533.0, 'is_specified': False}
            ]
        },
        {
            'service_id': 'S008',
            'service_date': '2023-09-02 20:45:00',
            'departure_time': '2023-09-02 22:15:00',
            'total_sessions': 2,
            'total_amount': 1840.0,
            'satisfaction': '4.0/5',
            'items': [
                {'project_name': '黄金射频紧致疗程', 'beautician_name': '周杰', 'unit_price': 1360.0, 'is_specified': True},
                {'project_name': '芦荟修复SPA', 'beautician_name': '摩莉', 'unit_price': 480.0, 'is_specified': False}
            ]
        },
        {
            'service_id': 'S009',
            'service_date': '2023-08-12 19:30:00',
            'departure_time': '2023-08-12 21:00:00',
            'total_sessions': 1,
            'total_amount': 480.0,
            'satisfaction': '4.0/5',
            'items': [
                {'project_name': '冰肌焕颜护理', 'beautician_name': '周杰', 'unit_price': 480.0, 'is_specified': False}
            ]
        },
        {
            'service_id': 'S010',
            'service_date': '2023-08-05 20:15:00',
            'departure_time': '2023-08-05 21:45:00',
            'total_sessions': 1,
            'total_amount': 293.0,
            'satisfaction': '3.0/5',
            'items': [
                {'project_name': '极光净透泡泡', 'beautician_name': '张莉', 'unit_price': 293.0, 'is_specified': True}
            ]
        }
    ]
    
    # 模拟沟通记录
    communications = [
        {'communication_date': '2023-10-08 20:15:00', 'communication_location': '线上问卷', 'communication_content': '差评后接受补偿方案，用免费护理置换小红书推广合作'},
        {'communication_date': '2023-09-12 18:30:00', 'communication_location': '分店C VIP室', 'communication_content': '指定男性美容师服务，称"女生手法力度不够"'},
        {'communication_date': '2023-08-25 22:00:00', 'communication_location': '微信客服', 'communication_content': '投诉清洁后爆痘，店长提供免费皮肤检测安抚'},
        {'communication_date': '2023-08-05 19:45:00', 'communication_location': '分店C网红打卡区', 'communication_content': '要求调整护理房灯光亮度以适应自拍需求'},
        {'communication_date': '2023-07-28 21:30:00', 'communication_location': '抖音私信', 'communication_content': '咨询网红泡泡清洁项目是否适合直播拍摄'}
    ]
    
    # 生成MD报告
    md_content = []
    
    # 客户基本信息
    md_content.append(f"## 客户: {customer['name']} ({customer['id']})\n")
    md_content.append("### 基本信息\n")
    md_content.append("| 字段 | 值 |")
    md_content.append("|------|----|")
    for field, value in [
        ('姓名', customer['name']),
        ('性别', customer['gender']),
        ('年龄', customer['age']),
        ('门店归属', customer['store']),
        ('籍贯', customer['hometown']),
        ('现居地', customer['residence']),
        ('居住时长', customer['residence_years']),
        ('家庭成员构成', customer['family_structure']),
        ('家庭人员年龄分布', customer['family_age_distribution']),
        ('家庭居住情况', customer['living_condition']),
        ('性格类型标签', customer['personality_tags']),
        ('消费决策主导', customer['consumption_decision']),
        ('兴趣爱好', customer['hobbies']),
        ('作息规律', customer['routine']),
        ('饮食偏好', customer['diet_preference']),
        ('职业', customer['occupation']),
        ('单位性质', customer['work_unit_type']),
        ('年收入', customer['annual_income'])
    ]:
        md_content.append(f"| {field} | {value} |")
    
    # 健康档案
    md_content.append("\n### 健康档案\n")
    md_content.append("| 类别 | 字段 | 值 |")
    md_content.append("|------|------|----|")
    for field, value in [
        ('皮肤状况', '肤质类型', health_record['skin_type']),
        ('皮肤状况', '水油平衡', health_record['oil_water_balance']),
        ('皮肤状况', '毛孔与黑头', health_record['pores_blackheads']),
        ('皮肤状况', '皱纹与纹理', health_record['wrinkles_texture']),
        ('皮肤状况', '色素沉着', health_record['pigmentation']),
        ('皮肤状况', '光老化与炎症', health_record['photoaging_inflammation']),
        ('中医体质', '体质类型', health_record['tcm_constitution']),
        ('中医体质', '舌象特征', health_record['tongue_features']),
        ('中医体质', '脉象数据', health_record['pulse_data']),
        ('生活习惯', '作息规律', health_record['sleep_routine']),
        ('生活习惯', '运动频率', health_record['exercise_pattern']),
        ('生活习惯', '饮食禁忌', health_record['diet_restrictions']),
        ('护理需求', '时间灵活度', health_record['care_time_flexibility']),
        ('护理需求', '手法力度偏好', health_record['massage_pressure_preference']),
        ('护理需求', '环境氛围', health_record['environment_requirements']),
        ('美容健康目标', '短期美丽目标', health_record['short_term_beauty_goal']),
        ('美容健康目标', '长期美丽目标', health_record['long_term_beauty_goal']),
        ('美容健康目标', '短期健康目标', health_record['short_term_health_goal']),
        ('美容健康目标', '长期健康目标', health_record['long_term_health_goal']),
        ('健康记录', '医美操作史', health_record['medical_cosmetic_history']),
        ('健康记录', '大健康服务史', health_record['wellness_service_history']),
        ('健康记录', '过敏史', health_record['allergies']),
        ('健康记录', '重大疾病历史', health_record['major_disease_history'])
    ]:
        md_content.append(f"| {field[0]} | {field[1]} | {value} |")
    
    # 消费记录
    md_content.append("\n### 消费记录\n")
    md_content.append("| 消费时间 | 项目名称 | 消费金额 | 支付方式 |")
    md_content.append("|----------|----------|----------|----------|")
    for consumption in consumptions:
        md_content.append(f"| {consumption['date']} | {consumption['project_name']} | {consumption['amount']} | {consumption['payment_method']} |")
    
    # 服务记录
    md_content.append("\n### 服务记录\n")
    md_content.append("| 到店时间 | 离店时间 | 总耗卡次数 | 总耗卡金额 | 服务满意度 | 项目详情1 | 项目详情2 | 项目详情3 | 项目详情4 | 项目详情5 |")
    md_content.append("|----------|----------|------------|------------|------------|-----------|-----------|-----------|-----------|------------|")
    
    for service in services:
        # 格式化项目详情
        project_details = []
        for item in service['items']:
            # 格式：项目内容\操作美容师\耗卡金额\是否指定
            specified_text = "✓指定" if item['is_specified'] else "未指定"
            detail = f"{item['project_name']} - {item['beautician_name']} - {item['unit_price']}元 - {specified_text}"
            project_details.append(detail)
        
        # 确保有5个项目详情字段
        while len(project_details) < 5:
            project_details.append("")
        
        # 添加服务记录行
        row = f"| {service['service_date']} | {service['departure_time']} | {service['total_sessions']} | {service['total_amount']} | {service['satisfaction']} | {' | '.join(project_details[:5])} |"
        md_content.append(row)
    
    # 沟通记录
    md_content.append("\n### 沟通记录\n")
    md_content.append("| 沟通时间 | 沟通地点 | 沟通内容 |")
    md_content.append("|----------|----------|----------|")
    for comm in communications:
        md_content.append(f"| {comm['communication_date']} | {comm['communication_location']} | {comm['communication_content']} |")
    
    # 保存到文件
    output_file = "C003_customer_report_mock.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md_content))
    
    logger.info(f"模拟客户报告已生成: {output_file}")
    return output_file

if __name__ == "__main__":
    generate_mock_report()