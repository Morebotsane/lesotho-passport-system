@echo off
REM Lesotho Passport System - Celery Worker Startup Script

echo ========================================
echo Starting Celery Worker
echo ========================================

IF EXIST venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) ELSE (
    echo ERROR: Virtual environment not found!
    pause
    exit /b 1
)

set PYTHONPATH=%CD%;%PYTHONPATH%

echo Starting Celery worker for notifications...
echo.
celery -A app.core.celery_app worker --loglevel=info --concurrency=4 --pool=solo --queues=notifications

pause
