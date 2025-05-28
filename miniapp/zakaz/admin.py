from webapp.database import get_session, User, Transaction, ReferralBonus, UserUpgrade, UserAchievement
from config import ADMIN_ID, LEVELS, ADMIN_IDS
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import logging
from transactions import confirm_transaction, cancel_transaction

logger = logging.getLogger(__name__)

def is_admin(user_id: int) -> bool:
    """Проверка является ли пользователь администратором"""
    return user_id in ADMIN_IDS

def get_user_stats(user: User) -> dict:
    """Получение статистики пользователя"""
    try:
        db = next(get_session())
        
        # Получаем все транзакции пользователя
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user.id
        ).all()
        
        # Считаем статистику
        total_deposits = sum(t.amount for t in transactions if t.type == 'deposit' and t.status == 'completed')
        total_withdraws = sum(t.amount for t in transactions if t.type == 'withdraw' and t.status == 'completed')
        total_income = sum(t.amount for t in transactions if t.type == 'income')
        
        # Получаем активные апгрейды
        active_upgrades = db.query(UserUpgrade).filter(
            UserUpgrade.user_id == user.id,
            UserUpgrade.is_active == True
        ).all()
        
        # Получаем достижения
        achievements = db.query(UserAchievement).filter(
            UserAchievement.user_id == user.id
        ).all()
        
        return {
            'user': user,
            'total_deposits': total_deposits,
            'total_withdraws': total_withdraws,
            'total_income': total_income,
            'active_upgrades': active_upgrades,
            'achievements': achievements
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики пользователя: {e}")
        return None

def get_system_stats() -> dict:
    """Получение статистики системы"""
    try:
        db = next(get_session())
        
        # Получаем всех пользователей
        users = db.query(User).all()
        
        # Считаем статистику
        total_users = len(users)
        active_users = sum(1 for u in users if u.total_deposit > 0)
        total_deposits = sum(u.total_deposit for u in users)
        total_withdraws = sum(u.total_withdraw for u in users)
        total_income = sum(u.balance for u in users)
        
        # Получаем ожидающие транзакции
        pending_transactions = db.query(Transaction).filter(
            Transaction.status == 'pending'
        ).all()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_deposits': total_deposits,
            'total_withdraws': total_withdraws,
            'total_income': total_income,
            'pending_transactions': pending_transactions
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики системы: {e}")
        return None

def format_user_stats(stats: dict) -> str:
    """Форматирование статистики пользователя"""
    if not stats:
        return "❌ Ошибка при получении статистики"
    
    text = f"👤 Статистика пользователя @{stats['user'].username}\n\n"
    text += f"📊 Уровень: {stats['user'].level}\n"
    text += f"💰 Баланс: {stats['user'].balance} USDT\n"
    text += f"📥 Всего депозитов: {stats['total_deposits']} USDT\n"
    text += f"📤 Всего выводов: {stats['total_withdraws']} USDT\n"
    text += f"💸 Всего доходов: {stats['total_income']} USDT\n"
    text += f"👥 Рефералов: {stats['user'].referral_count}\n"
    text += f"💎 Реферальный заработок: {stats['user'].referral_earnings} USDT\n\n"
    
    if stats['active_upgrades']:
        text += "🔧 Активные апгрейды:\n"
        for upgrade in stats['active_upgrades']:
            text += f"• {upgrade.upgrade_id} (Ур. {upgrade.level})\n"
    
    if stats['achievements']:
        text += "\n🏆 Достижения:\n"
        for achievement in stats['achievements']:
            text += f"• {achievement.achievement_id}\n"
    
    return text

def format_system_stats(stats: dict) -> str:
    """Форматирование статистики системы"""
    if not stats:
        return "❌ Ошибка при получении статистики"
    
    text = "📊 Статистика системы\n\n"
    text += f"👥 Всего пользователей: {stats['total_users']}\n"
    text += f"✅ Активных пользователей: {stats['active_users']}\n"
    text += f"📥 Всего депозитов: {stats['total_deposits']} USDT\n"
    text += f"📤 Всего выводов: {stats['total_withdraws']} USDT\n"
    text += f"💸 Всего в системе: {stats['total_income']} USDT\n\n"
    
    if stats['pending_transactions']:
        text += "⏳ Ожидающие транзакции:\n"
        for transaction in stats['pending_transactions']:
            text += f"• #{transaction.id} - {transaction.type} {transaction.amount} USDT\n"
    
    return text

def process_pending_transactions() -> dict:
    """Обработка ожидающих транзакций"""
    try:
        db = next(get_session())
        
        # Получаем все ожидающие транзакции
        transactions = db.query(Transaction).filter(
            Transaction.status == 'pending'
        ).all()
        
        results = {
            'confirmed': 0,
            'cancelled': 0,
            'errors': 0
        }
        
        for transaction in transactions:
            try:
                # Подтверждаем или отменяем транзакцию
                if transaction.type == 'deposit':
                    if confirm_transaction(transaction):
                        results['confirmed'] += 1
                    else:
                        results['errors'] += 1
                elif transaction.type == 'withdraw':
                    if cancel_transaction(transaction):
                        results['cancelled'] += 1
                    else:
                        results['errors'] += 1
            except Exception as e:
                logger.error(f"Ошибка при обработке транзакции {transaction.id}: {e}")
                results['errors'] += 1
        
        return results
        
    except Exception as e:
        logger.error(f"Ошибка при обработке ожидающих транзакций: {e}")
        return None

def format_processing_results(results: dict) -> str:
    """Форматирование результатов обработки транзакций"""
    if not results:
        return "❌ Ошибка при обработке транзакций"
    
    text = "📊 Результаты обработки транзакций\n\n"
    text += f"✅ Подтверждено: {results['confirmed']}\n"
    text += f"❌ Отменено: {results['cancelled']}\n"
    text += f"⚠️ Ошибок: {results['errors']}"
    
    return text

def get_user_stats(db: Session, user_id: int = None) -> dict:
    """
    Получает статистику по пользователям
    """
    stats = {
        'total_users': db.query(User).count(),
        'active_users': db.query(User).filter(User.total_deposit > 0).count(),
        'total_deposits': db.query(User).with_entities(func.sum(User.total_deposit)).scalar() or 0,
        'total_withdraws': db.query(User).with_entities(func.sum(User.total_withdraw)).scalar() or 0,
        'total_referrals': db.query(ReferralBonus).count(),
        'total_referral_bonuses': db.query(ReferralBonus).with_entities(func.sum(ReferralBonus.amount)).scalar() or 0
    }
    
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            stats.update({
                'user_level': LEVELS[user.level].name,
                'user_balance': user.balance,
                'user_deposits': user.total_deposit,
                'user_withdraws': user.total_withdraw,
                'user_referrals': db.query(User).filter(User.referred_by == user.id).count(),
                'user_referral_bonuses': db.query(ReferralBonus)
                    .filter(ReferralBonus.referrer_id == user.id)
                    .with_entities(func.sum(ReferralBonus.amount))
                    .scalar() or 0,
                'monthly_income': LEVELS[user.level].monthly_income
            })

            # Расчет рефералов до следующего уровня
            current_level_name = user.level
            levels_list = list(LEVELS.keys())
            current_level_index = levels_list.index(current_level_name)

            referrals_to_next_level = 0
            if current_level_index < len(levels_list) - 1:
                next_level_name = levels_list[current_level_index + 1]
                next_level_required_referrals = LEVELS[next_level_name].required_referrals
                # Убедитесь, что user имеет атрибут referral_count или получите его из БД, если его там нет
                # Исходя из прошлых ошибок, мы уже добавили referral_count в модель User
                user_referral_count = user.referral_count # Используем атрибут модели
                referrals_to_next_level = max(0, next_level_required_referrals - user_referral_count)

            stats['referrals_to_next_level'] = referrals_to_next_level

    return stats

def get_pending_transactions(db: Session) -> list:
    """
    Получает список ожидающих транзакций
    """
    return db.query(Transaction).filter(
        Transaction.status == 'pending'
    ).order_by(Transaction.created_at.desc()).all()

def approve_transaction(db: Session, transaction_id: int) -> bool:
    """
    Подтверждает транзакцию
    """
    try:
        transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not transaction or transaction.status != 'pending':
            return False
        
        transaction.status = 'completed'
        transaction.completed_at = datetime.utcnow()
        
        if transaction.type == 'deposit':
            user = db.query(User).filter(User.id == transaction.user_id).first()
            user.balance += transaction.amount
        
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при подтверждении транзакции: {str(e)}")
        return False

def cancel_transaction(db: Session, transaction_id: int) -> bool:
    """
    Отменяет транзакцию
    """
    try:
        transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not transaction or transaction.status != 'pending':
            return False
        
        transaction.status = 'cancelled'
        transaction.completed_at = datetime.utcnow()
        
        if transaction.type == 'withdraw':
            user = db.query(User).filter(User.id == transaction.user_id).first()
            user.balance += transaction.amount
        
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при отмене транзакции: {str(e)}")
        return False

def get_user_transactions(db: Session, user_id: int, limit: int = 10) -> list:
    """
    Получает последние транзакции пользователя
    """
    return db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).order_by(desc(Transaction.created_at)).limit(limit).all()

