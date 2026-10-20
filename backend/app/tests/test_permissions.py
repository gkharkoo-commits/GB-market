import pytest

def test_admin_dashboard_access_allowed(client, admin_token):
    response = client.get(
        "/api/v1/admin/dashboard-stats",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_sales" in data
    assert "total_orders" in data

def test_customer_denied_admin_dashboard(client, customer_token):
    response = client.get(
        "/api/v1/admin/dashboard-stats",
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert response.status_code == 403
    assert "administrator privileges required" in response.json()["detail"].lower()

def test_anonymous_denied_admin_dashboard(client):
    response = client.get("/api/v1/admin/dashboard-stats")
    assert response.status_code == 401

def test_customer_denied_rider_deliveries(client, customer_token):
    response = client.get(
        "/api/v1/deliveries/my-deliveries",
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert response.status_code == 403
    assert "delivery rider" in response.json()["detail"].lower()
