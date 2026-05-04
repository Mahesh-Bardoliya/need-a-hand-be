import pytest

from need_a_hand_be.constants import API_PREFIX


@pytest.mark.asyncio
async def test_register_user(client):
    response = await client.post(
        f"{API_PREFIX}/auth/register",
        json={
            "name": "Test User",
            "username": "testuser",
            "email": "test@example.com",
            "password": "strongpassword123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    # The response should have set an access_token cookie
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_register_existing_email(client):
    # First registration
    await client.post(
        f"{API_PREFIX}/auth/register",
        json={
            "name": "Test User",
            "username": "testuser1",
            "email": "duplicate@example.com",
            "password": "strongpassword123",
        },
    )

    # Second registration with same email
    client.cookies.clear()
    response = await client.post(
        f"{API_PREFIX}/auth/register",
        json={
            "name": "Test User 2",
            "username": "testuser2",
            "email": "duplicate@example.com",
            "password": "strongpassword123",
        },
    )
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_user(client):
    # Register first
    await client.post(
        f"{API_PREFIX}/auth/register",
        json={
            "name": "Test User",
            "username": "loginuser",
            "email": "login@example.com",
            "password": "strongpassword123",
        },
    )

    # Clear cookies
    client.cookies.clear()

    # Login by username
    response = await client.post(
        f"{API_PREFIX}/auth/login",
        data={"username": "loginuser", "password": "strongpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "login@example.com"
    assert "access_token" in response.cookies

    # Clear and Login by email (supported now)
    client.cookies.clear()
    response = await client.post(
        f"{API_PREFIX}/auth/login",
        data={"username": "login@example.com", "password": "strongpassword123"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "loginuser"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    response = await client.post(
        f"{API_PREFIX}/auth/login",
        data={"username": "wronguser", "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout(client):
    # Register
    await client.post(
        f"{API_PREFIX}/auth/register",
        json={
            "name": "Test User",
            "username": "logoutuser",
            "email": "logout@example.com",
            "password": "strongpassword123",
        },
    )
    assert "access_token" in client.cookies

    # Logout (DELETE)
    response = await client.delete(f"{API_PREFIX}/auth/logout")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Successfully logged out."

    # Cookie should be deleted/expired
    assert not client.cookies.get("access_token")
