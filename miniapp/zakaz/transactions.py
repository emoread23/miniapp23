from database import get_db, User, Transaction
from config import WITHDRAW_DELAY_MIN, WITHDRAW_DELAY_MAX
from notifications import notify_deposit_confirmed, notify_withdraw_confirmed, notify_withdraw_cancelled
import logging
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

def create_deposit(user: User, amount: float) -> Transaction:
    """Создание депозита"""
    try:
        db = next(get_db())
        
        # Создаем транзакцию
        transaction = Transaction(
            user_id=user.id,
            type='deposit',
            amount=amount,
            status='pending'
        )
        db.add(transaction)
        db.commit()
        
        logger.info(f"Создан депозит для пользователя {user.id}: {amount} USDT")
        return transaction
        
    except Exception as e:
        logger.error(f"Ошибка при создании депозита: {e}")
        return None

def create_withdraw(user: User, amount: float, wallet_address: str) -> Transaction:
    """Создание вывода средств"""
    try:
        db = next(get_db())
        
        # Проверяем баланс
        if user.balance < amount:
            return None
        
        # Создаем транзакцию
        transaction = Transaction(
            user_id=user.id,
            type='withdraw',
            amount=amount,
            status='pending',
            wallet_address=wallet_address
        )
        db.add(transaction)
        
        # Резервируем средства
        user.balance -= amount
        
        db.commit()
        
        logger.info(f"Создан вывод средств для пользователя {user.id}: {amount} USDT")
        return transaction
        
    except Exception as e:
        logger.error(f"Ошибка при создании вывода средств: {e}")
        return None

def confirm_transaction(transaction: Transaction) -> bool:
    """Подтверждение транзакции"""
    try:
        db = next(get_db())
        
        # Обновляем статус транзакции
        transaction.status = 'completed'
        transaction.completed_at = datetime.utcnow()
        
        # Обновляем статистику пользователя
        user = transaction.user
        if transaction.type == 'deposit':
            user.total_deposit += transaction.amount
            user.balance += transaction.amount
            notify_deposit_confirmed(user, transaction.amount)
        elif transaction.type == 'withdraw':
            user.total_withdraw += transaction.amount
            notify_withdraw_confirmed(user, transaction.amount)
        
        db.commit()
        
        logger.info(f"Подтверждена транзакция {transaction.id}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при подтверждении транзакции: {e}")
        return False

def cancel_transaction(transaction: Transaction) -> bool:
    """Отмена транзакции"""
    try:
        db = next(get_db())
        
        # Обновляем статус транзакции
        transaction.status = 'cancelled'
        transaction.completed_at = datetime.utcnow()
        
        # Возвращаем средства при отмене вывода
        if transaction.type == 'withdraw':
            user = transaction.user
            user.balance += transaction.amount
            notify_withdraw_cancelled(user, transaction.amount)
        
        db.commit()
        
        logger.info(f"Отменена транзакция {transaction.id}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при отмене транзакции: {e}")
        return False

def get_pending_transactions() -> list:
    """Получение ожидающих транзакций"""
    try:
        db = next(get_db())
        
        # Получаем все ожидающие транзакции
        transactions = db.query(Transaction).filter(
            Transaction.status == 'pending'
        ).all()
        
        return transactions
        
    except Exception as e:
        logger.error(f"Ошибка при получении ожидающих транзакций: {e}")
        return []

def get_user_transactions(user: User, limit: int = 10) -> list:
    """Получение транзакций пользователя"""
    try:
        db = next(get_db())
        
        # Получаем последние транзакции пользователя
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user.id
        ).order_by(Transaction.created_at.desc()).limit(limit).all()
        
        return transactions
        
    except Exception as e:
        logger.error(f"Ошибка при получении транзакций пользователя: {e}")
        return []

def format_transaction_info(transaction: Transaction) -> str:
    """Форматирование информации о транзакции"""
    text = f"💸 Транзакция #{transaction.id}\n\n"
    
    if transaction.type == 'deposit':
        text += f"📥 Депозит: {transaction.amount} USDT\n"
    elif transaction.type == 'withdraw':
        text += f"📤 Вывод: {transaction.amount} USDT\n"
        text += f"💳 Кошелек: {transaction.wallet_address}\n"
    elif transaction.type == 'income':
        text += f"💰 Доход: {transaction.amount} USDT\n"
    
    text += f"📅 Дата: {transaction.created_at.strftime('%d.%m.%Y %H:%M')}\n"
    text += f"📊 Статус: {transaction.status}"
    
    if transaction.completed_at:
        text += f"\n✅ Завершено: {transaction.completed_at.strftime('%d.%m.%Y %H:%M')}"
    
    return text

def format_transactions_list(transactions: list) -> str:
    """Форматирование списка транзакций"""
    text = "💸 История транзакций\n\n"
    
    if not transactions:
        text += "😔 У вас пока нет транзакций"
        return text
    
    for transaction in transactions:
        if transaction.type == 'deposit':
            text += f"📥 Депозит: {transaction.amount} USDT"
        elif transaction.type == 'withdraw':
            text += f"📤 Вывод: {transaction.amount} USDT"
        elif transaction.type == 'income':
            text += f"💰 Доход: {transaction.amount} USDT"
        
        text += f" - {transaction.created_at.strftime('%d.%m.%Y')}\n"
    
    return text

def get_withdraw_delay() -> int:
    """Получение случайной задержки для вывода"""
    return random.randint(WITHDRAW_DELAY_MIN, WITHDRAW_DELAY_MAX) 