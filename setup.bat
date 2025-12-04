@echo off
echo 🚀 Setting up HealthFourUs Backend...

REM Create virtual environment
python -m venv .venv
call .venv\Scripts\activate

REM Upgrade pip
python -m pip install --upgrade pip

REM Install dependencies
pip install -r requirements.txt

REM Create directories
mkdir logs uploads\medical_images uploads\documents knowledge_bases

REM Copy environment template
if not exist .env (
    copy .env.example .env
    echo ⚠️  Please edit .env file with your configuration
)

REM Initialize database
python -c "from database.database import init_db; init_db()"

echo ✅ Setup complete!
echo.
echo Next steps:
echo 1. Edit .env file with your API keys
echo 2. Wait for model training to complete
echo 3. Run: run.bat

pause
