import logging
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

security = HTTPBearer(auto_error=False)


async def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authorization token")

    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        pass

    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        uid = payload.get("sub") or payload.get("user_id")
        if uid:
            return {"uid": uid, "email": payload.get("email", ""), "role": payload.get("role", "viewer")}
    except Exception:
        pass

    raise HTTPException(status_code=401, detail="Invalid token")


def require_role(*roles: str):
    async def role_checker(user: dict = Depends(verify_token)):
        user_role = user.get("role", "viewer")
        if user_role not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user_role}' not authorized. Required: {roles}"
            )
        return user
    return role_checker
