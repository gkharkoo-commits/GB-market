import argparse
import hashlib
import os
import shutil
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings

def calculate_sha256(filepath):
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()

def restore_database():
    parser = argparse.ArgumentParser(description="Restore GB MARKET database from a backup file.")
    parser.add_argument("--file", required=True, help="Path to the backup .db file")
    args = parser.parse_args()

    backup_file = os.path.abspath(args.file)
    if not os.path.exists(backup_file):
        print(f"Error: Backup file does not exist: {backup_file}")
        sys.exit(1)

    # Verify Checksum if present
    checksum_file = f"{backup_file}.sha256"
    if os.path.exists(checksum_file):
        with open(checksum_file, "r") as f:
            expected_hash = f.read().split()[0].strip()
        actual_hash = calculate_sha256(backup_file)
        if expected_hash.lower() != actual_hash.lower():
            print("CRITICAL ERROR: Backup file checksum mismatch! File may be corrupted.")
            sys.exit(1)
        print("Checksum verification: PASSED")

    if settings.DATABASE_URL.startswith("sqlite"):
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        if not os.path.isabs(db_path):
            db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", db_path))

        # Create a safety pre-restore backup of current live DB
        if os.path.exists(db_path):
            pre_restore = f"{db_path}.prerestore.bak"
            shutil.copy2(db_path, pre_restore)
            print(f"Safety snapshot of live DB created at: {pre_restore}")

        shutil.copy2(backup_file, db_path)
        print("==================================================")
        print(" GB MARKET — Database Restoration Complete ")
        print("==================================================")
        print(f"Restored file:  {backup_file}")
        print(f"Live Database:  {db_path}")
        print("Status: SUCCESS")
    else:
        print("Non-SQLite database configured. Please use psql / pg_restore.")

if __name__ == "__main__":
    restore_database()
