@echo off
echo 🚀 Starting HealthFourUs Backend...

call .venv\Scripts\activate

echo 📊 Running database migrations...
alembic upgrade head

echo 🌐 Starting FastAPI server...
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
