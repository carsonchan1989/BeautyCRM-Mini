"""
更新服务记录表的唯一性约束，防止重复记录
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db
from sqlalchemy import text

def update_service_constraint():
    """更新服务记录表的唯一性约束"""
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URI', 'sqlite:///beauty_crm.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )
    db.init_app(app)
    
    with app.app_context():
        try:
            # 先删除旧约束
            db.session.execute(text("DROP INDEX IF EXISTS uix_service_complete_record"))
            
            # 添加新约束
            db.session.execute(text("""
                CREATE UNIQUE INDEX uix_service_record 
                ON services (customer_id, service_date, operator, total_amount)
            """))
            
            db.session.commit()
            print("成功更新服务记录表唯一性约束")
        except Exception as e:
            db.session.rollback()
            print(f"更新唯一性约束失败: {str(e)}")

if __name__ == "__main__":
    update_service_constraint()