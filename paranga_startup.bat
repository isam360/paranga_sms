@echo off
title Paranga SMS - Auto Server Startup
setlocal enabledelayedexpansion

REM === CONFIGURATION ===
set PROJECT_DIR=C:\Users\is-haka\Desktop\paranga_sms
set VENV_DIR=%PROJECT_DIR%\.env
set HOST=127.0.0.1
set PORT=8000
set WAIT_TIME=7
set BROWSER=default
REM Options for BROWSER: default, chrome, edge


REM === NAVIGATE TO PROJECT ===
echo Starting Paranga SMS...
cd /d "%PROJECT_DIR%" || (
    echo [ERROR] Could not find project directory: %PROJECT_DIR%
    pause
    exit /b 1
)


REM === ACTIVATE VIRTUAL ENVIRONMENT ===
if exist "%VENV_DIR%\Scripts\activate" (
    call "%VENV_DIR%\Scripts\activate"
) else (
    echo [ERROR] Virtual environment not found at %VENV_DIR%
    pause
    exit /b 1
)


REM === START DJANGO SERVER IN BACKGROUND ===
echo Launching Django development server...
start "Django Server" cmd /c "python manage.py runserver %HOST%:%PORT%"
if errorlevel 1 (
    echo [ERROR] Failed to start Django server.
    pause
    exit /b 1
)


REM === WAIT FOR SERVER TO INITIALIZE ===
echo Waiting %WAIT_TIME% seconds for server to initialize...
timeout /t %WAIT_TIME% /nobreak >nul


REM === OPEN BROWSER ===
echo Opening application in browser...
if /I "%BROWSER%"=="chrome" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" http://%HOST%:%PORT%/
) else if /I "%BROWSER%"=="edge" (
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" http://%HOST%:%PORT%/
) else (
    start "" http://%HOST%:%PORT%/
)


echo Server is running at: http://%HOST%:%PORT%/
echo You can close this window. The Django server is running in a separate window.
exit /b 0
