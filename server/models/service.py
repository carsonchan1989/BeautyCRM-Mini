from datetime import datetime
from . import db

class Service(db.Model):
    """项目信息模型"""
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, comment='项目名称')
    category = db.Column(db.String(50), nullable=False, comment='项目类别')
    sub_category = db.Column(db.String(50), comment='子类别')
    treatment_method = db.Column(db.String(100), comment='护理手法')
    description = db.Column(db.Text, comment='项目描述')
    price = db.Column(db.Float, comment='参考价格')
    duration = db.Column(db.Integer, comment='护理时长(分钟)')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'sub_category': self.sub_category,
            'treatment_method': self.treatment_method,
            'description': self.description,
            'price': self.price,
            'duration': self.duration,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }