"""
数据库模型定义 - 美容客户管理系统
"""

import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def generate_uuid():
    """生成UUID作为客户ID"""
    return f"CUST_{uuid.uuid4().hex[:16].upper()}"

class Customer(db.Model):
    """客户基础信息表"""
    __tablename__ = 'customers'
    
    id = db.Column(db.String(32), primary_key=True, default=generate_uuid)  # 客户唯一ID
    name = db.Column(db.String(64), nullable=False)  # 姓名
    gender = db.Column(db.String(8), default='未知')  # 性别
    age = db.Column(db.Integer, nullable=True)  # 年龄
    store = db.Column(db.String(64), nullable=True)  # 所属门店
    
    # 家庭及居住情况
    hometown = db.Column(db.String(128), nullable=True)  # 籍贯
    residence = db.Column(db.String(256), nullable=True)  # 现居地
    residence_years = db.Column(db.String(32), nullable=True)  # 居住时长
    family_structure = db.Column(db.String(256), nullable=True)  # 家庭成员构成
    family_age_distribution = db.Column(db.String(256), nullable=True)  # 家庭人员年龄分布
    living_condition = db.Column(db.String(256), nullable=True)  # 家庭居住情况
    
    # 个性与生活习惯
    personality_tags = db.Column(db.String(256), nullable=True)  # 性格类型标签
    consumption_decision = db.Column(db.String(64), nullable=True)  # 消费决策主导
    risk_sensitivity = db.Column(db.String(64), nullable=True)  # 风险敏感度
    hobbies = db.Column(db.String(256), nullable=True)  # 兴趣爱好
    routine = db.Column(db.String(256), nullable=True)  # 作息规律
    diet_preference = db.Column(db.String(256), nullable=True)  # 饮食偏好
    
    # 健康相关
    menstrual_record = db.Column(db.Text, nullable=True)  # 生理期记录
    family_medical_history = db.Column(db.Text, nullable=True)  # 家族遗传病史
    
    # 职业与收入
    occupation = db.Column(db.String(64), nullable=True)  # 职业
    work_unit_type = db.Column(db.String(64), nullable=True)  # 单位性质
    annual_income = db.Column(db.String(32), nullable=True)  # 年收入
    
    # 记录时间戳
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    health_records = db.relationship('HealthRecord', backref='customer', lazy=True)
    consumption_records = db.relationship('Consumption', backref='customer', lazy=True)
    service_records = db.relationship('Service', backref='customer', lazy=True)
    communication_records = db.relationship('Communication', backref='customer', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'gender': self.gender,
            'age': self.age,
            'store': self.store,
            'hometown': self.hometown,
            'residence': self.residence,
            'residence_years': self.residence_years,
            'family_structure': self.family_structure,
            'family_age_distribution': self.family_age_distribution,
            'living_condition': self.living_condition,
            'personality_tags': self.personality_tags,
            'consumption_decision': self.consumption_decision,
            'risk_sensitivity': self.risk_sensitivity,
            'hobbies': self.hobbies,
            'routine': self.routine,
            'diet_preference': self.diet_preference,
            'menstrual_record': self.menstrual_record,
            'family_medical_history': self.family_medical_history,
            'occupation': self.occupation,
            'work_unit_type': self.work_unit_type,
            'annual_income': self.annual_income,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class HealthRecord(db.Model):
    """健康与皮肤档案表"""
    __tablename__ = 'health_records'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.String(32), db.ForeignKey('customers.id'), nullable=False)
    
    # 皮肤状况
    skin_type = db.Column(db.String(32), nullable=True)  # 肤质类型
    oil_water_balance = db.Column(db.String(128), nullable=True)  # 水油情况
    pores_blackheads = db.Column(db.String(128), nullable=True)  # 毛孔与黑头
    wrinkles_texture = db.Column(db.String(128), nullable=True)  # 皱纹与纹理
    pigmentation = db.Column(db.String(128), nullable=True)  # 色素沉着
    photoaging_inflammation = db.Column(db.String(128), nullable=True)  # 光老化与炎症
    
    # 中医体质
    tcm_constitution = db.Column(db.String(64), nullable=True)  # 中医体质类型
    tongue_features = db.Column(db.String(256), nullable=True)  # 舌象特征
    pulse_data = db.Column(db.String(256), nullable=True)  # 脉象数据
    
    # 生活习惯
    sleep_routine = db.Column(db.String(256), nullable=True)  # 作息规律
    exercise_pattern = db.Column(db.String(256), nullable=True)  # 运动频率及类型
    diet_restrictions = db.Column(db.String(256), nullable=True)  # 饮食禁忌/偏好
    
    # 服务偏好
    care_time_flexibility = db.Column(db.String(64), nullable=True)  # 护理时间灵活度
    massage_pressure_preference = db.Column(db.String(64), nullable=True)  # 手法力度偏好
    environment_requirements = db.Column(db.String(256), nullable=True)  # 环境氛围要求
    
    # 个人目标
    short_term_beauty_goal = db.Column(db.Text, nullable=True)  # 短期美丽目标
    long_term_beauty_goal = db.Column(db.Text, nullable=True)  # 长期美丽目标
    short_term_health_goal = db.Column(db.Text, nullable=True)  # 短期健康目标
    long_term_health_goal = db.Column(db.Text, nullable=True)  # 长期健康目标
    
    # 病史
    medical_cosmetic_history = db.Column(db.Text, nullable=True)  # 医美操作史
    wellness_service_history = db.Column(db.Text, nullable=True)  # 大健康服务史
    major_disease_history = db.Column(db.Text, nullable=True)  # 重大疾病历史
    allergies = db.Column(db.Text, nullable=True)  # 过敏史
    
    # 记录时间戳
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'skin_type': self.skin_type,
            'oil_water_balance': self.oil_water_balance,
            'pores_blackheads': self.pores_blackheads,
            'wrinkles_texture': self.wrinkles_texture,
            'pigmentation': self.pigmentation,
            'photoaging_inflammation': self.photoaging_inflammation,
            'tcm_constitution': self.tcm_constitution,
            'tongue_features': self.tongue_features,
            'pulse_data': self.pulse_data,
            'sleep_routine': self.sleep_routine,
            'exercise_pattern': self.exercise_pattern,
            'diet_restrictions': self.diet_restrictions,
            'care_time_flexibility': self.care_time_flexibility,
            'massage_pressure_preference': self.massage_pressure_preference,
            'environment_requirements': self.environment_requirements,
            'short_term_beauty_goal': self.short_term_beauty_goal,
            'long_term_beauty_goal': self.long_term_beauty_goal,
            'short_term_health_goal': self.short_term_health_goal,
            'long_term_health_goal': self.long_term_health_goal,
            'medical_cosmetic_history': self.medical_cosmetic_history,
            'wellness_service_history': self.wellness_service_history,
            'major_disease_history': self.major_disease_history,
            'allergies': self.allergies,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class Consumption(db.Model):
    """消费行为记录表"""
    __tablename__ = 'consumptions'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.String(32), db.ForeignKey('customers.id'), nullable=False)
    
    date = db.Column(db.DateTime, nullable=False)  # 消费时间
    project_name = db.Column(db.String(128), nullable=False)  # 项目名称
    amount = db.Column(db.Float, nullable=False)  # 消费金额
    payment_method = db.Column(db.String(32), nullable=True)  # 支付方式
    total_sessions = db.Column(db.Integer, nullable=True)  # 总次数
    completion_date = db.Column(db.DateTime, nullable=True)  # 耗卡完成时间
    satisfaction = db.Column(db.String(32), nullable=True)  # 项目满意度
    
    # 记录时间戳
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S') if self.date else None,
            'project_name': self.project_name,
            'amount': self.amount,
            'payment_method': self.payment_method,
            'total_sessions': self.total_sessions,
            'completion_date': self.completion_date.strftime('%Y-%m-%d %H:%M:%S') if self.completion_date else None,
            'satisfaction': self.satisfaction,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class Service(db.Model):
    """服务消耗记录表"""
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.String(32), db.ForeignKey('customers.id'), nullable=False)
    
    service_date = db.Column(db.DateTime, nullable=False)  # 到店时间
    departure_time = db.Column(db.DateTime, nullable=True)  # 离店时间
    total_amount = db.Column(db.Float, nullable=True)  # 总耗卡金额
    satisfaction = db.Column(db.String(32), nullable=True)  # 服务满意度
    service_items = db.Column(db.String(256), nullable=True)  # 消耗项目
    item_content = db.Column(db.Text, nullable=True)  # 项目内容
    beautician = db.Column(db.String(64), nullable=True)  # 操作美容师
    service_amount = db.Column(db.Float, nullable=True)  # 耗卡金额
    is_specified = db.Column(db.Boolean, default=False)  # 是否指定
    
    # 记录时间戳
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'service_date': self.service_date.strftime('%Y-%m-%d %H:%M:%S') if self.service_date else None,
            'departure_time': self.departure_time.strftime('%Y-%m-%d %H:%M:%S') if self.departure_time else None,
            'total_amount': self.total_amount,
            'satisfaction': self.satisfaction,
            'service_items': self.service_items,
            'item_content': self.item_content,
            'beautician': self.beautician,
            'service_amount': self.service_amount,
            'is_specified': self.is_specified,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class Communication(db.Model):
    """客户沟通记录表"""
    __tablename__ = 'communications'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.String(32), db.ForeignKey('customers.id'), nullable=False)
    
    comm_time = db.Column(db.DateTime, nullable=False)  # 沟通时间
    comm_location = db.Column(db.String(128), nullable=True)  # 沟通地点
    comm_content = db.Column(db.Text, nullable=True)  # 沟通主要内容
    
    # 记录时间戳
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'comm_time': self.comm_time.strftime('%Y-%m-%d %H:%M:%S') if self.comm_time else None,
            'comm_location': self.comm_location,
            'comm_content': self.comm_content,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
