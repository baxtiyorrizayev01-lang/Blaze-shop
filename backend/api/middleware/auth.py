"""
JWT Auth + Security — Blaze CS2 Marketplace
"""
import hashlib, hmac, time, json
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.config import settings
from models.models import User, UserRole, get_db

security = HTTPBearer(auto_error=False)

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


# ── Token creation ───────────────────────────────────────────────────────────

def create_access_token(user_id: int, telegram_id: int,
                        role: str, jwt_version: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    data = {
        "sub": str(user_id),
        "tid": telegram_id,
        "role": role,
        "ver": jwt_version,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(data, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET,
                          algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise CREDENTIALS_EXCEPTION


# ── Telegram WebApp initData verification ────────────────────────────────────

def verify_telegram_init_data(init_data: str) -> Optional[dict]:
    """
    Verify Telegram WebApp initData HMAC signature.
    Returns parsed user dict if valid, None otherwise.
    """
    try:
        params = dict(p.split("=", 1) for p in init_data.split("&"))
        received_hash = params.pop("hash", None)
        if not received_hash:
            return None

        data_check = "\n".join(
            f"{k}={v}" for k, v in sorted(params.items())
        )

        secret = hmac.new(b"WebAppData",
                          settings.BOT_TOKEN.encode(),
                          hashlib.sha256).digest()
        expected = hmac.new(secret, data_check.encode(),
                            hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected, received_hash):
            return None

        # Check freshness (max 1 hour)
        auth_date = int(params.get("auth_date", 0))
        if time.time() - auth_date > 3600:
            return None

        user_str = params.get("user", "{}")
        return json.loads(user_str)
    except Exception:
        return None


# ── Dependency: current user ─────────────────────────────────────────────────

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    # 1) Check Authorization: Bearer JWT
    if credentials and credentials.credentials:
        payload = decode_token(credentials.credentials)
        user_id = int(payload.get("sub", 0))
        jwt_ver = payload.get("ver", 0)

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise CREDENTIALS_EXCEPTION
        if user.jwt_version != jwt_ver:
            raise CREDENTIALS_EXCEPTION  # Token revoked
        if user.is_banned:
            raise HTTPException(status_code=403, detail="Account banned")
        return user

    # 2) Fallback: X-Init-Data header (Telegram WebApp)
    init_data = request.headers.get("X-Init-Data")
    if init_data:
        tg_user = verify_telegram_init_data(init_data)
        if tg_user:
            tg_id = tg_user.get("id")
            result = await db.execute(
                select(User).where(User.telegram_id == tg_id)
            )
            user = result.scalar_one_or_none()
            if user:
                if user.is_banned:
                    raise HTTPException(status_code=403, detail="Account banned")
                return user

    raise CREDENTIALS_EXCEPTION


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    try:
        return await get_current_user(request, credentials, db)
    except HTTPException:
        return None


def require_role(*roles: UserRole):
    async def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles and user.telegram_id not in settings.admin_id_list:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency


require_admin = require_role(UserRole.ADMIN, UserRole.OWNER)
require_mod   = require_role(UserRole.MOD, UserRole.ADMIN, UserRole.OWNER)
