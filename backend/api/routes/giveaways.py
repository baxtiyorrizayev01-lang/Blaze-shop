"""giveaways.py"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from models.models import Giveaway, GiveawayParticipant, GiveawayStatus, User, Notification, get_db
from api.middleware.auth import get_current_user, require_admin
from core.config import settings

router = APIRouter()

@router.get("/")
async def list_giveaways(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            Giveaway,
            func.count(GiveawayParticipant.id).label("participant_count")
        )
        .outerjoin(GiveawayParticipant, GiveawayParticipant.giveaway_id == Giveaway.id)
        .where(Giveaway.status == GiveawayStatus.ACTIVE)
        .group_by(Giveaway.id)
        .order_by(Giveaway.end_time.asc())
    )
    rows = result.all()
    return [
        {
            "id": g.id, "title": g.title, "description": g.description,
            "prize_name": g.prize_name, "prize_image": g.prize_image,
            "max_participants": g.max_participants, "min_balance": g.min_balance,
            "participant_count": pc, "end_time": g.end_time.isoformat(),
            "require_channel": g.require_channel,
        }
        for g, pc in rows
    ]

@router.post("/{giveaway_id}/join")
async def join_giveaway(
    giveaway_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Giveaway).where(Giveaway.id == giveaway_id))
    gw = result.scalar_one_or_none()
    if not gw: raise HTTPException(404, "Giveaway topilmadi")
    if gw.status != GiveawayStatus.ACTIVE: raise HTTPException(400, "Giveaway tugagan")
    if gw.end_time < datetime.utcnow(): raise HTTPException(400, "Giveaway muddati o'tgan")
    if user.balance < gw.min_balance:
        raise HTTPException(400, f"Minimal balans: {gw.min_balance:,} so'm kerak")

    try:
        db.add(GiveawayParticipant(giveaway_id=giveaway_id, user_id=user.id))
        await db.commit()
        return {"ok": True}
    except IntegrityError:
        raise HTTPException(400, "Siz allaqachon qatnashyapsiz")

@router.get("/{giveaway_id}/status")
async def giveaway_status(
    giveaway_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(GiveawayParticipant).where(
            GiveawayParticipant.giveaway_id == giveaway_id,
            GiveawayParticipant.user_id == user.id
        )
    )
    return {"is_participating": existing.scalar_one_or_none() is not None}

class GiveawayCreateBody(BaseModel):
    title: str
    prize_name: str
    description: Optional[str] = None
    max_participants: int = 100
    min_balance: int = 0
    end_time: str
    require_channel: bool = False

@router.post("/", dependencies=[Depends(require_admin)])
async def create_giveaway(
    body: GiveawayCreateBody,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    gw = Giveaway(
        **body.model_dump(exclude={"end_time"}),
        end_time=datetime.fromisoformat(body.end_time),
        status=GiveawayStatus.ACTIVE,
        created_by=admin.id,
    )
    db.add(gw)
    await db.commit()
    return {"ok": True}

@router.post("/{giveaway_id}/pick-winner", dependencies=[Depends(require_admin)])
async def pick_winner(giveaway_id: int, db: AsyncSession = Depends(get_db)):
    import random
    result = await db.execute(
        select(GiveawayParticipant, User)
        .join(User, GiveawayParticipant.user_id == User.id)
        .where(GiveawayParticipant.giveaway_id == giveaway_id)
    )
    rows = result.all()
    if not rows: raise HTTPException(400, "Ishtirokchilar yo'q")
    gp, winner = random.choice(rows)

    result2 = await db.execute(select(Giveaway).where(Giveaway.id == giveaway_id))
    gw = result2.scalar_one_or_none()
    gw.status    = GiveawayStatus.ENDED
    gw.winner_id = winner.id

    db.add(Notification(
        user_id=winner.id, title="🎉 Giveaway g'olibisiz!",
        message=f"'{gw.title}' da g'olib bo'ldingiz! Sovg'a: {gw.prize_name}",
        type="success",
    ))
    await db.commit()

    import httpx
    try:
        async with httpx.AsyncClient() as c:
            await c.post(
                f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage",
                json={"chat_id": winner.telegram_id, "parse_mode": "HTML",
                      "text": f"🎉 <b>Tabriklaymiz!</b>\n🏆 {gw.prize_name} sizniki!\nAdmin bilan bog'laning."},
                timeout=10,
            )
    except Exception: pass

    return {"ok": True, "winner": {"id": winner.id, "username": winner.username,
                                    "first_name": winner.first_name, "telegram_id": winner.telegram_id}}
