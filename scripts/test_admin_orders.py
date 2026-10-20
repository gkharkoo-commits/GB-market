import urllib.request
import json

def test_live_order_flow():
    # 1. Login as Admin
    login_data = json.dumps({
        "identifier": "sattar.kharkoo@gmail.com",
        "password": "Admin@GBMarket2026!"
    }).encode("utf-8")

    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/auth/login",
        data=login_data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        token = json.loads(resp.read().decode("utf-8"))["access_token"]
        print("[SUCCESS] Admin logged in. Received JWT token.")

    # 2. Get list of orders
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/admin/orders",
        headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req) as resp:
        orders = json.loads(resp.read().decode("utf-8"))
        print(f"[SUCCESS] Fetched {len(orders)} orders from database:")
        for o in orders:
            print(f"  -> Order #{o['order_number']} | Customer: {o['customer_name']} | Status: {o['status']} | Amount: PKR {o['total_amount']}")

    if not orders:
        print("No orders to test.")
        return

    target_order = orders[0]
    target_id = target_order["id"]

    # 3. Accept Order
    print(f"\n[ACTION] Testing Accept Order for ID {target_id} (#{target_order['order_number']})...")
    req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/v1/admin/orders/{target_id}/accept",
        data=b"",
        headers={"Authorization": f"Bearer {token}"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print(f"[SUCCESS] Accept Order API Response: {res}")

    # 4. Verify updated status
    req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/v1/orders/{target_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req) as resp:
        updated = json.loads(resp.read().decode("utf-8"))
        print(f"[VERIFIED] Order status in database is now: {updated['status']}")
        assert updated["status"] == "Confirmed", f"Expected Confirmed, got {updated['status']}"

if __name__ == "__main__":
    test_live_order_flow()
