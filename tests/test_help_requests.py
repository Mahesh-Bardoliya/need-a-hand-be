import pytest
from httpx import ASGITransport
from httpx import AsyncClient

from need_a_hand_be.constants import API_PREFIX


@pytest.fixture
async def auth_client(client):
    """Fixture that registers and returns an authenticated client."""
    await client.post(
        f"{API_PREFIX}/auth/register",
        json={
            "name": "Requester User",
            "username": "requester",
            "email": "requester@example.com",
            "password": "strongpassword123",
        },
    )
    return client


@pytest.mark.asyncio
async def test_create_help_request(auth_client):
    response = await auth_client.post(
        f"{API_PREFIX}/help_requests",
        json={
            "title": "Need help moving a couch",
            "description": "It is quite heavy.",
            "location": "Downtown",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Need help moving a couch"
    assert "uuid" in data


@pytest.mark.asyncio
async def test_create_help_request_unauthorized(client):
    response = await client.post(
        f"{API_PREFIX}/help_requests",
        json={
            "title": "Need help with something",
            "description": "This is a detailed description that passes validation.",
            "location": "Somewhere City",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_help_requests(auth_client):
    # Create some requests
    for i in range(3):
        await auth_client.post(
            f"{API_PREFIX}/help_requests",
            json={
                "title": f"Help needed {i}",
                "description": "This is a sufficiently long description for testing.",
                "location": "Central City",
            },
        )

    response = await auth_client.post(f"{API_PREFIX}/help_requests/paginate", json={})
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 3
    assert data["size"] >= 3


@pytest.mark.asyncio
async def test_get_help_request_by_id(auth_client):
    create_res = await auth_client.post(
        f"{API_PREFIX}/help_requests",
        json={
            "title": "Specific Help Request",
            "description": "Providing a detailed description for this specific request.",
            "location": "North City",
        },
    )
    uuid = create_res.json()["uuid"]

    response = await auth_client.get(f"{API_PREFIX}/help_requests/{uuid}")
    assert response.status_code == 200
    assert response.json()["title"] == "Specific Help Request"


@pytest.mark.asyncio
async def test_delete_help_request(auth_client):
    create_res = await auth_client.post(
        f"{API_PREFIX}/help_requests",
        json={
            "title": "To Delete Request",
            "description": "Description for the request that is about to be deleted.",
            "location": "West City",
        },
    )
    uuid = create_res.json()["uuid"]

    # Another user tries to delete
    app = auth_client._transport.app
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as other_client:
        await other_client.post(
            f"{API_PREFIX}/auth/register",
            json={
                "name": "Other User",
                "username": "other",
                "email": "other@example.com",
                "password": "strongpassword456",
            },
        )

        del_res = await other_client.delete(f"{API_PREFIX}/help_requests/{uuid}")
        assert del_res.status_code == 403  # Unauthorized to delete (Forbidden)

    # Original user deletes
    del_res = await auth_client.delete(f"{API_PREFIX}/help_requests/{uuid}")
    assert del_res.status_code == 204

    # Verify deletion
    get_res = await auth_client.get(f"{API_PREFIX}/help_requests/{uuid}")
    assert get_res.status_code == 404
