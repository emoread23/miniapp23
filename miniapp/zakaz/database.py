from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
# from dotenv import load_dotenv # Закомментируем импорт

# Загрузка переменных окружения
# load_dotenv() # Закомментируем вызов

# Создание базового класса для моделей
Base = declarative_base()

# Модель пользователя
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String)
    level = Column(String, default='Новичок')
    balance = Column(Float, default=0.0)
    total_deposit = Column(Float, default=0.0)
    total_withdraw = Column(Float, default=0.0)
    referral_code = Column(String, unique=True)
    referral_count = Column(Integer, default=0)
    referral_earnings = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_income = Column(DateTime, default=datetime.utcnow)
    next_income = Column(DateTime, default=datetime.utcnow)

    # Отношения
    transactions = relationship('Transaction', back_populates='user')
    # Отношение для бонусов, которые пользователь получил
    received_bonuses = relationship('ReferralBonus', 
                                    back_populates='user',
                                    foreign_keys='ReferralBonus.user_id')
    # Отношение для бонусов, которые пользователь дал (как реферер)
    given_bonuses = relationship('ReferralBonus',
                                 back_populates='referrer',
                                 foreign_keys='ReferralBonus.referrer_id')
    upgrades = relationship('UserUpgrade', back_populates='user')
    achievements = relationship('UserAchievement', back_populates='user')

    def __repr__(self):
        return f"<User {self.username}>"

# Модель транзакции
class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    type = Column(String)  # deposit, withdraw, income, bonus
    amount = Column(Float)
    status = Column(String)  # pending, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    wallet_address = Column(String)
    tx_hash = Column(String)

    # Отношения
    user = relationship('User', back_populates='transactions')

    def __repr__(self):
        return f"<Transaction {self.type} {self.amount}>"

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

# Инициализация базы данных
def init_db():
    engine = create_engine(os.getenv('DATABASE_URL'))
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()

# Получение сессии базы данных
def get_db():
    db = init_db()
    try:
        yield db
    finally:
        db.close()

# Функции для работы с пользователями
def get_user_by_telegram_id(db, telegram_id):
    return db.query(User).filter(User.telegram_id == telegram_id).first()

def get_user_by_referral_code(db, referral_code):
    return db.query(User).filter(User.referral_code == referral_code).first()

def create_user(db, telegram_id, username, referral_code):
    user = User(
        telegram_id=telegram_id,
        username=username,
        referral_code=referral_code
    )
    db.add(user)
    db.commit()
    return user

def update_user_level(db, user, new_level):
    user.level = new_level
    db.commit()
    return user

def update_user_balance(db, user, amount):
    user.balance += amount
    db.commit()
    return user

# Функции для работы с транзакциями
def create_transaction(db, user_id, type, amount, wallet_address=None):
    transaction = Transaction(
        user_id=user_id,
        type=type,
        amount=amount,
        status='pending',
        wallet_address=wallet_address
    )
    db.add(transaction)
    db.commit()
    return transaction

def update_transaction_status(db, transaction, status, tx_hash=None):
    transaction.status = status
    if tx_hash:
        transaction.tx_hash = tx_hash
    db.commit()
    return transaction

def get_pending_transactions(db):
    return db.query(Transaction).filter(Transaction.status == 'pending').all()

# Функции для работы с рефералами
def add_referral_bonus(db, user_id, referrer_id, amount):
    bonus = ReferralBonus(
        user_id=user_id,
        referrer_id=referrer_id,
        amount=amount
    )
    db.add(bonus)
    db.commit()
    return bonus

def get_user_referrals(db, user_id):
    return db.query(User).filter(User.referrer_id == user_id).all()

# Функции для работы с апгрейдами
def add_user_upgrade(db, user_id, upgrade_id, level=1, expires_at=None):
    upgrade = UserUpgrade(
        user_id=user_id,
        upgrade_id=upgrade_id,
        level=level,
        expires_at=expires_at
    )
    db.add(upgrade)
    db.commit()
    return upgrade

def get_user_upgrades(db, user_id):
    return db.query(UserUpgrade).filter(UserUpgrade.user_id == user_id).all()

# Функции для работы с достижениями
def add_user_achievement(db, user_id, achievement_id):
    achievement = UserAchievement(
        user_id=user_id,
        achievement_id=achievement_id
    )
    db.add(achievement)
    db.commit()
    return achievement

def get_user_achievements(db, user_id):
    return db.query(UserAchievement).filter(UserAchievement.user_id == user_id).all()

# Функции для статистики
def get_user_stats(db, user_id):
    """Получение статистики пользователя"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    
    # TODO: Пересчитать total_deposit, total_withdraw, referral_count, referral_earnings
    # на основе транзакций и реферальных бонусов
    total_deposits = sum(t.amount for t in user.transactions if t.type == 'deposit' and t.status == 'completed')
    total_withdraws = sum(t.amount for t in user.transactions if t.type == 'withdraw' and t.status == 'completed')
    referral_count = db.query(User).filter(User.referrer_id == user_id).count()
    referral_earnings = sum(b.amount for b in user.received_bonuses) # Используем новое отношение

    # Определяем текущий уровень и следующий
    current_level = user.level
    next_level = None
    referrals_to_next_level = 0
    monthly_income_percent = 0

    for i, level in enumerate(LEVELS):
        if level.name == current_level:
            monthly_income_percent = level.monthly_income
            if i < len(LEVELS) - 1:
                next_level_info = LEVELS[i+1]
                next_level = next_level_info.name
                referrals_to_next_level = max(0, next_level_info.required_referrals - referral_count)
            break

    # Рассчитываем ежемесячный доход
    monthly_income = (user.balance * monthly_income_percent) / 100

    return {
        'user_level': user.level,
        'user_balance': user.balance,
        'user_deposits': total_deposits,
        'user_withdraws': total_withdraws,
        'user_referrals': referral_count,
        'user_referral_bonuses': referral_earnings,
        'monthly_income': monthly_income,
        'next_level': next_level,
        'referrals_to_next_level': referrals_to_next_level,
    }

def get_top_users(db, limit=10, by='balance'):
    if by == 'balance':
        return db.query(User).order_by(User.balance.desc()).limit(limit).all()
    elif by == 'referrals':
        return db.query(User).order_by(User.referral_count.desc()).limit(limit).all()
    return [] 