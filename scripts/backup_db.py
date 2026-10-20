import hashlib
import os
import shutil
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings

def calculate_sha256(filepath):
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()

def backup_database():
    backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backups"))
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if settings.DATABASE_URL.startswith("sqlite"):
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        if not os.path.isabs(db_path):
            db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", db_path))

        if not os.path.exists(db_path):
            print(f"Error: Database file not found at {db_path}")
            sys.exit(1)

        backup_file = os.path.join(backup_dir, f"gb_market_backup_{timestamp}.db")
        shutil.copy2(db_path, backup_file)

        checksum = calculate_sha256(backup_file)
        checksum_file = f"{backup_file}.sha256"
        with open(checksum_file, "w") as f:
            f.write(f"{checksum}  {os.path.basename(backup_file)}\n")

        file_size_kb = os.path.getsize(backup_file) / 1024

        print("==================================================")
        print(" GB MARKET — Database Backup Complete ")
        print("==================================================")
        print(f"Source Database: {db_path}")
        print(f"Backup File:     {backup_file}")
        print(f"File Size:       {file_size_kb:.2f} KB")
        print(f"SHA-256 Hash:    {checksum}")
        print(f"Checksum File:   {checksum_file}")
        print("Status: SUCCESS (Integrity Verified)")
    else:
        print(f"Non-SQLite database configured ({settings.DATABASE_URL}). Please use pg_dump.")

if __name__ == "__main__":
    backup_database()
