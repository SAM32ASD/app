import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock

import pytest
import pytest_asyncio
from jose import jwt

from config import get_settings

settings = get_settings()


@pytest.mark.asyncio
async def test_verify_with_valid_token(client, admin_token):
    resp = await client.post(
        "/api/v1/auth/verify",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "authenticated"
    assert data["role"] == "admin"
    assert data["email"] == "admin@test.com"


@pytest.mark.asyncio
async def test_verify_with_expired_token(client, expired_token):
    resp = await client.post(
        "/api/v1/auth/verify",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_verify_without_token(client):
    resp = await client.post("/api/v1/auth/verify")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_verify_with_invalid_token(client):
    resp = await client.post(
        "/api/v1/auth/verify",
        headers={"Authorization": "Bearer invalid-garbage-token"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_google_auth_valid_token(client):
    mock_user = {
        "uid": "firebase_uid_123",
        "email": "newuser@gmail.com",
        "name": "New User",
        "picture": "https://photo.url/pic.jpg",
    }

    with patch("routers.auth._verify_google_token", new_callable=AsyncMock, return_value=mock_user):
        resp = await client.post(
            "/api/v1/auth/google",
            json={"id_token": "valid-google-token"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "newuser@gmail.com"
    assert data["user"]["role"] == "viewer"


@pytest.mark.asyncio
async def test_google_auth_invalid_token(client):
    with patch("routers.auth._verify_google_token", new_callable=AsyncMock, side_effect=Exception("Invalid")):
        resp = await client.post(
            "/api/v1/auth/google",
            json={"id_token": "invalid-token"},
        )
    assert resp.status_code in (401, 500)


@pytest.mark.asyncio
async def test_google_auth_creates_user_then_updates(client):
    mock_user = {
        "uid": "firebase_uid_456",
        "email": "repeat@gmail.com",
        "name": "First Name",
        "picture": "https://photo.url/1.jpg",
    }

    with patch("routers.auth._verify_google_token", new_callable=AsyncMock, return_value=mock_user):
        resp1 = await client.post("/api/v1/auth/google", json={"id_token": "token1"})
    assert resp1.status_code == 200
    assert resp1.json()["user"]["display_name"] == "First Name"

    mock_user["name"] = "Updated Name"
    mock_user["picture"] = "https://photo.url/2.jpg"

    with patch("routers.auth._verify_google_token", new_callable=AsyncMock, return_value=mock_user):
        resp2 = await client.post("/api/v1/auth/google", json={"id_token": "token2"})
    assert resp2.status_code == 200
    assert resp2.json()["user"]["display_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_refresh_token_valid(client):
    mock_user = {
        "uid": "firebase_uid_refresh",
        "email": "refresh@gmail.com",
        "name": "Refresh User",
        "picture": "",
    }

    with patch("routers.auth._verify_google_token", new_callable=AsyncMock, return_value=mock_user):
        login_resp = await client.post("/api/v1/auth/google", json={"id_token": "token"})

    refresh_token = login_resp.json()["refresh_token"]

    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_refresh_token_invalid(client):
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "totally-invalid-refresh-token"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_access_admin_route(client, admin_token):
    resp = await client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_viewer_blocked_from_admin_route(client, viewer_token):
    resp = await client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_viewer_blocked_from_trading_start(client, viewer_token):
    resp = await client.post(
        "/api/v1/trading/start",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_trader_can_start_trading(client, trader_token):
    resp = await client.post(
        "/api/v1/trading/start",
        headers={"Authorization": f"Bearer {trader_token}"},
    )
    # 200 or 503 (engine not initialized in test), but NOT 403
    assert resp.status_code != 403


@pytest.mark.asyncio
async def test_trader_blocked_from_emergency_stop(client, trader_token):
    resp = await client.post(
        "/api/v1/trading/emergency-stop",
        headers={"Authorization": f"Bearer {trader_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_rate_limiting(client, admin_token):
    """Rate limit is tested via the rate_limit dependency - not applied globally by default."""
    # This test verifies that the rate_limit function works when applied
    from middleware.auth import rate_limit
    from unittest.mock import MagicMock

    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value="11")  # Over limit
    mock_pipe = AsyncMock()
    mock_redis.pipeline = MagicMock(return_value=mock_pipe)

    with patch("middleware.auth.get_redis", new_callable=AsyncMock, return_value=mock_redis):
        from fastapi import HTTPException
        mock_request = MagicMock()
        user = {"sub": "test-user", "email": "test@test.com", "role": "admin"}
        try:
            await rate_limit(mock_request, user)
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 429
