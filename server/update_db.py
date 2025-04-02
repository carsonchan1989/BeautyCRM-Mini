"""
更新数据库表结构
"""
from app import create_app
from models import db

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
        print("数据库表已成功更新")