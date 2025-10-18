echo "🌸 Starting Flower Monitoring Dashboard..."

if [ -d "venv" ]; then
    source venv/bin/activate
fi

export PYTHONPATH="${PYTHONPATH}:$(pwd)"

celery -A app.core.celery_app flower \
    --port=5555 \
    --broker=redis://localhost:6379/0 \
    --url_prefix=flower

# Access dashboard at: http://localhost:5555