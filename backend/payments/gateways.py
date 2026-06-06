"""
Payment Integrations — Payme, Click, Uzum Bank, UzCard/Humo
Blaze CS2 Marketplace
"""
import hashlib, base64, hmac, json, time
from typing import Optional
import httpx

from core.config import settings


# ═══════════════════════════════════════════════════════════════════════════════
#  PAYME (PAYCOM)
# ═══════════════════════════════════════════════════════════════════════════════

class PaymeService:
    """
    Payme JSONRPC 2.0 integration.
    Docs: https://developer.help.paycom.uz/
    """

    BASE_URL = settings.PAYME_API_URL

    def _auth_header(self, test: bool = False) -> dict:
        key = settings.PAYME_TEST_KEY if test else settings.PAYME_SECRET_KEY
        token = base64.b64encode(
            f"{settings.PAYME_MERCHANT_ID}:{key}".encode()
        ).decode()
        return {
            "X-Auth": token,
            "Content-Type": "application/json",
        }

    def generate_checkout_url(
        self, amount_som: int, order_id: int, description: str = "Blaze CS2 deposit"
    ) -> str:
        """Generate Payme checkout URL for redirect."""
        amount_tiyin = amount_som * 100
        params = {
            "m": settings.PAYME_MERCHANT_ID,
            "ac.order_id": str(order_id),
            "ac.description": description,
            "a": str(amount_tiyin),
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        encoded = base64.b64encode(query.encode()).decode()
        return f"{settings.PAYME_URL}/{encoded}"

    async def check_transaction(self, payme_tx_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.BASE_URL,
                headers=self._auth_header(test=settings.PAYME_TEST_MODE),
                json={
                    "id": 1,
                    "method": "CheckTransaction",
                    "params": {"id": payme_tx_id},
                },
                timeout=15,
            )
            return resp.json()

    async def create_transaction(
        self, amount_som: int, order_id: int, payme_tx_id: str
    ) -> dict:
        amount_tiyin = amount_som * 100
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.BASE_URL,
                headers=self._auth_header(test=settings.PAYME_TEST_MODE),
                json={
                    "id": 1,
                    "method": "CreateTransaction",
                    "params": {
                        "id": payme_tx_id,
                        "time": int(time.time() * 1000),
                        "amount": amount_tiyin,
                        "account": {"order_id": str(order_id)},
                    },
                },
                timeout=15,
            )
            return resp.json()

    def verify_callback(self, auth_header: str) -> bool:
        """Verify incoming Payme webhook auth."""
        try:
            decoded = base64.b64decode(auth_header.replace("Basic ", "")).decode()
            _, key = decoded.split(":", 1)
            expected = settings.PAYME_TEST_KEY if settings.PAYME_TEST_MODE else settings.PAYME_SECRET_KEY
            return key == expected
        except Exception:
            return False

    # Standard Payme RPC methods for webhook
    PAYME_METHODS = {
        "CheckPerformTransaction": "check_perform",
        "CreateTransaction": "create",
        "PerformTransaction": "perform",
        "CancelTransaction": "cancel",
        "CheckTransaction": "check",
        "GetStatement": "statement",
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  CLICK
# ═══════════════════════════════════════════════════════════════════════════════

class ClickService:
    """
    Click payment integration.
    Docs: https://docs.click.uz/
    """

    PAYMENT_URL = "https://my.click.uz/services/pay"

    def generate_payment_url(
        self, amount_som: int, order_id: int, return_url: str = ""
    ) -> str:
        """Generate Click payment URL."""
        return (
            f"{self.PAYMENT_URL}"
            f"?service_id={settings.CLICK_SERVICE_ID}"
            f"&merchant_id={settings.CLICK_MERCHANT_ID}"
            f"&amount={amount_som}"
            f"&transaction_param={order_id}"
            f"&return_url={return_url}"
        )

    def verify_prepare(
        self,
        click_trans_id: str,
        service_id: str,
        merchant_trans_id: str,
        amount: str,
        action: str,
        sign_time: str,
        sign_string: str,
    ) -> tuple[bool, str]:
        """Verify Click PREPARE webhook signature."""
        expected = hashlib.md5(
            f"{click_trans_id}"
            f"{settings.CLICK_SECRET_KEY}"
            f"{merchant_trans_id}"
            f"{amount}"
            f"{action}"
            f"{sign_time}".encode()
        ).hexdigest()
        if not hmac.compare_digest(expected, sign_string):
            return False, "SIGN_CHECK_FAILED"
        if service_id != settings.CLICK_SERVICE_ID:
            return False, "INVALID_SERVICE_ID"
        return True, "OK"

    def verify_complete(
        self,
        click_trans_id: str,
        merchant_trans_id: str,
        merchant_prepare_id: str,
        amount: str,
        action: str,
        sign_time: str,
        sign_string: str,
    ) -> tuple[bool, str]:
        """Verify Click COMPLETE webhook signature."""
        expected = hashlib.md5(
            f"{click_trans_id}"
            f"{settings.CLICK_SECRET_KEY}"
            f"{merchant_trans_id}"
            f"{merchant_prepare_id}"
            f"{amount}"
            f"{action}"
            f"{sign_time}".encode()
        ).hexdigest()
        if not hmac.compare_digest(expected, sign_string):
            return False, "SIGN_CHECK_FAILED"
        return True, "OK"


# ═══════════════════════════════════════════════════════════════════════════════
#  UZUM BANK
# ═══════════════════════════════════════════════════════════════════════════════

class UzumBankService:
    """
    Uzum Bank payment integration.
    Docs: https://developers.uzumbank.uz/
    """

    API_URL = settings.UZUM_API_URL

    def _headers(self) -> dict:
        token = base64.b64encode(
            f"{settings.UZUM_MERCHANT_ID}:{settings.UZUM_SECRET_KEY}".encode()
        ).decode()
        return {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
        }

    async def create_order(
        self, amount_som: int, order_id: int, description: str = "Blaze CS2"
    ) -> Optional[dict]:
        """Create Uzum payment order."""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"{self.API_URL}/payment/order/create",
                    headers=self._headers(),
                    json={
                        "serviceId": int(settings.UZUM_MERCHANT_ID),
                        "orderId": str(order_id),
                        "amount": amount_som * 100,  # tiyin
                        "currency": "UZS",
                        "description": description,
                        "returnUrl": f"{settings.WEBAPP_URL}/payment/success",
                        "failUrl": f"{settings.WEBAPP_URL}/payment/fail",
                    },
                    timeout=15,
                )
                data = resp.json()
                return data if resp.status_code == 200 else None
            except Exception:
                return None

    async def check_order(self, uzum_order_id: str) -> Optional[dict]:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{self.API_URL}/payment/order/{uzum_order_id}",
                    headers=self._headers(),
                    timeout=15,
                )
                return resp.json() if resp.status_code == 200 else None
            except Exception:
                return None

    def verify_webhook(self, signature: str, body: bytes) -> bool:
        expected = hmac.new(
            settings.UZUM_SECRET_KEY.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)


