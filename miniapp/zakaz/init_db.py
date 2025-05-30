from webapp import app, db
from flask_sqlalchemy import SQLAlchemy
from init_levels import init_levels

db = SQLAlchemy(app)

def init_database():
    with app.app_context():
        # Создаем все таблицы
        db.create_all()
        print("База данных успешно инициализирована!")
        
        # Инициализируем уровни
        init_levels()
        print("Уровни инициализированы успешно!")

if __name__ == '__main__':
    init_database() 