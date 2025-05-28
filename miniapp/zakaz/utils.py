from database import User, ReferralBonus
from config import REFERRAL_PERCENTS, LEVELS
from sqlalchemy.orm import Session

def process_referral_bonus(db: Session, user_id: int, amount: float):
    """
    Обработка реферальных бонусов при депозите
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.referred_by:
        return
    
    # Получаем цепочку рефералов
    referrer = user.referrer
    level = 1
    
    while referrer and level <= 3:
        # Рассчитываем бонус
        bonus_percent = REFERRAL_PERCENTS[level]
        bonus_amount = amount * (bonus_percent / 100)
        
        # Создаем запись о бонусе
        referral_bonus = ReferralBonus(
            referrer_id=referrer.id,
            referred_id=user.id,
            amount=bonus_amount,
            level=level
        )
        db.add(referral_bonus)
        
        # Начисляем бонус
        referrer.balance += bonus_amount
        
        # Проверяем повышение уровня
        if len(referrer.referrals) >= LEVELS[referrer.level].required_referrals:
            referrer.level = min(referrer.level + 1, len(LEVELS) - 1)
        
        # Переходим к следующему уровню
        referrer = referrer.referrer
        level += 1
    
    db.commit()

def check_level_upgrade(db: Session, user_id: int):
    """
    Проверка и повышение уровня пользователя
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return
    
    current_level = LEVELS[user.level]
    referrals_count = len(user.referrals)
    
    if referrals_count >= current_level.required_referrals:
        user.level = min(user.level + 1, len(LEVELS) - 1)
        db.commit()
        return True
    
    return False 