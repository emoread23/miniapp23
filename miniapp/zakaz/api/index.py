from flask import Flask, render_template, jsonify, request, session
from database import User, Transaction, UserUpgrade, UserAchievement, ReferralBonus
from config import BOT_TOKEN, LEVELS, UPGRADES, ACHIEVEMENTS
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import logging
import os
# from dotenv import load_dotenv # Закомментируем импорт

# load_dotenv() # Закомментируем вызов

# Создаем Flask приложение
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key')

logger = logging.getLogger(__name__)

def get_user_data(db: Session, telegram_id: int) -> dict:
    """
    Получает данные пользователя для веб-интерфейса
    """
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        return None
    
    # Получаем уровень пользователя
    level = LEVELS[user.level]
    
    # Получаем апгрейды пользователя
    upgrades = db.query(UserUpgrade).filter(UserUpgrade.user_id == user.id).all()
    user_upgrades = []
    for upgrade in upgrades:
        upgrade_info = UPGRADES[upgrade.upgrade_id]
        user_upgrades.append({
            'name': upgrade_info['name'],
            'description': upgrade_info['description'],
            'level': upgrade.level,
            'max_level': upgrade_info['max_level'],
            'effect': upgrade_info['effect']
        })
    
    # Получаем достижения пользователя
    achievements = db.query(UserAchievement).filter(UserAchievement.user_id == user.id).all()
    user_achievements = []
    for achievement in achievements:
        achievement_info = ACHIEVEMENTS[achievement.achievement_id]
        user_achievements.append({
            'name': achievement_info['name'],
            'description': achievement_info['description'],
            'image_url': achievement_info['image_url'],
            'received_at': achievement.received_at
        })
    
    # Получаем последние транзакции
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user.id
    ).order_by(desc(Transaction.created_at)).limit(10).all()
    
    # Получаем рефералов
    referrals = db.query(User).filter(User.referred_by == user.id).all()
    referral_stats = {
        'total': len(referrals),
        'required': level.required_referrals,
        'bonuses': db.query(ReferralBonus)
            .filter(ReferralBonus.referrer_id == user.id)
            .with_entities(func.sum(ReferralBonus.amount))
            .scalar() or 0
    }
    
    return {
        'user': {
            'username': user.username,
            'balance': user.balance,
            'total_deposit': user.total_deposit,
            'total_withdraw': user.total_withdraw,
            'created_at': user.created_at
        },
        'level': {
            'name': level.name,
            'monthly_income': level.monthly_income,
            'required_referrals': level.required_referrals,
            'referral_bonus': level.referral_bonus
        },
        'upgrades': user_upgrades,
        'achievements': user_achievements,
        'transactions': [{
            'type': t.type,
            'amount': t.amount,
            'status': t.status,
            'created_at': t.created_at
        } for t in transactions],
        'referrals': referral_stats
    }

@app.route('/')
def index():
    """
    Главная страница мини-приложения
    """
    logger.info("Запрос к корневому пути '/' получен.")
    return render_template('index.html')

@app.route('/api/user/<int:telegram_id>')
def get_user(telegram_id):
    """
    API для получения данных пользователя
    """
    db = next(get_db())
    user_data = get_user_data(db, telegram_id)
    
    if not user_data:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user_data)

@app.route('/api/upgrades')
def get_available_upgrades():
    """
    API для получения списка доступных апгрейдов
    """
    return jsonify(UPGRADES)

@app.route('/api/achievements')
def get_available_achievements():
    """
    API для получения списка доступных достижений
    """
    return jsonify(ACHIEVEMENTS)

@app.route('/api/levels')
def get_levels():
    """
    API для получения информации об уровнях
    """
    return jsonify([{
        'name': level.name,
        'min_deposit': level.min_deposit,
        'monthly_income': level.monthly_income,
        'required_referrals': level.required_referrals,
        'referral_bonus': level.referral_bonus
    } for level in LEVELS])

# Экспортируем app для Vercel
app = app 
