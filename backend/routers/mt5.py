import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from middleware.auth import verify_token, require_role
from models.database import get_db
from models.mt5_account import MT5Account
from services.encryption import encrypt_password, decrypt_password

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mt5", tags=["MT5"])

_engine_manager = None


def set_engine_manager(manager):
    global _engine_manager
    _engine_manager = manager


class MT5AccountCreate(BaseModel):
    broker: str
    account_number: str
    password: str
    server: str


class MT5AccountResponse(BaseModel):
    id: str
    broker: str
    account_number: str
    server: str
    is_active: bool
    connection_status: str
    last_connected_at: str | None


@router.post("/accounts", response_model=MT5AccountResponse)
async def add_mt5_account(
    request: MT5AccountCreate,
    user: dict = Depends(require_role("admin", "trader")),
    db: AsyncSession = Depends(get_db),
):
    user_id = user.get("sub") or user.get("uid")

    result = await db.execute(
        select(MT5Account).where(
            MT5Account.user_id == user_id,
            MT5Account.account_number == request.account_number,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.encrypted_password = encrypt_password(request.password)
        existing.server = request.server
        existing.broker = request.broker
        existing.is_active = True
        await db.flush()
        account = existing
    else:
        account = MT5Account(
            user_id=uuid.UUID(user_id),
            broker=request.broker,
            account_number=request.account_number,
            encrypted_password=encrypt_password(request.password),
            server=request.server,
        )
        db.add(account)
        await db.flush()

    return MT5AccountResponse(
        id=str(account.id),
        broker=account.broker,
        account_number=account.account_number,
        server=account.server,
        is_active=account.is_active,
        connection_status=account.connection_status,
        last_connected_at=account.last_connected_at.isoformat() if account.last_connected_at else None,
    )


@router.get("/accounts")
async def list_mt5_accounts(
    user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    user_id = user.get("sub") or user.get("uid")
    result = await db.execute(
        select(MT5Account).where(MT5Account.user_id == user_id).order_by(MT5Account.created_at.desc())
    )
    accounts = result.scalars().all()
    return {
        "accounts": [
            {
                "id": str(a.id),
                "broker": a.broker,
                "account_number": a.account_number,
                "server": a.server,
                "is_active": a.is_active,
                "connection_status": a.connection_status,
                "last_connected_at": a.last_connected_at.isoformat() if a.last_connected_at else None,
            }
            for a in accounts
        ]
    }


@router.post("/accounts/{account_id}/connect")
async def connect_mt5_account(
    account_id: str,
    user: dict = Depends(require_role("admin", "trader")),
    db: AsyncSession = Depends(get_db),
):
    user_id = user.get("sub") or user.get("uid")

    result = await db.execute(
        select(MT5Account).where(MT5Account.id == account_id, MT5Account.user_id == user_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="MT5 account not found")

    if account.connection_status == "CONNECTED":
        return {"status": "already_connected", "connection_status": "CONNECTED"}

    password = decrypt_password(account.encrypted_password)

    if _engine_manager is None:
        raise HTTPException(status_code=503, detail="Engine manager not available")

    success = await _engine_manager.connect_mt5(
        user_id=user_id,
        account_number=account.account_number,
        password=password,
        server=account.server,
    )

    if success:
        account.connection_status = "CONNECTED"
        account.last_connected_at = datetime.now(timezone.utc)
        return {"status": "connected", "connection_status": "CONNECTED"}
    else:
        account.connection_status = "ERROR"
        raise HTTPException(status_code=502, detail="Failed to connect to MT5 server")


@router.post("/accounts/{account_id}/disconnect")
async def disconnect_mt5_account(
    account_id: str,
    user: dict = Depends(require_role("admin", "trader")),
    db: AsyncSession = Depends(get_db),
):
    user_id = user.get("sub") or user.get("uid")

    result = await db.execute(
        select(MT5Account).where(MT5Account.id == account_id, MT5Account.user_id == user_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="MT5 account not found")

    if _engine_manager:
        await _engine_manager.disconnect_mt5(user_id)

    account.connection_status = "DISCONNECTED"
    return {"status": "disconnected", "connection_status": "DISCONNECTED"}


@router.get("/accounts/{account_id}/status")
async def get_mt5_account_status(
    account_id: str,
    user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    user_id = user.get("sub") or user.get("uid")

    result = await db.execute(
        select(MT5Account).where(MT5Account.id == account_id, MT5Account.user_id == user_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="MT5 account not found")

    live_status = account.connection_status
    if _engine_manager:
        live_status = _engine_manager.get_connection_status(user_id) or account.connection_status

    return {
        "account_id": str(account.id),
        "account_number": account.account_number,
        "connection_status": live_status,
        "last_connected_at": account.last_connected_at.isoformat() if account.last_connected_at else None,
    }
