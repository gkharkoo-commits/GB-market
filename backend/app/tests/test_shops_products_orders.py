from decimal import Decimal
import pytest

from backend.app.core.permissions import ShopVerificationStatus

def test_shop_registration_and_workflow(client, customer_user, customer_token, admin_token):
    # 1. Customer registers a shop
    shop_data = {
        "name": "Baltistan Walnut Store",
        "owner_name": "Test Seller",
        "phone": "03451122334",
        "city": "Skardu",
        "locality": "Hussainabad",
        "address": "Bazar Street 5",
        "description": "Finest walnuts and organic products from Skardu",
        "opening_hours": "09:00 AM - 08:00 PM",
        "available_delivery_methods": "Standard Delivery",
        "exterior_image": "/uploads/shops/shop_ext.jpg"
    }
    res = client.post(
        "/api/v1/shops/register",
        json=shop_data,
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert res.status_code == 201
    shop = res.json()
    assert shop["name"] == "Baltistan Walnut Store"
    assert shop["verification_status"] == ShopVerificationStatus.PENDING.value
    shop_id = shop["id"]

    # 2. Unapproved shop attempts to add product -> 403 Forbidden
    prod_data = {
        "title": "Fresh Walnuts 1KG",
        "description": "Rich in omega 3",
        "price": 1200.0,
        "stock_quantity": 20,
        "unit": "kg",
        "image_urls": ["/uploads/products/walnut.jpg"]
    }
    prod_res = client.post(
        "/api/v1/products/",
        json=prod_data,
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert prod_res.status_code == 403
    assert "only approved shops can sell" in prod_res.json()["detail"].lower()

    # 3. Admin approves the shop
    review_res = client.put(
        f"/api/v1/shops/admin/{shop_id}/review",
        json={"status": "approved", "verification_notes": "All documents verified"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert review_res.status_code == 200
    assert review_res.json()["verification_status"] == "approved"

    # 4. Now seller can successfully add the product
    prod_res2 = client.post(
        "/api/v1/products/",
        json=prod_data,
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert prod_res2.status_code == 201
    product = prod_res2.json()
    assert product["title"] == "Fresh Walnuts 1KG"
    assert product["price"] == 1200.0
    assert product["stock_quantity"] == 20
    product_id = product["id"]

    # 5. Customer adds product to cart
    cart_res = client.post(
        "/api/v1/cart/items",
        json={"product_id": product_id, "quantity": 2},
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert cart_res.status_code == 200
    cart_data = cart_res.json()
    assert cart_data["total_items"] == 2
    assert cart_data["subtotal"] == 2400.0

    # 6. Customer checks out order
    order_payload = {
        "delivery_name": "Test Receiver",
        "delivery_phone": "03450009999",
        "delivery_city": "Skardu",
        "delivery_locality": "Satellite Town",
        "delivery_address": "House 10, St 3",
        "customer_notes": "Please call before arrival"
    }
    checkout_res = client.post(
        "/api/v1/orders/checkout",
        json=order_payload,
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert checkout_res.status_code == 201
    order = checkout_res.json()
    assert order["subtotal"] == 2400.0
    assert order["status"] == "Pending Confirmation"
    assert order["payment_method"] == "Cash on Delivery"
    assert len(order["shop_groups"]) == 1
    assert len(order["items"]) == 1

    # 7. Verify stock quantity decreased from 20 to 18
    prod_check = client.get(f"/api/v1/products/detail/{product['slug']}")
    assert prod_check.status_code == 200
    assert prod_check.json()["stock_quantity"] == 18
