"""steam.py — Steam inventory sync"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from models.models import User, get_db
from api.middleware.auth import get_current_user
from steam.integrations import steam_api

router = APIRouter()

@router.get("/inventory")
async def get_inventory(user: User = Depends(get_current_user)):
    if not user.steam_id:
        raise HTTPException(400, "Steam akkauntingiz ulanmagan")
    result = await steam_api.get_cs2_inventory(user.steam_id)
    return result

@router.get("/profile")
async def get_steam_profile(user: User = Depends(get_current_user)):
    if not user.steam_id:
        raise HTTPException(400, "Steam akkauntingiz ulanmagan")
    profile = await steam_api.get_player_summary(user.steam_id)
    return profile or {"error": "Profil topilmadi"}

@router.get("/price/{market_hash_name:path}")
async def get_item_price(market_hash_name: str):
    price = await steam_api.get_item_price(market_hash_name)
    return price or {"error": "Narx topilmadi"}
