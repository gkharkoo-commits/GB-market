# GB MARKET — Security Architecture & Threat Model

This document outlines the security controls, validation rules, data protection policies, and residual limitations implemented across **GB MARKET**.

---

## 1. Authentication & Password Security

1. **Password Hashing**:
   - Primary algorithm: **Argon2id** (`argon2-cffi`), the winner of the Password Hashing Competition and recommended by OWASP.
   - Fallback verification for standard `bcrypt` hashes.
   - Plain-text passwords are never logged or stored in the database.
2. **Timing-Safe User Verification**:
   - Failed authentication returns a generic message (`Invalid email/phone or password`) to prevent account enumeration.
3. **Session & Token Security**:
   - Stateless **JWT (JSON Web Tokens)** signed with SHA-256 (`HS256`) and a secret key (`SECRET_KEY`).
   - Tokens contain user ID, role, issued-at, and expiration claims.
   - Default token expiration is configured to 24 hours.

---

## 2. Authorization & Role-Based Access Control (RBAC)

Authorization is strictly enforced **on the backend** using FastAPI dependencies:
- `get_current_user`: Verifies token signature, expiration, and ensures user is active (`is_active == True`).
- `get_current_customer`: Confirms active customer status. Customers can access only their own profile, addresses, orders, and complaints.
- `get_current_shopkeeper`: Confirms user has `shopkeeper` or `admin` role. Shopkeepers are restricted by database queries to managing **only their own shop**, their own products, and their own order fulfillment groups.
- `get_current_rider`: Confirms rider role. Riders can access **only deliveries assigned to their user ID** and cannot access other orders.
- `get_current_admin`: Confirms `role == "admin"`. Restricts shop approvals, user role changes, marketplace settings, and audit log inspection.
- **Frontend Independence**: Hiding buttons or links in the UI is never used as a security boundary; all endpoints validate server-side session claims.

---

## 3. Upload Protection & Media Security

1. **File Extension Whitelisting**: Only `.jpg`, `.jpeg`, `.png`, and `.webp` for images; `.pdf` allowed for private business verification records. Executable (`.exe`, `.bat`, `.sh`, `.php`) and script extensions are rejected immediately.
2. **File Signature & Content Verification**: Images are loaded and verified using Python Pillow (`Image.open(BytesIO).verify()`) to ensure the file binary is actually a valid image and not malware disguised with an image extension.
3. **Server-Side Safe Filenames**: Client-supplied file names are discarded. Files are stored using cryptographic UUIDs (`uuid.uuid4().hex + ext`) preventing directory traversal (`../`) and overwrite attacks.
4. **File Size Limits**: Enforced strictly at `5MB` (`MAX_UPLOAD_SIZE_MB`).
5. **Private Document Protection**: Sensitive merchant verification documents (e.g. CNIC / Trade proof) are stored in a dedicated folder (`uploads/documents/`) and can only be downloaded through the authenticated admin endpoint (`/api/v1/uploads/documents/{id}`).

---

## 4. Database Security & Concurrency

1. **SQL Injection Protection**: All database queries are executed through **SQLAlchemy ORM** using parameterized prepared statements. No raw SQL string interpolation is used.
2. **Transactional Inventory Operations**: Order checkout uses database transactions. Stock is verified and decremented atomically. If another customer buys out the stock concurrently, the transaction rolls back cleanly without creating negative inventory or partial records.
3. **Immutable Price Snapshots**: Historical order items record immutable snapshots of product titles, unit prices, and quantities. Subsequent changes to product catalog prices do not alter past order totals.

---

## 5. Audit Logging

Sensitive actions generate tamper-evident audit records in the `audit_logs` table:
- User registration and login events
- Shop registration submissions
- Administrator shop approvals, rejections, and suspensions
- Order checkouts and cancellations
- User role promotions/demotions and account suspensions
- Configuration setting changes

Audit records store actor ID, actor email, action code, entity type, entity ID, action summary, and client IP address. Passwords, auth tokens, and private identification numbers are excluded from audit log text.

---

## 6. Residual Limitations & Operational Warnings

1. **Transport Layer Security (HTTPS)**: When deploying publicly, HTTPS must be enforced using a TLS certificate (e.g. via Let's Encrypt or platform proxy). Do not send bearer tokens over unencrypted HTTP over public Wi-Fi.
2. **Rate Limiting**: In high-traffic public deployments, placing a reverse proxy (e.g., Cloudflare or NGINX) in front of the application is recommended to defend against brute-force login attempts and DDoS attacks.
3. **No Infallibility**: No system is 100% impenetrable. Regularly update pip dependencies, take daily database backups, and store production secret keys in private environment variable stores.
