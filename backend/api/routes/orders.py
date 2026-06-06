"""
Orders Routes — Buy skin, order processing, status updates, trade offers
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from models.models import (
    Order, OrderStatus, Skin, User, Notification, get_db
)
from api.middleware.auth import get_current_user, require_admin
from core.config import settings

router = APIRouter()


class BuyRequest(BaseModel):
    skin_id:   int
    trade_url: Optional[str] = None


class OrderOut(BaseModel):
    id:             int
    skin_id:        int
    skin_name:      Optional[str]
    skin_image:     Optional[str]
    exterior:       Optional[str]
    price:          int
    status:         str
    trade_url:      Optional[str]
    trade_offer_id: Optional[str]
    notes:          Optional[str]
    created_at:     str
    updated_at:     Optional[str]


class AdminUpdateOrder(BaseModel):
    status:         OrderStatus
    notes:          Optional[str]    = None
    trade_offer_id: Optional[str]    = None


async def notify_user_order(
    db: AsyncSession,
    bot_token: str,
    user: User,
    order: Order,
    skin: Skin,
    status: OrderStatus,
):
    """Send Telegram notification to user about order status change."""
    import httpx
    msgs = {
        OrderStatus.CONFIRMED: (
            f"✅ <b>Buyurtma #{order.id} tasdiqlandi!</b>\n"
            f"🔫 {skin.name}\n"
            f"Trade offer jo'natilmoqda..."
        ),
        OrderStatus.SENT: (
            f"📤 <b>Buyurtma #{order.id} jo'natildi!</b>\n"
            f"🔫 {skin.name}\n"
            f"Steam Trade Offer ID: <code>{order.trade_offer_id or '—'}</code>\n"
            f"Trade URL ni tekshiring!"
        ),
        OrderStatus.DELIVERED: (
            f"🎉 <b>Buyurtma #{order.id} yetkazildi!</b>\n"
            f"🔫 {skin.name} — endi sizniki!\n"
            f"Xarid uchun rahmat! 🔥"
        ),
        OrderStatus.CANCELLED: (
            f"❌ <b>Buyurtma #{order.id} bekor qilindi.</b>\n"
            f"💰 {order.price:,} so'm balansga qaytarildi."
        ),
    }
    msg = msgs.get(status)
    if not msg or not user.telegram_id:
        return
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": user.telegram_id,
                    "text": msg,
                    "parse_mode": "HTML",
                },
                timeout=10,
            )
    except Exception:
        pass


# ── Buy skin ─────────────────────────────────────────────────────────────────

@router.post("/buy", response_model=dict)
async def buy_skin(
    body: BuyRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db:   AsyncSession = Depends(get_db),
):
    if user.is_banned:
        raise HTTPException(403, "Account banned")

    # Load skin
    result = await db.execute(
        select(Skin).where(Skin.id == body.skin_id, Skin.is_active == True)
    )
    skin = result.scalar_one_or_none()
    if not skin:
        raise HTTPException(404, "Skin topilmadi")
    if skin.stock < 1:
        raise HTTPException(400, "Skin tugagan (stok yo'q)")

    # Balance check
    if user.balance < skin.price:
        raise HTTPException(400, f"Balans yetarli emas. Kerak: {skin.price:,} so'm, mavjud: {user.balance:,} so'm")

    # Trade URL
    trade_url = body.trade_url or user.trade_url
    if not trade_url:
        raise HTTPException(400, "Trade URL ko'rsatilmagan. Profilda saqlang.")

    # Deduct balance & decrement stock atomically
    await db.execute(
        update(User)
        .where(User.id == user.id, User.balance >= skin.price)
        .values(balance=User.balance - skin.price, total_spent=User.total_spent + skin.price)
    )
    await db.execute(
        update(Skin)
        .where(Skin.id == skin.id, Skin.stock > 0)
        .values(stock=Skin.stock - 1)
    )

    # Create order
    order = Order(
        user_id   = user.id,
        skin_id   = skin.id,
        price     = skin.price,
        trade_url = trade_url,
        status    = OrderStatus.PENDING,
    )
    db.add(order)

    # In-app notification
    notif = Notification(
        user_id = user.id,
        title   = "Buyurtma qabul qilindi",
        message = f"#{order.id} buyurtmangiz — {skin.name}. Admin tez orada tasdiqlaydi.",
        type    = "info",
    )
    db.add(notif)

    await db.commit()
    await db.refresh(order)

    # Notify admins via Telegram (background)
    async def notify_admins():
        import httpx
        for aid in settings.admin_id_list:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage",
                        json={
                            "chat_id": aid,
                            "parse_mode": "HTML",
                            "text": (
                                f"🛒 <b>Yangi buyurtma #{order.id}!</b>\n"
                                f"👤 {user.first_name} (@{user.username or '—'})\n"
                                f"🔫 {skin.name} ({skin.exterior})\n"
                                f"💰 {skin.price:,} so'm\n"
                                f"🔗 Trade URL: {trade_url}"
                            ),
                        },
                        timeout=10,
                    )
            except Exception:
                pass

    background_tasks.add_task(notify_admins)

    return {"ok": True, "order_id": order.id, "status": order.status.value}


# ── Get user orders ───────────────────────────────────────────────────────────

@router.get("/", response_model=List[dict])
async def get_orders(
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None,
    user: User = Depends(get_current_user),
    db:   AsyncSession = Depends(get_db),
):
    q = (
        select(Order, Skin)
        .join(Skin, Order.skin_id == Skin.id)
        .where(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if status:
        q = q.where(Order.status == status)

    result = await db.execute(q)
    rows = result.all()

    return [
        {
            "id":             o.id,
            "skin_id":        o.skin_id,
            "skin_name":      s.name,
            "skin_image":     s.image_url,
            "exterior":       s.exterior,
            "weapon_type":    s.weapon_type,
            "price":          o.price,
            "status":         o.status.value,
            "trade_url":      o.trade_url,
            "trade_offer_id": o.trade_offer_id,
            "notes":          o.notes,
            "created_at":     o.created_at.isoformat(),
        }
        for o, s in rows
    ]


@router.get("/{order_id}")
async def get_order(
    order_id: int,
    user: User = Depends(get_current_user),
    db:   AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order, Skin)
        .join(Skin, Order.skin_id == Skin.id)
        .where(Order.id == order_id, Order.user_id == user.id)
    )
    row = result.first()
    if not row:
        raise HTTPException(404, "Buyurtma topilmadi")
    o, s = row
    return {
        "id": o.id, "skin_name": s.name, "skin_image": s.image_url,
        "exterior": s.exterior, "price": o.price, "status": o.status.value,
        "trade_url": o.trade_url, "trade_offer_id": o.trade_offer_id,
        "notes": o.notes, "created_at": o.created_at.isoformat(),
    }


# ── Admin order management ────────────────────────────────────────────────────

@router.get("/admin/all", dependencies=[Depends(require_admin)])
async def admin_get_orders(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(Order, Skin, User)
        .join(Skin, Order.skin_id == Skin.id)
        .join(User, Order.user_id == User.id)
        .order_by(Order.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if status:
        q = q.where(Order.status == status)

    result = await db.execute(q)
    rows = result.all()

    return [
        {
            "id":             o.id,
            "skin_name":      s.name,
            "exterior":       s.exterior,
            "weapon_type":    s.weapon_type,
            "skin_image":     s.image_url,
            "price":          o.price,
            "status":         o.status.value,
            "trade_url":      o.trade_url,
            "trade_offer_id": o.trade_offer_id,
            "user_id":        u.id,
            "username":       u.username,
            "first_name":     u.first_name,
            "telegram_id":    u.telegram_id,
            "notes":          o.notes,
            "admin_notes":    o.admin_notes,
            "created_at":     o.created_at.isoformat(),
            "updated_at":     o.updated_at.isoformat() if o.updated_at else None,
        }
        for o, s, u in rows
    ]


@router.patch("/admin/{order_id}", dependencies=[Depends(require_admin)])
async def admin_update_order(
    order_id: int,
    body: AdminUpdateOrder,
    background_tasks: BackgroundTasks,
    admin: User = Depends(require_admin),
    db:    AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Buyurtma topilmadi")

    prev_status = order.status
    order.status    = body.status
    order.admin_id  = admin.id
    order.updated_at = datetime.utcnow()

    if body.notes:
        order.admin_notes = body.notes
    if body.trade_offer_id:
        order.trade_offer_id = body.trade_offer_id
    if body.status == OrderStatus.CONFIRMED:
        order.confirmed_at = datetime.utcnow()
    if body.status == OrderStatus.DELIVERED:
        order.delivered_at = datetime.utcnow()

    # Refund on cancel
    if body.status == OrderStatus.CANCELLED and prev_status != OrderStatus.CANCELLED:
        await db.execute(
            update(User)
            .where(User.id == order.user_id)
            .values(
                balance=User.balance + order.price,
                total_spent=User.total_spent - order.price,
            )
        )
        await db.execute(
            update(Skin)
            .where(Skin.id == order.skin_id)
            .values(stock=Skin.stock + 1)
        )

    # Create in-app notification
    msgs = {
        OrderStatus.CONFIRMED: ("Buyurtma tasdiqlandi", f"#{order_id} buyurtmangiz tasdiqlandi. Trade offer kutilmoqda."),
        OrderStatus.SENT:      ("Trade offer jo'natildi", f"#{order_id} — trade offeringizni qabul qiling!"),
        OrderStatus.DELIVERED: ("Buyurtma yetkazildi", f"#{order_id} muvaffaqiyatli yetkazildi. 🎉"),
        OrderStatus.CANCELLED: ("Buyurtma bekor qilindi", f"#{order_id} bekor qilindi. {order.price:,} so'm qaytarildi."),
    }
    if body.status in msgs:
        title, msg = msgs[body.status]
        notif = Notification(
            user_id=order.user_id, title=title, message=msg, type="info"
        )
        db.add(notif)

    await db.commit()

    # Telegram notification (background)
    result2 = await db.execute(select(User).where(User.id == order.user_id))
    buyer = result2.scalar_one_or_none()
    result3 = await db.execute(select(Skin).where(Skin.id == order.skin_id))
    skin = result3.scalar_one_or_none()

    if buyer and skin:
        background_tasks.add_task(
            notify_user_order,
            db, settings.BOT_TOKEN, buyer, order, skin, body.status
        )

    return {"ok": True, "order_id": order_id, "status": body.status.value}
