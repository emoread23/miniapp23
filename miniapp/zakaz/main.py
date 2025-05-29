import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler
from config import BOT_TOKEN, WELCOME_MESSAGE, HELP_MESSAGE, MESSAGES, LEVELS, REFERRAL_PERCENTS, WITHDRAW_DELAY_MIN, WITHDRAW_DELAY_MAX, UPGRADES, WEBAPP_URL
from webapp.database import init_db_standalone, get_session, User, Transaction, ReferralBonus, UserUpgrade, UserAchievement
from keyboards import (
    get_main_keyboard, get_admin_keyboard, get_level_keyboard,
    get_confirm_keyboard, get_shop_keyboard, get_back_keyboard, get_miniapp_keyboard
)
import random
import string
from datetime import datetime, timedelta
from utils import process_referral_bonus
from income import calculate_user_income, process_monthly_income, format_time_until_next_income
from admin import (
    is_admin, get_user_stats, get_pending_transactions, approve_transaction,
    cancel_transaction, get_user_transactions, get_user_referrals,
    get_user_upgrades, get_user_achievements, search_users, get_recent_activity
)
from notifications import (
    notify_income_received, notify_deposit_confirmed, notify_withdraw_confirmed,
    notify_withdraw_cancelled, notify_referral_bonus, notify_level_up,
    notify_achievement, notify_upgrade_purchased, process_notifications
)
import asyncio
import threading
import os

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
DEPOSIT_AMOUNT, WITHDRAW_AMOUNT = range(2)
ADMIN_SEARCH, ADMIN_USER_ACTION = range(2)
APPROVE_CONFIRM, CANCEL_CONFIRM = range(2)

# Состояния для админ-панели
ADMIN_SEARCH, ADMIN_USER_ACTION = range(2)

# Генерация реферального кода
def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает команду /start и отправляет приветственное сообщение с кнопкой миниаппа."""
    web_app_url = "https://miniapp123.vercel.app/" # Укажите ваш URL на Vercel
    user_id = update.effective_user.id # Получаем ID пользователя
    keyboard = get_miniapp_keyboard(web_app_url, user_id) # Передаем user_id в функцию

    welcome_message = (
        "Привет! Добро пожаловать в Crypto Empire Quest.\n\n"
        "Здесь ты строишь свою финансовую империю, привлекая друзей и прокачивая свой уровень.\n\n"
        "Нажми на кнопку ниже, чтобы открыть свою Империю!"
    )

    await update.message.reply_text(
        welcome_message,
        reply_markup=keyboard
    )

# Обработчик команды /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_MESSAGE)

# Обработчик команды /admin
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ У вас нет доступа к админ-панели")
        return
    
    db = next(get_session())
    stats = get_user_stats(db)
    
    text = f"""
👨‍💼 Админ-панель

📊 Статистика:
👥 Всего пользователей: {stats['total_users']}
✅ Активных пользователей: {stats['active_users']}
💎 Всего депозитов: {stats['total_deposits']:.2f} USDT
💰 Всего выводов: {stats['total_withdraws']:.2f} USDT
👥 Всего рефералов: {stats['total_referrals']}
🎁 Всего реферальных бонусов: {stats['total_referral_bonuses']:.2f} USDT

