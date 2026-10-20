# GB MARKET — Gilgit-Baltistan Multi-Vendor Marketplace

**GB MARKET** is a multi-vendor e-commerce platform designed and built specifically for **Gilgit-Baltistan, Pakistan**. It enables local merchants, farmers, and artisans in Skardu, Gilgit, Hunza, Nagar, Ghizer, Diamer, Astore, Shigar, Kharmang, and Ghanche to register verified storefronts, upload products, manage inventory, receive orders, and deliver to regional customers via **Cash on Delivery (COD)**.

---

## 1. Project Information & Ownership

- **Platform Name**: GB MARKET
- **Lead Developer & Owner**: **Abdul Sattar**
- **Email**: `sattar.kharkoo@gmail.com`
- **Contact Numbers**: `03498188394` / `03140058798`
- **Region**: Gilgit-Baltistan, Pakistan
- **Payment Method**: Cash on Delivery (COD) in Pakistani Rupees (PKR)

---

## 2. Technology Stack

- **Backend**: Python 3.13+, FastAPI, Pydantic v2, SQLAlchemy 2.0 ORM, Alembic migrations
- **Security**: Argon2id password hashing (`argon2-cffi`), JWT authentication, server-side RBAC
- **Database**: SQLite (Local Windows development), PostgreSQL (Production-ready schema & migrations)
- **Frontend**: Accessible HTML5, modern responsive CSS3 design system, vanilla JavaScript API client
- **File Storage**: Configurable media storage with file-type validation via Python Pillow
- **Testing**: Pytest automated test suite (12/12 passing unit & integration tests)

---

## 3. Implemented Architecture & User Roles

```
                                      +--------------------------+
                                      |   GB MARKET FASTAPI      |
                                      |  JWT & RBAC Middleware   |
                                      +-------------+------------+
                                                    |
         +---------------------+--------------------+--------------------+---------------------+
         |                     |                                         |                     |
+--------v-------+    +--------v--------+                       +--------v--------+   +--------v--------+
|    Visitor     |    |    Customer     |                       |   Shopkeeper    |   |  Administrator  |
| - Browse Shops |    | - Save Address  |                       | - Apply Store   |   | - Review Stores |
| - Filter By    |    | - Real-time     |                       | - Add Products  |   | - User Roles    |
|   Category     |    |   Cart & Stock  |                       | - Update Stock  |   | - Commission %  |
| - Search Title |    | - Place COD     |                       | - Pack & Prep   |   | - Payouts       |
| - Sign Up /    |    |   Orders        |                       |   Orders        |   | - Audit Logs    |
|   Log In       |    | - Track Status  |                       | - Seller Payout |   | - Backup /      |
+----------------+    +-----------------+                       +-----------------+   |   Restore       |
                                                                                      +-----------------+
```

### Supported User Roles:
1. **Visitor**: Public browsing, regional city filtering, category navigation, product search.
2. **Customer**: Profile and delivery address book, real-time cart with backend stock verification, multi-seller checkout, Cash on Delivery, order tracking timeline, cancellation requests.
3. **Shopkeeper (Merchant)**: Dedicated shop registration with storefront exterior photo upload, verification status tracking (Pending, Approved, Rejected, Suspended), product catalog management, order fulfillment dashboard (Confirmed, Preparing, Packed, Ready for Pickup).
4. **Delivery Rider**: Assigned order viewing, pickup from vendor, drop-off to customer, delivery completion confirmation, and delivery failure recording.
5. **Administrator**: Application review and approval with reason logging, user role management, cancellation request review, commission rate configuration, and tamper-evident audit logs.

---

## 4. Quick Start on Windows

```powershell
# 1. Clone or open the workspace
cd "d:\GB Market"

# 2. Activate virtual environment
.venv\Scripts\Activate.ps1

# 3. Apply database migrations
.venv\Scripts\alembic upgrade head

# 4. Create the initial administrator
.venv\Scripts\python scripts/create_admin.py --password "YourAdminPasswordHere!"

# 5. Seed sample Gilgit-Baltistan categories, shops, and products
.venv\Scripts\python scripts/seed_data.py

# 6. Run automated test suite
.venv\Scripts\pytest

# 7. Start the server
.venv\Scripts\uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### Access URLs:
- **Public Website**: [http://127.0.0.1:8000/static/index.html](http://127.0.0.1:8000/static/index.html)
- **API Documentation (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Seller Hub**: [http://127.0.0.1:8000/static/seller/index.html](http://127.0.0.1:8000/static/seller/index.html)
- **Admin Control Center**: [http://127.0.0.1:8000/static/admin/index.html](http://127.0.0.1:8000/static/admin/index.html)
- **Rider Portal**: [http://127.0.0.1:8000/static/rider/index.html](http://127.0.0.1:8000/static/rider/index.html)

---

## 5. Documentation Directory

- [`docs/SETUP.md`](docs/SETUP.md): Exact step-by-step Windows development setup.
- [`docs/SECURITY.md`](docs/SECURITY.md): Security architecture, Argon2id, RBAC, upload validation, and residual risks.
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md): Zero-budget deployment strategy, free-tier limits, and cloud instructions.
- [`docs/BACKUP-RESTORE.md`](docs/BACKUP-RESTORE.md): Database backup, SHA-256 verification, and disaster recovery.
- [`docs/USER-GUIDE.md`](docs/USER-GUIDE.md): Step-by-step user guide for Customers, Merchants, Riders, and Admins.
- [`mobile/README.md`](mobile/README.md): Architecture, endpoints, and build instructions for future Android APK development.
