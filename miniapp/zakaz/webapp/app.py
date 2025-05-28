from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from webapp.database import get_session, get_user_by_telegram_id, get_user_stats, User, Transaction, ReferralBonus
from webapp.config import LEVELS, UPGRADES, ACHIEVEMENTS, MIN_WITHDRAW, TELEGRAM_BOT_TOKEN
from transactions import create_deposit, create_withdraw, confirm_transaction
from shop import purchase_upgrade
from referral import process_referral_bonus
import os
from dotenv import load_dotenv
import logging
import hashlib
import hmac
import time
from functools import wraps
import json
from datetime import datetime
import uuid

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key')

def verify_telegram_data(data):
    """Проверка данных от Telegram"""
    received_hash = data.get('hash', '')
    auth_date = data.get('auth_date', '')
    
    # Проверка времени авторизации (не более 24 часов)
    if int(time.time()) - int(auth_date) > 86400:
        return False
    
    # Формирование строки для проверки
    check_string = '\n'.join(f'{k}={v}' for k, v in sorted(data.items()) if k != 'hash')
    
    # Создание секретного ключа
    secret_key = hashlib.sha256(TELEGRAM_BOT_TOKEN.encode()).digest()
    
    # Вычисление хеша
    hmac_obj = hmac.new(secret_key, check_string.encode(), hashlib.sha256)
    calculated_hash = hmac_obj.hexdigest()
    
    return calculated_hash == received_hash

def login_required(f):
    """Декоратор для проверки авторизации"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'telegram_id' not in session:
            # Возвращаем JSON ошибку для API маршрутов
            if request.path.startswith('/api/'):
                 return jsonify({'error': 'Требуется авторизация'}), 401
            # Перенаправляем на главную для обычных маршрутов
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Главная страница или страница авторизации"""
    if 'telegram_id' in session:
        # Если пользователь авторизован, показываем основное приложение
        return render_template('index.html')
    else:
        # Если не авторизован, показываем заглушку или форму авторизации
        # Пока что просто покажем сообщение об ошибке, позже можно сделать страницу авторизации
        return "<h1>Требуется авторизация через Telegram Mini App</h1><p>Пожалуйста, откройте приложение через Telegram.</p>"

