"""telegram.py — Telegram bot webhook + channel subscription check"""
import hmac, hashlib, json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models.models import User, Referral, Notification, get_db
from api.middleware.auth import get_current_user
from core.config import settings
import httpx

router = APIRouter()


@router.get("/channel/check")
async def check_channel_subscription(
    user: User = Depends(get_current_user),
):
    """Check if user is subscribed to the required Telegram channel."""
    if not settings.CHANNEL_ID:
        return {"subscribed": True}
    try:
        async with httpx.AsyncClient() as c:
            resp = await c.get(
                f"https://api.telegram.org/bot{settings.BOT_TOKEN}/getChatMember",
                params={"chat_id": settings.CHANNEL_ID, "user_id": user.telegram_id},
                timeout=10,
            )
            data = resp.json()
            status = data.get("result", {}).get("status", "left")
            return {"subscribed": status in ("member", "administrator", "creator")}
    except Exception:
        return {"subscribed": False}


@router.post("/webhook")
async def telegram_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Telegram bot webhook handler.
    Handles /start with referral codes, promo codes, etc.
    This endpoint is for the bot's webhook — it processes updates server-side.
    """
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    # Verify webhook secret (set via setWebhook)
    # In production, set a secret token and verify it here

    body = await request.json()

    message = body.get("message") or body.get("callback_query", {}).get("message")
    if not message:
        return {"ok": True}

    text    = message.get("text", "")
    from_u  = body.get("message", {}).get("from") or body.get("callback_query", {}).get("from")
    if not from_u:
        return {"ok": True}

    tid = from_u["id"]

    # Handle /start with referral
    if text.startswith("/start"):
        args = text.split(" ")
        ref_code = None
        if len(args) > 1 and args[1].startswith("ref_"):
            ref_code = args[1][4:]

        result = await db.execute(select(User).where(User.telegram_id == tid))
        user = result.scalar_one_or_none()

        if user and ref_code and not user.referred_by_id:
            # Find referrer
            ref_result = await db.execute(
                select(User).where(User.referral_code == ref_code, User.telegram_id != tid)
            )
            referrer = ref_result.scalar_one_or_none()
            if referrer:
                user.referred_by_id = referrer.id
                referrer.balance     += settings.REFERRAL_BONUS
                referrer.referral_count += 1
                referrer.referral_earned += settings.REFERRAL_BONUS

                db.add(Referral(referrer_id=referrer.id, referred_id=user.id,
                                bonus_paid=settings.REFERRAL_BONUS))
                db.add(Notification(
                    user_id=referrer.id, title="Yangi referal! 👥",
                    message=f"{user.first_name} sizning havolangiz orqali ro'yxatdan o'tdi! +{settings.REFERRAL_BONUS:,} so'm",
                    type="success",
                ))
                await db.commit()

    return {"ok": True}


@router.post("/set-webhook")
async def set_webhook(secret: str, _=Depends(lambda: None)):
    """Helper endpoint to register bot webhook (call once during setup)."""
    webhook_url = f"{settings.WEBAPP_URL}/api/telegram/webhook"
    async with httpx.AsyncClient() as c:
        resp = await c.post(
            f"https://api.telegram.org/bot{settings.BOT_TOKEN}/setWebhook",
            json={"url": webhook_url, "secret_token": secret, "drop_pending_updates": True},
        )
        return resp.json()
