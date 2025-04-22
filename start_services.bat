@echo off
echo Starting services using WSL...

echo Starting Redis...
wsl docker-compose up -d

echo Starting Celery worker...
start cmd /k "wsl cd /mnt/d/Code/KP/kp-forecasting-bma/forecaster && celery -A api.main.celery worker --loglevel=info"

echo Starting FastAPI application...
start cmd /k "wsl cd /mnt/d/Code/KP/kp-forecasting-bma/forecaster && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"

echo All services started!
echo Redis is running on port 6379
echo FastAPI is running on http://localhost:8000
echo Celery worker is running 