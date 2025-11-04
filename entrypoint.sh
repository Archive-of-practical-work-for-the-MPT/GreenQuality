#!/bin/bash

# Переход в директорию с manage.py
cd /app/greenquality

# Ждем готовности базы данных
echo "Ждем готовности базы данных..."
while ! pg_isready -h db -p 5432 -U postgres > /dev/null 2> /dev/null; do
    sleep 1
done

echo "База данных готова."

# Выполнить миграции
# python manage.py makemigrations --noinput

# Применить миграции
# python manage.py migrate --noinput

# Запустить сервер разработки
python manage.py runserver 0.0.0.0:8000