def get_user_referrals(db: Session, user_id: int) -> list:
    """
    Получает список рефералов пользователя
    """
    return db.query(User).filter(User.referred_by == user_id).all()

def get_user_upgrades(db: Session, user_id: int) -> list:
    """
    Получает список апгрейдов пользователя
    """
    return db.query(UserUpgrade).filter(UserUpgrade.user_id == user_id).all()

def get_user_achievements(db: Session, user_id: int) -> list:
    """
    Получает список достижений пользователя
    """
    return db.query(UserAchievement).filter(UserAchievement.user_id == user_id).all()

def search_users(db: Session, query: str) -> list:
    """
    Поиск пользователей по username или telegram_id
    """
    try:
        telegram_id = int(query)
        return db.query(User).filter(User.telegram_id == telegram_id).all()
    except ValueError:
        return db.query(User).filter(User.username.ilike(f"%{query}%")).all()

def get_recent_activity(db: Session, days: int = 7) -> dict:
    """
    Получает статистику активности за последние дни
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    return {
        'new_users': db.query(User).filter(User.created_at >= start_date).count(),
        'new_deposits': db.query(Transaction).filter(
            Transaction.type == 'deposit',
            Transaction.created_at >= start_date
        ).count(),
        'total_deposits_amount': db.query(Transaction).filter(
            Transaction.type == 'deposit',
            Transaction.created_at >= start_date
        ).with_entities(func.sum(Transaction.amount)).scalar() or 0,
        'new_withdraws': db.query(Transaction).filter(
            Transaction.type == 'withdraw',
            Transaction.created_at >= start_date
        ).count(),
        'total_withdraws_amount': db.query(Transaction).filter(
            Transaction.type == 'withdraw',
            Transaction.created_at >= start_date
        ).with_entities(func.sum(Transaction.amount)).scalar() or 0
    } 