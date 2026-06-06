"""users.py — User profile, referrals, daily bonus, notifications"""
from datetime import datetime, timedelta
import secrets, string
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from models.models import (
    User, Referral, PromoCode, PromoUse, Notification, get_db
)
from api.middleware.auth import get_current_user
from core.config import settings

router = APIRouter()


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id": user.id, "telegram_id": user.telegram_id,
        "username": user.username, "first_name": user.first_name,
        "last_name": user.last_name, "role": user.role.value,
        "balance": user.balance, "total_spent": user.total_spent,
        "total_deposited": user.total_deposited,
        "steam_id": user.steam_id, "steam_username": user.steam_username,
        "steam_avatar": user.steam_avatar, "trade_url": user.trade_url,
        "referral_code": user.referral_code, "referral_count": user.referral_count,
        "referral_earned": user.referral_earned, "daily_streak": user.daily_streak,
        "last_daily_bonus": user.last_daily_bonus.isoformat() if user.last_daily_bonus else None,
        "created_at": user.created_at.isoformat(),
    }


class UpdateProfileBody(BaseModel):
    trade_url: Optional[str] = None


@router.patch("/me")
async def update_profile(
    body: UpdateProfileBody,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.trade_url is not None:
        if body.trade_url and "steamcommunity.com/tradeoffer" not in body.trade_url:
            raise HTTPException(400, "Noto'g'ri Trade URL format")
        user.trade_url = body.trade_url
        await db.commit()
    return {"ok": True}


@router.post("/daily-bonus")
async def claim_daily_bonus(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.utcnow()
    if user.last_daily_bonus:
        diff = now - user.last_daily_bonus
        if diff.total_seconds() < 86400:
            next_in = 86400 - diff.total_seconds()
            raise HTTPException(400, f"Ertaga qayta oling! {int(next_in // 3600)}s {int((next_in % 3600) // 60)}m qoldi")
        # Check streak
        if diff.total_seconds() < 172800:
            user.daily_streak += 1
        else:
            user.daily_streak = 1
    else:
        user.daily_streak = 1

    streak_bonus = min(user.daily_streak * 500, 5000)  # max 5000 bonus
    amount = settings.DAILY_BONUS_AMOUNT + streak_bonus

    user.balance          += amount
    user.last_daily_bonus  = now
    notif = Notification(
        user_id=user.id,
        title="Kunlik bonus! 🎁",
        message=f"+{amount:,} so'm olindi! ({user.daily_streak} kun ketma-ket)",
        type="success",
    )
    db.add(notif)
    await db.commit()
    return {"ok": True, "amount": amount, "streak": user.daily_streak}


@router.post("/promo")
async def use_promo(
    code: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    code = code.upper().strip()
    now  = datetime.utcnow()

    result = await db.execute(
        select(PromoCode).where(PromoCode.code == code, PromoCode.is_active == True)
    )
    promo = result.scalar_one_or_none()
    if not promo:
        raise HTTPException(400, "Promo kod topilmadi yoki nofaol")
    if promo.expires_at and promo.expires_at < now:
        raise HTTPException(400, "Promo kod muddati tugagan")
    if promo.uses >= promo.max_uses:
        raise HTTPException(400, "Promo kod tugagan")

    used_check = await db.execute(
        select(PromoUse).where(PromoUse.user_id == user.id, PromoUse.promo_id == promo.id)
    )
    if used_check.scalar_one_or_none():
        raise HTTPException(400, "Bu kodni allaqachon ishlatgansiz")

    db.add(PromoUse(user_id=user.id, promo_id=promo.id))
    promo.uses     += 1
    user.balance   += promo.bonus_amount
    db.add(Notification(
        user_id=user.id, title="Promo kod qabul qilindi! 🎟",
        message=f"+{promo.bonus_amount:,} so'm qo'shildi!", type="success",
    ))
    await db.commit()
    return {"ok": True, "amount": promo.bonus_amount}


@router.get("/referrals")
async def get_referrals(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Referral, User)
        .join(User, Referral.referred_id == User.id)
        .where(Referral.referrer_id == user.id)
        .order_by(Referral.created_at.desc())
    )
    rows = result.all()
    return {
        "code": user.referral_code,
        "count": len(rows),
        "earned": user.referral_earned,
        "link": f"https://t.me/{settings.BOT_USERNAME}?start=ref_{user.referral_code}",
        "referrals": [
            {
                "username": u.username, "first_name": u.first_name,
                "joined_at": r.created_at.isoformat(),
            }
            for r, u in rows
        ],
    }


@router.get("/notifications")
async def get_notifications(
    limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    notifs = result.scalars().all()
    # Mark all as read
    await db.execute(
        update(Notification)
        .where(Notification.user_id == user.id, Notification.is_read == False)
        .values(is_read=True)
    )
    await db.commit()
    return [
        {
            "id": n.id, "title": n.title, "message": n.message,
            "type": n.type, "is_read": n.is_read,
            "created_at": n.created_at.isoformat(),
        }
        for n in notifs
    ]


@router.get("/notifications/unread-count")
async def unread_count(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import func
    result = await db.execute(
        select(func.count()).where(
            Notification.user_id == user.id, Notification.is_read == False
        )
    )
    return {"count": result.scalar() or 0}
