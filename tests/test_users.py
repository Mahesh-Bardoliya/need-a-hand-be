import pytest
from httpx import ASGITransport
from httpx import AsyncClient

from need_a_hand_be.constants import API_PREFIX

# ── helpers ──────────────────────────────────────────────────────────────────


async def _register(
    client,
    *,
    username="user1",
    email="u1@test.com",
    name="User One",
    password="strongpassword123",
):
    res = await client.post(
        f"{API_PREFIX}/auth/register",
        json={
            "name": name,
            "username": username,
            "email": email,
            "password": password,
        },
    )
    return res


# ── /users/profile ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_own_profile_authenticated(client):
    """Authenticated user should receive their full profile."""
    await _register(client)
    res = await client.get(f"{API_PREFIX}/users/profile")
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == "user1"
    assert data["email"] == "u1@test.com"
    # profile schema fields
    assert "help_requests" in data
    assert "help_offers" in data
    assert "total_help_requests_count" in data
    assert "total_help_offers_count" in data


@pytest.mark.asyncio
async def test_get_profile_unauthenticated(client):
    """Unauthenticated request to /profile must return 401."""
    res = await client.get(f"{API_PREFIX}/users/profile")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_profile_counts_update_after_creating_request(client):
    """total_help_requests_count should reflect created requests."""
    await _register(client)

    # Initially zero
    profile_res = await client.get(f"{API_PREFIX}/users/profile")
    assert profile_res.status_code == 200
    profile = profile_res.json()
    assert profile["total_help_requests_count"] == 0

    # Create a request
    await client.post(
        f"{API_PREFIX}/help_requests",
        json={
            "title": "Need some help",
            "description": "This is a detailed description.",
            "location": "Somewhere City",
        },
    )

    profile = (await client.get(f"{API_PREFIX}/users/profile")).json()
    assert profile["total_help_requests_count"] == 1


# ── /users/{uuid} ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fetch_user_by_uuid(client):
    """Anyone should be able to fetch a public user profile by UUID."""
    await _register(client, username="publicuser", email="pub@test.com")

    # get UUID from own profile
    profile = (await client.get(f"{API_PREFIX}/users/profile")).json()
    user_uuid = profile["uuid"]

    # Fetch as the same user (or unauthenticated – route is open)
    client.cookies.clear()
    res = await client.get(f"{API_PREFIX}/users/{user_uuid}")
    assert res.status_code == 200
    assert res.json()["username"] == "publicuser"


@pytest.mark.asyncio
async def test_fetch_user_not_found(client):
    """Fetching a non-existent UUID returns 404."""
    res = await client.get(f"{API_PREFIX}/users/00000000-0000-0000-0000-000000000000")
    assert res.status_code == 404


# ── /auth/refresh ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_refresh_token(client):
    """Refresh should issue a new cookie and return the user object."""
    await _register(client)
    old_cookie = client.cookies.get("access_token")

    res = await client.get(f"{API_PREFIX}/auth/refresh")
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == "user1"
    # a new (or same) cookie is still present
    assert "access_token" in client.cookies


@pytest.mark.asyncio
async def test_refresh_unauthenticated(client):
    """Refresh without a valid cookie should return 401."""
    res = await client.get(f"{API_PREFIX}/auth/refresh")
    assert res.status_code == 401


# ── registration edge-cases ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_duplicate_username(client):
    """Registering with a taken username returns 400."""
    await _register(client, username="dupeuser", email="a@test.com")
    client.cookies.clear()
    res = await _register(client, username="dupeuser", email="b@test.com")
    assert res.status_code == 400
    assert "Username already taken" in res.json()["detail"]


@pytest.mark.asyncio
async def test_register_missing_fields(client):
    """Missing required fields should return 422 Unprocessable Entity."""
    res = await client.post(
        f"{API_PREFIX}/auth/register",
        json={
            "name": "No Email User",
            "username": "noemail",
            # email intentionally omitted
            "password": "pass1234",
        },
    )
    assert res.status_code == 422
