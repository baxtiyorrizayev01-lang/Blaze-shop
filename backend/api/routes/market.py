"""market.py — CSFloat & Skinport price feeds"""
from typing import Optional
from fastapi import APIRouter, Depends
from api.middleware.auth import require_admin
from steam.integrations import csfloat_api, skinport_api

router = APIRouter()

@router.get("/csfloat/listings")
async def csfloat_listings(
    name: Optional[str] = None,
    limit: int = 20,
    _=Depends(require_admin),
):
    data = await csfloat_api.get_listings(market_hash_name=name or "", limit=limit)
    return data or {"error": "CSFloat API xatosi"}

@router.get("/skinport/items")
async def skinport_items(_=Depends(require_admin)):
    data = await skinport_api.get_items()
    if data:
        return {"count": len(data), "items": data[:50]}
    return {"error": "Skinport API xatosi"}