# ═══════════════════════════════════════════════════════════════════════════════
#  UZCARD / HUMO Gateway
# ═══════════════════════════════════════════════════════════════════════════════

class UzcardHumoService:
    """
    UzCard/Humo card payment gateway.
    This is a simplified implementation — actual gateway depends on your
    acquiring bank (e.g. Kapitalbank, Aloqabank, OCTO).
    """

    OCTO_API_URL = "https://secure.octo.uz/prepare_payment"

    def generate_payment_link(
        self, amount_som: int, order_id: int, card_type: str = "uzcard"
    ) -> str:
        """
        For manual card payments, show card number to user and they
        transfer + submit txid. Returns instruction payload.
        """
        card_info = {
            "uzcard": {
                "number": "8600 0000 0000 0000",   # Replace with your actual card
                "owner": "BLAZE CS2 MARKET",
                "bank": "Your Bank Name",
            },
            "humo": {
                "number": "9860 0000 0000 0000",   # Replace with your actual card
                "owner": "BLAZE CS2 MARKET",
                "bank": "Your Bank Name",
            },
        }
        info = card_info.get(card_type, card_info["uzcard"])
        return json.dumps({
            "type": card_type,
            "amount": amount_som,
            "order_id": order_id,
            **info,
            "note": f"Blaze #{order_id}",
        })

    async def create_octo_payment(
        self, amount_som: int, order_id: int
    ) -> Optional[dict]:
        """
        Create OCTO (Mastercard) payment session.
        Supports UzCard/Humo/Visa through OCTO acquiring.
        """
        async with httpx.AsyncClient() as client:
            try:
                payload = {
                    "octo_shop_id": settings.UZCARD_MERCHANT_ID,
                    "octo_secret": settings.UZCARD_SECRET,
                    "shop_transaction_id": str(order_id),
                    "total_sum": amount_som,
                    "currency": "UZS",
                    "tag": f"blaze_deposit_{order_id}",
                    "allow_card_save": False,
                    "ttl": 600,  # 10 minutes
                    "return_url": f"{settings.WEBAPP_URL}/payment/success",
                    "notify_url": f"{settings.WEBAPP_URL}/webhooks/octo",
                    "auto_capture": True,
                }
                resp = await client.post(
                    self.OCTO_API_URL,
                    json=payload,
                    timeout=15,
                )
                return resp.json() if resp.status_code == 200 else None
            except Exception:
                return None


# ── Singleton instances ──────────────────────────────────────────────────────
payme_service   = PaymeService()
click_service   = ClickService()
uzum_service    = UzumBankService()
uzcard_service  = UzcardHumoService()
