import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Токен бота Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Минимальная сумма вывода
MIN_WITHDRAW = 1

# Уровни пользователей
LEVELS = {
    'Новичок': {
        'minDeposit': 50,
        'incomePercent': 10,
        'referralsNeeded': 3
    },
    'Трейдер': {
        'minDeposit': 100,
        'incomePercent': 15,
        'referralsNeeded': 6
    },
    'Инвестор': {
        'minDeposit': 200,
        'incomePercent': 20,
        'referralsNeeded': 9
    },
    'Магнат': {
        'minDeposit': 500,
        'incomePercent': 25,
        'referralsNeeded': 12
    },
    'Император': {
        'minDeposit': 1000,
        'incomePercent': 30,
        'referralsNeeded': 15
    }
}

# Улучшения
UPGRADES = [
    {
        'id': 'income_boost_1',
        'name': 'Ускорение дохода I',
        'description': 'Увеличивает доход на 5%',
        'price': 100,
        'bonus': 5
    },
    {
        'id': 'income_boost_2',
        'name': 'Ускорение дохода II',
        'description': 'Увеличивает доход на 10%',
        'price': 250,
        'bonus': 10
    },
    {
        'id': 'referral_boost_1',
        'name': 'Реферальный бонус I',
        'description': 'Увеличивает реферальный бонус на 2%',
        'price': 150,
        'bonus': 2
    }
]

# Достижения
ACHIEVEMENTS = [
    {
        'id': 'first_investment',
        'name': 'Первая инвестиция',
        'description': 'Сделайте первую инвестицию',
        'icon': 'fa-coins'
    },
    {
        'id': 'first_referral',
        'name': 'Первый реферал',
        'description': 'Пригласите первого реферала',
        'icon': 'fa-user-plus'
    },
    {
        'id': 'level_up',
        'name': 'Повышение уровня',
        'description': 'Достигните нового уровня',
        'icon': 'fa-level-up-alt'
    }
] 