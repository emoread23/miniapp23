from webapp import app
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)

class Level(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    level_number = db.Column(db.Integer, unique=True, nullable=False)
    required_xp = db.Column(db.Integer, nullable=False)
    reward = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f'<Level {self.level_number}>'

def init_levels():
    with app.app_context():
        # Очищаем существующие уровни
        Level.query.delete()
        
        # Создаем уровни
        levels = [
            Level(level_number=1, required_xp=0, reward=0.1, description="Начальный уровень"),
            Level(level_number=2, required_xp=100, reward=0.2, description="Уровень 2"),
            Level(level_number=3, required_xp=300, reward=0.3, description="Уровень 3"),
            Level(level_number=4, required_xp=600, reward=0.4, description="Уровень 4"),
            Level(level_number=5, required_xp=1000, reward=0.5, description="Уровень 5"),
            Level(level_number=6, required_xp=1500, reward=0.6, description="Уровень 6"),
            Level(level_number=7, required_xp=2100, reward=0.7, description="Уровень 7"),
            Level(level_number=8, required_xp=2800, reward=0.8, description="Уровень 8"),
            Level(level_number=9, required_xp=3600, reward=0.9, description="Уровень 9"),
            Level(level_number=10, required_xp=4500, reward=1.0, description="Уровень 10"),
            Level(level_number=11, required_xp=5500, reward=1.2, description="Уровень 11"),
            Level(level_number=12, required_xp=6600, reward=1.4, description="Уровень 12"),
            Level(level_number=13, required_xp=7800, reward=1.6, description="Уровень 13"),
            Level(level_number=14, required_xp=9100, reward=1.8, description="Уровень 14"),
            Level(level_number=15, required_xp=10500, reward=2.0, description="Уровень 15"),
            Level(level_number=16, required_xp=12000, reward=2.3, description="Уровень 16"),
            Level(level_number=17, required_xp=13600, reward=2.6, description="Уровень 17"),
            Level(level_number=18, required_xp=15300, reward=2.9, description="Уровень 18"),
            Level(level_number=19, required_xp=17100, reward=3.2, description="Уровень 19"),
            Level(level_number=20, required_xp=19000, reward=3.5, description="Уровень 20")
        ]
        
        # Добавляем уровни в базу данных
        for level in levels:
            db.session.add(level)
        
        db.session.commit()
        print("Уровни успешно инициализированы!")

if __name__ == '__main__':
    init_levels() 