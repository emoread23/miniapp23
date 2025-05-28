from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Создание базового класса для моделей
Base = declarative_base()

# Модель пользователя
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    level = Column(String, default='Новичок')
    balance = Column(Float, default=0.0)
    invested_amount = Column(Float, default=0.0)
    total_deposit = Column(Float, default=0.0)
    total_withdraw = Column(Float, default=0.0)
    referral_code = Column(String, unique=True)
    referred_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    referral_count = Column(Integer, default=0)
    referral_earnings = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_income = Column(DateTime, default=datetime.utcnow)
    next_income = Column(DateTime, default=datetime.utcnow)

    # Отношения
    referrals = relationship('User', backref='referrer', remote_side=[id])
    transactions = relationship('Transaction', back_populates='user')
    received_bonuses = relationship('ReferralBonus', 
                                  back_populates='user',
                                  foreign_keys='ReferralBonus.user_id')
    given_bonuses = relationship('ReferralBonus',
                               back_populates='referrer',
                               foreign_keys='ReferralBonus.referrer_id')
    upgrades = relationship('UserUpgrade', back_populates='user')
    achievements = relationship('UserAchievement', back_populates='user')

# Модель транзакции
class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float)
    type = Column(String)  # 'deposit' или 'withdraw'
    status = Column(String, default='pending')  # 'pending', 'completed', 'cancelled'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    user = relationship('User', back_populates='transactions')

# Модель реферального бонуса
class ReferralBonus(Base):
    __tablename__ = 'referral_bonuses'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    referrer_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    user = relationship('User', back_populates='received_bonuses', foreign_keys=[user_id])
    referrer = relationship('User', back_populates='given_bonuses', foreign_keys=[referrer_id])

    def __repr__(self):
        return f"<ReferralBonus {self.amount}>"

# Модель апгрейда пользователя
class UserUpgrade(Base):
    __tablename__ = 'user_upgrades'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    upgrade_id = Column(String)
    level = Column(Integer, default=1)
    purchased_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

    # Отношения
    user = relationship('User', back_populates='upgrades')

    def __repr__(self):
        return f"<UserUpgrade {self.upgrade_id}>"

# Модель достижения пользователя
class UserAchievement(Base):
    __tablename__ = 'user_achievements'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    achievement_id = Column(String)
    completed_at = Column(DateTime, default=datetime.utcnow)
    reward_claimed = Column(Boolean, default=False)

    # Отношения
    user = relationship('User', back_populates='achievements')

    def __repr__(self):
        return f"<UserAchievement {self.achievement_id}>"

# Создание подключения к базе данных
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///crypto_empire.db')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Создание таблиц
def create_tables():
    Base.metadata.create_all(bind=engine)

# Получение сессии базы данных
def get_session():
    """Получение сессии базы данных"""
    db = Session()
    try:
        yield db
    finally:
        db.close()

# Получение пользователя по Telegram ID
def get_user_by_telegram_id(db, telegram_id):
    """Получение пользователя по Telegram ID"""
    return db.query(User).filter(User.telegram_id == telegram_id).first()

# Получение статистики пользователя
def get_user_stats(db, user_id):
    """Получение статистики пользователя"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    return {
        'total_deposits': sum(t.amount for t in user.transactions if t.type == 'deposit' and t.status == 'completed'),
        'total_withdraws': sum(t.amount for t in user.transactions if t.type == 'withdraw' and t.status == 'completed'),
        'referral_count': len(user.referrals),
        'referral_earnings': sum(b.amount for b in user.given_bonuses)
    }

# Создание реферального кода
def generate_referral_code():
    import random
    import string
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return code

# Инициализация базы данных
def init_db():
    """Инициализация базы данных"""
    create_tables()
    db_generator = get_session()
    db = next(db_generator)
    
    # Проверка наличия тестового пользователя
    test_user = get_user_by_telegram_id(db, 123456)
    if not test_user:
        test_user = User(
            telegram_id=123456,
            username='test_user',
            level='Новичок',
            balance=1000.0,
            invested_amount=1000.0,
            referral_code=generate_referral_code()
        )
        db.add(test_user)
        db.commit()
    
    # Закрытие сессии после использования в init_db, если она не управляется yield
    # Если get_session использует yield, то next() уже получил первую сессию,
    # и ее нужно закрыть вручную или убедиться, что yield сработает до конца.
    # В данном случае, т.к. мы берем только одну сессию и не итерируемся,
    # нужно явное закрытие или изменение логики init_db.
    # Проще всего изменить init_db, чтобы она просто создавала таблицы и добавляла тестового юзера без использования get_session как генератора.
    # Вернем get_session к простому возврату сессии для init_db.
    # Но для main.py нужен генератор. Это две разные потребности.
    # Лучший подход: init_db не использует get_session как генератор.
    # init_db просто создает таблицы и добавляет пользователя напрямую.
    # Вернем init_db к более простому виду, который не зависит от get_session как генератора.
    
# Инициализация базы данных (пересмотренная для init_db.py)
def init_db_standalone():
    """Инициализация базы данных без использования генератора get_session"""
    create_tables()
    engine = create_engine(os.getenv('DATABASE_URL', 'sqlite:///crypto_empire.db'))
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # Проверка наличия тестового пользователя
    test_user = db.query(User).filter(User.telegram_id == 123456).first()
    if not test_user:
        test_user = User(
            telegram_id=123456,
            username='test_user',
            level='Новичок',
            balance=1000.0,
            invested_amount=1000.0,
            referral_code=generate_referral_code()
        )
        db.add(test_user)
        db.commit()
    
    db.close()

# Обновим вызов в if __name__ == '__main__':
if __name__ == '__main__':
    init_db_standalone() 