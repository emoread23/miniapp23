# Crypto Empire Quest - Telegram Mini App

## Описание
Мини-приложение для Telegram, реализующее игру "Crypto Empire Quest" с системой уровней, реферальной программой и возможностью вывода средств.

## Установка и настройка

### Локальная разработка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте файл `.env` в корневой директории проекта со следующими переменными:
```
DATABASE_URL=sqlite:///game.db  # Для локальной разработки
# или
DATABASE_URL=postgresql://user:password@host:port/dbname  # Для продакшена
```

3. Инициализируйте базу данных и создайте начальные уровни:
```bash
python init_levels.py
```

4. Запустите приложение:
```bash
python webapp.py
```

### Деплой на Vercel

1. Создайте новый проект на Vercel и подключите ваш Git репозиторий.

2. В настройках проекта на Vercel добавьте следующие переменные окружения:
   - `DATABASE_URL` - URL вашей базы данных PostgreSQL
   - `BOT_TOKEN` - токен вашего Telegram бота

3. В настройках проекта на Vercel установите:
   - Build Command: `pip install -r requirements.txt`
   - Output Directory: `.`
   - Install Command: `pip install -r requirements.txt`
   - Root Directory: `miniapp/zakaz`

4. После деплоя выполните инициализацию уровней через консоль Vercel:
```bash
python init_levels.py
```

## API Endpoints

### Пользователи
- `GET /api/user/<telegram_id>` - Получить информацию о пользователе
- `POST /api/register` - Регистрация нового пользователя
  ```json
  {
    "telegram_id": 123456789,
    "username": "user123",
    "referral_code": "optional_referral_code"
  }
  ```

### Игровые действия
- `POST /api/action` - Выполнить игровое действие
  ```json
  {
    "telegram_id": 123456789,
    "action_type": "click"
  }
  ```

### Бонусы
- `POST /api/daily-bonus` - Получить ежедневный бонус
  ```json
  {
    "telegram_id": 123456789
  }
  ```

### Реферальная система
- `GET /api/referral-info/<telegram_id>` - Получить информацию о рефералах

### Вывод средств
- `POST /api/withdraw` - Запросить вывод средств
  ```json
  {
    "telegram_id": 123456789,
    "amount": 1.0
  }
  ```

### Уровни
- `GET /api/levels` - Получить список всех уровней

## Игровая механика

### Начисление опыта и наград
- За каждый клик: +1 XP, +0.01 USDT
- Ежедневный бонус: +0.1 USDT
- Реферальный бонус: 5% от заработка реферала

### Уровни
- Всего 20 уровней
- Награды за уровни растут с каждым уровнем
- Требуемый опыт для следующего уровня увеличивается

### Вывод средств
- Минимальная сумма вывода: 1.0 USDT
- Вывод осуществляется в USDT (TRC20)

## Безопасность
- Все транзакции логируются
- Проверка минимальной суммы вывода
- Проверка баланса перед выводом
- Защита от повторного получения ежедневного бонуса 