import pytest
from httpx import ASGITransport
from httpx import AsyncClient

from need_a_hand_be.constants import API_PREFIX


@pytest.fixture
async def clients(client):
    """Fixture that returns two authenticated clients."""
    # We can use the 'client' fixture's app to create another one
    app = client._transport.app
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c2:
        # client (c1) is already available from the fixture
        c1 = client

        await c1.post(
            f"{API_PREFIX}/auth/register",
            json={
                "name": "User One",
                "username": "user1",
                "email": "u1@example.com",
                "password": "strongpassword123",
            },
        )

        await c2.post(
            f"{API_PREFIX}/auth/register",
            json={
                "name": "User Two",
                "username": "user2",
                "email": "u2@example.com",
                "password": "strongpassword123",
            },
        )

        yield c1, c2


@pytest.mark.asyncio
async def test_offer_help(clients):
    c1, c2 = clients

    # User 1 creates request
    res = await c1.post(
        f"{API_PREFIX}/help_requests",
        json={
            "title": "Need help with garden",
            "description": "My garden is overgrown and I need someone to help me weed it.",
            "location": "Green Suburb",
        },
    )
    assert res.status_code == 201
    req_uuid = res.json()["uuid"]

    # User 2 offers help
    offer_res = await c2.post(
        f"{API_PREFIX}/help_offers",
        json={
            "help_request_uuid": req_uuid,
            "message": "I am a great gardener and can help you!",
        },
    )
    assert offer_res.status_code == 201
    offer_data = offer_res.json()
    assert offer_data["message"] == "I am a great gardener and can help you!"

    # User 1 cannot offer help to their own request
    self_offer_res = await c1.post(
        f"{API_PREFIX}/help_offers",
        json={
            "help_request_uuid": req_uuid,
            "message": "I can help myself with the garden.",
        },
    )
    assert self_offer_res.status_code == 400


@pytest.mark.asyncio
async def test_accept_offer(clients):
    c1, c2 = clients

    # User 1 creates request
    res = await c1.post(
        f"{API_PREFIX}/help_requests",
        json={
            "title": "Need help moving heavy furniture",
            "description": "I have a large sofa that needs moving to another room.",
            "location": "West End",
        },
    )
    req_uuid = res.json()["uuid"]

    # User 2 offers help
    offer_res = await c2.post(
        f"{API_PREFIX}/help_offers",
        json={
            "help_request_uuid": req_uuid,
            "message": "I am strong and available this weekend!",
        },
    )
    offer_uuid = offer_res.json()["uuid"]

    # User 2 tries to accept their own offer (should fail - only owner can accept)
    bad_accept = await c2.put(f"{API_PREFIX}/help_offers/{offer_uuid}/accept")
    # In our app logic, it raises 400 if not the owner of the request?
    # Let's check help_offers.py
    assert bad_accept.status_code in [400, 401, 403]

    # User 1 accepts the offer
    accept_res = await c1.put(f"{API_PREFIX}/help_offers/{offer_uuid}/accept")
    assert accept_res.status_code == 200

    # Check that offer is accepted
    assert accept_res.json()["is_accepted"] is True

    # Check that request is no longer active
    req_check = await c1.get(f"{API_PREFIX}/help_requests/{req_uuid}")
    assert req_check.json()["is_active"] is False
