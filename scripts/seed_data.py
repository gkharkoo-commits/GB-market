import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.permissions import ProductStatus, ShopVerificationStatus, UserRole
from backend.app.core.security import hash_password
from backend.app.db.base import Base
from backend.app.db.session import SessionLocal, engine
from backend.app.models.category import Category
from backend.app.models.delivery import DeliveryArea
from backend.app.models.product import Product, ProductImage
from backend.app.models.shop import Shop
from backend.app.models.user import Address, User

def seed_demo_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        print("Seeding sample users, shops, and products for Gilgit-Baltistan...")

        # 1. Create a Shopkeeper user
        seller_user = db.query(User).filter(User.email == "seller.skardu@gbmarket.pk").first()
        if not seller_user:
            seller_user = User(
                email="seller.skardu@gbmarket.pk",
                phone="03450000001",
                full_name="Muhammad Ali Balti",
                hashed_password=hash_password("SellerPass123!"),
                role=UserRole.SHOPKEEPER.value,
                is_active=True,
                is_verified=True
            )
            db.add(seller_user)
            db.commit()
            db.refresh(seller_user)
            print("Created demo seller user")

        # 2. Create a Customer user
        customer_user = db.query(User).filter(User.email == "customer.gilgit@gbmarket.pk").first()
        if not customer_user:
            customer_user = User(
                email="customer.gilgit@gbmarket.pk",
                phone="03450000002",
                full_name="Karim Khan",
                hashed_password=hash_password("CustomerPass123!"),
                role=UserRole.CUSTOMER.value,
                is_active=True,
                is_verified=True
            )
            db.add(customer_user)
            db.commit()
            db.refresh(customer_user)

            # Add default address
            addr = Address(
                user_id=customer_user.id,
                title="Home",
                full_name="Karim Khan",
                phone="03450000002",
                city="Gilgit",
                locality="Jutial",
                address_line="House 42, Near KIU Gate 2",
                landmark="Karakoram International University",
                is_default=True
            )
            db.add(addr)
            db.commit()
            print("Created demo customer user with address")

        # 3. Create a Delivery Rider user
        rider_user = db.query(User).filter(User.email == "rider.gilgit@gbmarket.pk").first()
        if not rider_user:
            rider_user = User(
                email="rider.gilgit@gbmarket.pk",
                phone="03450000003",
                full_name="Shabbir Hussain",
                hashed_password=hash_password("RiderPass123!"),
                role=UserRole.RIDER.value,
                is_active=True,
                is_verified=True
            )
            db.add(rider_user)
            db.commit()
            print("Created demo rider user")

        # Get categories
        cat_dry_fruits = db.query(Category).filter(Category.slug == "dry-fruits-nuts").first()
        cat_handicrafts = db.query(Category).filter(Category.slug == "gb-handicrafts").first()
        cat_honey = db.query(Category).filter(Category.slug == "honey-salajeet").first()

        # 4. Create Approved Demo Shops
        shop_1 = db.query(Shop).filter(Shop.slug == "karakoram-dry-fruits-skardu").first()
        if not shop_1:
            shop_1 = Shop(
                owner_id=seller_user.id,
                category_id=cat_dry_fruits.id if cat_dry_fruits else None,
                name="Karakoram Organic Dry Fruits",
                slug="karakoram-dry-fruits-skardu",
                owner_name="Muhammad Ali Balti",
                phone="03450000001",
                city="Skardu",
                locality="Naya Bazar",
                address="Shop 14, Main Naya Bazar, Skardu",
                landmark="Near Yadgar Chowk",
                description="Finest organic dry fruits directly sourced from Shigar, Kharmang, and Skardu valleys. Premium almonds, sun-dried apricots, walnuts, and chilgoza.",
                opening_hours="09:00 AM - 08:30 PM",
                available_delivery_methods="Standard Delivery, Store Pickup",
                exterior_image="https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=800&q=80",
                verification_status=ShopVerificationStatus.APPROVED.value,
                is_active=True,
                commission_rate=5.0
            )
            db.add(shop_1)
            db.commit()
            db.refresh(shop_1)
            print("Created Shop 1: Karakoram Organic Dry Fruits")

        shop_2 = db.query(Shop).filter(Shop.slug == "hunza-heritage-handicrafts").first()
        if not shop_2:
            shop_2 = Shop(
                owner_id=seller_user.id,
                category_id=cat_handicrafts.id if cat_handicrafts else None,
                name="Hunza Heritage & Woolens",
                slug="hunza-heritage-handicrafts",
                owner_name="Muhammad Ali Balti",
                phone="03450000001",
                city="Hunza",
                locality="Karimabad",
                address="Heritage Street, Below Baltit Fort, Karimabad",
                landmark="Baltit Fort Footpath",
                description="Authentic handwoven Gilgit and Hunza caps with traditional feather plumes, woolen pattu coats, pure sheep-wool shawls, and handmade embroidery.",
                opening_hours="08:30 AM - 09:00 PM",
                available_delivery_methods="Standard Delivery",
                exterior_image="https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=800&q=80",
                verification_status=ShopVerificationStatus.APPROVED.value,
                is_active=True,
                commission_rate=5.0
            )
            db.add(shop_2)
            db.commit()
            db.refresh(shop_2)
            print("Created Shop 2: Hunza Heritage & Woolens")

        # 5. Create Demo Products
        products_data = [
            {
                "shop_id": shop_1.id,
                "category_id": cat_dry_fruits.id if cat_dry_fruits else None,
                "title": "Premium Skardu Sweet Almonds (Kagzi Badam) - 1 KG",
                "slug": f"{shop_1.slug}-skardu-sweet-almonds-1kg",
                "description": "100% natural, thin-shelled soft Kagzi almonds harvested from high altitude orchards in Skardu. High oil content and unmatched sweet taste.",
                "price": Decimal("2400.00"),
                "original_price": Decimal("2700.00"),
                "stock_quantity": 45,
                "unit": "kg",
                "is_featured": True,
                "image_url": "https://images.unsplash.com/photo-1508061253366-f7da158b6d46?auto=format&fit=crop&w=800&q=80"
            },
            {
                "shop_id": shop_1.id,
                "category_id": cat_dry_fruits.id if cat_dry_fruits else None,
                "title": "Sun-Dried Shigar Valley Apricots (Khubani) - 1 KG",
                "slug": f"{shop_1.slug}-shigar-apricots-1kg",
                "description": "Naturally sun-dried organic golden apricots from Shigar Valley, Baltistan. No preservatives, rich in iron, fiber, and vitamins.",
                "price": Decimal("1650.00"),
                "original_price": Decimal("1900.00"),
                "stock_quantity": 60,
                "unit": "kg",
                "is_featured": True,
                "image_url": "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?auto=format&fit=crop&w=800&q=80"
            },
            {
                "shop_id": shop_1.id,
                "category_id": cat_dry_fruits.id if cat_dry_fruits else None,
                "title": "Gilgit Mountain Wild Walnuts (Akhrot Giri) - 500g",
                "slug": f"{shop_1.slug}-mountain-walnuts-500g",
                "description": "Freshly shelled, extra-crisp whole walnut kernels from Gilgit valleys. Rich in Omega-3 fatty acids and heart-healthy nutrients.",
                "price": Decimal("1350.00"),
                "original_price": Decimal("1500.00"),
                "stock_quantity": 35,
                "unit": "pack",
                "is_featured": False,
                "image_url": "https://images.unsplash.com/photo-1557308536-ee471ef2c390?auto=format&fit=crop&w=800&q=80"
            },
            {
                "shop_id": shop_1.id,
                "category_id": cat_honey.id if cat_honey else None,
                "title": "Pure Himalayan Salajeet (Shilajit) Gold Grade - 30g",
                "slug": f"{shop_1.slug}-himalayan-salajeet-30g",
                "description": "Authentic mountain purified Salajeet collected from high rock cliffs above 16,000 feet in the Karakoram range. Lab-tested purity.",
                "price": Decimal("2800.00"),
                "original_price": Decimal("3200.00"),
                "stock_quantity": 25,
                "unit": "jar",
                "is_featured": True,
                "image_url": "https://images.unsplash.com/photo-1587049352846-4a222e784d38?auto=format&fit=crop&w=800&q=80"
            },
            {
                "shop_id": shop_2.id,
                "category_id": cat_handicrafts.id if cat_handicrafts else None,
                "title": "Traditional Gilgiti Woolen Cap with Peacock Plume",
                "slug": f"{shop_2.slug}-traditional-gilgiti-cap",
                "description": "Hand-stitched pure sheep-wool Gilgiti Pakol cap adorned with traditional embroidery band and vibrant feather plume. A symbol of GB honor.",
                "price": Decimal("1950.00"),
                "original_price": Decimal("2200.00"),
                "stock_quantity": 20,
                "unit": "piece",
                "is_featured": True,
                "image_url": "https://images.unsplash.com/photo-1576871337622-98d48d1cf531?auto=format&fit=crop&w=800&q=80"
            },
            {
                "shop_id": shop_2.id,
                "category_id": cat_handicrafts.id if cat_handicrafts else None,
                "title": "Handmade Hunza Floral Embroidered Wool Shawl",
                "slug": f"{shop_2.slug}-hunza-embroidered-shawl",
                "description": "Magnificent handwoven winter shawl crafted by master women artisans in Karimabad, Hunza. Warm, elegant, and timeless.",
                "price": Decimal("5500.00"),
                "original_price": Decimal("6500.00"),
                "stock_quantity": 12,
                "unit": "piece",
                "is_featured": True,
                "image_url": "https://images.unsplash.com/photo-1607344645866-009c320b5ab8?auto=format&fit=crop&w=800&q=80"
            }
        ]

        for p_data in products_data:
            existing = db.query(Product).filter(Product.slug == p_data["slug"]).first()
            if not existing:
                img_url = p_data.pop("image_url")
                prod = Product(**p_data, status=ProductStatus.ACTIVE.value)
                db.add(prod)
                db.flush()

                p_img = ProductImage(
                    product_id=prod.id,
                    image_url=img_url,
                    is_primary=True,
                    display_order=0
                )
                db.add(p_img)
                db.commit()
                print(f"Created product: {prod.title}")

        print("SUCCESS: Demo data successfully seeded!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_data()
