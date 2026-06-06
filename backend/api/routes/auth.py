"""
Auth Routes — Telegram WebApp + Steam OpenID
"""
import secrets, string
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.models import User, UserRole, get_db
from api.middleware.auth import (
    create_access_token, verify_telegram_init_data,
    get_current_user, CREDENTIALS_EXCEPTION
)
from steam.integrations import (
    get_steam_login_url, verify_steam_openid, steam_api
)
from core.config import settings

router = APIRouter()


def gen_referral_code() -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(8))


class TelegramAuthRequest(BaseModel):
    init_data: str


class TelegramAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    telegram_id: int
    role: str
    is_new: bool


@router.post("/telegram", response_model=TelegramAuthResponse)
async def telegram_auth(
    body: TelegramAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate via Telegram WebApp initData.
    Called when Mini App loads — verifies HMAC, upserts user, returns JWT.
    """
    tg_user = verify_telegram_init_data(body.init_data)
    if not tg_user:
        raise CREDENTIALS_EXCEPTION

    tid        = tg_user["id"]
    username   = tg_user.get("username")
    first_name = tg_user.get("first_name", "")
    last_name  = tg_user.get("last_name", "")

    # Upsert user
    result = await db.execute(select(User).where(User.telegram_id == tid))
    user   = result.scalar_one_or_none()
    is_new = False

    if user:
        # Update profile info
        user.username   = username
        user.first_name = first_name
        user.last_name  = last_name
        user.last_seen_at = datetime.utcnow()
        # Auto-promote if in ADMIN_IDS env
        if tid in settings.admin_id_list and user.role == UserRole.USER:
            user.role = UserRole.ADMIN
        await db.commit()
    else:
        is_new = True
        role = UserRole.ADMIN if tid in settings.admin_id_list else UserRole.USER
        user = User(
            telegram_id   = tid,
            username      = username,
            first_name    = first_name,
            last_name     = last_name,
            role          = role,
            referral_code = gen_referral_code(),
            last_seen_at  = datetime.utcnow(),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_access_token(
        user_id=user.id,
        telegram_id=user.telegram_id,
        role=user.role.value,
        jwt_version=user.jwt_version,
    )
    return TelegramAuthResponse(
        access_token=token,
        user_id=user.id,
        telegram_id=user.telegram_id,
        role=user.role.value,
        is_new=is_new,
    )


# ── Steam OpenID ─────────────────────────────────────────────────────────────

@router.get("/steam/login")
async def steam_login(user: User = Depends(get_current_user)):
    """Return Steam OpenID redirect URL."""
    return_url = f"{settings.STEAM_REALM}{settings.STEAM_RETURN_URL}"
    return {"redirect_url": get_steam_login_url(return_url)}


@router.get("/steam/callback")
async def steam_callback(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Steam OpenID callback.
    Verifies identity, fetches Steam profile, links to user.
    """
    params = dict(request.query_params)
    steam_id = await verify_steam_openid(params)
    if not steam_id:
        raise HTTPException(status_code=400, detail="Steam verification failed")

    # Check if steam_id already linked to another account
    result = await db.execute(
        select(User).where(User.steam_id == steam_id, User.id != user.id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Steam account already linked")

    # Fetch Steam profile
    profile = await steam_api.get_player_summary(steam_id)

    user.steam_id        = steam_id
    user.steam_username  = profile.get("steam_username") if profile else None
    user.steam_avatar    = profile.get("steam_avatar") if profile else None
    user.steam_linked_at = datetime.utcnow()

    await db.commit()
    return {
        "ok":            True,
        "steam_id":      steam_id,
        "steam_username": user.steam_username,
        "steam_avatar":  user.steam_avatar,
    }


@router.delete("/steam/unlink")
async def steam_unlink(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unlink Steam account."""
    user.steam_id        = None
    user.steam_username  = None
    user.steam_avatar    = None
    user.steam_linked_at = None
    await db.commit()
    return {"ok": True}
