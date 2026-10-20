import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.routes import (
    admin,
    auth,
    carts,
    categories,
    complaints,
    deliveries,
    orders,
    products,
    shops,
    uploads,
    users,
)
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.base import Base
from backend.app.db.session import SessionLocal, engine
from backend.app.models.category import Category
from backend.app.models.delivery import DeliveryArea
from backend.app.models.setting import MarketplaceSetting

# Ensure upload directories exist
for folder in ["shops", "products", "profiles", "documents", "general"]:
    os.makedirs(os.path.join(settings.UPLOAD_DIR, folder), exist_ok=True)

def seed_defaults():
    """Seeds essential categories, delivery areas, and default settings if database is empty."""
    db = SessionLocal()
    try:
        # 1. Default Categories
        if db.query(Category).count() == 0:
            default_categories = [
                {"name": "Dry Fruits & Nuts", "slug": "dry-fruits-nuts", "description": "Gilgit-Baltistan famous almonds, walnuts, dried apricots, pine nuts & cherries", "icon": "fa-seedling", "display_order": 1},
                {"name": "GB Handicrafts & Woolens", "slug": "gb-handicrafts", "description": "Authentic Gilgiti pattu, woolen caps, shawls, carpets & local embroidery", "icon": "fa-vest", "display_order": 2},
                {"name": "Organic Honey & Salajeet", "slug": "honey-salajeet", "description": "Pure mountain wild honey, Himalayan Salajeet / Shilajit & natural herbs", "icon": "fa-jar", "display_order": 3},
                {"name": "Fresh Mountain Fruits", "slug": "fresh-fruits", "description": "Fresh cherries, Hunza apples, apricots, pears, and pomegranates in season", "icon": "fa-apple-whole", "display_order": 4},
                {"name": "Local Spices & Herbal Teas", "slug": "spices-tea", "description": "Traditional Tumuro tea, mountain thyme, wild cumin and herbs", "icon": "fa-mug-hot", "display_order": 5},
                {"name": "Grocery & Daily Essentials", "slug": "grocery-essentials", "description": "Daily food supplies, flours, grains, and kitchen staples", "icon": "fa-cart-shopping", "display_order": 6},
                {"name": "Electronics & Mobile Accessories", "slug": "electronics", "description": "Phones, chargers, power banks, lights, and consumer electronics", "icon": "fa-mobile-screen", "display_order": 7},
                {"name": "Clothing & Traditional Wear", "slug": "clothing", "description": "Men's, women's, and children's apparel, shoes, and winter coats", "icon": "fa-shirt", "display_order": 8},
            ]
            for cat_data in default_categories:
                db.add(Category(**cat_data))
            logger.info("Default Gilgit-Baltistan categories seeded")

        # 2. Default Serviceable Delivery Areas
        if db.query(DeliveryArea).count() == 0:
            default_areas = [
                {"name": "Gilgit City Central", "city": "Gilgit", "delivery_fee": 150.0, "estimated_days": 1},
                {"name": "Jutial & Konodas", "city": "Gilgit", "delivery_fee": 180.0, "estimated_days": 1},
                {"name": "Danyore & Sultanabad", "city": "Gilgit", "delivery_fee": 200.0, "estimated_days": 1},
                {"name": "Skardu City & Bazar", "city": "Skardu", "delivery_fee": 150.0, "estimated_days": 1},
                {"name": "Aliabad & Karimabad", "city": "Hunza", "delivery_fee": 250.0, "estimated_days": 2},
                {"name": "Chilas Town", "city": "Diamer", "delivery_fee": 300.0, "estimated_days": 2},
                {"name": "Astore Bazar", "city": "Astore", "delivery_fee": 300.0, "estimated_days": 2},
                {"name": "Khaplu Town", "city": "Ghanche", "delivery_fee": 300.0, "estimated_days": 2},
            ]
            for area_data in default_areas:
                db.add(DeliveryArea(**area_data))
            logger.info("Default Gilgit-Baltistan delivery areas seeded")

        # 3. Default Settings
        default_settings = [
            ("marketplace_name", "GB MARKET", "Public Marketplace Brand Name"),
            ("commission_percent", "5.0", "Marketplace platform sales commission percentage"),
            ("default_delivery_fee", "150.0", "Standard delivery charge in PKR"),
            ("support_phone", "03498188394", "Official Support Helpline Phone Number"),
            ("support_email", "sattar.kharkoo@gmail.com", "Official Customer Support Email"),
        ]
        for key, val, desc in default_settings:
            if not db.query(MarketplaceSetting).filter(MarketplaceSetting.key == key).first():
                db.add(MarketplaceSetting(key=key, value=val, description=desc))

        db.commit()
    except Exception as e:
        logger.error(f"Error during seed_defaults: {e}")
        db.rollback()
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema is present and seed initial data
    Base.metadata.create_all(bind=engine)
    seed_defaults()
    logger.info(f"Started {settings.APP_NAME} in {settings.APP_ENV} mode")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")

app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-vendor e-commerce marketplace API for Gilgit-Baltistan, Pakistan",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS if isinstance(settings.ALLOWED_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploaded media files
uploads_abs_path = os.path.abspath(settings.UPLOAD_DIR)
os.makedirs(uploads_abs_path, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_abs_path), name="uploads")

# Mount public website directory
website_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "website"))
if os.path.exists(website_dir):
    app.mount("/static", StaticFiles(directory=website_dir), name="static")

# Health Check
@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint to verify backend service status."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "1.0.0"
    }

@app.get("/", include_in_schema=False)
def root():
    """Redirect root access directly to public marketplace homepage."""
    return RedirectResponse(url="/static/index.html")

@app.get("/admin", include_in_schema=False)
def admin_root():
    """Direct route to admin panel."""
    return RedirectResponse(url="/static/admin/index.html")

# Register API Routers under /api/v1
api_v1 = settings.API_V1_STR
app.include_router(auth.router, prefix=api_v1)
app.include_router(users.router, prefix=api_v1)
app.include_router(categories.router, prefix=api_v1)
app.include_router(shops.router, prefix=api_v1)
app.include_router(products.router, prefix=api_v1)
app.include_router(carts.router, prefix=api_v1)
app.include_router(orders.router, prefix=api_v1)
app.include_router(deliveries.router, prefix=api_v1)
app.include_router(uploads.router, prefix=api_v1)
app.include_router(complaints.router, prefix=api_v1)
app.include_router(admin.router, prefix=api_v1)
