echo "🚀 Starting ALL Lesotho Passport System Services..."

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running. Starting Redis..."
    redis-server --daemonize yes
    sleep 2
fi

echo "✅ Redis is running"

# Start services in background with process management
echo "Starting FastAPI server..."
uvicorn app.main:app --reload --port 8000 > logs/fastapi.log 2>&1 &
FASTAPI_PID=$!
echo "FastAPI PID: $FASTAPI_PID"

sleep 3

echo "Starting Celery Worker..."
celery -A app.core.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --queues=notifications \
    > logs/celery_worker.log 2>&1 &
WORKER_PID=$!
echo "Celery Worker PID: $WORKER_PID"

sleep 2

echo "Starting Celery Beat Scheduler..."
celery -A app.core.celery_app beat \
    --loglevel=info \
    > logs/celery_beat.log 2>&1 &
BEAT_PID=$!
echo "Celery Beat PID: $BEAT_PID"

sleep 2

echo "Starting Flower Monitoring..."
celery -A app.core.celery_app flower \
    --port=5555 \
    > logs/flower.log 2>&1 &
FLOWER_PID=$!
echo "Flower PID: $FLOWER_PID"

echo ""
echo "✅ All services started successfully!"
echo ""
echo "Service URLs:"
echo "  📱 FastAPI:  http://localhost:8000"
echo "  📚 API Docs: http://localhost:8000/docs"
echo "  🌸 Flower:   http://localhost:5555"
echo ""
echo "Process IDs saved to .pids file"
echo "$FASTAPI_PID $WORKER_PID $BEAT_PID $FLOWER_PID" > .pids

echo ""
echo "To stop all services, run: ./scripts/stop_all_services.sh"