Выберите действие:
"""
    
    keyboard = [
        [InlineKeyboardButton("🔍 Поиск пользователя", callback_data="admin_search")],
        [InlineKeyboardButton("📝 Ожидающие транзакции", callback_data="admin_pending")],
        [InlineKeyboardButton("📊 Статистика за неделю", callback_data="admin_stats")]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# Обработчик поиска пользователя
async def admin_search_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_search":
        await query.message.reply_text(
            "Введите username или telegram_id пользователя:"
        )
        return ADMIN_SEARCH

# Обработчик результатов поиска
async def process_admin_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    search_query = update.message.text
    db = next(get_session())
    users = search_users(db, search_query)
    
    if not users:
        await update.message.reply_text("❌ Пользователи не найдены")
        return ConversationHandler.END
    
    text = "🔍 Результаты поиска:\n\n"
    keyboard = []
    
    for user in users:
        text += f"👤 @{user.username} (ID: {user.telegram_id})\n"
        text += f"💰 Баланс: {user.balance:.2f} USDT\n"
        text += f"💎 Депозиты: {user.total_deposit:.2f} USDT\n"
        text += f"👥 Рефералов: {len(user.referrals)}\n\n"
        
        keyboard.append([InlineKeyboardButton(
            f"Выбрать @{user.username}",
            callback_data=f"admin_user_{user.id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_back")])
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ADMIN_USER_ACTION

# Обработчик действий с пользователем
async def admin_user_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_back":
        await admin_panel(update, context)
        return ConversationHandler.END
    
    if query.data.startswith("admin_user_"):
        user_id = int(query.data.split("_")[2])
        db = next(get_session())
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            await query.message.reply_text("❌ Пользователь не найден")
            return ConversationHandler.END
        
        stats = get_user_stats(db, user.id)
        transactions = get_user_transactions(db, user.id)
        
        text = f"""
👤 Информация о пользователе:
Username: @{user.username}
ID: {user.telegram_id}
Уровень: {stats['user_level']}
Баланс: {stats['user_balance']:.2f} USDT
Депозиты: {stats['user_deposits']:.2f} USDT
Выводы: {stats['user_withdraws']:.2f} USDT
Рефералы: {stats['user_referrals']}
Реферальные бонусы: {stats['user_referral_bonuses']:.2f} USDT

Последние транзакции:
"""
        
        for trans in transactions:
            text += f"\n{trans.type}: {trans.amount:.2f} USDT ({trans.status})"
        
        keyboard = [
            [InlineKeyboardButton("📊 Подробная статистика", callback_data=f"admin_stats_{user.id}")],
            [InlineKeyboardButton("👥 Рефералы", callback_data=f"admin_referrals_{user.id}")],
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
        ]
        
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# Обработчик ожидающих транзакций
async def admin_pending_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_pending":
        db = next(get_session())
        transactions = get_pending_transactions(db)
        
        if not transactions:
            await query.message.reply_text("✅ Нет ожидающих транзакций")
            return
        
        text = "📝 Ожидающие транзакции:\n\n"
        keyboard = []
        
        for trans in transactions:
            user = db.query(User).filter(User.id == trans.user_id).first()
            text += f"ID: {trans.id}\n"
            text += f"Пользователь: @{user.username}\n"
            text += f"Тип: {trans.type}\n"
            text += f"Сумма: {trans.amount:.2f} USDT\n"
            text += f"Дата: {trans.created_at}\n\n"
            
            keyboard.extend([
                [InlineKeyboardButton(
                    f"✅ Подтвердить {trans.id}",
                    callback_data=f"admin_approve_{trans.id}"
                )],
                [InlineKeyboardButton(
                    f"❌ Отменить {trans.id}",
                    callback_data=f"admin_cancel_{trans.id}"
                )]
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_back")])
        
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# Обработчик статистики
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_stats":
        db = next(get_session())
        activity = get_recent_activity(db)
        
        text = f"""
📊 Статистика за последние 7 дней:

