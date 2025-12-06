@echo off
chcp 65001 > nul
echo ============================================
echo   Создание релиза Playerok Cardinal
echo ============================================
echo.

:: Проверяем, что мы в git репозитории
git rev-parse --git-dir >nul 2>&1
if errorlevel 1 (
    echo ❌ Ошибка: это не git репозиторий!
    echo    Сначала инициализируйте git: git init
    pause
    exit /b 1
)

:: Получаем текущую версию из main.py
for /f "tokens=3 delims== """ %%i in ('findstr /c:"VERSION = " main.py') do set VERSION=%%i
echo 📌 Текущая версия: %VERSION%
echo.

:: Проверяем, есть ли изменения
git status --short
echo.

:: Спрашиваем подтверждение
set /p CONFIRM="❓ Создать тег v%VERSION% и опубликовать? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo ❌ Отменено
    pause
    exit /b 0
)

echo.
echo 📝 Добавление всех изменений...
git add .

echo 💾 Создание коммита...
git commit -m "Release v%VERSION%"

echo 🏷️ Создание тега v%VERSION%...
git tag -a v%VERSION% -m "Playerok Cardinal v%VERSION%"

echo 📤 Отправка в GitHub...
git push origin main
git push origin v%VERSION%

echo.
echo ✅ Готово!
echo.
echo 📋 Следующие шаги:
echo    1. Перейдите на https://github.com/KITUSTTT/PlayerokCardinal/releases/new
echo    2. Выберите тег v%VERSION%
echo    3. Заполните описание релиза (можно взять из CHANGELOG.md)
echo    4. Нажмите "Publish release"
echo.

pause

