# Используем базовый образ Python 3.10
FROM python:3.10-slim

# Устанавливаем supervisord и другие необходимые зависимости на уровне ОС
RUN apt-get update && apt-get install -y --no-install-recommends \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем переменные окружения
ENV PYTHONUNBUFFERED 1

# Создаем директорию для приложения
WORKDIR /app

# Копируем requirements.txt и устанавливаем зависимости Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . /app

# Копируем файл конфигурации supervisord
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Указываем команду для запуска supervisord при старте контейнера
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"] 