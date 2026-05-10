import uuid
from unittest.mock import patch, AsyncMock, MagicMock

import pytest
import pytest_asyncio

from services.encryption import encrypt_password, decrypt_password


class TestEncryption:
    def test_encrypt_decrypt_roundtrip(self):
        password = "MySecret123!"
        encrypted = encrypt_password(password)
        assert encrypted != password
        decrypted = decrypt_password(encrypted)
        assert decrypted == password

    def test_encrypted_is_different_each_time(self):
        password = "SamePassword"
        enc1 = encrypt_password(password)
        enc2 = encrypt_password(password)
        assert enc1 != enc2
        assert decrypt_password(enc1) == password
        assert decrypt_password(enc2) == password


@pytest.mark.asyncio
async def test_add_mt5_account(client, trader_token):
    resp = await client.post(
        "/api/v1/mt5/accounts",
        json={
            "broker": "Exness",
            "account_number": "12345678",
            "password": "mt5pass123",
            "server": "Exness-Real",
        },
        headers={"Authorization": f"Bearer {trader_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["broker"] == "Exness"
    assert data["account_number"] == "12345678"
    assert data["server"] == "Exness-Real"
    assert data["connection_status"] == "DISCONNECTED"


@pytest.mark.asyncio
async def test_list_mt5_accounts(client, trader_token):
    await client.post(
        "/api/v1/mt5/accounts",
        json={
            "broker": "Exness",
            "account_number": "11111111",
            "password": "pass1",
            "server": "Exness-Demo",
        },
        headers={"Authorization": f"Bearer {trader_token}"},
    )

    resp = await client.get(
        "/api/v1/mt5/accounts",
        headers={"Authorization": f"Bearer {trader_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "accounts" in data


@pytest.mark.asyncio
async def test_viewer_cannot_add_mt5_account(client, viewer_token):
    resp = await client.post(
        "/api/v1/mt5/accounts",
        json={
            "broker": "Exness",
            "account_number": "99999999",
            "password": "pass",
            "server": "Exness-Real",
        },
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_connect_mt5_account_success(client, trader_token):
    resp = await client.post(
        "/api/v1/mt5/accounts",
        json={
            "broker": "Exness",
            "account_number": "55555555",
            "password": "mypass",
            "server": "Exness-Real",
        },
        headers={"Authorization": f"Bearer {trader_token}"},
    )
    account_id = resp.json()["id"]

    mock_manager = MagicMock()
    mock_manager.connect_mt5 = AsyncMock(return_value=True)

    with patch("routers.mt5._engine_manager", mock_manager):
        resp = await client.post(
            f"/api/v1/mt5/accounts/{account_id}/connect",
            headers={"Authorization": f"Bearer {trader_token}"},
        )
    assert resp.status_code == 200
    assert resp.json()["connection_status"] == "CONNECTED"


@pytest.mark.asyncio
async def test_connect_mt5_account_failure(client, trader_token):
    resp = await client.post(
        "/api/v1/mt5/accounts",
        json={
            "broker": "Exness",
            "account_number": "66666666",
            "password": "badpass",
            "server": "Exness-Real",
        },
        headers={"Authorization": f"Bearer {trader_token}"},
    )
    account_id = resp.json()["id"]

    mock_manager = MagicMock()
    mock_manager.connect_mt5 = AsyncMock(return_value=False)

    with patch("routers.mt5._engine_manager", mock_manager):
        resp = await client.post(
            f"/api/v1/mt5/accounts/{account_id}/connect",
            headers={"Authorization": f"Bearer {trader_token}"},
        )
    assert resp.status_code == 502


@pytest.mark.asyncio
async def test_disconnect_mt5_account(client, trader_token):
    resp = await client.post(
        "/api/v1/mt5/accounts",
        json={
            "broker": "Exness",
            "account_number": "77777777",
            "password": "mypass",
            "server": "Exness-Real",
        },
        headers={"Authorization": f"Bearer {trader_token}"},
    )
    account_id = resp.json()["id"]

    mock_manager = MagicMock()
    mock_manager.disconnect_mt5 = AsyncMock(return_value=None)

    with patch("routers.mt5._engine_manager", mock_manager):
        resp = await client.post(
            f"/api/v1/mt5/accounts/{account_id}/disconnect",
            headers={"Authorization": f"Bearer {trader_token}"},
        )
    assert resp.status_code == 200
    assert resp.json()["connection_status"] == "DISCONNECTED"


@pytest.mark.asyncio
async def test_user_isolation_mt5_accounts(client, trader_token, admin_token):
    await client.post(
        "/api/v1/mt5/accounts",
        json={
            "broker": "Exness",
            "account_number": "88888888",
            "password": "pass_trader",
            "server": "Exness-Real",
        },
        headers={"Authorization": f"Bearer {trader_token}"},
    )

    resp = await client.get(
        "/api/v1/mt5/accounts",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    admin_accounts = resp.json()["accounts"]
    account_numbers = [a["account_number"] for a in admin_accounts]
    assert "88888888" not in account_numbers


@pytest.mark.asyncio
async def test_trading_start_requires_mt5_connected(client, trader_token):
    mock_manager = MagicMock()
    mock_manager.get_user_engine = MagicMock(return_value=None)

    with patch("routers.trading._engine_manager", mock_manager):
        resp = await client.post(
            "/api/v1/trading/start",
            headers={"Authorization": f"Bearer {trader_token}"},
        )
    assert resp.status_code == 400
    assert "Connect first" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_emergency_stop_admin_only(client, trader_token):
    mock_manager = MagicMock()
    with patch("routers.trading._engine_manager", mock_manager):
        resp = await client.post(
            "/api/v1/trading/emergency-stop",
            headers={"Authorization": f"Bearer {trader_token}"},
        )
    assert resp.status_code == 403
