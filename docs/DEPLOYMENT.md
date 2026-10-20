# GB MARKET — Public Deployment & Zero-Budget Strategy

This document provides a realistic, honest deployment guide for launching **GB MARKET** to the public while minimizing initial expenses.

---

## 1. Zero-Budget Hosting Analysis & Free-Tier Reality

While initial hosting can be started on zero-cost tiers, it is critical to understand the operational limitations of free cloud services:

| Component | Recommended Free Provider | Free Tier Limits | Potential Operational Risks |
| :--- | :--- | :--- | :--- |
| **Backend API** | **Render** or **Railway** (Trial) | 512MB RAM, sleeps after 15 min of inactivity | First visitor experiences a 30-50 second cold-start delay |
| **Relational Database** | **Neon** or **Supabase** (PostgreSQL) | ~500MB storage, 0.5 vCPU | Pauses after prolonged inactivity; query capacity is limited |
| **Static Frontend** | **Vercel** or **Cloudflare Pages** | Unlimited static bandwidth (within fair use) | None for static HTML/CSS/JS files |
| **Image Storage** | **Cloudinary** (Free Tier) or Local Disk | 25GB managed storage / bandwidth | Free cloud tier has monthly transformation credits |
| **HTTPS Certificate** | **Cloudflare** / **Let's Encrypt** | 100% Free SSL/TLS | Automated renewals |

> [!WARNING]
> Ephemeral Disk Warning: Cloud container hosts (like Render or Heroku free instances) wipe their local file system on restart. For persistent product and shop photos in public cloud deployments, configure an external storage bucket (such as Cloudinary, Supabase Storage, or AWS S3).

---

## 2. Recommended Production Architecture

### Recommended Setup:
1. **Frontend**: Hosted on Cloudflare Pages or Vercel (free, blazing fast CDN).
2. **Backend**: Python FastAPI service running on a Render Web Service (`render.yaml` or Docker).
3. **Database**: Managed PostgreSQL instance from Neon / Supabase.
4. **Domain**: Can start on free subdomains (e.g., `gb-market.onrender.com` / `gbmarket.pages.dev`) before purchasing a custom `.pk` or `.com` domain.

---

## 3. Step-by-Step Cloud Deployment

### Step 1: Set Up Cloud PostgreSQL Database
1. Create a free account at [neon.tech](https://neon.tech) or [supabase.com](https://supabase.com).
2. Create a new database project named `gb_market_prod`.
3. Copy the database connection string:
   ```
   postgresql://username:password@ep-host.neon.tech/gb_market_prod?sslmode=require
   ```

### Step 2: Configure Production Environment Variables
On your backend host, set the following environment variables:
```env
APP_NAME="GB MARKET"
APP_ENV=production
DEBUG=False
SECRET_KEY=<generate-a-strong-64-character-hex-secret>
DATABASE_URL=postgresql://username:password@ep-host.neon.tech/gb_market_prod?sslmode=require
ALLOWED_ORIGINS=https://your-frontend-domain.com
MARKETPLACE_COMMISSION_PERCENT=5.0
DEFAULT_DELIVERY_FEE=150.0
```

### Step 3: Run Alembic Migrations on PostgreSQL
In your deployment build command:
```bash
alembic upgrade head
```

### Step 4: Run Initial Admin Account Setup
```bash
python scripts/create_admin.py --password "SecureAdminProductionPass2026!"
```

### Step 5: Start Uvicorn Server in Production
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT --workers 2
```

---

## 4. Why Self-Hosting on a Local Windows PC in Gilgit-Baltistan Has Risks

Some project owners consider running the server directly from their home or office Windows PC in Gilgit-Baltistan. You must consider the following technical realities:

1. **Power Outages & Winter Load-Shedding**: If the PC loses power or UPS battery depletes, the entire marketplace and all merchant stores go offline.
2. **Dynamic Residential IP Addresses**: Local ISPs (SCO, PTCL, Nayatel) assign dynamic IP addresses that change periodically, breaking external access without dynamic DNS configuration.
3. **Firewall & Port Forwarding**: Exposing port 80/443 directly to your local PC exposes your personal computer to internet automated port scanners and vulnerability probes.
4. **Hardware Wear**: A personal laptop or desktop is not designed to run 24 hours a day, 365 days a year.

**Conclusion**: Keep local development on your Windows PC. For public customer access, deploy to cloud hosting providers with automated uptime and backups.
