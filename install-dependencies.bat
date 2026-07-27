@echo off
echo Installing Python dependencies...
python -m pip install -r requirements.txt
echo.
echo Installation complete!
echo.
echo Next steps:
echo 1. Run: python manage.py migrate
echo 2. Run: python manage.py seed_products
