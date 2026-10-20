# GB MARKET — Database Backup & Recovery Procedure

Regular database backups protect merchant orders, vendor accounts, customer addresses, and financial payout records from accidental data loss or server hardware failures.

---

## 1. Automated Local Backup Script (`scripts/backup_db.py`)

The project includes an automated backup utility that:
1. Takes a safe binary snapshot of the active database.
2. Formats a timestamped archive file in the `backups/` directory (e.g. `gb_market_backup_20261020_103244.db`).
3. Computes a cryptographic **SHA-256 hash** of the backup and saves it alongside the database file (e.g. `.sha256`).
4. Verifies file integrity before finishing.

### Running a Backup:
```powershell
# From project root in Windows PowerShell:
.venv\Scripts\python scripts/backup_db.py
```

### Sample Output:
```
==================================================
 GB MARKET — Database Backup Complete 
==================================================
Source Database: D:\GB Market\gb_market.db
Backup File:     D:\GB Market\backups\gb_market_backup_20261020_103244.db
File Size:       384.00 KB
SHA-256 Hash:    e88678a9ac17f77189316425bf02debf6d66a6a6330c36304b7899d9e45d1005
Checksum File:   D:\GB Market\backups\gb_market_backup_20261020_103244.db.sha256
Status: SUCCESS (Integrity Verified)
```

---

## 2. Restoration Procedure (`scripts/restore_db.py`)

To restore a previous database backup:

```powershell
.venv\Scripts\python scripts/restore_db.py --file "backups\gb_market_backup_20261020_103244.db"
```

### Safety Features Built Into Restoration:
1. **Checksum Verification**: The script checks the backup file against its recorded `.sha256` hash. If corrupted or tampered with, restoration terminates immediately.
2. **Pre-Restore Snapshot**: Before overwriting the live database, the script creates a safety backup of the existing live database as `gb_market.db.prerestore.bak`.

---

## 3. Off-Site Backup Recommendation

Keeping backups only on the same hard drive as the live server does not protect against hard drive failures, power surges, or filesystem corruption.

**Best Practice**:
- Automatically sync the `backups/` folder to an independent, secure remote location (such as Google Drive, an external encrypted USB drive, or an AWS S3 Glacier archive).
