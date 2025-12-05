@echo off
title Upload to GitHub

echo ========================================
echo  Uploading PlayerokCardinal to GitHub
echo ========================================
echo.

echo [1/6] Initializing git...
git init
if errorlevel 1 (
    echo ERROR: git not found!
    pause
    exit /b 1
)
echo.

echo [2/6] Adding all files...
git add .
echo.

echo [3/6] Creating commit...
git commit -m "Initial commit: PlayerokCardinal v1.0.0 - Clean version"
echo.

echo [4/6] Setting branch to main...
git branch -M main
echo.

echo [5/6] Adding remote...
git remote add origin https://github.com/KITUSTTT/PlayerokCardinal.git
echo.

echo [6/6] Pushing to GitHub...
git push -u origin main --force
echo.

echo ========================================
echo  Upload completed!
echo ========================================
echo.
pause

