# scripts/stop_all_services.bat
#!/bin/bash

# Stop all services

echo "🛑 Stopping all services..."

if [ -f ".pids" ]; then
    read FASTAPI_PID WORKER_PID BEAT_PID FLOWER_PID < .pids
    
    echo "Stopping FastAPI (PID: $FASTAPI_PID)..."
    kill $FASTAPI_PID 2>/dev/null
    
    echo "Stopping Celery Worker (PID: $WORKER_PID)..."
    kill $WORKER_PID 2>/dev/null
    
    echo "Stopping Celery Beat (PID: $BEAT_PID)..."
    kill $BEAT_PID 2>/dev/null
    
    echo "Stopping Flower (PID: $FLOWER_PID)..."
    kill $FLOWER_PID 2>/dev/null
    
    rm .pids
    echo "✅ All services stopped"
else
    echo "No .pids file found. Manually killing processes..."
    pkill -f "uvicorn app.main:app"
    pkill -f "celery.*worker"
    pkill -f "celery.*beat"
    pkill -f "celery.*flower"
    echo "✅ Killed all matching processes"
fi