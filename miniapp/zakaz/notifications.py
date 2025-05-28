from telegram import Bot
from database import User, Transaction, UserAchievement
from config import BOT_TOKEN, MESSAGES, NOTIFICATION_INTERVAL
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging
import asyncio
from database import (
    get_user_by_telegram_id,
    get_pending_transactions,
    get_user_achievements,
    get_user_upgrades
)

logger = logging.getLogger(__name__)

async def send_notification(bot: Bot, user_id: int, message: str):
    """
    Отправляет уведомление пользователю
    """
    try:
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='HTML'
        )
        logger.info(f"Уведомление отправлено пользователю {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления пользователю {user_id}: {str(e)}")

async def notify_income_received(bot: Bot, user_id: int, amount: float, balance: float):
    """Уведомление о получении дохода"""
    try:
        message = MESSAGES['income_received'].format(
            amount=amount,
            balance=balance
        )
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error sending income notification to {user_id}: {e}")

async def notify_deposit_confirmed(bot: Bot, user_id: int, amount: float, balance: float):
    """Уведомление о подтверждении депозита"""
    try:
        message = MESSAGES['deposit_confirmed'].format(
            amount=amount,
            balance=balance
        )
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error sending deposit confirmation to {user_id}: {e}")

async def notify_withdraw_confirmed(bot: Bot, user_id: int, amount: float, balance: float):
    """Уведомление о подтверждении вывода"""
    try:
        message = MESSAGES['withdraw_confirmed'].format(
            amount=amount,
            balance=balance
        )
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error sending withdraw confirmation to {user_id}: {e}")

async def notify_withdraw_cancelled(bot: Bot, user_id: int, amount: float, balance: float):
    """Уведомление об отмене вывода"""
    try:
        message = MESSAGES['withdraw_cancelled'].format(
            amount=amount,
            balance=balance
        )
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error sending withdraw cancellation to {user_id}: {e}")

async def notify_referral_bonus(bot: Bot, user_id: int, amount: float, balance: float, referred):
    """Уведомление о реферальном бонусе"""
    try:
        message = MESSAGES['referral_bonus'].format(
            username=referred.username,
            amount=amount,
            balance=balance
        )
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error sending referral bonus notification to {user_id}: {e}")

async def notify_level_up(bot: Bot, user_id: int, level: str):
    """Уведомление о повышении уровня"""
    try:
        message = MESSAGES['level_up'].format(level=level)
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error sending level up notification to {user_id}: {e}")

async def notify_achievement(bot: Bot, user_id: int, achievement: dict):
    """Уведомление о достижении"""
    try:
        message = MESSAGES['achievement'].format(
            name=achievement['name'],
            description=achievement['description']
        )
        if 'reward' in achievement:
            message += f"\n\n🎁 Награда: {achievement['reward']['amount']} USDT"
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error sending achievement notification to {user_id}: {e}")

async def notify_upgrade_purchased(bot: Bot, user_id: int, upgrade: dict, level: int):
    """Уведомление о покупке апгрейда"""
    try:
        message = MESSAGES['upgrade_purchased'].format(
            name=upgrade['name'],
            level=level,
            effect=upgrade['effect_description']
        )
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error sending upgrade purchase notification to {user_id}: {e}")

async def notify_system_message(bot: Bot, user_id: int, message: str):
    """Отправка системного сообщения"""
    try:
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error sending system message to {user_id}: {e}")

async def notify_broadcast(bot: Bot, user_ids: list, message: str):
    """Отправка широковещательного сообщения"""
    for user_id in user_ids:
        try:
            await bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error sending broadcast to {user_id}: {e}")

async def notify_income_reminder(bot: Bot, user: User, days_until: int):
    """
    Уведомляет пользователя о приближающемся начислении
    """
    message = f"""
⏳ <b>Напоминание о начислении</b>

До следующего начисления осталось: {days_until} дней
Текущий баланс: {user.balance:.2f} USDT

Не забудьте проверить свой баланс!
"""
    await send_notification(bot, user.telegram_id, message)

async def process_notifications(bot: Bot, db):
    """Обработка всех уведомлений"""
    while True:
        try:
            # Проверка ожидающих транзакций
            pending_transactions = get_pending_transactions(db)
            for transaction in pending_transactions:
                if transaction.type == 'deposit':
                    await notify_deposit_confirmed(
                        bot,
                        transaction.user.telegram_id,
                        transaction.amount,
                        transaction.user.balance
                    )
                elif transaction.type == 'withdraw':
                    await notify_withdraw_confirmed(
                        bot,
                        transaction.user.telegram_id,
                        transaction.amount,
                        transaction.user.balance
                    )

            # Проверка достижений
            users = db.query(User).all()
            for user in users:
                achievements = get_user_achievements(db, user.id)
                for achievement in achievements:
                    if not achievement.reward_claimed:
                        await notify_achievement(
                            bot,
                            user.telegram_id,
                            achievement
                        )

            # Проверка апгрейдов
            for user in users:
                upgrades = get_user_upgrades(db, user.id)
                for upgrade in upgrades:
                    if upgrade.expires_at and upgrade.expires_at <= datetime.utcnow():
                        await notify_system_message(
                            bot,
                            user.telegram_id,
                            f"⚠️ Ваш апгрейд {upgrade.upgrade_id} истек!"
                        )

            # Ожидание перед следующей проверкой
            await asyncio.sleep(NOTIFICATION_INTERVAL)

        except Exception as e:
            logger.error(f"Error in notification processing: {e}")
            await asyncio.sleep(60)  # Пауза перед повторной попыткой 