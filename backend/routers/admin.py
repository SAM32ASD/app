import logging
from fastapi import APIRouter, Depends, HTTPException
from middleware.auth import require_role

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users")
async def list_users(user: dict = Depends(require_role("admin"))):
    return {"users": []}


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str, role: str,
    user: dict = Depends(require_role("admin")),
):
    if role not in ("admin", "trader", "viewer"):
        raise HTTPException(status_code=400, detail="Invalid role")
    return {"status": "updated", "user_id": user_id, "role": role}


@router.get("/audit")
async def get_audit_logs(
    page: int = 1, per_page: int = 50,
    user: dict = Depends(require_role("admin")),
):
    return {"logs": [], "page": page, "per_page": per_page, "total": 0}
