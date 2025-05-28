from database import get_db, User, UserAchievement
from config import ACHIEVEMENTS
from notifications import notify_achievement
import logging

logger = logging.getLogger(__name__)

def check_achievements(user: User) -> list:
    """Проверка достижений пользователя"""
    try:
        db = next(get_db())
        
        # Получаем все достижения пользователя
        user_achievements = db.query(UserAchievement).filter(
            UserAchievement.user_id == user.id
        ).all()
        
        # Создаем множество полученных достижений
        earned_achievements = {ua.achievement_id for ua in user_achievements}
        
        # Проверяем все достижения
        new_achievements = []
        for achievement in ACHIEVEMENTS:
            if achievement['id'] not in earned_achievements:
                # Проверяем условия достижения
                if check_achievement_conditions(user, achievement):
                    # Создаем запись о достижении
                    user_achievement = UserAchievement(
                        user_id=user.id,
                        achievement_id=achievement['id']
                    )
                    db.add(user_achievement)
                    
                    # Начисляем награду
                    if achievement.get('reward'):
                        reward_type = achievement['reward']['type']
                        reward_amount = achievement['reward']['amount']
                        
                        if reward_type == 'balance':
                            user.balance += reward_amount
                        elif reward_type == 'income_boost':
                            # Применяем временный бонус к доходу
                            user.income_boost = reward_amount
                            user.income_boost_expires = datetime.utcnow() + timedelta(days=30)
                    
                    new_achievements.append(achievement)
        
        if new_achievements:
            db.commit()
            
            # Отправляем уведомления
            for achievement in new_achievements:
                notify_achievement(user, achievement)
        
        return new_achievements
        
    except Exception as e:
        logger.error(f"Ошибка при проверке достижений: {e}")
        return []

def check_achievement_conditions(user: User, achievement: dict) -> bool:
    """Проверка условий достижения"""
    try:
        conditions = achievement['conditions']
        
        for condition in conditions:
            condition_type = condition['type']
            condition_value = condition['value']
            
            if condition_type == 'total_deposit':
                if user.total_deposit < condition_value:
                    return False
                    
            elif condition_type == 'total_withdraw':
                if user.total_withdraw < condition_value:
                    return False
                    
            elif condition_type == 'referral_count':
                if user.referral_count < condition_value:
                    return False
                    
            elif condition_type == 'referral_earnings':
                if user.referral_earnings < condition_value:
                    return False
                    
            elif condition_type == 'level':
                if user.level != condition_value:
                    return False
                    
            elif condition_type == 'upgrade_level':
                upgrade_id = condition['upgrade_id']
                required_level = condition_value
                
                db = next(get_db())
                user_upgrade = db.query(UserUpgrade).filter(
                    UserUpgrade.user_id == user.id,
                    UserUpgrade.upgrade_id == upgrade_id
                ).first()
                
                if not user_upgrade or user_upgrade.level < required_level:
                    return False
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при проверке условий достижения: {e}")
        return False

def get_user_achievements(user: User) -> list:
    """Получение достижений пользователя"""
    try:
        db = next(get_db())
        
        # Получаем все достижения пользователя
        user_achievements = db.query(UserAchievement).filter(
            UserAchievement.user_id == user.id
        ).all()
        
        # Добавляем информацию о достижениях
        result = []
        for user_achievement in user_achievements:
            achievement_info = next(
                (a for a in ACHIEVEMENTS if a['id'] == user_achievement.achievement_id),
                None
            )
            if achievement_info:
                result.append({
                    **achievement_info,
                    'earned_at': user_achievement.created_at
                })
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при получении достижений пользователя: {e}")
        return []

def format_achievement_info(achievement: dict) -> str:
    """Форматирование информации о достижении"""
    text = f"🏆 {achievement['name']}\n\n"
    text += f"📝 {achievement['description']}\n\n"
    
    if achievement.get('earned_at'):
        text += f"✅ Получено: {achievement['earned_at'].strftime('%d.%m.%Y')}\n"
    
    if achievement.get('reward'):
        reward = achievement['reward']
        if reward['type'] == 'balance':
            text += f"💰 Награда: {reward['amount']} USDT"
        elif reward['type'] == 'income_boost':
            text += f"📈 Награда: +{reward['amount']}% к доходу на 30 дней"
    
    return text

def format_achievements_list(achievements: list) -> str:
    """Форматирование списка достижений"""
    text = "🏆 Достижения\n\n"
    
    if not achievements:
        text += "😔 У вас пока нет достижений"
        return text
    
    for achievement in achievements:
        text += f"• {achievement['name']}"
        if achievement.get('earned_at'):
            text += f" ✅"
        text += "\n"
    
    return text 