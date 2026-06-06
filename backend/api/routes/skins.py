"""skins.py — Skin listing, search, favorites"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from models.models import Skin, Favorite, User, get_db
from api.middleware.auth import get_current_user, get_current_user_optional

router = APIRouter()

@router.get("/")
async def list_skins(
    weapon_type: Optional[str]  = None,
    search:      Optional[str]  = None,
    sort:        str            = "newest",
    min_price:   Optional[int]  = None,
    max_price:   Optional[int]  = None,
    exterior:    Optional[str]  = None,
    featured:    Optional[bool] = None,
    limit:       int            = 24,
    offset:      int            = 0,
    db:    AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    q = select(Skin).where(Skin.is_active == True, Skin.stock > 0)
    if weapon_type: q = q.where(Skin.weapon_type == weapon_type)
    if search:      q = q.where(Skin.name.ilike(f"%{search}%"))
    if min_price:   q = q.where(Skin.price >= min_price)
    if max_price:   q = q.where(Skin.price <= max_price)
    if exterior:    q = q.where(Skin.exterior == exterior)
    if featured:    q = q.where(Skin.is_featured == True)

    sort_map = {
        "newest":     Skin.created_at.desc(),
        "price_asc":  Skin.price.asc(),
        "price_desc": Skin.price.desc(),
        "featured":   Skin.is_featured.desc(),
    }
    q = q.order_by(sort_map.get(sort, Skin.created_at.desc())).limit(limit).offset(offset)
    result = await db.execute(q)
    skins  = result.scalars().all()

    # Get user favorites if logged in
    fav_ids = set()
    if user:
        favs = await db.execute(
            select(Favorite.skin_id).where(Favorite.user_id == user.id)
        )
        fav_ids = {r[0] for r in favs.all()}

    return [
        {
            "id": s.id, "name": s.name, "weapon_type": s.weapon_type,
            "collection": s.collection, "exterior": s.exterior, "rarity": s.rarity,
            "float_val": s.float_val, "pattern": s.pattern,
            "price": s.price, "market_price": s.market_price,
            "image_url": s.image_url, "inspect_url": s.inspect_url,
            "is_featured": s.is_featured, "stock": s.stock,
            "is_favorite": s.id in fav_ids,
        }
        for s in skins
    ]

@router.get("/featured")
async def featured_skins(limit: int = 6, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Skin).where(Skin.is_featured == True, Skin.is_active == True, Skin.stock > 0).limit(limit)
    )
    skins = result.scalars().all()
    return [{"id": s.id, "name": s.name, "exterior": s.exterior, "price": s.price,
             "image_url": s.image_url, "weapon_type": s.weapon_type, "rarity": s.rarity} for s in skins]

@router.get("/{skin_id}")
async def get_skin(skin_id: int, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException
    result = await db.execute(select(Skin).where(Skin.id == skin_id))
    s = result.scalar_one_or_none()
    if not s: raise HTTPException(404, "Skin topilmadi")
    return {"id": s.id, "name": s.name, "weapon_type": s.weapon_type, "collection": s.collection,
            "exterior": s.exterior, "rarity": s.rarity, "float_val": s.float_val,
            "pattern": s.pattern, "price": s.price, "market_price": s.market_price,
            "image_url": s.image_url, "inspect_url": s.inspect_url,
            "stickers": s.stickers, "is_featured": s.is_featured, "stock": s.stock}

@router.post("/{skin_id}/favorite")
async def toggle_favorite(
    skin_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy.exc import IntegrityError
    existing = await db.execute(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.skin_id == skin_id)
    )
    fav = existing.scalar_one_or_none()
    if fav:
        await db.delete(fav)
        await db.commit()
        return {"is_favorite": False}
    db.add(Favorite(user_id=user.id, skin_id=skin_id))
    await db.commit()
    return {"is_favorite": True}

@router.get("/user/favorites")
async def get_favorites(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Skin).join(Favorite, Favorite.skin_id == Skin.id).where(Favorite.user_id == user.id)
    )
    skins = result.scalars().all()
    return [{"id": s.id, "name": s.name, "exterior": s.exterior, "price": s.price,
             "image_url": s.image_url, "weapon_type": s.weapon_type} for s in skins]
