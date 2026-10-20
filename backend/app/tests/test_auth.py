import pytest

def test_register_success(client):
    response = client.post("/api/v1/auth/register", json={
        "full_name": "Test User",
        "email": "new.customer@gbmarket.pk",
        "phone": "03409998877",
        "password": "SecurePassword123!",
        "password_confirm": "SecurePassword123!"
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["email"] == "new.customer@gbmarket.pk"
    assert data["role"] == "customer"

def test_register_password_mismatch(client):
    response = client.post("/api/v1/auth/register", json={
        "full_name": "Mismatch User",
        "email": "mismatch@gbmarket.pk",
        "phone": "03409998878",
        "password": "Password123!",
        "password_confirm": "DifferentPassword123!"
    })
    assert response.status_code == 422
    assert "Passwords do not match" in response.json()["detail"]

def test_login_success(client, customer_user):
    response = client.post("/api/v1/auth/login", json={
        "identifier": customer_user.email,
        "password": "CustomerPass123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user_id"] == customer_user.id

def test_login_invalid_credentials(client, customer_user):
    response = client.post("/api/v1/auth/login", json={
        "identifier": customer_user.email,
        "password": "WrongPassword999!"
    })
    assert response.status_code == 401
    assert "Invalid email/phone or password" in response.json()["detail"]

def test_get_me_authenticated(client, customer_user, customer_token):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == customer_user.id
    assert data["email"] == customer_user.email

def test_get_me_unauthorized(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
