"""
Steam Integration — OpenID login, profile, inventory sync
Blaze CS2 Marketplace
"""
import re
from typing import Optional
import httpx
from urllib.parse import urlencode, urlparse, parse_qs

from core.config import settings


STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"
STEAM_API_BASE   = "https://api.steampowered.com"
CS2_APP_ID       = 730


# ── OpenID helpers ───────────────────────────────────────────────────────────

def get_steam_login_url(return_url: str) -> str:
    """Build Steam OpenID redirect URL."""
    params = {
        "openid.ns":         "http://specs.openid.net/auth/2.0",
        "openid.mode":       "checkid_setup",
        "openid.return_to":  return_url,
        "openid.realm":      settings.STEAM_REALM,
        "openid.identity":   "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
    }
    return f"{STEAM_OPENID_URL}?{urlencode(params)}"


async def verify_steam_openid(params: dict) -> Optional[str]:
    """
    Verify Steam OpenID response and extract Steam64 ID.
    Returns steam_id string or None if invalid.
    """
    verify_params = dict(params)
    verify_params["openid.mode"] = "check_authentication"

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            STEAM_OPENID_URL,
            data=verify_params,
            timeout=15,
        )

    if "is_valid:true" not in resp.text:
        return None

    claimed_id = params.get("openid.claimed_id", "")
    match = re.search(r"https://steamcommunity\.com/openid/id/(\d+)", claimed_id)
    if not match:
        return None

    return match.group(1)


# ── Steam API calls ──────────────────────────────────────────────────────────

class SteamAPIService:

    async def get_player_summary(self, steam_id: str) -> Optional[dict]:
        """Fetch Steam profile info."""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{STEAM_API_BASE}/ISteamUser/GetPlayerSummaries/v2/",
                    params={
                        "key": settings.STEAM_API_KEY,
                        "steamids": steam_id,
                    },
                    timeout=15,
                )
                data = resp.json()
                players = data.get("response", {}).get("players", [])
                if players:
                    p = players[0]
                    return {
                        "steam_id":       p.get("steamid"),
                        "steam_username": p.get("personaname"),
                        "steam_avatar":   p.get("avatarfull"),
                        "profile_url":    p.get("profileurl"),
                        "visibility":     p.get("communityvisibilitystate"),
                    }
            except Exception:
                pass
        return None

    async def get_cs2_inventory(
        self, steam_id: str, start_assetid: str = ""
    ) -> dict:
        """
        Fetch CS2 inventory from Steam.
        Returns dict with items list and next cursor.
        """
        url = (
            f"https://steamcommunity.com/inventory/{steam_id}"
            f"/{CS2_APP_ID}/2"
        )
        params = {
            "l": "english",
            "count": 100,
        }
        if start_assetid:
            params["start_assetid"] = start_assetid

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, params=params, timeout=20)
                if resp.status_code == 200:
                    data = resp.json()
                    return self._parse_inventory(data)
                elif resp.status_code == 403:
                    return {"error": "inventory_private", "items": []}
                else:
                    return {"error": "steam_error", "items": []}
            except Exception as e:
                return {"error": str(e), "items": []}

    def _parse_inventory(self, raw: dict) -> dict:
        """Parse Steam inventory JSON into simplified item list."""
        if not raw or not raw.get("success"):
            return {"items": [], "more": False}

        assets      = {a["assetid"]: a for a in raw.get("assets", [])}
        descriptions = {
            f"{d['classid']}_{d['instanceid']}": d
            for d in raw.get("descriptions", [])
        }

        items = []
        for asset_id, asset in assets.items():
            key  = f"{asset['classid']}_{asset['instanceid']}"
            desc = descriptions.get(key, {})
            if not desc:
                continue

            # Only tradable items
            if not desc.get("tradable"):
                continue

            tags       = desc.get("tags", [])
            exterior   = next((t["localized_tag_name"] for t in tags if t.get("category") == "Exterior"), None)
            rarity     = next((t["localized_tag_name"] for t in tags if t.get("category") == "Rarity"), None)
            weapon_type = next((t["localized_tag_name"] for t in tags if t.get("category") == "Weapon"), None)

            items.append({
                "asset_id":   asset_id,
                "class_id":   asset["classid"],
                "name":       desc.get("market_hash_name", desc.get("name", "")),
                "icon_url":   f"https://community.akamai.steamstatic.com/economy/image/{desc.get('icon_url', '')}",
                "tradable":   bool(desc.get("tradable")),
                "exterior":   exterior,
                "rarity":     rarity,
                "weapon_type": weapon_type,
                "type":       desc.get("type", ""),
            })

        return {
            "items":      items,
            "total":      raw.get("total_inventory_count", len(items)),
            "more":       bool(raw.get("more_items")),
            "last_assetid": raw.get("last_assetid"),
        }

    async def get_item_price(self, market_hash_name: str) -> Optional[dict]:
        """Get Steam Market lowest price for an item."""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    "https://steamcommunity.com/market/priceoverview/",
                    params={
                        "appid":            CS2_APP_ID,
                        "currency":         1,  # USD
                        "market_hash_name": market_hash_name,
                    },
                    timeout=10,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success"):
                        return {
                            "lowest_price": data.get("lowest_price"),
                            "median_price": data.get("median_price"),
                            "volume":       data.get("volume"),
                        }
            except Exception:
                pass
        return None