👥 Новых пользователей: {activity['new_users']}
💎 Новых депозитов: {activity['new_deposits']}
💰 Сумма депозитов: {activity['total_deposits_amount']:.2f} USDT
💸 Новых выводов: {activity['new_withdraws']}
💵 Сумма выводов: {activity['total_withdraws_amount']:.2f} USDT
"""
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]]
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# Обработчик кнопки "Моя Империя"
async def my_empire(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Моя Империя'"""
    user = update.effective_user
    db = next(get_session())
    db_user = db.query(User).filter(User.telegram_id == user.id).first()
    
    if not db_user:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    # Получаем статистику пользователя
    stats = get_user_stats(db, db_user.id)
    
    text = f"""
👑 Моя Империя

Уровень: {stats['user_level']}
Баланс: {stats['user_balance']:.2f} USDT
Доход в месяц: {stats['monthly_income']:.2f} USDT
Следующая выплата через: {format_time_until_next_income(db_user)}

👥 Реферальная программа:
Всего рефералов: {stats['user_referrals']}
Заработано с рефералов: {stats['user_referral_bonuses']:.2f} USDT
До следующего уровня: {stats['referrals_to_next_level']} друзей
"""
    
    keyboard = [
        [InlineKeyboardButton("📊 Подробная статистика", callback_data="stats_detailed")],
        [InlineKeyboardButton("👥 Мои рефералы", callback_data="my_referrals")]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# Обработчик кнопки "Инвестировать"
async def invest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Инвестировать'"""
    user = update.effective_user
    db = next(get_session())
    db_user = db.query(User).filter(User.telegram_id == user.id).first()
    
    if not db_user:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    text = """
💎 Инвестировать

Выберите сумму инвестиции:
"""
    
    keyboard = get_level_keyboard()
    await update.message.reply_text(text, reply_markup=keyboard)

# Обработчик кнопки "Вывести прибыль"
async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Вывести прибыль'"""
    user = update.effective_user
    db = next(get_session())
    db_user = db.query(User).filter(User.telegram_id == user.id).first()
    
    if not db_user:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    if db_user.balance <= 0:
        await update.message.reply_text("❌ Недостаточно средств для вывода")
        return
    
    text = f"""
💰 Вывести прибыль

Доступно для вывода: {db_user.balance:.2f} USDT
Минимальная сумма вывода: 10 USDT

Введите сумму для вывода:
"""
    
    await update.message.reply_text(text)
    return WITHDRAW_AMOUNT

# Обработчик кнопки "Друзья"
async def friends(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Друзья'"""
    user = update.effective_user
    db = next(get_session())
    db_user = db.query(User).filter(User.telegram_id == user.id).first()
    
    if not db_user:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    referrals = get_user_referrals(db, db_user.id)
    
    text = f"""
👥 Друзья

Ваша реферальная ссылка:
https://t.me/{context.bot.username}?start={db_user.referral_code}

Всего рефералов: {len(referrals)}
"""
    
    if referrals:
        text += "\nВаши рефералы:\n"
        for i, ref in enumerate(referrals, 1):
            text += f"{i}. @{ref.username} - {ref.total_deposit:.2f} USDT\n"
    
    keyboard = [
        [InlineKeyboardButton("📊 Статистика рефералов", callback_data="referral_stats")],
        [InlineKeyboardButton("🎁 Реферальные бонусы", callback_data="referral_bonuses")]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# Обработчик кнопки "Магазин"
async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Магазин'"""
    text = """
🏪 Магазин

Выберите категорию:
"""
    
    keyboard = get_shop_keyboard()
    await update.message.reply_text(text, reply_markup=keyboard)

# Обработчик кнопки "Топ игроков"
async def top_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Топ игроков'"""
    db = next(get_session())
    
    # Получаем топ игроков по балансу
    top_balance = db.query(User).order_by(User.balance.desc()).limit(10).all()
    
    # Получаем топ игроков по рефералам
    top_referrals = db.query(User).order_by(User.referral_count.desc()).limit(10).all()
    
    text = """
🏆 Топ игроков

Топ по балансу:
"""
    
    for i, user in enumerate(top_balance, 1):
        text += f"{i}. @{user.username} - {user.balance:.2f} USDT\n"
    
    text += "\nТоп по рефералам:\n"
    for i, user in enumerate(top_referrals, 1):
        text += f"{i}. @{user.username} - {user.referral_count} рефералов\n"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="refresh_top")],
        [InlineKeyboardButton("📊 Моя позиция", callback_data="my_position")]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# Обработчик покупки апгрейда
async def buy_upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith('buy_upgrade_'):
        return
    
    upgrade_id = int(query.data.split('_')[2])
    user = update.effective_user
    db = next(get_session())
    db_user = db.query(User).filter(User.telegram_id == user.id).first()
    
    # Получаем информацию об апгрейде
    upgrade_info = UPGRADES[upgrade_id]
    
    # Проверяем, есть ли уже этот апгрейд у пользователя
    user_upgrade = db.query(UserUpgrade).filter(
        UserUpgrade.user_id == db_user.id,
        UserUpgrade.upgrade_id == upgrade_id
    ).first()
    
    if user_upgrade and user_upgrade.level >= upgrade_info['max_level']:
        await query.message.reply_text("❌ Достигнут максимальный уровень апгрейда")
        return
    
    # Проверяем баланс
    if db_user.balance < upgrade_info['price']:
        await query.message.reply_text(MESSAGES['shop']['not_enough'])
        return
    
    # Списываем средства и применяем апгрейд
    db_user.balance -= upgrade_info['price']
    
    if user_upgrade:
        user_upgrade.level += 1
        new_level = user_upgrade.level
    else:
        new_upgrade = UserUpgrade(
            user_id=db_user.id,
            upgrade_id=upgrade_id,
            level=1
        )
        db.add(new_upgrade)
        new_level = 1
    
    db.commit()
    
    # Отправляем уведомление
    await notify_upgrade_purchased(context.bot, db_user, upgrade_info['name'], new_level)
    
    await query.message.reply_text(
        f"{MESSAGES['shop']['success']}\n\n"
        f"🎮 Апгрейд: {upgrade_info['name']}\n"
        f"📝 Уровень: {new_level}\n"
        f"💰 Стоимость: {upgrade_info['price']} USDT"
    )

# Обработчик просмотра достижений
async def show_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = next(get_session())
    db_user = db.query(User).filter(User.telegram_id == user.id).first()
    
    # Получаем все достижения пользователя
    user_achievements = db.query(UserAchievement).filter(
        UserAchievement.user_id == db_user.id
    ).all()
    
    text = "🏆 Ваши достижения:\n\n"
    
    for achievement in UPGRADES:
        is_achieved = any(ua.upgrade_id == UPGRADES.index(achievement) for ua in user_achievements)
        status = "✅" if is_achieved else "⏳"
        text += f"{status} {achievement['name']}\n"
        text += f"📝 {achievement['description']}\n"
        if is_achieved:
            text += f"🎁 Награда: {achievement['reward']['value']} USDT\n"
        text += "\n"
    
    await update.message.reply_text(text)

# Обработчик просмотра апгрейдов
async def show_upgrades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = next(get_session())
    db_user = db.query(User).filter(User.telegram_id == user.id).first()
    
    # Получаем все апгрейды пользователя
    user_upgrades = db.query(UserUpgrade).filter(
        UserUpgrade.user_id == db_user.id
    ).all()
    
    text = "🎮 Доступные апгрейды:\n\n"
    keyboard = []
    
    for i, upgrade in enumerate(UPGRADES):
        # Проверяем, есть ли уже этот апгрейд у пользователя
        user_upgrade = next((u for u in user_upgrades if u.upgrade_id == i), None)
        current_level = user_upgrade.level if user_upgrade else 0
        
        text += f"{upgrade['name']}\n"
        text += f"📝 {upgrade['description']}\n"
        text += f"💰 Цена: {upgrade['price']} USDT\n"
        text += f"📈 Текущий уровень: {current_level}/{upgrade['max_level']}\n\n"
        
        if current_level < upgrade['max_level']:
            keyboard.append([InlineKeyboardButton(
                f"Купить {upgrade['name']}",
                callback_data=f"buy_upgrade_{i}"
            )])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back")])
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# Обновляем обработчик callback-запросов
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех callback-кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("level_"):
        level_index = int(query.data.split("_")[1])
        levels = list(LEVELS.keys())
        level = levels[level_index]
        
        text = f"""
Вы выбрали уровень: {level}
Минимальный депозит: {LEVELS[level]['minDeposit']} USDT
Доход в месяц: {LEVELS[level]['income']}%

Для пополнения используйте адрес:
TRC20: {context.bot_data.get('wallet_address', 'ADDRESS_NOT_SET')}

После пополнения нажмите кнопку подтверждения.
"""
        
        keyboard = get_confirm_keyboard()
        await query.message.edit_text(text, reply_markup=keyboard)
    
    elif query.data == "confirm_yes":
        # Здесь будет логика подтверждения депозита
        await query.message.edit_text("✅ Ваш депозит принят на проверку")
    
    elif query.data == "confirm_no":
        await query.message.edit_text("❌ Операция отменена")
    
    elif query.data.startswith("shop_"):
        category = query.data.split("_")[1]
        if category == "upgrades":
            text = "🎮 Доступные апгрейды:\n\n"
            for upgrade in UPGRADES:
                text += f"{upgrade['name']} - {upgrade['price']} USDT\n"
                text += f"{upgrade['description']}\n\n"
        elif category == "achievements":
            text = "🏆 NFT-ачивки:\n\n"
            # Здесь будет список ачивок
        elif category == "boosts":
            text = "⚡️ Доступные бусты:\n\n"
            # Здесь будет список бустов
        
        keyboard = get_back_keyboard()
        await query.message.edit_text(text, reply_markup=keyboard)
    
    elif query.data == "back":
        await query.message.edit_text("Выберите действие:", reply_markup=get_main_keyboard())
    
    elif query.data == "stats_detailed":
        # Здесь будет подробная статистика
        pass
    
    elif query.data == "my_referrals":
        # Здесь будет список рефералов
        pass
    
    elif query.data == "referral_stats":
        # Здесь будет статистика рефералов
        pass
    
    elif query.data == "referral_bonuses":
        # Здесь будет информация о реферальных бонусах
        pass
    
    elif query.data == "refresh_top":
        # Обновление топа игроков
        await top_players(update, context)
    
    elif query.data == "my_position":
        # Показ позиции пользователя в топе
        pass

async def process_monthly_income_task(context: ContextTypes.DEFAULT_TYPE):
    """
    Задача для автоматического начисления процентов
    """
    try:
        db = next(get_session())
        users = db.query(User).filter(User.total_deposit > 0).all()

        for user in users:
            # Получаем актуального пользователя из базы в этой сессии
            current_user = db.query(User).filter(User.id == user.id).first()
            if current_user:
                income = calculate_user_income(db, current_user)
                if income > 0:
                    # Создаем транзакцию
                    transaction = Transaction(
                        user_id=current_user.id,
                        amount=income,
                        type='income',
                        status='completed',
                        created_at=datetime.utcnow(),
                        completed_at=datetime.utcnow()
                    )
                    db.add(transaction)

                    # Начисляем средства
                    current_user.balance += income

                    # Отправляем уведомление
                    # Передаем bot явно
                    await notify_income_received(context.bot, current_user, income)

        db.commit()

        # Обрабатываем уведомления
        # Передаем bot явно
        await process_notifications(db, context.bot)

    except Exception as e:
        logger.error(f"Ошибка в задаче начисления процентов: {str(e)}")

# Обработчик команды /users для админов
async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ У вас нет доступа к админ-панели")
        return
    
    db = next(get_session())
    users = db.query(User).all()
    
    text = "👥 Список пользователей:\n\n"
    keyboard = []
    
    for user in users:
        text += f"👤 @{user.username} (ID: {user.telegram_id})\n"
        text += f"💰 Баланс: {user.balance:.2f} USDT\n"
        text += f"💎 Депозиты: {user.total_deposit:.2f} USDT\n"
        text += f"👥 Рефералов: {len(user.referrals)}\n\n"
        
        keyboard.append([InlineKeyboardButton(
            f"Выбрать @{user.username}",
            callback_data=f"admin_user_{user.id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_back")])
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# Обработчик команды /transactions для админов
async def admin_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ У вас нет доступа к админ-панели")
        return
    
    db = next(get_session())
    transactions = db.query(Transaction).order_by(Transaction.created_at.desc()).limit(10).all()
    
    text = "📝 Последние транзакции:\n\n"
    keyboard = []
    
    for trans in transactions:
        user = db.query(User).filter(User.id == trans.user_id).first()
        text += f"ID: {trans.id}\n"
        text += f"👤 Пользователь: @{user.username}\n"
        text += f"💰 Сумма: {trans.amount:.2f} USDT\n"
        text += f"📋 Тип: {trans.type}\n"
        text += f"📊 Статус: {trans.status}\n"
        text += f"🕒 Дата: {trans.created_at}\n\n"
        
        if trans.status == 'pending':
            keyboard.extend([
                [InlineKeyboardButton(
                    f"✅ Подтвердить {trans.id}",
                    callback_data=f"admin_approve_{trans.id}"
                )],
                [InlineKeyboardButton(
                    f"❌ Отменить {trans.id}",
                    callback_data=f"admin_cancel_{trans.id}"
                )]
            ])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_back")])
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# Обработчик подтверждения транзакции
async def confirm_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ У вас нет доступа к админ-панели")
        return ConversationHandler.END
    
    try:
        transaction_id = int(update.message.text)
        db = next(get_session())
        
        if approve_transaction(db, transaction_id):
            transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
            if transaction.type == 'deposit':
                await notify_deposit_confirmed(context.bot, transaction.user, transaction.amount)
            elif transaction.type == 'withdraw':
                await notify_withdraw_confirmed(context.bot, transaction.user, transaction.amount)
            await update.message.reply_text("✅ Транзакция подтверждена")
        else:
            await update.message.reply_text("❌ Ошибка при подтверждении транзакции")
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("❌ Неверный формат ID транзакции")
        return ConversationHandler.END

# Обработчик отмены транзакции
async def confirm_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ У вас нет доступа к админ-панели")
        return ConversationHandler.END
    
    try:
        transaction_id = int(update.message.text)
        db = next(get_session())
        
        if cancel_transaction(db, transaction_id):
            transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
            if transaction.type == 'withdraw':
                await notify_withdraw_cancelled(context.bot, transaction.user, transaction.amount)
            await update.message.reply_text("✅ Транзакция отменена")
        else:
            await update.message.reply_text("❌ Ошибка при отмене транзакции")
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("❌ Неверный формат ID транзакции")
        return ConversationHandler.END

# Обработчик отмены действия
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Действие отменено")
    return ConversationHandler.END

# Обработчик кнопки "Открыть веб-приложение"
async def open_webapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # TODO: Замените этот URL на реальный URL вашего развернутого веб-приложения
    webapp_url = "ВАШ_URL_МИНИ_ПРИЛОЖЕНИЯ_НА_AMVERA"
    keyboard = [
        [KeyboardButton("🌐 Открыть веб-приложение", web_app=WebAppInfo(url=webapp_url))]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Нажмите кнопку ниже, чтобы открыть веб-приложение:",
        reply_markup=reply_markup
    )

def main():
    # Инициализация базы данных
    # Используем standalone функцию, которая не зависит от генератора get_session
    # Временно закомментируем инициализацию при каждом запуске бота на Amvera
    # init_db_standalone() # <-- Закомментировано
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_panel))

    # Добавляем обработчики кнопок (текстовых сообщений)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, my_empire, block=False))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, invest, block=False))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw, block=False))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, friends, block=False))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, shop, block=False))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, top_players, block=False))
    # Обработчик для кнопки "Открыть веб-приложение" (она тоже отправляет текстовое сообщение)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, open_webapp, block=False))

    # Добавляем обработчик callback query для админ-панели
    admin_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_search_user, pattern='^admin_search')],
        states={
            ADMIN_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_admin_search)],
            ADMIN_USER_ACTION: [CallbackQueryHandler(admin_user_action, pattern='^admin_')],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    application.add_handler(admin_conv_handler)

    # Обработчики для подтверждения админ-действий
    application.add_handler(CallbackQueryHandler(admin_pending_transactions, pattern='^admin_pending'))
    application.add_handler(CallbackQueryHandler(admin_stats, pattern='^admin_stats'))
    application.add_handler(CallbackQueryHandler(confirm_approve, pattern='^admin_approve_'))
    application.add_handler(CallbackQueryHandler(confirm_cancel, pattern='^admin_cancel_'))

    # Запуск бота
    logger.info("Бот запущен...")
    
    # Планируем фоновые задачи
    # Запуск задачи по начислению дохода
    # Передаем context в job_queue - исправлено
    # application.job_queue.run_repeating(process_monthly_income_task, interval=timedelta(days=30), first=timedelta(days=30)) # <-- Закомментировано

    # Запуск задачи по обработке уведомлений
    # Передаем context в job_queue - исправлено
    # application.job_queue.run_repeating(process_notifications, interval=timedelta(minutes=1)) # <-- Закомментировано

    # Запускаем Polling
    application.run_polling(poll_interval=3)

if __name__ == '__main__':
    main() 