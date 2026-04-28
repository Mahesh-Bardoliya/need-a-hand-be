"""
Extended tests for /help_requests – pagination, filtering, search, validation,
and ownership-related edge-cases.
"""
import json as _json

import pytest
from httpx import ASGITransport
from httpx import AsyncClient

from need_a_hand_be.constants import API_PREFIX

# ── helpers ──────────────────────────────────────────────────────────────────


async def _create_request(
    client,
    *,
    title="General Help Request",
    description="This is a sufficiently long description for testing purposes.",
    location="Test City",
):
    res = await client.post(
        f"{API_PREFIX}/help_requests",
        json={
            "title": title,
            "description": description,
            "location": location,
        },
    )
    assert res.status_code == 201
    return res.json()


@pytest.fixture
async def auth_client2(client):
    """An independently authenticated client sharing the DB."""
    await client.post(
        f"{API_PREFIX}/auth/register",
        json={
            "name": "Owner",
            "username": "owner",
            "email": "owner@test.com",
            "password": "pass1234",
        },
    )
    return client


# ── validation ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_request_missing_title(auth_client2):
    """Creating a request without a title should fail with 422."""
    res = await auth_client2.post(
        f"{API_PREFIX}/help_requests", json={"description": "D", "location": "L"}
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_create_request_missing_description(auth_client2):
    res = await auth_client2.post(
        f"{API_PREFIX}/help_requests", json={"title": "T", "location": "L"}
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_create_request_missing_location(auth_client2):
    res = await auth_client2.post(
        f"{API_PREFIX}/help_requests", json={"title": "T", "description": "D"}
    )
    assert res.status_code == 422


# ── get by ID ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_nonexistent_request(auth_client2):
    res = await auth_client2.get(
        f"{API_PREFIX}/help_requests/00000000-0000-0000-0000-000000000000"
    )
    assert res.status_code == 404


# ── paginate: basic ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_paginate_returns_all_items(auth_client2):
    for i in range(5):
        await _create_request(auth_client2, title=f"Request {i}")

    res = await auth_client2.post(f"{API_PREFIX}/help_requests/paginate")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 5
    assert data["size"] == 5
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_paginate_respects_size(auth_client2):
    for i in range(5):
        await _create_request(auth_client2, title=f"Request {i}")

    res = await auth_client2.post(f"{API_PREFIX}/help_requests/paginate?size=2&page=1")
    assert res.status_code == 200
    assert len(res.json()["items"]) == 2


@pytest.mark.asyncio
async def test_paginate_page_2(auth_client2):
    for i in range(5):
        await _create_request(auth_client2, title=f"Request {i}")

    res = await auth_client2.post(f"{API_PREFIX}/help_requests/paginate?size=2&page=2")
    assert res.status_code == 200
    assert len(res.json()["items"]) == 2


@pytest.mark.asyncio
async def test_paginate_invalid_page(auth_client2):
    res = await auth_client2.post(f"{API_PREFIX}/help_requests/paginate?page=0")
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_paginate_invalid_size(auth_client2):
    res = await auth_client2.post(f"{API_PREFIX}/help_requests/paginate?size=0")
    assert res.status_code == 400


# ── paginate: search ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_paginate_search_matches_title(auth_client2):
    await _create_request(auth_client2, title="Moving a couch downtown")
    await _create_request(auth_client2, title="Fix my computer")

    res = await auth_client2.post(f"{API_PREFIX}/help_requests/paginate?search=couch")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert "couch" in items[0]["title"].lower()


@pytest.mark.asyncio
async def test_paginate_search_no_results(auth_client2):
    await _create_request(auth_client2, title="Gardening help")

    res = await auth_client2.post(
        f"{API_PREFIX}/help_requests/paginate?search=zzznomatch"
    )
    assert res.status_code == 200
    assert res.json()["size"] == 0


# ── paginate: filter by is_active ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_paginate_filter_active(auth_client2):
    """After accepting an offer, the request becomes inactive; filter should exclude it."""
    req = await _create_request(auth_client2, title="Active request")
    req_uuid = req["uuid"]

    app = auth_client2._transport.app
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as helper:
        await helper.post(
            f"{API_PREFIX}/auth/register",
            json={
                "name": "Helper",
                "username": "helper",
                "email": "helper@test.com",
                "password": "pass1234",
            },
        )
        offer_res = await helper.post(
            f"{API_PREFIX}/help_offers",
            json={"help_request_uuid": req_uuid, "message": "I can help"},
        )
        offer_uuid = offer_res.json()["uuid"]

    # Owner accepts => request goes inactive
    await auth_client2.put(f"{API_PREFIX}/help_offers/{offer_uuid}/accept")

    # Send query as a Form field (JSON string) — the route uses Form(...)
    res = await auth_client2.post(
        f"{API_PREFIX}/help_requests/paginate",
        data={"query": _json.dumps({"is_active": True})},
    )
    assert res.status_code == 200
    items = res.json()["items"]
    assert all(item["is_active"] for item in items)


# ── delete ownership ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_already_deleted_request(auth_client2):
    """Deleting a soft-deleted request should return 404."""
    req = await _create_request(auth_client2)
    uuid = req["uuid"]

    await auth_client2.delete(f"{API_PREFIX}/help_requests/{uuid}")
    res = await auth_client2.delete(f"{API_PREFIX}/help_requests/{uuid}")
    assert res.status_code == 404


# ── response shape ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_request_response_has_user(auth_client2):
    """The help request response must embed the creator's user info."""
    req = await _create_request(auth_client2)
    assert "user" in req
    assert req["user"]["username"] == "owner"


@pytest.mark.asyncio
async def test_request_is_active_by_default(auth_client2):
    """Newly created requests must have is_active = True."""
    req = await _create_request(auth_client2)
    assert req["is_active"] is True
