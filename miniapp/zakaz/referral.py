from database import get_db, User, ReferralBonus
from config import REFERRAL_PERCENTS, LEVELS
from notifications import notify_referral_bonus
import logging
import secrets

logger = logging.getLogger(__name__)

def generate_referral_code() -> str:
    """Генерация уникального реферального кода"""
    while True:
        code = secrets.token_hex(4).upper()
        db = next(get_db())
        if not db.query(User).filter(User.referral_code == code).first():
            return code

def get_referral_link(user: User) -> str:
    """Получение реферальной ссылки пользователя"""
    return f"https://t.me/{user.username}?start={user.referral_code}"

def process_referral_bonus(referrer: User, referred: User, amount: float) -> bool:
    """Обработка реферального бонуса"""
    try:
        # Получаем процент бонуса для уровня реферера
        bonus_percent = REFERRAL_PERCENTS[referrer.level]
        
        # Рассчитываем сумму бонуса
        bonus_amount = amount * (bonus_percent / 100)
        
        # Создаем запись о бонусе
        db = next(get_db())
        referral_bonus = ReferralBonus(
            referrer_id=referrer.id,
            referred_id=referred.id,
            amount=bonus_amount,
            percent=bonus_percent
        )
        db.add(referral_bonus)
        
        # Начисляем бонус рефереру
        referrer.balance += bonus_amount
        referrer.referral_earnings += bonus_amount
        
        db.commit()
        
        # Отправляем уведомление
        notify_referral_bonus(referrer, referred, bonus_amount)
        
        logger.info(f"Начислен реферальный бонус пользователю {referrer.id}: {bonus_amount} USDT")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при начислении реферального бонуса: {e}")
        return False

def get_referral_stats(user: User) -> dict:
    """Получение статистики рефералов"""
    try:
        db = next(get_db())
        
        # Получаем всех рефералов
        referrals = db.query(User).filter(User.referrer_id == user.id).all()
        
        # Считаем статистику
        total_referrals = len(referrals)
        active_referrals = sum(1 for r in referrals if r.total_deposit > 0)
        total_earnings = user.referral_earnings
        
        # Получаем последних рефералов
        recent_referrals = db.query(User).filter(
            User.referrer_id == user.id
        ).order_by(User.created_at.desc()).limit(5).all()
        
        return {
            'total_referrals': total_referrals,
            'active_referrals': active_referrals,
            'total_earnings': total_earnings,
            'recent_referrals': recent_referrals
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики рефералов: {e}")
        return {
            'total_referrals': 0,
            'active_referrals': 0,
            'total_earnings': 0,
            'recent_referrals': []
        }

def check_referral_achievements(user: User) -> list:
    """Проверка достижений реферальной программы"""
    try:
        achievements = []
        db = next(get_db())
        
        # Проверяем достижения по количеству рефералов
        referral_count = user.referral_count
        for level, params in LEVELS.items():
            if referral_count >= params['requiredReferrals']:
                achievement = {
                    'type': 'referral_count',
                    'level': level,
                    'count': params['requiredReferrals']
                }
                achievements.append(achievement)
        
        # Проверяем достижения по заработку с рефералов
        if user.referral_earnings >= 1000:
            achievement = {
                'type': 'referral_earnings',
                'amount': 1000
            }
            achievements.append(achievement)
        
        return achievements
        
    except Exception as e:
        logger.error(f"Ошибка при проверке достижений реферальной программы: {e}")
        return []

def format_referral_stats(stats: dict) -> str:
    """Форматирование статистики рефералов для отображения"""
    text = f"📊 Статистика рефералов:\n\n"
    text += f"👥 Всего рефералов: {stats['total_referrals']}\n"
    text += f"✅ Активных рефералов: {stats['active_referrals']}\n"
    text += f"💰 Общий заработок: {stats['total_earnings']:.2f} USDT\n\n"
    
    if stats['recent_referrals']:
        text += "🆕 Последние рефералы:\n"
        for ref in stats['recent_referrals']:
            text += f"• @{ref.username} - {ref.created_at.strftime('%d.%m.%Y')}\n"
    
    return text 