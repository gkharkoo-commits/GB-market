# GB MARKET — Windows Local Development Setup Guide

This document contains exact, tested instructions for setting up and running **GB MARKET** on a Windows 10/11 development machine using Python 3.13+ and PowerShell / Command Prompt.

---

## 1. Prerequisites

1. **Python 3.11+** installed (verified working with Python 3.13.15).
   - Ensure "Add Python to PATH" was checked during installation.
2. **Git** for version control.

---

## 2. Step-by-Step Setup Instructions

### Step 1: Open PowerShell in Project Directory
Open Windows PowerShell and navigate to the project directory:
```powershell
cd "d:\GB Market"
```

### Step 2: Create and Activate Virtual Environment
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment in PowerShell
.venv\Scripts\Activate.ps1

# (If using standard Windows Command Prompt instead of PowerShell, run: .venv\Scripts\activate.bat)
```

### Step 3: Install Dependencies
```powershell
pip install -r backend/requirements.txt
```

### Step 4: Environment Configuration
Copy the template configuration file:
```powershell
copy backend\.env.example backend\.env
```
Ensure `backend/.env` contains a secure `SECRET_KEY` and your database path.

### Step 5: Run Database Migrations
Run Alembic to apply all relational schema tables:
```powershell
.venv\Scripts\alembic upgrade head
```

### Step 6: Create the Initial Administrator Account
Run the secure administrator setup CLI:
```powershell
.venv\Scripts\python scripts/create_admin.py --password "YourAdminPasswordHere!"
```
*Default initial admin configuration: Abdul Sattar (`sattar.kharkoo@gmail.com`, `03498188394`).*

### Step 7: Seed Sample Marketplace Data (Optional but Recommended)
Populate sample Gilgit-Baltistan categories, shops, and products:
```powershell
.venv\Scripts\python scripts/seed_data.py
```

### Step 8: Run Automated Test Suite
Verify that all 12 test suites pass:
```powershell
.venv\Scripts\pytest
```

---

## 3. Starting the Application

Start the FastAPI application with Uvicorn:
```powershell
.venv\Scripts\uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Once running, access the application in your browser:
- **Public Customer Website**: [http://127.0.0.1:8000/static/index.html](http://127.0.0.1:8000/static/index.html)
- **Interactive OpenAPI Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative ReDoc API Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Backend Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Seller Hub**: [http://127.0.0.1:8000/static/seller/index.html](http://127.0.0.1:8000/static/seller/index.html)
- **Admin Control Center**: [http://127.0.0.1:8000/static/admin/index.html](http://127.0.0.1:8000/static/admin/index.html)
- **Rider Portal**: [http://127.0.0.1:8000/static/rider/index.html](http://127.0.0.1:8000/static/rider/index.html)

---

## 4. Stopping and Restarting

- **To Stop**: Press `Ctrl + C` in the running PowerShell terminal.
- **To Restart**: Run `.venv\Scripts\uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000`.

---

## 5. Database Backup and Recovery

### Backup:
```powershell
.venv\Scripts\python scripts/backup_db.py
```
This saves a verified timestamped `.db` file and its SHA-256 hash in the `backups/` directory.

### Restore:
```powershell
.venv\Scripts\python scripts/restore_db.py --file "backups\gb_market_backup_YYYYMMDD_HHMMSS.db"
```
The script validates the SHA-256 checksum, takes an automatic safety backup of the existing live database, and restores the database file.