# ── CSFloat API ──────────────────────────────────────────────────────────────

class CSFloatService:
    """
    CSFloat (formerly CSGOFloat) market API.
    Docs: https://csfloat.com/docs
    """
    BASE_URL = "https://csfloat.com/api/v1"

    def _headers(self) -> dict:
        return {
            "Authorization": settings.CSFLOAT_API_KEY,
            "Content-Type": "application/json",
        }

    async def get_listings(
        self,
        market_hash_name: str = "",
        min_price: int = 0,
        max_price: int = 0,
        limit: int = 20,
        page: int = 0,
        sort_by: str = "lowest_price",
    ) -> Optional[dict]:
        params = {
            "limit": limit,
            "page": page,
            "sort_by": sort_by,
        }
        if market_hash_name:
            params["market_hash_name"] = market_hash_name
        if min_price:
            params["min_price"] = min_price * 100  # cents
        if max_price:
            params["max_price"] = max_price * 100

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{self.BASE_URL}/listings",
                    params=params,
                    headers=self._headers(),
                    timeout=15,
                )
                return resp.json() if resp.status_code == 200 else None
            except Exception:
                return None

    async def get_listing(self, listing_id: str) -> Optional[dict]:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{self.BASE_URL}/listings/{listing_id}",
                    headers=self._headers(),
                    timeout=15,
                )
                return resp.json() if resp.status_code == 200 else None
            except Exception:
                return None

    async def get_float_value(self, inspect_url: str) -> Optional[float]:
        """Get float value for a specific item via inspect link."""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{self.BASE_URL}/inspect",
                    params={"url": inspect_url},
                    headers=self._headers(),
                    timeout=15,
                )
                if resp.status_code == 200:
                    return resp.json().get("iteminfo", {}).get("floatvalue")
            except Exception:
                pass
        return None


# ── Skinport API ─────────────────────────────────────────────────────────────

class SkinportService:
    """
    Skinport marketplace API.
    Docs: https://docs.skinport.com/
    """
    BASE_URL = "https://api.skinport.com/v1"

    def _headers(self) -> dict:
        return {
            "Authorization": f"Basic {base64_encode(settings.SKINPORT_API_KEY, settings.SKINPORT_SECRET)}",
            "Content-Type": "application/json",
        }

    async def get_items(
        self,
        app_id: int = CS2_APP_ID,
        currency: str = "USD",
        tradable: int = 1,
    ) -> Optional[list]:
        """Get all listed items (bulk endpoint, cached by Skinport for 5 min)."""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{self.BASE_URL}/items",
                    params={
                        "app_id": app_id,
                        "currency": currency,
                        "tradable": tradable,
                    },
                    headers=self._headers(),
                    timeout=30,
                )
                return resp.json() if resp.status_code == 200 else None
            except Exception:
                return None

    async def get_sales_history(
        self, market_hash_name: str, app_id: int = CS2_APP_ID
    ) -> Optional[list]:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{self.BASE_URL}/sales/history",
                    params={
                        "app_id": app_id,
                        "market_hash_name": market_hash_name,
                        "currency": "USD",
                    },
                    headers=self._headers(),
                    timeout=15,
                )
                return resp.json() if resp.status_code == 200 else None
            except Exception:
                return None


def base64_encode(key: str, secret: str) -> str:
    import base64
    return base64.b64encode(f"{key}:{secret}".encode()).decode()


# ── Singleton instances ──────────────────────────────────────────────────────
steam_api     = SteamAPIService()
csfloat_api   = CSFloatService()
skinport_api  = SkinportService()
