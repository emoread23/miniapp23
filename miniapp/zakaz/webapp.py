from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc, func
import requests

app = Flask(__name__, template_folder='api/templates')

# Конфигурация базы данных
basedir = os.path.abspath(os.path.dirname(__file__))
# Используем переменную окружения DATABASE_URL, если она есть, иначе используем SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'crypto_empire.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_timeout': 30,
    'pool_recycle': 1800,
}

db = SQLAlchemy(app)

# Модели данных
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=True)
    level = db.Column(db.Integer, default=1)
    xp = db.Column(db.Integer, default=0)
    balance = db.Column(db.Float, default=0.0)
    referrer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    referred = db.relationship('User', backref=db.backref('referrer', remote_side=[id]))
    last_daily_bonus = db.Column(db.DateTime, default=datetime.utcnow)
    total_earned = db.Column(db.Float, default=0.0)
    total_withdrawn = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'

class Level(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    level_number = db.Column(db.Integer, unique=True, nullable=False)
    required_xp = db.Column(db.Integer, nullable=False)
    reward = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f'<Level {self.level_number}>'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'earn', 'withdraw', 'referral_bonus'
    status = db.Column(db.String(20), default='pending')  # 'pending', 'completed', 'failed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Transaction {self.id}>'

# Константы игры
CLICK_XP = 1
CLICK_REWARD = 0.01  # USDT
REFERRAL_BONUS_PERCENT = 5  # 5% от заработка реферала
DAILY_BONUS = 0.1  # USDT
MIN_WITHDRAW = 1.0  # USDT

CRYPTOBOT_TOKEN = "370599:AAebN2XL0BqD5Sw9TlUwrUDCOrSjTmEdV4j"
CRYPTOBOT_API = "https://pay.crypt.bot/api"

# Вспомогательные функции
def calculate_level_reward(level):
    return level * 0.1  # Награда растет с уровнем

def process_level_up(user):
    next_level = Level.query.filter(Level.level_number > user.level).order_by(Level.level_number).first()
    if next_level and user.xp >= next_level.required_xp:
        user.level = next_level.level_number
        reward = calculate_level_reward(next_level.level_number)
        user.balance += reward
        user.total_earned += reward
        return True, reward
    return False, 0

def process_referral_bonus(referrer, amount):
    if referrer:
        bonus = amount * (REFERRAL_BONUS_PERCENT / 100)
        referrer.balance += bonus
        referrer.total_earned += bonus
        transaction = Transaction(
            user_id=referrer.id,
            amount=bonus,
            type='referral_bonus',
            status='completed',
            completed_at=datetime.utcnow()
        )
        db.session.add(transaction)

# Эндпоинты
@app.route('/')
def index():
    user_id = request.args.get('user_id')
    user = None
    if user_id:
        try:
            user = User.query.filter_by(telegram_id=int(user_id)).first()
        except ValueError:
            user = None
    return render_template(
        'index.html',
        username=user.username if user else None,
        user_id=user.telegram_id if user else None
    )

@app.route('/api/user/<int:telegram_id>')
def get_user(telegram_id):
    user = User.query.filter_by(telegram_id=telegram_id).first_or_404()
    
    # Получаем уровень пользователя (нужно адаптировать под ваши модели Level)
    level = Level.query.filter_by(level_number=user.level).first()
    next_level = Level.query.filter(Level.level_number > user.level).order_by(Level.level_number).first()

    # Получаем апгрейды пользователя (нужно адаптировать)
    # Предполагаем, что у User есть связь с UserUpgrade или как-то еще их можно получить
    user_upgrades = [] # Пока заглушка

    # Получаем достижения пользователя (нужно адаптировать)
    # Предполагаем, что у User есть связь с UserAchievement или как-то еще их можно получить
    user_achievements = [] # Пока заглушка

    # Получаем последние транзакции (нужно адаптировать)
    # Предполагаем, что у User есть связь с Transaction или как-то еще их можно получить
    transactions = [] # Пока заглушка

    # Получаем рефералов (нужно адаптировать)
    referrals_count = User.query.filter_by(referrer_id=user.id).count()
    referral_bonuses = Transaction.query.filter_by(type='referral_bonus', user_id=user.id).with_entities(db.func.sum(Transaction.amount)).scalar() or 0
    referral_stats = {
        'total': referrals_count,
        'required': level.required_referrals if level else 0, # Нужно убедиться, что level существует
        'bonuses': referral_bonuses
    }

    return jsonify({
        'user': {
            'username': user.username,
            'balance': user.balance,
            'total_deposit': user.total_earned, # Возможно, total_earned соответствует total_deposit из фронтенда
            'total_withdraw': user.total_withdrawn,
            'created_at': user.created_at
        },
        'level': {
            'name': f'Уровень {user.level}', # Используем номер уровня как имя, если нет поля name в Level
            'monthly_income': level.reward if level else 0, # Используем reward как месячный доход, если нет поля monthly_income в Level
            'required_referrals': level.required_xp if level else 0, # Используем required_xp как required_referrals, если нет такого поля
            'referral_bonus': REFERRAL_BONUS_PERCENT # Используем константу
        },
        'upgrades': user_upgrades,
        'achievements': user_achievements,
        'transactions': transactions,
        'referrals': referral_stats
    })

@app.route('/api/levels')
def get_levels():
    levels = Level.query.order_by(Level.level_number).all()
    return jsonify([{
        'level_number': level.level_number,
        'required_xp': level.required_xp,
        'reward': level.reward,
        'description': level.description
    } for level in levels])

@app.route('/api/action', methods=['POST'])
def perform_action():
    data = request.json
    telegram_id = data.get('telegram_id')
    action_type = data.get('action_type')

    user = User.query.filter_by(telegram_id=telegram_id).first_or_404()
    
    if action_type == 'click':
        # Начисляем опыт и награду за клик
        user.xp += CLICK_XP
        user.balance += CLICK_REWARD
        user.total_earned += CLICK_REWARD
        
        # Проверяем повышение уровня
        leveled_up, level_reward = process_level_up(user)
        
        # Начисляем бонус рефереру
        if user.referrer:
            process_referral_bonus(user.referrer, CLICK_REWARD)
            if leveled_up:
                process_referral_bonus(user.referrer, level_reward)
        
        db.session.commit()
        
        return {
            'success': True,
            'new_xp': user.xp,
            'new_level': user.level,
            'new_balance': user.balance,
            'leveled_up': leveled_up,
            'level_reward': level_reward if leveled_up else 0
        }
    
    return {'success': False, 'message': 'Неизвестное действие'}, 400

@app.route('/api/daily-bonus', methods=['POST'])
def claim_daily_bonus():
    data = request.json
    telegram_id = data.get('telegram_id')
    
    user = User.query.filter_by(telegram_id=telegram_id).first_or_404()
    
    if (datetime.utcnow() - user.last_daily_bonus) <= timedelta(days=1):
        return {'success': False, 'message': 'Бонус уже получен сегодня'}, 400
    
    user.balance += DAILY_BONUS
    user.total_earned += DAILY_BONUS
    user.last_daily_bonus = datetime.utcnow()
    
    # Начисляем бонус рефереру
    if user.referrer:
        process_referral_bonus(user.referrer, DAILY_BONUS)
    
    db.session.commit()
    
    return {
        'success': True,
        'new_balance': user.balance,
        'next_bonus_time': user.last_daily_bonus + timedelta(days=1)
    }

@app.route('/api/withdraw', methods=['POST'])
def withdraw():
    data = request.json
    telegram_id = data.get('telegram_id')
    amount = float(data.get('amount', 0))
    
    user = User.query.filter_by(telegram_id=telegram_id).first_or_404()
    
    if amount < MIN_WITHDRAW:
        return {'success': False, 'message': f'Минимальная сумма вывода {MIN_WITHDRAW} USDT'}, 400
    
    if amount > user.balance:
        return {'success': False, 'message': 'Недостаточно средств'}, 400
    
    # Создаем транзакцию на вывод
    transaction = Transaction(
        user_id=user.id,
        amount=amount,
        type='withdraw',
        status='pending'
    )
    
    user.balance -= amount
    user.total_withdrawn += amount
    
    db.session.add(transaction)
    db.session.commit()
    
    return {
        'success': True,
        'new_balance': user.balance,
        'transaction_id': transaction.id
    }

@app.route('/api/referral-info/<int:telegram_id>')
def get_referral_info(telegram_id):
    user = User.query.filter_by(telegram_id=telegram_id).first_or_404()
    
    # Получаем список рефералов
    referrals = User.query.filter_by(referrer_id=user.id).all()
    
    return {
        'referral_code': user.id,  # Используем ID пользователя как реферальный код
        'referrals_count': len(referrals),
        'referrals': [{
            'username': ref.username,
            'level': ref.level,
            'total_earned': ref.total_earned
        } for ref in referrals]
    }

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    telegram_id = data.get('telegram_id')
    username = data.get('username')
    referral_code = data.get('referral_code')
    
    # Проверяем, не зарегистрирован ли уже пользователь
    if User.query.filter_by(telegram_id=telegram_id).first():
        return {'success': False, 'message': 'Пользователь уже зарегистрирован'}, 400
    
    # Создаем нового пользователя
    user = User(
        telegram_id=telegram_id,
        username=username
    )
    
    # Если указан реферальный код, связываем пользователя с реферером
    if referral_code:
        referrer = User.query.get(referral_code)
        if referrer:
            user.referrer_id = referrer.id
    
    db.session.add(user)
    db.session.commit()
    
    return {
        'success': True,
        'user_id': user.id,
        'level': user.level,
        'balance': user.balance
    }

@app.route('/api/upgrades')
def get_available_upgrades():
    # return jsonify(UPGRADES) # Если UPGRADES будет доступна
    return jsonify([])

@app.route('/api/achievements')
def get_available_achievements():
    # return jsonify(ACHIEVEMENTS) # Если ACHIEVEMENTS будет доступна
    return jsonify([])

@app.route('/api/save_user', methods=['POST'])
def save_user():
    data = request.get_json()
    telegram_id = data.get('telegram_id')
    username = data.get('username')
    if not telegram_id or not username:
        return jsonify({'success': False, 'message': 'Не передан telegram_id или username'}), 400
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if user:
        user.username = username
    else:
        user = User(telegram_id=telegram_id, username=username)
        db.session.add(user)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Пользователь сохранён'})

@app.route('/api/create_invoice', methods=['POST'])
def create_invoice():
    data = request.get_json()
    amount = data.get('amount')
    user_id = data.get('user_id')
    if not amount or not user_id:
        return jsonify({'success': False, 'message': 'Нет суммы или user_id'}), 400

    payload = {
        "asset": "USDT",
        "amount": str(amount),
        "description": "Пополнение баланса через CryptoBot",
        "hidden_message": f"User ID: {user_id}",
        "paid_btn_name": "openBot",
        "paid_btn_url": "https://t.me/CryptoEmpBot"  # можешь заменить на свой бот
    }
    headers = {
        "Crypto-Pay-API-Token": CRYPTOBOT_TOKEN,
        "Content-Type": "application/json"
    }
    resp = requests.post(f"{CRYPTOBOT_API}/createInvoice", json=payload, headers=headers)
    if resp.status_code == 200:
        invoice = resp.json()['result']
        return jsonify({'success': True, 'pay_url': invoice['pay_url']})
    else:
        return jsonify({'success': False, 'message': resp.text}), 500

if __name__ == '__main__':
    # Создаем таблицы в базе данных (только для локального запуска/тестирования)
    # На Vercel миграции базы данных нужно будет выполнять отдельно
    with app.app_context():
        db.create_all()
    app.run(debug=True) 