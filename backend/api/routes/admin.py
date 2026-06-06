"""
Admin Routes — Analytics, Revenue, User Management, Skin CRUD
"""
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete, text

from models.models import (
    User, Skin, Order, Deposit, Giveaway, Notification,
    UserRole, OrderStatus, DepositStatus, PromoCode, AuditLog,
    DailyStats, MarketSource, get_db
)
from api.middleware.auth import get_current_user, require_admin, require_mod
from core.config import settings

router = APIRouter()


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard")
async def dashboard(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.utcnow()

    async def count(model, *filters):
        q = select(func.count()).select_from(model)
        for f in filters: q = q.where(f)
        r = await db.execute(q)
        return r.scalar()

    async def sum_col(model, col, *filters):
        q = select(func.coalesce(func.sum(col), 0)).select_from(model)
        for f in filters: q = q.where(f)
        r = await db.execute(q)
        return r.scalar() or 0

    today      = now.date()
    week_ago   = now - timedelta(days=7)
    month_ago  = now - timedelta(days=30)

    return {
        # User stats
        "total_users":        await count(User),
        "new_users_today":    await count(User, func.date(User.created_at) == today),
        "new_users_week":     await count(User, User.created_at >= week_ago),
        "banned_users":       await count(User, User.is_banned == True),
        "steam_linked":       await count(User, User.steam_id != None),

        # Order stats
        "total_orders":       await count(Order),
        "pending_orders":     await count(Order, Order.status == OrderStatus.PENDING),
        "confirmed_orders":   await count(Order, Order.status == OrderStatus.CONFIRMED),
        "delivered_orders":   await count(Order, Order.status == OrderStatus.DELIVERED),
        "cancelled_orders":   await count(Order, Order.status == OrderStatus.CANCELLED),
        "orders_today":       await count(Order, func.date(Order.created_at) == today),
        "orders_week":        await count(Order, Order.created_at >= week_ago),

        # Revenue
        "revenue_today":      await sum_col(Order, Order.price,
                                            func.date(Order.created_at) == today,
                                            Order.status != OrderStatus.CANCELLED),
        "revenue_week":       await sum_col(Order, Order.price,
                                            Order.created_at >= week_ago,
                                            Order.status != OrderStatus.CANCELLED),
        "revenue_month":      await sum_col(Order, Order.price,
                                            Order.created_at >= month_ago,
                                            Order.status != OrderStatus.CANCELLED),
        "revenue_total":      await sum_col(Order, Order.price,
                                            Order.status != OrderStatus.CANCELLED),

        # Deposit stats
        "pending_deposits":   await count(Deposit, Deposit.status == DepositStatus.PENDING),
        "deposits_today":     await sum_col(Deposit, Deposit.amount,
                                            func.date(Deposit.created_at) == today,
                                            Deposit.status == DepositStatus.CONFIRMED),

        # Inventory
        "total_skins":        await count(Skin, Skin.is_active == True),
        "out_of_stock":       await count(Skin, Skin.is_active == True, Skin.stock == 0),
        "featured_skins":     await count(Skin, Skin.is_featured == True),

        # Giveaways
        "active_giveaways":   await count(Giveaway),
    }


@router.get("/analytics/revenue")
async def revenue_chart(
    days: int = 30,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Daily revenue chart for the last N days."""
    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(
            func.date(Order.created_at).label("date"),
            func.coalesce(func.sum(Order.price), 0).label("revenue"),
            func.count(Order.id).label("orders"),
        )
        .where(Order.created_at >= since, Order.status != OrderStatus.CANCELLED)
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
    )
    rows = result.all()
    return [{"date": str(r.date), "revenue": r.revenue, "orders": r.orders} for r in rows]


@router.get("/analytics/users")
async def users_chart(
    days: int = 30,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Daily new user registrations for the last N days."""
    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(
            func.date(User.created_at).label("date"),
            func.count(User.id).label("new_users"),
        )
        .where(User.created_at >= since)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
    )
    rows = result.all()
    return [{"date": str(r.date), "new_users": r.new_users} for r in rows]


@router.get("/analytics/top_skins")
async def top_skins(
    limit: int = 10,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Top selling skins by revenue."""
    result = await db.execute(
        select(
            Skin.name,
            Skin.exterior,
            Skin.weapon_type,
            func.count(Order.id).label("sales"),
            func.coalesce(func.sum(Order.price), 0).label("revenue"),
        )
        .join(Order, Order.skin_id == Skin.id)
        .where(Order.status != OrderStatus.CANCELLED)
        .group_by(Skin.id)
        .order_by(func.sum(Order.price).desc())
        .limit(limit)
    )
    rows = result.all()
    return [{"name": r.name, "exterior": r.exterior, "weapon_type": r.weapon_type,
             "sales": r.sales, "revenue": r.revenue} for r in rows]


@router.get("/analytics/deposits")
async def deposit_chart(
    days: int = 30,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Daily confirmed deposits."""
    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(
            func.date(Deposit.created_at).label("date"),
            func.coalesce(func.sum(Deposit.amount), 0).label("amount"),
            func.count(Deposit.id).label("count"),
        )
        .where(Deposit.created_at >= since, Deposit.status == DepositStatus.CONFIRMED)
        .group_by(func.date(Deposit.created_at))
        .order_by(func.date(Deposit.created_at))
    )
    rows = result.all()
    return [{"date": str(r.date), "amount": r.amount, "count": r.count} for r in rows]


# ── User management ──────────────────────────────────────────────────────────

@router.get("/users")
async def admin_users(
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    _: User = Depends(require_mod),
    db: AsyncSession = Depends(get_db),
):
    q = select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
    if search:
        q = q.where(
            User.username.ilike(f"%{search}%") |
            User.first_name.ilike(f"%{search}%") |
            (User.telegram_id == int(search) if search.isdigit() else False)
        )
    result = await db.execute(q)
    users  = result.scalars().all()
    return [
        {
            "id": u.id, "telegram_id": u.telegram_id,
            "username": u.username, "first_name": u.first_name,
            "role": u.role.value, "is_banned": u.is_banned,
            "balance": u.balance, "total_spent": u.total_spent,
            "total_deposited": u.total_deposited,
            "steam_id": u.steam_id, "steam_username": u.steam_username,
            "referral_code": u.referral_code,
            "created_at": u.created_at.isoformat(),
            "last_seen_at": u.last_seen_at.isoformat() if u.last_seen_at else None,
        }
        for u in users
    ]


class UserUpdateBody(BaseModel):
    is_banned:  Optional[bool]      = None
    ban_reason: Optional[str]       = None
    role:       Optional[UserRole]  = None
    balance:    Optional[int]       = None  # direct set (for admin corrections)


@router.patch("/users/{user_id}")
async def admin_update_user(
    user_id: int,
    body: UserUpdateBody,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(404, "Foydalanuvchi topilmadi")

    if body.is_banned is not None:
        target.is_banned  = body.is_banned
        target.ban_reason = body.ban_reason
        # Invalidate JWT
        target.jwt_version += 1
    if body.role is not None:
        target.role = body.role
        target.jwt_version += 1
    if body.balance is not None:
        target.balance = body.balance

    # Audit log
    log = AuditLog(
        admin_id    = admin.id,
        action      = "update_user",
        target_id   = user_id,
        target_type = "user",
        details     = body.model_dump(exclude_none=True),
    )
    db.add(log)
    await db.commit()
    return {"ok": True}


# ── Skin management ──────────────────────────────────────────────────────────

class SkinCreateBody(BaseModel):
    name:        str
    weapon_type: str
    collection:  Optional[str] = None
    exterior:    str
    rarity:      Optional[str] = None
    float_val:   Optional[float] = None
    pattern:     Optional[int] = None
    price:       int
    image_url:   Optional[str] = None
    inspect_url: Optional[str] = None
    is_featured: bool = False
    stock:       int  = 1


@router.post("/skins")
async def admin_create_skin(
    body: SkinCreateBody,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    skin = Skin(**body.model_dump(), market_source=MarketSource.MANUAL)
    db.add(skin)
    await db.commit()
    await db.refresh(skin)
    return {"ok": True, "skin_id": skin.id}


class SkinUpdateBody(BaseModel):
    name:        Optional[str]   = None
    price:       Optional[int]   = None
    stock:       Optional[int]   = None
    is_featured: Optional[bool]  = None
    is_active:   Optional[bool]  = None
    image_url:   Optional[str]   = None
    inspect_url: Optional[str]   = None
    float_val:   Optional[float] = None
    pattern:     Optional[int]   = None


@router.patch("/skins/{skin_id}")
async def admin_update_skin(
    skin_id: int,
    body: SkinUpdateBody,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    vals = body.model_dump(exclude_none=True)
    if not vals:
        raise HTTPException(400, "Hech narsa o'zgartirilmadi")
    await db.execute(update(Skin).where(Skin.id == skin_id).values(**vals))
    await db.commit()
    return {"ok": True}


@router.delete("/skins/{skin_id}")
async def admin_delete_skin(
    skin_id: int,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(update(Skin).where(Skin.id == skin_id).values(is_active=False))
    await db.commit()
    return {"ok": True}


# ── Promo code management ────────────────────────────────────────────────────

class PromoCreateBody(BaseModel):
    code:         str
    bonus_amount: int
    max_uses:     int = 1
    expires_at:   Optional[str] = None


@router.post("/promos")
async def create_promo(
    body: PromoCreateBody,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    promo = PromoCode(
        code         = body.code.upper().strip(),
        bonus_amount = body.bonus_amount,
        max_uses     = body.max_uses,
        created_by   = admin.id,
        expires_at   = datetime.fromisoformat(body.expires_at) if body.expires_at else None,
    )
    db.add(promo)
    await db.commit()
    return {"ok": True}


@router.get("/promos")
async def list_promos(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PromoCode).order_by(PromoCode.created_at.desc())
    )
    promos = result.scalars().all()
    return [
        {
            "id": p.id, "code": p.code, "bonus_amount": p.bonus_amount,
            "max_uses": p.max_uses, "uses": p.uses, "is_active": p.is_active,
            "expires_at": p.expires_at.isoformat() if p.expires_at else None,
        }
        for p in promos
    ]


@router.delete("/promos/{promo_id}")
async def delete_promo(
    promo_id: int,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(PromoCode).where(PromoCode.id == promo_id).values(is_active=False)
    )
    await db.commit()
    return {"ok": True}


# ── Broadcast notification ────────────────────────────────────────────────────

class BroadcastBody(BaseModel):
    title:   str
    message: str
    user_ids: Optional[List[int]] = None  # None = all users


@router.post("/broadcast")
async def broadcast_notification(
    body: BroadcastBody,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if body.user_ids:
        users_q = await db.execute(
            select(User).where(User.id.in_(body.user_ids), User.is_banned == False)
        )
    else:
        users_q = await db.execute(
            select(User).where(User.is_banned == False)
        )
    users = users_q.scalars().all()

    notifs = [
        Notification(
            user_id=u.id, title=body.title, message=body.message, type="info"
        )
        for u in users
    ]
    db.add_all(notifs)
    await db.commit()

    # Also send Telegram message (background, best-effort)
    import httpx, asyncio
    async def send_tg():
        async with httpx.AsyncClient() as client:
            for u in users:
                if not u.telegram_id:
                    continue
                try:
                    await client.post(
                        f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage",
                        json={"chat_id": u.telegram_id, "parse_mode": "HTML",
                              "text": f"📢 <b>{body.title}</b>\n\n{body.message}"},
                        timeout=5,
                    )
                    await asyncio.sleep(0.05)  # ~20 msg/sec
                except Exception:
                    pass
    asyncio.create_task(send_tg())

    return {"ok": True, "sent_to": len(users)}


# ── Audit log ─────────────────────────────────────────────────────────────────

@router.get("/audit")
async def audit_log(
    limit: int = 100,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AuditLog, User)
        .join(User, AuditLog.admin_id == User.id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    rows = result.all()
    return [
        {
            "id": log.id, "action": log.action, "target_id": log.target_id,
            "target_type": log.target_type, "details": log.details,
            "admin": f"{admin.first_name} (@{admin.username})",
            "created_at": log.created_at.isoformat(),
        }
        for log, admin in rows
    ]
