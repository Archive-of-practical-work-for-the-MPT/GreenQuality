FROM python:3.13.9-slim

# Установка необходимых пакетов для PostgreSQL
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копируем зависимости
COPY requirements.txt /app/

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем Bash-скрипт в контейнер
COPY entrypoint.sh /app/entrypoint.sh

# Делаем Bash-скрипт исполняемым
RUN chmod +x /app/entrypoint.sh

# Копирование проекта
COPY . /app/

# Инструкция для порта
EXPOSE 8000

# Команда для запуска приложения
CMD ["/app/entrypoint.sh"]