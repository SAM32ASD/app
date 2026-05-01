from fastapi import APIRouter, Depends
from middleware.auth import verify_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/verify")
async def verify(user: dict = Depends(verify_token)):
    return {
        "status": "authenticated",
        "uid": user.get("uid"),
        "email": user.get("email"),
        "role": user.get("role", "viewer"),
    }
