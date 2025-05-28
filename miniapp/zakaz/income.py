from database import User, Transaction, UserUpgrade
from config import LEVELS, INCOME_INTERVAL
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging
from notifications import notify_income_received
import asyncio

logger = logging.getLogger(__name__)

def calculate_user_income(user: User) -> float:
    """Расчет дохода пользователя"""
    try:
        # Получаем параметры уровня
        level_params = LEVELS[user.level]
        
        # Базовый доход
        base_income = user.total_deposit * (level_params['income'] / 100)
        
        # Проверяем активные апгрейды
        db = next(get_db())
        active_upgrades = db.query(UserUpgrade).filter(
            UserUpgrade.user_id == user.id,
            UserUpgrade.is_active == True
        ).all()
        
        # Применяем бонусы от апгрейдов
        total_bonus = 0
        for upgrade in active_upgrades:
            if upgrade.upgrade_id == 'income_boost':
                total_bonus += upgrade.effect
        
        # Итоговый доход с учетом бонусов
        final_income = base_income * (1 + total_bonus / 100)
        
        return final_income
    except Exception as e:
        logger.error(f"Ошибка при расчете дохода пользователя {user.id}: {e}")
        return 0

async def process_monthly_income(bot):
    """Обработка ежемесячных начислений"""
    while True:
        try:
            db = next(get_db())
            users = db.query(User).filter(User.total_deposit > 0).all()
            
            for user in users:
                # Проверяем, прошло ли достаточно времени с последнего начисления
                if user.next_income and datetime.utcnow() >= user.next_income:
                    # Рассчитываем доход
                    income = calculate_user_income(user)
                    
                    if income > 0:
                        # Создаем транзакцию
                        transaction = Transaction(
                            user_id=user.id,
                            type='income',
                            amount=income,
                            status='completed'
                        )
                        db.add(transaction)
                        
                        # Обновляем баланс пользователя
                        user.balance += income
                        
                        # Обновляем время следующего начисления
                        user.last_income = datetime.utcnow()
                        user.next_income = datetime.utcnow() + timedelta(days=30)
                        
                        db.commit()
                        
                        # Отправляем уведомление
                        await notify_income_received(bot, user, income)
                        
                        logger.info(f"Начислен доход пользователю {user.id}: {income} USDT")
            
            await asyncio.sleep(INCOME_INTERVAL)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке ежемесячных начислений: {e}")
            await asyncio.sleep(60)  # Пауза перед повторной попыткой

def format_time_until_next_income(user: User) -> str:
    """Форматирование времени до следующего начисления"""
    if not user.next_income:
        return "Не определено"
    
    time_left = user.next_income - datetime.utcnow()
    
    if time_left.total_seconds() <= 0:
        return "Сейчас"
    
    days = time_left.days
    hours = time_left.seconds // 3600
    minutes = (time_left.seconds % 3600) // 60
    
    if days > 0:
        return f"{days}д {hours}ч {minutes}м"
    elif hours > 0:
        return f"{hours}ч {minutes}м"
    else:
        return f"{minutes}м"

def check_level_upgrade(user: User) -> bool:
    """Проверка возможности повышения уровня"""
    try:
        current_level = user.level
        current_level_index = list(LEVELS.keys()).index(current_level)
        
        # Проверяем, есть ли следующий уровень
        if current_level_index + 1 >= len(LEVELS):
            return False
        
        next_level = list(LEVELS.keys())[current_level_index + 1]
        required_referrals = LEVELS[next_level]['requiredReferrals']
        
        # Проверяем количество рефералов
        if user.referral_count >= required_referrals:
            # Проверяем минимальный депозит
            if user.total_deposit >= LEVELS[next_level]['minDeposit']:
                return True
        
        return False
    except Exception as e:
        logger.error(f"Ошибка при проверке повышения уровня пользователя {user.id}: {e}")
        return False

def upgrade_user_level(user: User) -> bool:
    """Повышение уровня пользователя"""
    try:
        current_level_index = list(LEVELS.keys()).index(user.level)
        next_level = list(LEVELS.keys())[current_level_index + 1]
        
        user.level = next_level
        db = next(get_db())
        db.commit()
        
        logger.info(f"Пользователь {user.id} повышен до уровня {next_level}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при повышении уровня пользователя {user.id}: {e}")
        return False 