from webapp.database import init_db_standalone
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("Инициализация базы данных...")
        init_db_standalone()
        
        # Проверяем подключение (опционально, можно убрать)
        # Если нужно проверить, то нужно использовать get_session и next()
        # Но init_db_standalone уже сама добавляет тестового пользователя
        # Простая проверка на существование тестового пользователя
        # from webapp.database import get_session, User
        # db = next(get_session())
        # test_user = db.query(User).filter(User.telegram_id == 123456).first()
        # if test_user:
        #     logger.info("Тестовый пользователь создан")
        # else:
        #     logger.error("Тестовый пользователь не создан")
        # db.close()

        logger.info("База данных успешно инициализирована")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        raise

if __name__ == '__main__':
    main() 