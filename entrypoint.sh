#!/bin/bash

# Переход в директорию с manage.py
cd /app/greenquality

# Выполнить миграции
python manage.py makemigrations --noinput

# Применить миграции
python manage.py migrate --noinput

# Запустить сервер разработки
python manage.py runserver 0.0.0.0:8000