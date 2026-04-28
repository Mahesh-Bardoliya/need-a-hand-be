"""
Extended tests for /help_offers – edge-cases around creation and acceptance.
"""
import pytest
from httpx import ASGITransport
from httpx import AsyncClient

from need_a_hand_be.constants import API_PREFIX

# ── helpers ──────────────────────────────────────────────────────────────────


async def _two_client_setup(base_client):
    """Register owner on base_client, return (base_client, helper_client)."""
    app = base_client._transport.app
    await base_client.post(
        f"{API_PREFIX}/auth/register",
        json={
            "name": "Owner",
            "username": "owner",
            "email": "owner@test.com",
            "password": "pass1234",
        },
    )
    helper = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    await helper.post(
        f"{API_PREFIX}/auth/register",
        json={
            "name": "Helper",
            "username": "helper",
            "email": "helper@test.com",
            "password": "pass1234",
        },
    )
    return base_client, helper


async def _create_request(owner_client, *, title="Help Request Title"):
    res = await owner_client.post(
        f"{API_PREFIX}/help_requests",
        json={
            "title": title,
            "description": "This is a detailed description for testing.",
            "location": "Test City",
        },
    )
    assert res.status_code == 201
    return res.json()["uuid"]


# ── unauthenticated ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_offer_without_auth(client):
    res = await client.post(
        f"{API_PREFIX}/help_offers",
        json={
            "help_request_uuid": "00000000-0000-0000-0000-000000000000",
            "message": "I can help with that",
        },
    )
    assert res.status_code == 401


# ── 404 on non-existent request ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_offer_on_nonexistent_request(client):
    await client.post(
        f"{API_PREFIX}/auth/register",
        json={
            "name": "Helper User",
            "username": "helper_h",
            "email": "h@test.com",
            "password": "pass1234password",
        },
    )
    res = await client.post(
        f"{API_PREFIX}/help_offers",
        json={
            "help_request_uuid": "00000000-0000-0000-0000-000000000000",
            "message": "Happy to help",
        },
    )
    assert res.status_code == 404


# ── own-request guard ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cannot_offer_on_own_request(client):
    await client.post(
        f"{API_PREFIX}/auth/register",
        json={
            "name": "Self",
            "username": "self",
            "email": "self@test.com",
            "password": "pass1234",
        },
    )
    req_uuid = await _create_request(client, title="My own request")
    res = await client.post(
        f"{API_PREFIX}/help_offers",
        json={"help_request_uuid": req_uuid, "message": "helping myself"},
    )
    assert res.status_code == 400


# ── accept: 404 on non-existent offer ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_accept_nonexistent_offer(client):
    await client.post(
        f"{API_PREFIX}/auth/register",
        json={
            "name": "User X",
            "username": "user_x",
            "email": "x@test.com",
            "password": "pass1234password",
        },
    )
    res = await client.put(
        f"{API_PREFIX}/help_offers/00000000-0000-0000-0000-000000000000/accept"
    )
    assert res.status_code == 404


# ── accept: inactive request ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_accept_offer_on_inactive_request(client):
    """After a request is closed (one offer accepted), accepting another offer fails."""
    owner, helper = await _two_client_setup(client)
    req_uuid = await _create_request(owner)

    # helper makes two offers
    o1 = (
        await helper.post(
            f"{API_PREFIX}/help_offers",
            json={"help_request_uuid": req_uuid, "message": "offer number 1"},
        )
    ).json()["uuid"]

    # Need a third user for a second offer (same user can't offer twice in one request—
    # but the BE doesn't enforce uniqueness yet, so we just do second offer as same helper)
    o2 = (
        await helper.post(
            f"{API_PREFIX}/help_offers",
            json={"help_request_uuid": req_uuid, "message": "offer number 2"},
        )
    ).json()["uuid"]

    # owner accepts first offer → request deactivated
    accept_res = await owner.put(f"{API_PREFIX}/help_offers/{o1}/accept")
    assert accept_res.status_code == 200

    # second acceptance must fail because request is no longer active
    res = await owner.put(f"{API_PREFIX}/help_offers/{o2}/accept")
    assert res.status_code == 400


# ── accept: wrong user (not request owner) ────────────────────────────────────


@pytest.mark.asyncio
async def test_helper_cannot_accept_own_offer(client):
    owner, helper = await _two_client_setup(client)
    req_uuid = await _create_request(owner)

    offer_uuid = (
        await helper.post(
            f"{API_PREFIX}/help_offers",
            json={"help_request_uuid": req_uuid, "message": "I can help"},
        )
    ).json()["uuid"]

    # helper tries to accept their own offer
    res = await helper.put(f"{API_PREFIX}/help_offers/{offer_uuid}/accept")
    assert res.status_code == 403
    await helper.aclose()


# ── response shape ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_offer_response_shape(client):
    owner, helper = await _two_client_setup(client)
    req_uuid = await _create_request(owner)

    res = await helper.post(
        f"{API_PREFIX}/help_offers",
        json={"help_request_uuid": req_uuid, "message": "Ready to help!"},
    )
    assert res.status_code == 201
    data = res.json()
    assert "uuid" in data
    assert data["message"] == "Ready to help!"
    assert data["is_accepted"] is False
    assert "helper" in data
    await helper.aclose()
