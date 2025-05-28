from flask import Flask, request, jsonify
from database import get_db, User, Transaction, UserUpgrade, UserAchievement
from config import WEBAPP_URL
import logging
import json

app = Flask(__name__)
logger = logging.getLogger(__name__)

@app.route('/api/user', methods=['GET'])
def get_user():
    """Получение информации о пользователе"""
    try:
        # Получаем данные из запроса
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({'error': 'Missing user_id'}), 400
        
        # Получаем пользователя
        db = next(get_db())
        user = db.query(User).filter(User.id == data['user_id']).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Формируем ответ
        response = {
            'id': user.id,
            'username': user.username,
            'level': user.level,
            'balance': user.balance,
            'total_deposit': user.total_deposit,
            'total_withdraw': user.total_withdraw,
            'referral_count': user.referral_count,
            'referral_earnings': user.referral_earnings,
            'created_at': user.created_at.isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Ошибка при получении информации о пользователе: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """Получение транзакций пользователя"""
    try:
        # Получаем данные из запроса
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({'error': 'Missing user_id'}), 400
        
        # Получаем транзакции
        db = next(get_db())
        transactions = db.query(Transaction).filter(
            Transaction.user_id == data['user_id']
        ).order_by(Transaction.created_at.desc()).limit(10).all()
        
        # Формируем ответ
        response = []
        for transaction in transactions:
            response.append({
                'id': transaction.id,
                'type': transaction.type,
                'amount': transaction.amount,
                'status': transaction.status,
                'created_at': transaction.created_at.isoformat(),
                'completed_at': transaction.completed_at.isoformat() if transaction.completed_at else None
            })
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Ошибка при получении транзакций: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/upgrades', methods=['GET'])
def get_upgrades():
    """Получение апгрейдов пользователя"""
    try:
        # Получаем данные из запроса
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({'error': 'Missing user_id'}), 400
        
        # Получаем апгрейды
        db = next(get_db())
        upgrades = db.query(UserUpgrade).filter(
            UserUpgrade.user_id == data['user_id']
        ).all()
        
        # Формируем ответ
        response = []
        for upgrade in upgrades:
            response.append({
                'id': upgrade.upgrade_id,
                'level': upgrade.level,
                'is_active': upgrade.is_active,
                'created_at': upgrade.created_at.isoformat()
            })
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Ошибка при получении апгрейдов: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/achievements', methods=['GET'])
def get_achievements():
    """Получение достижений пользователя"""
    try:
        # Получаем данные из запроса
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({'error': 'Missing user_id'}), 400
        
        # Получаем достижения
        db = next(get_db())
        achievements = db.query(UserAchievement).filter(
            UserAchievement.user_id == data['user_id']
        ).all()
        
        # Формируем ответ
        response = []
        for achievement in achievements:
            response.append({
                'id': achievement.achievement_id,
                'created_at': achievement.created_at.isoformat()
            })
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Ошибка при получении достижений: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/deposit', methods=['POST'])
def create_deposit():
    """Создание депозита"""
    try:
        # Получаем данные из запроса
        data = request.get_json()
        if not data or 'user_id' not in data or 'amount' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Получаем пользователя
        db = next(get_db())
        user = db.query(User).filter(User.id == data['user_id']).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Создаем транзакцию
        transaction = Transaction(
            user_id=user.id,
            type='deposit',
            amount=data['amount'],
            status='pending'
        )
        db.add(transaction)
        db.commit()
        
        return jsonify({
            'id': transaction.id,
            'amount': transaction.amount,
            'status': transaction.status
        })
        
    except Exception as e:
        logger.error(f"Ошибка при создании депозита: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/withdraw', methods=['POST'])
def create_withdraw():
    """Создание вывода средств"""
    try:
        # Получаем данные из запроса
        data = request.get_json()
        if not data or 'user_id' not in data or 'amount' not in data or 'wallet_address' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Получаем пользователя
        db = next(get_db())
        user = db.query(User).filter(User.id == data['user_id']).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Проверяем баланс
        if user.balance < data['amount']:
            return jsonify({'error': 'Insufficient balance'}), 400
        
        # Создаем транзакцию
        transaction = Transaction(
            user_id=user.id,
            type='withdraw',
            amount=data['amount'],
            status='pending',
            wallet_address=data['wallet_address']
        )
        db.add(transaction)
        
        # Резервируем средства
        user.balance -= data['amount']
        
        db.commit()
        
        return jsonify({
            'id': transaction.id,
            'amount': transaction.amount,
            'status': transaction.status
        })
        
    except Exception as e:
        logger.error(f"Ошибка при создании вывода средств: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 