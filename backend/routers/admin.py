import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from middleware.auth import require_role
from models.database import get_db
from models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users")
async def list_users(
    user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return {
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "role": u.role,
                "display_name": u.display_name,
                "is_online": u.is_online,
                "last_seen_at": u.last_seen_at.isoformat() if u.last_seen_at else None,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]
    }


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    if role not in ("admin", "trader", "viewer"):
        raise HTTPException(status_code=400, detail="Invalid role")

    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    target_user.role = role
    return {"status": "updated", "user_id": user_id, "new_role": role}


@router.get("/audit")
async def get_audit_logs(
    page: int = 1,
    per_page: int = 50,
    user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    from models.trading import AuditLog

    total_result = await db.execute(select(func.count(AuditLog.id)))
    total = total_result.scalar() or 0

    offset = (page - 1) * per_page
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).offset(offset).limit(per_page)
    )
    logs = result.scalars().all()

    return {
        "logs": [
            {
                "id": str(log.id),
                "user_id": str(log.user_id),
                "action": log.action,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "page": page,
        "per_page": per_page,
        "total": total,
    }
