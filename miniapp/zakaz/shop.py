from database import get_db, User, UserUpgrade
from config import UPGRADES
from notifications import notify_upgrade_purchased
import logging

logger = logging.getLogger(__name__)

def get_available_upgrades(user: User) -> list:
    """Получение доступных апгрейдов для пользователя"""
    try:
        db = next(get_db())
        
        # Получаем все апгрейды пользователя
        user_upgrades = db.query(UserUpgrade).filter(
            UserUpgrade.user_id == user.id
        ).all()
        
        # Создаем словарь с текущими уровнями апгрейдов
        current_upgrades = {up.upgrade_id: up.level for up in user_upgrades}
        
        # Фильтруем доступные апгрейды
        available_upgrades = []
        for upgrade in UPGRADES:
            current_level = current_upgrades.get(upgrade['id'], 0)
            
            # Проверяем, можно ли купить следующий уровень
            if current_level < upgrade['max_level']:
                # Проверяем требования к уровню пользователя
                if user.level in upgrade['required_levels']:
                    available_upgrades.append({
                        **upgrade,
                        'current_level': current_level,
                        'next_level': current_level + 1,
                        'price': upgrade['base_price'] * (current_level + 1)
                    })
        
        return available_upgrades
        
    except Exception as e:
        logger.error(f"Ошибка при получении доступных апгрейдов: {e}")
        return []

def purchase_upgrade(user: User, upgrade_id: str) -> bool:
    """Покупка апгрейда"""
    try:
        db = next(get_db())
        
        # Получаем информацию об апгрейде
        upgrade_info = next((u for u in UPGRADES if u['id'] == upgrade_id), None)
        if not upgrade_info:
            return False
        
        # Получаем текущий уровень апгрейда
        user_upgrade = db.query(UserUpgrade).filter(
            UserUpgrade.user_id == user.id,
            UserUpgrade.upgrade_id == upgrade_id
        ).first()
        
        current_level = user_upgrade.level if user_upgrade else 0
        
        # Проверяем, можно ли купить следующий уровень
        if current_level >= upgrade_info['max_level']:
            return False
        
        # Проверяем требования к уровню пользователя
        if user.level not in upgrade_info['required_levels']:
            return False
        
        # Рассчитываем стоимость
        price = upgrade_info['base_price'] * (current_level + 1)
        
        # Проверяем баланс
        if user.balance < price:
            return False
        
        # Списываем средства
        user.balance -= price
        
        # Создаем или обновляем апгрейд
        if user_upgrade:
            user_upgrade.level += 1
            user_upgrade.is_active = True
        else:
            user_upgrade = UserUpgrade(
                user_id=user.id,
                upgrade_id=upgrade_id,
                level=1,
                is_active=True
            )
            db.add(user_upgrade)
        
        db.commit()
        
        # Отправляем уведомление
        notify_upgrade_purchased(user, upgrade_info, current_level + 1)
        
        logger.info(f"Пользователь {user.id} купил апгрейд {upgrade_id} уровня {current_level + 1}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при покупке апгрейда: {e}")
        return False

def get_active_upgrades(user: User) -> list:
    """Получение активных апгрейдов пользователя"""
    try:
        db = next(get_db())
        
        # Получаем все активные апгрейды
        active_upgrades = db.query(UserUpgrade).filter(
            UserUpgrade.user_id == user.id,
            UserUpgrade.is_active == True
        ).all()
        
        # Добавляем информацию об апгрейдах
        result = []
        for upgrade in active_upgrades:
            upgrade_info = next((u for u in UPGRADES if u['id'] == upgrade.upgrade_id), None)
            if upgrade_info:
                result.append({
                    **upgrade_info,
                    'current_level': upgrade.level
                })
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при получении активных апгрейдов: {e}")
        return []

def format_upgrade_info(upgrade: dict) -> str:
    """Форматирование информации об апгрейде для отображения"""
    text = f"🛍 {upgrade['name']}\n\n"
    text += f"📝 {upgrade['description']}\n\n"
    
    if upgrade.get('current_level'):
        text += f"📊 Текущий уровень: {upgrade['current_level']}/{upgrade['max_level']}\n"
        if upgrade['current_level'] < upgrade['max_level']:
            text += f"💰 Стоимость следующего уровня: {upgrade['base_price'] * (upgrade['current_level'] + 1)} USDT\n"
    else:
        text += f"💰 Стоимость: {upgrade['base_price']} USDT\n"
        text += f"📊 Максимальный уровень: {upgrade['max_level']}\n"
    
    text += f"\n🔧 Эффект: {upgrade['effect_description']}"
    
    return text

def format_shop_menu(upgrades: list) -> str:
    """Форматирование меню магазина"""
    text = "🛍 Магазин апгрейдов\n\n"
    
    if not upgrades:
        text += "😔 Нет доступных апгрейдов"
        return text
    
    for upgrade in upgrades:
        text += f"• {upgrade['name']} "
        if upgrade.get('current_level'):
            text += f"(Ур. {upgrade['current_level']}/{upgrade['max_level']})"
        text += f" - {upgrade['base_price'] * (upgrade.get('current_level', 0) + 1)} USDT\n"
    
    return text 