from flask import Flask, render_template, jsonify, request, session
from database import User, Transaction, UserUpgrade, UserAchievement, ReferralBonus
from config import BOT_TOKEN, LEVELS, UPGRADES, ACHIEVEMENTS
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
import logging
import os
from dotenv import load_dotenv

load_dotenv()

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

def init_webapp():
    """
    Инициализация веб-приложения
    """
    # Создаем директорию для шаблонов, если её нет
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Создаем базовый шаблон
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write("""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crypto Empire Quest</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #1a1a1a;
            color: #ffffff;
        }
        .card {
            background-color: #2d2d2d;
            border: none;
            border-radius: 15px;
            margin-bottom: 20px;
        }
        .card-header {
            background-color: #3d3d3d;
            border-radius: 15px 15px 0 0 !important;
        }
        .btn-primary {
            background-color: #007bff;
            border: none;
        }
        .btn-primary:hover {
            background-color: #0056b3;
        }
        .progress {
            background-color: #3d3d3d;
        }
        .progress-bar {
            background-color: #007bff;
        }
    </style>
</head>
<body>
    <div class="container py-4">
        <div class="row">
            <div class="col-md-4">
                <!-- Профиль пользователя -->
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">👤 Профиль</h5>
                    </div>
                    <div class="card-body">
                        <h4 id="username"></h4>
                        <p>Баланс: <span id="balance"></span> USDT</p>
                        <p>Всего вложено: <span id="total-deposit"></span> USDT</p>
                        <p>Всего выведено: <span id="total-withdraw"></span> USDT</p>
                    </div>
                </div>

                <!-- Уровень -->
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">📊 Уровень</h5>
                    </div>
                    <div class="card-body">
                        <h4 id="level-name"></h4>
                        <p>Доход в месяц: <span id="monthly-income"></span>%</p>
                        <p>Реферальный бонус: <span id="referral-bonus"></span>%</p>
                        <div class="progress">
                            <div id="level-progress" class="progress-bar" role="progressbar"></div>
                        </div>
                        <p class="mt-2">До следующего уровня: <span id="next-level"></span></p>
                    </div>
                </div>
            </div>

            <div class="col-md-8">
                <!-- Апгрейды -->
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">⚡️ Апгрейды</h5>
                    </div>
                    <div class="card-body">
                        <div id="upgrades-list" class="row"></div>
                    </div>
                </div>

                <!-- Достижения -->
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">🏆 Достижения</h5>
                    </div>
                    <div class="card-body">
                        <div id="achievements-list" class="row"></div>
                    </div>
                </div>

                <!-- Транзакции -->
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">📝 Последние транзакции</h5>
                    </div>
                    <div class="card-body">
                        <div id="transactions-list"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Получаем telegram_id из URL
        const urlParams = new URLSearchParams(window.location.search);
        const telegramId = urlParams.get('user_id');

        // Загружаем данные пользователя
        async function loadUserData() {
            const response = await fetch(`/api/user/${telegramId}`);
            const data = await response.json();

            // Заполняем профиль
            document.getElementById('username').textContent = data.user.username;
            document.getElementById('balance').textContent = data.user.balance.toFixed(2);
            document.getElementById('total-deposit').textContent = data.user.total_deposit.toFixed(2);
            document.getElementById('total-withdraw').textContent = data.user.total_withdraw.toFixed(2);

            // Заполняем уровень
            document.getElementById('level-name').textContent = data.level.name;
            document.getElementById('monthly-income').textContent = data.level.monthly_income;
            document.getElementById('referral-bonus').textContent = data.level.referral_bonus;

            const progress = (data.referrals.total / data.level.required_referrals) * 100;
            document.getElementById('level-progress').style.width = `${progress}%`;
            document.getElementById('next-level').textContent = 
                `${data.referrals.total}/${data.level.required_referrals} рефералов`;

            // Заполняем апгрейды
            const upgradesList = document.getElementById('upgrades-list');
            data.upgrades.forEach(upgrade => {
                upgradesList.innerHTML += `
                    <div class="col-md-6 mb-3">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">${upgrade.name}</h5>
                                <p class="card-text">${upgrade.description}</p>
                                <p>Уровень: ${upgrade.level}/${upgrade.max_level}</p>
                            </div>
                        </div>
                    </div>
                `;
            });

            // Заполняем достижения
            const achievementsList = document.getElementById('achievements-list');
            data.achievements.forEach(achievement => {
                achievementsList.innerHTML += `
                    <div class="col-md-4 mb-3">
                        <div class="card">
                            <div class="card-body text-center">
                                <img src="${achievement.image_url}" alt="${achievement.name}" class="img-fluid mb-2">
                                <h5 class="card-title">${achievement.name}</h5>
                                <p class="card-text">${achievement.description}</p>
                            </div>
                        </div>
                    </div>
                `;
            });

            // Заполняем транзакции
            const transactionsList = document.getElementById('transactions-list');
            data.transactions.forEach(transaction => {
                const date = new Date(transaction.created_at).toLocaleString();
                transactionsList.innerHTML += `
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <div>
                            <span class="badge bg-${transaction.type === 'deposit' ? 'success' : 'primary'}">
                                ${transaction.type}
                            </span>
                            ${transaction.amount.toFixed(2)} USDT
                        </div>
                        <div>
                            <span class="badge bg-${transaction.status === 'completed' ? 'success' : 'warning'}">
                                ${transaction.status}
                            </span>
                            ${date}
                        </div>
                    </div>
                `;
            });
        }

        // Загружаем данные при загрузке страницы
        if (telegramId) {
            loadUserData();
        }
    </script>
</body>
</html>
        """)
    
    return app 