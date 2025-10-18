@echo off
REM scripts/start_celery_beat.bat

echo Starting Celery Beat Scheduler...

IF EXIST venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

set PYTHONPATH=%CD%;%PYTHONPATH%

celery -A app.core.celery_app beat ^
    --loglevel=info ^
    --scheduler=celery.beat.PersistentScheduler

pause