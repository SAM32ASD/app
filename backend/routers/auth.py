import logging
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from middleware.auth import verify_token
from models.database import get_db
from models.user import User, RefreshToken

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/auth", tags=["Auth"])


class GoogleAuthRequest(BaseModel):
    id_token: str


class RefreshRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict


def _create_access_token(user_id: str, email: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _create_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def _verify_google_token(id_token: str) -> dict:
    try:
        import firebase_admin
        from firebase_admin import auth as firebase_auth

        if not firebase_admin._apps:
            if settings.firebase_credentials_path:
                cred = firebase_admin.credentials.Certificate(settings.firebase_credentials_path)
                firebase_admin.initialize_app(cred)
            else:
                firebase_admin.initialize_app()

        decoded = firebase_auth.verify_id_token(id_token)
        return {
            "uid": decoded["uid"],
            "email": decoded.get("email", ""),
            "name": decoded.get("name", ""),
            "picture": decoded.get("picture", ""),
        }
    except ImportError:
        raise HTTPException(status_code=500, detail="Firebase Admin SDK not configured")
    except Exception as e:
        logger.warning(f"Google token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid Google token")


@router.post("/google", response_model=AuthResponse)
async def auth_google(
    request: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    google_user = await _verify_google_token(request.id_token)

    result = await db.execute(
        select(User).where(
            (User.firebase_uid == google_user["uid"]) | (User.email == google_user["email"])
        )
    )
    user = result.scalar_one_or_none()

    now = datetime.utcnow()

    if user is None:
        user = User(
            firebase_uid=google_user["uid"],
            email=google_user["email"],
            display_name=google_user["name"],
            photo_url=google_user["picture"],
            role="viewer",
            is_online=True,
            last_seen_at=now,
            created_at=now,
        )
        db.add(user)
        await db.flush()
        logger.info(f"New user created: {user.email} (role: viewer)")
    else:
        user.display_name = google_user["name"] or user.display_name
        user.photo_url = google_user["picture"] or user.photo_url
        user.last_seen_at = now
        user.is_online = True
        await db.flush()

    access_token = _create_access_token(str(user.id), user.email, user.role)
    raw_refresh = _create_refresh_token()

    refresh_entry = RefreshToken(
        user_id=user.id,
        token_hash=_hash_token(raw_refresh),
        expires_at=now + timedelta(days=settings.jwt_refresh_expire_days),
    )
    db.add(refresh_entry)

    return AuthResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        user={
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "display_name": user.display_name,
            "photo_url": user.photo_url,
        },
    )


@router.post("/refresh")
async def refresh_access_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    token_hash = _hash_token(request.refresh_token)

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,
        )
    )
    refresh_entry = result.scalar_one_or_none()

    if not refresh_entry:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if refresh_entry.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        refresh_entry.revoked = True
        raise HTTPException(status_code=401, detail="Refresh token expired")

    result = await db.execute(select(User).where(User.id == refresh_entry.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = _create_access_token(str(user.id), user.email, user.role)

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/verify")
async def verify(user: dict = Depends(verify_token)):
    return {
        "status": "authenticated",
        "uid": user.get("sub") or user.get("uid"),
        "email": user.get("email"),
        "role": user.get("role", "viewer"),
    }


@router.post("/logout")
async def logout(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(verify_token),
):
    token_hash = _hash_token(request.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    refresh_entry = result.scalar_one_or_none()
    if refresh_entry:
        refresh_entry.revoked = True

    db_user_result = await db.execute(
        select(User).where(User.id == (user.get("sub") or user.get("uid")))
    )
    db_user = db_user_result.scalar_one_or_none()
    if db_user:
        db_user.is_online = False

    return {"status": "logged_out"}
