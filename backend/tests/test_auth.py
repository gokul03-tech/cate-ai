"""
LexOrch-KG — Authentication & Profile Unit Tests
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Verify root endpoint displays API metadata and disclaimer."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "disclaimer" in data
    assert "SUPPORT" in data["disclaimer"]


@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    """Verify health check endpoint reports status."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "postgres" in data["services"]


@pytest.mark.asyncio
async def test_user_registration_and_login(client: AsyncClient, db_session: AsyncSession):
    """Verify registration, password rules validation, and login workflow."""
    # 1. Invalid role defaults to analyst
    reg_data = {
        "email": "test_analyst@lexorch.ai",
        "password": "PasswordVal@123",
        "first_name": "Jane",
        "last_name": "Smith",
        "role": "analyst"
    }
    response = await client.post("/api/v1/auth/register", json=reg_data)
    assert response.status_code == 201
    user_data = response.json()
    assert user_data["email"] == reg_data["email"]
    assert user_data["role"] == "analyst"
    assert "id" in user_data

    # 2. Duplicate registration fails with 409
    response = await client.post("/api/v1/auth/register", json=reg_data)
    assert response.status_code == 409

    # 3. Weak password validation fails
    weak_reg = reg_data.copy()
    weak_reg["email"] = "weak@lexorch.ai"
    weak_reg["password"] = "weak"
    response = await client.post("/api/v1/auth/register", json=weak_reg)
    assert response.status_code == 422

    # 4. Login with correct credentials returns token pair
    login_data = {
        "email": "test_analyst@lexorch.ai",
        "password": "PasswordVal@123"
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

    # 5. Profile /me access checks
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    profile = response.json()
    assert profile["email"] == reg_data["email"]
