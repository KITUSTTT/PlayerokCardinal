@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

echo ============================================
echo   Creating Playerok Cardinal Release
echo ============================================
echo.

:: Check git repository
git rev-parse --git-dir >nul 2>&1
if errorlevel 1 (
    echo [INFO] Initializing git repository...
    git init
    git branch -M main
    echo [OK] Git repository initialized
    echo.
    echo [WARNING] Configure remote repository:
    echo    git remote add origin https://github.com/KITUSTTT/PlayerokCardinal.git
    echo.
)

:: Get version from main.py using Python script
set VERSION=
for /f "delims=" %%a in ('python get_version.py') do set "VERSION=%%a"

if "!VERSION!"=="" (
    echo [ERROR] Failed to get version from main.py
    echo Make sure main.py contains: VERSION = "1.0.0"
    echo.
    pause
    exit /b 1
)

echo [INFO] Current version: !VERSION!
echo.

:: Show status
echo [INFO] Repository status:
git status --short
echo.

:: Delete old tag if exists
git tag -l v!VERSION! >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Tag v!VERSION! already exists, deleting...
    git tag -d v!VERSION! >nul 2>&1
    git push origin :refs/tags/v!VERSION! >nul 2>&1
    echo [OK] Old tag deleted
)

:: Add all files
echo.
echo [INFO] Adding all changes...
git add .

:: Create commit
echo [INFO] Creating commit...
git commit -m "Release v!VERSION!" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] No changes to commit
) else (
    echo [OK] Commit created
)

:: Create tag
echo.
echo [INFO] Creating tag v!VERSION!...
git tag -a v!VERSION! -m "Playerok Cardinal v!VERSION!" -f
if errorlevel 1 (
    echo [ERROR] Failed to create tag
    echo.
    pause
    exit /b 1
)
echo [OK] Tag created

:: Push to GitHub
echo.
echo [INFO] Pushing to GitHub...
git push origin main
if errorlevel 1 (
    echo [ERROR] Failed to push to main
    echo Check: git remote -v
    echo.
    pause
    exit /b 1
)
echo [OK] Changes pushed to main

git push origin v!VERSION! --force
if errorlevel 1 (
    echo [ERROR] Failed to push tag
    echo Check: git remote -v
    echo.
    pause
    exit /b 1
)
echo [OK] Tag v!VERSION! pushed

echo.
echo ============================================
echo [OK] Done!
echo ============================================
echo.
echo Next steps:
echo 1. Go to: https://github.com/KITUSTTT/PlayerokCardinal/releases/new
echo 2. Select tag: v!VERSION!
echo 3. Title: Playerok Cardinal v!VERSION!
echo 4. Description: Copy from CHANGELOG.md if available
echo 5. Click Publish release
echo.
echo.
pause
