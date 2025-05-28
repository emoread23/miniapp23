from dataclasses import dataclass
from typing import Dict, List
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
SECRET_KEY = os.getenv('SECRET_KEY', 'fdjwzuiiuhs8d9y128dwd0sqe1')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

@dataclass
class Level:
    name: str
    min_deposit: float
    monthly_income: float
    required_referrals: int
    referral_bonus: float  # Процент от вклада реферала

LEVELS = {
    "Новичок": Level("Новичок", 50, 10, 3, 5),
    "Трейдер": Level("Трейдер", 100, 15, 6, 6),
    "Инвестор": Level("Инвестор", 200, 20, 9, 7),
    "Магнат": Level("Магнат", 500, 25, 12, 8),
    "Император": Level("Император", 1000, 30, 15, 10)
}

REFERRAL_PERCENTS = {
    1: 10,  # Первая линия
    2: 5,   # Вторая линия
    3: 3    # Третья линия
}

# Настройки вывода средств
WITHDRAW_DELAY_MIN = 24  # часов
WITHDRAW_DELAY_MAX = 72  # часов

# Апгрейды в магазине
UPGRADES = [
    {
        "name": "🚀 Ускоренный рост",
        "price": 50,
        "description": "Увеличивает доход на 5% на 7 дней",
        "type": "boost",
        "duration": 7,
        "effect": 5
    },
    {
        "name": "💎 Премиум статус",
        "price": 100,
        "description": "Увеличивает реферальный бонус на 2% навсегда",
        "type": "permanent",
        "effect": 2
    },
    {
        "name": "⚡️ Мгновенный вывод",
        "price": 200,
        "description": "Позволяет выводить средства без задержки (3 раза)",
        "type": "consumable",
        "uses": 3
    }
]

# Достижения
ACHIEVEMENTS = [
    {
        "name": "🎯 Первые шаги",
        "description": "Сделайте первый депозит",
        "reward": 5
    },
    {
        "name": "👥 Команда",
        "description": "Пригласите 3 друзей",
        "reward": 10
    },
    {
        "name": "💎 Инвестор",
        "description": "Достигните уровня Инвестор",
        "reward": 20
    }
]

# Текст приветствия
WELCOME_MESSAGE = """
👋 Добро пожаловать в Crypto Empire Quest!

🎮 Это игра, где вы можете:
• Строить свою крипто-империю
• Зарабатывать пассивный доход
• Приглашать друзей и получать бонусы
• Покупать апгрейды и улучшения

💰 Начните с минимального депозита в 50 USDT и начните свой путь к успеху!

📱 Используйте меню ниже для навигации.
"""

# Текст помощи
HELP_MESSAGE = """
📚 Список доступных команд:

/start - Начать игру
/help - Показать это сообщение
/balance - Проверить баланс
/deposit - Пополнить баланс
/withdraw - Вывести средства
/referral - Реферальная программа
/shop - Магазин апгрейдов
/top - Топ игроков
/settings - Настройки

💡 Используйте кнопки меню для удобной навигации.
"""

# Сообщения для разных действий
MESSAGES = {
    'deposit': {
        'start': "💎 Введите сумму для пополнения (минимум 50 USDT):",
        'invalid': "❌ Неверная сумма. Минимальный депозит: 50 USDT",
        'success': "✅ Депозит успешно создан! Ожидайте подтверждения.",
    },
    'withdraw': {
        'start': "💰 Введите сумму для вывода:",
        'invalid': "❌ Неверная сумма или недостаточно средств",
        'success': "✅ Заявка на вывод создана! Ожидайте обработки (24-72 часа).",
    },
    'referral': {
        'link': "🔗 Ваша реферальная ссылка:",
        'stats': "📊 Статистика рефералов:",
    },
    'shop': {
        'welcome': "🏪 Добро пожаловать в магазин!",
        'not_enough': "❌ Недостаточно средств",
        'success': "✅ Покупка успешно совершена!",
    },
    'achievement': {
        'new': "🏆 Получено новое достижение: {name}",
        'reward': "🎁 Награда: {reward}",
    },
    'deposit_confirmed': '✅ Ваш депозит подтвержден! Баланс пополнен на {amount} USDT',
    'withdraw_confirmed': '✅ Ваш вывод подтвержден! {amount} USDT отправлены на ваш кошелек',
    'withdraw_cancelled': '❌ Вывод отменен. Средства возвращены на баланс',
    'referral_bonus': '🎁 Вы получили реферальный бонус {amount} USDT от {username}',
    'level_up': '🎉 Поздравляем! Вы достигли уровня {level}!',
    'income_received': '💰 Получен доход: {amount} USDT'
}

# Настройки веб-приложения
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://your-webapp-url.com')

# Настройки базы данных
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///crypto_empire.db')

# Настройки администратора
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]

# Настройки безопасности
MIN_WITHDRAW = 10  # Минимальная сумма вывода
MAX_WITHDRAW = 10000  # Максимальная сумма вывода
DAILY_WITHDRAW_LIMIT = 50000  # Дневной лимит на вывод

# Настройки уведомлений
NOTIFICATION_INTERVAL = 3600  # Интервал проверки уведомлений (в секундах)
INCOME_INTERVAL = 86400  # Интервал начисления дохода (в секундах) 