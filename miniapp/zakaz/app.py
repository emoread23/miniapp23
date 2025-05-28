from webapp.app import app
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("Запуск приложения...")
    app.run(debug=True, host='0.0.0.0', port=5000) 