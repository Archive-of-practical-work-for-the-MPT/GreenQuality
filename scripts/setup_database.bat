@echo off
REM Запуск создания и заполнения БД GreenQuality
REM Запускать из корня проекта: scripts\setup_database.bat

cd /d "%~dp0.."
python scripts\setup_database.py %*
pause
