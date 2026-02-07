#!/usr/bin/env python
"""
Скрипт создания и заполнения базы данных GreenQuality.

Использование:
    python scripts/setup_database.py                 # создать БД, таблицы + заполнить данными
    python scripts/setup_database.py --create        # только создать таблицы
    python scripts/setup_database.py --seed          # только заполнить данными
    python scripts/setup_database.py --init-db       # только создать БД, если не существует
    python scripts/setup_database.py --fake-migrate  # пометить миграции Django как применённые

Запускать из корня проекта (GreenQuality). Требуется .env с настройками DB_*.
После создания таблиц скриптом рекомендовано: python manage.py migrate
(создаст таблицы Django: auth, sessions и т.д.)
"""

import argparse
import os
import sys
from pathlib import Path

# Добавляем Django-проект в путь (папка с manage.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DJANGO_PROJECT = PROJECT_ROOT / 'greenquality'
sys.path.insert(0, str(DJANGO_PROJECT))

# Загружаем .env до импорта Django
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')

# Настройки Django для получения конфига БД
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greenquality.settings')

import django
django.setup()

from django.conf import settings
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def get_db_config():
    """Получить параметры подключения к БД из Django settings."""
    db = settings.DATABASES['default']
    return {
        'dbname': db['NAME'],
        'user': db['USER'],
        'password': db['PASSWORD'],
        'host': db.get('HOST', 'localhost'),
        'port': db.get('PORT', '5432'),
    }


def create_database_if_not_exists(config):
    """Создать базу данных, если она не существует."""
    conn_config = config.copy()
    conn_config['dbname'] = 'postgres'  # подключаемся к служебной БД
    try:
        conn = psycopg2.connect(**conn_config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute(
            sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"),
            [config['dbname']]
        )
        if not cur.fetchone():
            cur.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(config['dbname'])
            ))
            print(f"  ✓ База данных '{config['dbname']}' создана")
        else:
            print(f"  - База данных '{config['dbname']}' уже существует")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"  ✗ Ошибка при создании БД: {e}")
        raise


def run_sql_file(conn, filepath, description):
    """Выполнить SQL-файл."""
    path = Path(__file__).parent / filepath
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    with conn.cursor() as cur:
        cur.execute(content)
    print(f"  ✓ {description}")


def main():
    parser = argparse.ArgumentParser(
        description='Создание и заполнение БД GreenQuality'
    )
    parser.add_argument(
        '--create',
        action='store_true',
        help='Только создать таблицы (create_tables.sql)'
    )
    parser.add_argument(
        '--seed',
        action='store_true',
        help='Только заполнить данными (insert_initial_data.sql)'
    )
    parser.add_argument(
        '--init-db',
        action='store_true',
        help='Создать базу данных, если не существует'
    )
    parser.add_argument(
        '--fake-migrate',
        action='store_true',
        help='Пометить миграции airline как применённые (после создания таблиц скриптом)'
    )
    args = parser.parse_args()

    # Если не указаны флаги — делаем всё (кроме fake-migrate)
    do_all = not (args.create or args.seed or args.init_db or args.fake_migrate)

    config = get_db_config()
    print("Подключение к PostgreSQL...")

    try:
        if args.init_db or do_all:
            print("\n[1/3] Проверка базы данных...")
            create_database_if_not_exists(config)

        conn = psycopg2.connect(**config)

        if args.create or do_all:
            step = "[2/5]" if do_all else "[1/3]"
            print(f"\n{step} Создание таблиц (create_tables.sql)...")
            run_sql_file(conn, 'create_tables.sql', 'Таблицы созданы')
            conn.commit()

        if args.create or do_all:
            step = "[3/5]" if do_all else "[2/3]"
            print(f"\n{step} Создание триггеров (triggers.sql)...")
            run_sql_file(conn, 'triggers.sql', 'Триггеры созданы')
            conn.commit()

        if args.create or do_all:
            step = "[4/5]" if do_all else "[3/3]"
            print(f"\n{step} Создание процедур и представлений (procedures_views.sql)...")
            run_sql_file(conn, 'procedures_views.sql', 'Процедуры и представления созданы')
            conn.commit()

        if args.seed or do_all:
            if args.seed and not do_all:
                print(f"\n[1/3] Создание триггеров (triggers.sql)...")
                run_sql_file(conn, 'triggers.sql', 'Триггеры созданы')
                conn.commit()
                print(f"\n[2/3] Создание процедур и представлений (procedures_views.sql)...")
                run_sql_file(conn, 'procedures_views.sql', 'Процедуры и представления созданы')
                conn.commit()
            step = "[5/5]" if do_all else "[3/3]"
            print(f"\n{step} Заполнение начальными данными (insert_initial_data.sql)...")
            run_sql_file(conn, 'insert_initial_data.sql', 'Данные загружены')
            conn.commit()

        conn.close()

        if args.fake_migrate:
            print("\n[4/4] Пометка миграций как применённых...")
            from django.core.management import call_command
            call_command('migrate', 'airline', '--fake')
            print("  ✓ Миграции airline помечены как применённые")

        print("\n✓ Готово!")

    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
