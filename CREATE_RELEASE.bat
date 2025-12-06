@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul

echo ============================================
echo   Создание релиза Playerok Cardinal
echo ============================================
echo.

:: Проверяем git репозиторий
git rev-parse --git-dir >nul 2>&1
if errorlevel 1 (
    echo [INFO] Инициализация git репозитория...
    git init
    git branch -M main
    echo [OK] Git репозиторий инициализирован
    echo.
    echo [WARNING] Настройте удаленный репозиторий:
    echo    git remote add origin https://github.com/KITUSTTT/PlayerokCardinal.git
    echo.
)

:: Извлекаем версию из main.py
set VERSION=
for /f "tokens=*" %%a in ('findstr /c:"VERSION = " main.py') do (
    set "LINE=%%a"
    for /f "tokens=2 delims=^=" %%b in ("!LINE!") do (
        set "VERSION=%%b"
        set "VERSION=!VERSION: =!"
        set "VERSION=!VERSION:"=!"
    )
)

if "!VERSION!"=="" (
    echo [ERROR] Не удалось определить версию из main.py
    echo Убедитесь, что в main.py есть: VERSION = "1.0.0"
    echo.
    echo Нажмите любую клавишу для выхода...
    pause
    exit /b 1
)

echo [INFO] Текущая версия: !VERSION!
echo.

:: Показываем статус
echo [INFO] Статус репозитория:
git status --short
echo.

:: Удаляем старый тег, если существует
git tag -l v!VERSION! >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Тег v!VERSION! уже существует, удаляю...
    git tag -d v!VERSION! >nul 2>&1
    git push origin :refs/tags/v!VERSION! >nul 2>&1
    echo [OK] Старый тег удален
)

:: Добавляем все файлы
echo.
echo [INFO] Добавление всех изменений...
git add .

:: Создаем коммит
echo [INFO] Создание коммита...
git commit -m "Release v!VERSION!" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Нет изменений для коммита
) else (
    echo [OK] Коммит создан
)

:: Создаем тег
echo.
echo [INFO] Создание тега v!VERSION!...
git tag -a v!VERSION! -m "Playerok Cardinal v!VERSION!" -f
if errorlevel 1 (
    echo [ERROR] Ошибка при создании тега
    echo.
    echo Нажмите любую клавишу для выхода...
    pause
    exit /b 1
)
echo [OK] Тег создан

:: Отправляем в GitHub
echo.
echo [INFO] Отправка в GitHub...
git push origin main
if errorlevel 1 (
    echo [ERROR] Ошибка при отправке в main
    echo Проверьте: git remote -v
    echo.
    echo Нажмите любую клавишу для выхода...
    pause
    exit /b 1
)
echo [OK] Изменения отправлены в main

git push origin v!VERSION! --force
if errorlevel 1 (
    echo [ERROR] Ошибка при отправке тега
    echo Проверьте: git remote -v
    echo.
    echo Нажмите любую клавишу для выхода...
    pause
    exit /b 1
)
echo [OK] Тег v!VERSION! отправлен

echo.
echo ============================================
echo [OK] Готово!
echo ============================================
echo.
echo Следующие шаги:
echo 1. Перейдите: https://github.com/KITUSTTT/PlayerokCardinal/releases/new
echo 2. Выберите тег: v!VERSION!
echo 3. Заголовок: Playerok Cardinal v!VERSION!
echo 4. Описание: Скопируйте из CHANGELOG.md
echo 5. Нажмите "Publish release"
echo.
echo.
echo Нажмите любую клавишу для выхода...
pause
