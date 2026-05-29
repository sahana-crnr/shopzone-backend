# Backend Setup Guide - Image Carousel

## Issue
```
ModuleNotFoundError: No module named 'django'
```

## Reason
Python dependencies are not installed. You need to install them from `requirements.txt`.

---

## ✅ Quick Setup (3 Steps)

### Step 1: Install Dependencies
Open **Command Prompt** in the backend folder:

```cmd
cd "C:\Users\Vasant\OneDrive\Desktop\react-login-ui\backend-repo"
python -m pip install -r requirements.txt
```

**Wait for completion** - this may take 1-2 minutes.

### Step 2: Run Database Migration
```cmd
python manage.py migrate
```

Expected output:
```
Running migrations:
  Applying catalog.0004_product_images... OK
  [other migrations...]
```

### Step 3: Load Product Data
```cmd
python manage.py seed_products
```

Expected output:
```
Seeded products successfully. Created: 0, updated: 58.
```

---

## 🚀 Run the Application

### Terminal 1: Backend
```cmd
cd backend-repo
python manage.py runserver
```

Output should show:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

### Terminal 2: Frontend
```cmd
cd frontend-repo
npm start
```

Output should show:
```
webpack compiled successfully
```

---

## ✔️ Verify Everything Works

1. **Open browser**: http://localhost:3000
2. **Go to product**: Click on any product
3. **Check for carousel**:
   - ✅ Main image displays
   - ✅ Left/Right arrows visible
   - ✅ Thumbnail strip below
   - ✅ Can click thumbnails
   - ✅ Arrow keys work

---

## 📋 What Gets Installed

| Package | Purpose |
|---------|---------|
| Django 6.0.4 | Web framework |
| DRF 3.17.1 | REST API |
| JWT 5.5.1 | Authentication |
| CORS 4.9.0 | Frontend communication |
| python-dotenv | Environment variables |
| gunicorn | Production server |
| psycopg | Database driver |

---

## 🔧 Troubleshooting

### Still getting "No module named 'django'"?

**Check Python version:**
```cmd
python --version
```
Should be 3.8 or higher. If not, install latest Python.

**Check pip installation:**
```cmd
pip --version
python -m pip --version
```

**Try installing with verbose output:**
```cmd
python -m pip install -v -r requirements.txt
```

### Migration fails?

```cmd
# See all migrations
python manage.py showmigrations

# If stuck, mark as complete
python manage.py migrate --fake-initial
```

### Products don't have images?

```cmd
# Re-run seed
python manage.py seed_products --verbosity 2
```

---

## 📁 Folder Structure

```
backend-repo/
├── manage.py              ← Main entry point
├── requirements.txt       ← Dependencies (needed)
├── catalog/
│   ├── models.py         ← Updated with images field
│   ├── serializers.py    ← Updated to expose images
│   ├── migrations/
│   │   └── 0004_product_images.py  ← New migration
│   ├── data/
│   │   └── products.json ← Sample data with images
│   └── management/commands/
│       └── seed_products.py  ← Updated with images
├── install-dependencies.bat   ← Helper script
└── SETUP_INSTRUCTIONS.txt     ← This guide
```

---

## ✅ Success Indicators

✅ **Step 1 Complete** when:
- No errors during pip install
- Shows "Successfully installed..." messages

✅ **Step 2 Complete** when:
- Shows "Applying catalog.0004_product_images... OK"

✅ **Step 3 Complete** when:
- Shows "Seeded products successfully. Updated: 58"

✅ **Running** when:
- Backend server shows "Starting development server..."
- Frontend shows "webpack compiled successfully"

✅ **Working** when:
- Carousel appears on product page
- Multiple images display
- Thumbnails are clickable

---

## 🎯 Common Commands Reference

```cmd
# Install/Update dependencies
python -m pip install -r requirements.txt

# Create new migration (if models change)
python manage.py makemigrations catalog

# Run migrations
python manage.py migrate

# Load sample data
python manage.py seed_products

# Start dev server
python manage.py runserver

# Access admin panel
python manage.py createsuperuser
# Then visit http://localhost:8000/admin/

# Run tests
python manage.py test catalog

# Access Django shell
python manage.py shell
```

---

## 📞 Need Help?

If you encounter errors:

1. **Check Python version**: `python --version` (need 3.8+)
2. **Check pip**: `python -m pip --version`
3. **Check Django installed**: `python -c "import django; print(django.VERSION)"`
4. **Check migrations**: `python manage.py showmigrations catalog`
5. **Check database**: Check if `db.sqlite3` exists

---

## ✨ All Set!

Once the dependencies are installed and migrations run, your image carousel is ready to use!

**Total time:** ~5 minutes
**Next step:** Run the servers and visit a product page!
