@echo off
echo 🎓 StudyMate AI - Starting...
echo ================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Run StudyMate startup script
python start_studymate.py

pause