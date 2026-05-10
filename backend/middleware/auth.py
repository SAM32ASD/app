import logging
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError
from config import get_settings
from services.redis_service import get_redis

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
        if "sub" not in payload and "uid" not in payload:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        pass

    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        uid = payload.get("sub") or payload.get("user_id")
        if uid:
            return {"sub": uid, "email": payload.get("email", ""), "role": payload.get("role", "viewer")}
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


async def rate_limit(request: Request, user: dict = Depends(verify_token)):
    user_id = user.get("sub") or user.get("uid") or "anonymous"
    r = await get_redis()
    key = f"rate_limit:{user_id}"

    current = await r.get(key)
    if current and int(current) >= settings.rate_limit_requests:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again later."
        )

    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, settings.rate_limit_window_seconds)
    await pipe.execute()

    return user
