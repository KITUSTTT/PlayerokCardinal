@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
echo ============================================
echo   Создание релиза Playerok Cardinal
echo ============================================
echo.

:: Проверяем, что мы в git репозитории
git rev-parse --git-dir >nul 2>&1
if errorlevel 1 (
    echo 📝 Инициализация git репозитория...
    git init
    git branch -M main
    echo ✅ Git репозиторий инициализирован
    echo.
    echo ⚠️  ВНИМАНИЕ: Необходимо настроить удаленный репозиторий!
    echo    Выполните: git remote add origin https://github.com/KITUSTTT/PlayerokCardinal.git
    echo.
)

:: Получаем текущую версию из main.py
set VERSION=
for /f "tokens=*" %%a in ('findstr /c:"VERSION = " main.py') do (
    set "LINE=%%a"
    set "LINE=!LINE:VERSION =!"
    set "LINE=!LINE: =!"
    set "LINE=!LINE:"=!"
    set "LINE=!LINE:==!"
    set "VERSION=!LINE!"
)
if "!VERSION!"=="" (
    echo ❌ Ошибка: не удалось определить версию из main.py
    echo    Убедитесь, что в main.py есть строка: VERSION = "1.0.0"
    pause
    exit /b 1
)
echo 📌 Текущая версия: !VERSION!
echo.

:: Проверяем, есть ли изменения
echo 📋 Статус репозитория:
git status --short
echo.

:: Проверяем, существует ли уже тег
git tag -l v!VERSION! >nul 2>&1
if not errorlevel 1 (
    echo ⚠️  Тег v!VERSION! уже существует, перезаписываю...
    git tag -d v!VERSION! >nul 2>&1
    git push origin :refs/tags/v!VERSION! >nul 2>&1
    echo ✅ Старый тег удален
)

echo.
echo 📝 Добавление всех изменений...
git add .

echo 💾 Создание коммита...
git commit -m "Release v!VERSION!" --quiet
if errorlevel 1 (
    echo ⚠️  Нет изменений для коммита или коммит не создан
) else (
    echo ✅ Коммит создан
)

echo 🏷️ Создание тега v!VERSION!...
git tag -a v!VERSION! -m "Playerok Cardinal v!VERSION!" -f
if errorlevel 1 (
    echo ❌ Ошибка при создании тега
    pause
    exit /b 1
)
echo ✅ Тег создан

echo.
echo 📤 Отправка в GitHub...
git push origin main --quiet
if errorlevel 1 (
    echo ⚠️  Ошибка при отправке в main
    echo    Проверьте настройки удаленного репозитория: git remote -v
) else (
    echo ✅ Изменения отправлены в main
)

git push origin v!VERSION! --force --quiet
if errorlevel 1 (
    echo ⚠️  Ошибка при отправке тега
    echo    Проверьте настройки удаленного репозитория: git remote -v
) else (
    echo ✅ Тег v!VERSION! отправлен
)

echo.
echo ✅ Готово!
echo.
echo 📋 Следующие шаги для создания релиза на GitHub:
echo    1. Перейдите на: https://github.com/KITUSTTT/PlayerokCardinal/releases/new
echo    2. Выберите тег: v!VERSION!
echo    3. Заголовок: Playerok Cardinal v!VERSION!
echo    4. Описание: Скопируйте содержимое из CHANGELOG.md
echo    5. Нажмите "Publish release"
echo.
echo 💡 После создания релиза пользователи смогут обновиться командой /update
echo.

pause