@app.route('/api/auth/telegram', methods=['POST'])
def telegram_auth():
    """Аутентификация через Telegram"""
    try:
        data = request.get_json()
        
        if not verify_telegram_data(data):
            return jsonify({'error': 'Неверные данные авторизации'}), 401
        
        telegram_id = data.get('id')
        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        
        db = get_session()
        user = get_user_by_telegram_id(db, telegram_id)
        
        if not user:
            # Создание нового пользователя
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                level='Новичок',
                balance=0,
                invested_amount=0,
                referral_code=str(uuid.uuid4())[:8]
            )
            db.add(user)
            db.commit()

        # Сохранение данных в сессии
        session['telegram_id'] = user.telegram_id
        
        return jsonify({
            'success': True,
            'data': {
                'telegram_id': user.telegram_id,
                'username': user.username,
                'level': user.level,
                'balance': user.balance
            }
        })
    except Exception as e:
        logger.error(f"Ошибка при авторизации: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/api/logout')
def logout():
    """Выход из системы"""
    session.clear()
    return jsonify({'success': True})

@app.route('/api/user/me')
@login_required
def get_current_user():
    """Получение данных текущего пользователя"""
    try:
        db = get_session()
        user = get_user_by_telegram_id(db, session['telegram_id'])
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404

        stats = get_user_stats(db, user.id)
        return jsonify({
            'success': True,
            'data': {
                'telegram_id': user.telegram_id,
                'username': user.username,
                'level': user.level,
                'balance': user.balance,
                'invested_amount': user.invested_amount,
                'referral_code': user.referral_code,
                'created_at': user.created_at.isoformat(),
                'stats': stats
            }
        })
    except Exception as e:
        logger.error(f"Ошибка при получении данных пользователя: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'})

@app.route('/api/levels')
@login_required
def get_levels():
    """Получение списка уровней"""
    try:
        return jsonify({
            'success': True,
            'data': LEVELS
        })
    except Exception as e:
        logger.error(f"Ошибка при получении списка уровней: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/api/upgrades')
@login_required
def get_upgrades():
    """Получение списка апгрейдов"""
    try:
        return jsonify({
            'success': True,
            'data': UPGRADES
        })
    except Exception as e:
        logger.error(f"Ошибка при получении списка апгрейдов: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/api/achievements')
@login_required
def get_achievements():
    """Получение списка достижений"""
    try:
        return jsonify({
            'success': True,
            'data': ACHIEVEMENTS
        })
    except Exception as e:
        logger.error(f"Ошибка при получении списка достижений: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/api/invest', methods=['POST'])
@login_required
def invest():
    """Обработка инвестиции"""
    try:
        data = request.get_json()
        amount = data.get('amount')

        if not amount:
            return jsonify({'error': 'Отсутствует сумма инвестиции'}), 400

        if amount < LEVELS['Новичок']['minDeposit']:
            return jsonify({'error': f'Минимальная сумма инвестиции: {LEVELS["Новичок"]["minDeposit"]} USDT'}), 400

        db = get_session()
        user = get_user_by_telegram_id(db, session['telegram_id'])
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404

        # Создаем транзакцию
        transaction = Transaction(
            user_id=user.id,
            amount=amount,
            type='deposit',
            status='pending'
        )
        
        db.add(transaction)
        db.commit()
        
        return jsonify({
            'success': True,
            'transaction_id': transaction.id
        })
    except Exception as e:
        logger.error(f"Ошибка при обработке инвестиции: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/api/withdraw', methods=['POST'])
@login_required
def withdraw():
    """Обработка вывода средств"""
    try:
        data = request.get_json()
        amount = data.get('amount')
        wallet = data.get('wallet')

        if not amount or not wallet:
            return jsonify({'error': 'Отсутствуют обязательные поля'}), 400

        if amount < MIN_WITHDRAW:
            return jsonify({'error': f'Минимальная сумма вывода: {MIN_WITHDRAW} USDT'}), 400

        db = get_session()
        user = get_user_by_telegram_id(db, session['telegram_id'])
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404

        if user.balance < amount:
            return jsonify({'error': 'Недостаточно средств'}), 400

        # Создаем транзакцию
        transaction = Transaction(
            user_id=user.id,
            amount=amount,
            type='withdraw',
            status='pending'
        )
        
        db.add(transaction)
        db.commit()
        
        return jsonify({
            'success': True,
            'transaction_id': transaction.id
        })
    except Exception as e:
        logger.error(f"Ошибка при обработке вывода: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/api/referrals/<int:telegram_id>')
@login_required
def get_referrals(telegram_id):
    """Получение списка рефералов"""
    try:
        db = get_session()
        user = get_user_by_telegram_id(db, telegram_id)
        
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        referrals = []
        for ref in user.referrals:
            referrals.append({
                'id': ref.id,
                'username': ref.username,
                'level': ref.level,
                'invested_amount': ref.invested_amount,
                'created_at': ref.created_at.isoformat()
            })
        
        return jsonify(referrals)
    except Exception as e:
        logger.error(f"Ошибка при получении списка рефералов: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/api/top')
def get_top_users():
    """Получение топа игроков"""
    try:
        db = get_session()
        users = db.query(User).order_by(User.invested_amount.desc()).limit(10).all()
        
        top_users = []
        for user in users:
            top_users.append({
                'username': user.username,
                'level': user.level,
                'invested_amount': user.invested_amount,
                'referral_count': len(user.referrals)
            })
        
        return jsonify(top_users)
    except Exception as e:
        logger.error(f"Ошибка при получении топа игроков: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

if __name__ == '__main__':
    # Получаем порт из переменной окружения, по умолчанию 5000
    port = int(os.getenv('PORT', 5000))
    # Запускаем Flask-приложение
    app.run(host='0.0.0.0', port=port) 