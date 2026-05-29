@echo off
cd /d "C:\Users\Vasant\OneDrive\Desktop\react-login-ui\backend-repo"
echo Installing Python dependencies...
python -m pip install -r requirements.txt
echo.
echo Installation complete!
echo.
echo Next steps:
echo 1. Run: python manage.py migrate
echo 2. Run: python manage.py seed_products
