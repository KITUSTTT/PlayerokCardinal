@echo off
title PlayerokCardinal Setup

echo ========================================
echo  PlayerokCardinal - Setup
echo ========================================
echo.

echo [1/3] Checking Python...
python --version
if errorlevel 1 (
    echo.
    echo ERROR: Python not found!
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo OK
echo.

echo [2/3] Upgrading pip...
python -m pip install --upgrade pip
echo.

echo [3/3] Installing ALL dependencies...
python -m pip install --upgrade psutil>=5.9.4
python -m pip install --upgrade beautifulsoup4>=4.12.3
python -m pip install --upgrade colorama>=0.4.6
python -m pip install --upgrade requests==2.32.3
python -m pip install --upgrade pytelegrambotapi==4.15.2
python -m pip install --upgrade pillow>=9.3.0
python -m pip install --upgrade requests_toolbelt==0.10.1
python -m pip install --upgrade lxml>=5.2.2
python -m pip install --upgrade bcrypt>=4.2.0
python -m pip install --upgrade curl-cffi>=0.13.0
python -m pip install --upgrade validators>=0.34.0
python -m pip install --upgrade asyncio>=3.4.3
python -m pip install --upgrade aiogram>=3.10.0
python -m pip install --upgrade colorlog>=6.9.0
python -m pip install --upgrade tqdm>=4.67.1
echo.

echo ========================================
echo  Setup completed successfully!
echo ========================================
echo.
echo Now run Start.bat
echo.
pause
