import os
import getpass
import urllib.request
import json

def get_credentials():
    admin_id = os.getenv("TEST_ADMIN_IDENTIFIER") or "sattar.kharkoo@gmail.com"
    admin_pass = os.getenv("TEST_ADMIN_PASSWORD")
    cust_id = os.getenv("TEST_CUSTOMER_IDENTIFIER") or "03498188394"
    cust_pass = os.getenv("TEST_CUSTOMER_PASSWORD")

    if not admin_pass:
        admin_pass = getpass.getpass(f"Enter password for admin ({admin_id}): ")
    if not cust_pass:
        cust_pass = admin_pass

    return admin_id, admin_pass, cust_id, cust_pass

def test_full_admin_order_lifecycle():
    admin_id, admin_pass, cust_id, cust_pass = get_credentials()

    # 1. Login as Admin
    login_data = json.dumps({
        "identifier": admin_id,
        "password": admin_pass
    }).encode("utf-8")

    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/auth/login",
        data=login_data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        admin_token = json.loads(resp.read().decode("utf-8"))["access_token"]
        print("[SUCCESS] Admin logged in.")

    # 2. Login as Customer
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/auth/login",
        data=json.dumps({"identifier": cust_id, "password": cust_pass}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        cust_token = json.loads(resp.read().decode("utf-8"))["access_token"]
        print("[SUCCESS] Customer logged in.")

    # 3. Customer creates a new real test order
    # First get an active product
    req = urllib.request.Request("http://127.0.0.1:8000/api/v1/products/?limit=1")
    with urllib.request.urlopen(req) as resp:
        prods_res = json.loads(resp.read().decode("utf-8"))
        prods = prods_res.get("items", [])
        if not prods:
            raise Exception("No active products available for testing.")
        prod = prods[0]
        prod_id = prod["id"]
        initial_stock = prod["stock_quantity"]
        print(f"[INFO] Using product '{prod['title']}' (ID: {prod_id}, Initial Stock: {initial_stock})")

    # Add 1 item to cart
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/cart/items",
        data=json.dumps({"product_id": prod_id, "quantity": 1}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {cust_token}"}
    )
    with urllib.request.urlopen(req) as resp:
        cart = json.loads(resp.read().decode("utf-8"))
        print(f"[SUCCESS] Item added to cart. Total items: {cart['total_items']}")

    # Checkout new test order
    checkout_payload = {
        "delivery_name": "Abdul Sattar",
        "delivery_phone": "03498188394",
        "delivery_city": "Gilgit",
        "delivery_locality": "Jutial",
        "delivery_address": "Near Karakoram Highway, Jutial, Gilgit",
        "customer_notes": "Call upon arrival"
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/orders/checkout",
        data=json.dumps(checkout_payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {cust_token}"}
    )
    with urllib.request.urlopen(req) as resp:
        new_order = json.loads(resp.read().decode("utf-8"))
        order_id = new_order["id"]
        order_num = new_order["order_number"]
        print(f"[SUCCESS] Created real test order ID: {order_id} (#{order_num}), Status: {new_order['status']}")
        assert new_order["status"] == "Pending Confirmation"

    # Verify stock decremented by 1
    req = urllib.request.Request(f"http://127.0.0.1:8000/api/v1/products/detail/{prod['slug']}")
    with urllib.request.urlopen(req) as resp:
        p_data = json.loads(resp.read().decode("utf-8"))
        assert p_data["stock_quantity"] == initial_stock - 1, "Stock did not decrement!"
        print(f"[VERIFIED] Stock decremented to {p_data['stock_quantity']}.")

    # 4. Admin accepts the new order
    req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/v1/admin/orders/{order_id}/accept",
        data=b"",
        headers={"Authorization": f"Bearer {admin_token}"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        accept_res = json.loads(resp.read().decode("utf-8"))
        print(f"[SUCCESS] Admin Accepted Order #{order_num}: {accept_res['status']}")
        assert accept_res["status"] == "Confirmed"

    # Verify status in database
    req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    with urllib.request.urlopen(req) as resp:
        o_detail = json.loads(resp.read().decode("utf-8"))
        assert o_detail["status"] == "Confirmed"
        print(f"[VERIFIED] Database order status confirmed: {o_detail['status']}")

    # 5. Now test Reject Order on another order to verify rejection + stock restoration
    # Add 1 item to cart again
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/cart/items",
        data=json.dumps({"product_id": prod_id, "quantity": 1}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {cust_token}"}
    )
    with urllib.request.urlopen(req) as resp:
        pass

    # Checkout second test order
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/orders/checkout",
        data=json.dumps(checkout_payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {cust_token}"}
    )
    with urllib.request.urlopen(req) as resp:
        order2 = json.loads(resp.read().decode("utf-8"))
        order2_id = order2["id"]
        order2_num = order2["order_number"]
        print(f"\n[INFO] Created second test order ID: {order2_id} (#{order2_num}) to test REJECT button")

    # Admin rejects order2
    reject_reason = "Customer unreachable by phone"
    req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/v1/admin/orders/{order2_id}/reject?reason={urllib.parse.quote(reject_reason)}",
        data=b"",
        headers={"Authorization": f"Bearer {admin_token}"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        reject_res = json.loads(resp.read().decode("utf-8"))
        print(f"[SUCCESS] Admin Rejected Order #{order2_num}: {reject_res['status']}")
        assert reject_res["status"] == "Cancelled"

    # Verify order 2 is Cancelled in database
    req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/v1/orders/{order2_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    with urllib.request.urlopen(req) as resp:
        o2_detail = json.loads(resp.read().decode("utf-8"))
        assert o2_detail["status"] == "Cancelled"
        assert o2_detail["cancellation_reason"] == reject_reason
        print(f"[VERIFIED] Order #{order2_num} is Cancelled with reason: '{o2_detail['cancellation_reason']}'")

    # Verify product stock was restored back
    req = urllib.request.Request(f"http://127.0.0.1:8000/api/v1/products/detail/{prod['slug']}")
    with urllib.request.urlopen(req) as resp:
        p_restored = json.loads(resp.read().decode("utf-8"))
        # We checked out 1 in order 1 (which was confirmed) and 1 in order 2 (which was rejected and restored)
        # So current stock should be initial_stock - 1
        assert p_restored["stock_quantity"] == initial_stock - 1
        print(f"[VERIFIED] Inventory stock successfully restored to {p_restored['stock_quantity']}.")

    print("\n[ALL TESTS PASSED SUCCESSFULLY!]")

if __name__ == "__main__":
    test_full_admin_order_lifecycle()
