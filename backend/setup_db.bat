@echo off
echo ========================================
echo MIS Database Setup Script
echo ========================================
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo Running database initialization...
python init_database.py --create-admin

echo.
echo Done!
pause
