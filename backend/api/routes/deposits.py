"""
Deposits Routes — Payme, Click, Uzum Bank, UzCard/Humo webhooks + manual
"""
import hashlib, json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from models.models import Deposit, DepositMethod, DepositStatus, User, Notification, get_db
from api.middleware.auth import get_current_user, require_admin
from payments.gateways import payme_service, click_service, uzum_service, uzcard_service
from core.config import settings

router = APIRouter()


class InitDepositRequest(BaseModel):
    amount:  int            # som
    method:  DepositMethod


class ManualDepositRequest(BaseModel):
    amount:         int
    method:         DepositMethod   # uzcard or humo
    transaction_id: str             # txid the user submits manually
    screenshot_url: Optional[str]   = None


class DepositOut(BaseModel):
    id:             int
    amount:         int
    method:         str
    status:         str
    transaction_id: Optional[str]
    created_at:     str


async def credit_user(db: AsyncSession, deposit: Deposit):
    """Credit user balance and mark deposit confirmed."""
    await db.execute(
        update(User)
        .where(User.id == deposit.user_id)
        .values(
            balance=User.balance + deposit.amount,
            total_deposited=User.total_deposited + deposit.amount,
        )
    )
    deposit.status       = DepositStatus.CONFIRMED
    deposit.confirmed_at = datetime.utcnow()
    notif = Notification(
        user_id = deposit.user_id,
        title   = "To'lov tasdiqlandi ✅",
        message = f"{deposit.amount:,} so'm balansga qo'shildi!",
        type    = "success",
    )
    db.add(notif)
    await db.commit()


async def telegram_notify_admin(amount: int, method: str, username: str, tid: str):
    import httpx
    for aid in settings.admin_id_list:
        try:
            async with httpx.AsyncClient() as c:
                await c.post(
                    f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": aid,
                        "parse_mode": "HTML",
                        "text": (
                            f"💳 <b>Yangi to'lov!</b>\n"
                            f"👤 @{username or '—'} ({tid})\n"
                            f"💰 {amount:,} so'm | {method}"
                        ),
                    },
                    timeout=10,
                )
        except Exception:
            pass


# ── Initiate deposit ──────────────────────────────────────────────────────────

@router.post("/init")
async def init_deposit(
    body: InitDepositRequest,
    user: User = Depends(get_current_user),
    db:   AsyncSession = Depends(get_db),
):
    if body.amount < settings.MIN_DEPOSIT:
        raise HTTPException(400, f"Minimal summa: {settings.MIN_DEPOSIT:,} so'm")
    if body.amount > settings.MAX_DEPOSIT:
        raise HTTPException(400, f"Maksimal summa: {settings.MAX_DEPOSIT:,} so'm")

    # Create pending deposit record
    deposit = Deposit(
        user_id = user.id,
        amount  = body.amount,
        method  = body.method,
        status  = DepositStatus.PENDING,
    )
    db.add(deposit)
    await db.commit()
    await db.refresh(deposit)

    response = {"deposit_id": deposit.id, "amount": body.amount, "method": body.method.value}

    if body.method == DepositMethod.PAYME:
        url = payme_service.generate_checkout_url(body.amount, deposit.id)
        response["payment_url"] = url

    elif body.method == DepositMethod.CLICK:
        url = click_service.generate_payment_url(
            body.amount, deposit.id,
            return_url=f"{settings.WEBAPP_URL}/payment/success"
        )
        response["payment_url"] = url

    elif body.method == DepositMethod.UZUM:
        order = await uzum_service.create_order(body.amount, deposit.id)
        if order:
            deposit.uzum_order_id = order.get("orderId")
            await db.commit()
            response["payment_url"] = order.get("paymentUrl")
        else:
            response["error"] = "Uzum xizmati vaqtincha ishlamayapti"

    elif body.method in (DepositMethod.UZCARD, DepositMethod.HUMO):
        card_info = json.loads(
            uzcard_service.generate_payment_link(body.amount, deposit.id, body.method.value)
        )
        response["card_info"] = card_info

    return response


# ── Manual deposit (UzCard/Humo txid submit) ─────────────────────────────────

@router.post("/manual")
async def manual_deposit(
    body: ManualDepositRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db:   AsyncSession = Depends(get_db),
):
    if body.amount < settings.MIN_DEPOSIT:
        raise HTTPException(400, f"Minimal summa: {settings.MIN_DEPOSIT:,} so'm")

    # Check txid not already used
    result = await db.execute(
        select(Deposit).where(Deposit.transaction_id == body.transaction_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(400, "Bu tranzaksiya ID allaqachon ishlatilgan")

    deposit = Deposit(
        user_id        = user.id,
        amount         = body.amount,
        method         = body.method,
        transaction_id = body.transaction_id,
        screenshot_url = body.screenshot_url,
        status         = DepositStatus.PENDING,
    )
    db.add(deposit)
    await db.commit()

    background_tasks.add_task(
        telegram_notify_admin,
        body.amount, body.method.value, user.username, str(user.telegram_id)
    )
    return {"ok": True, "message": "To'lov so'rovi yuborildi. Admin tekshiradi."}


# ── Payme webhook ─────────────────────────────────────────────────────────────

@router.post("/webhook/payme")
async def payme_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    auth = request.headers.get("Authorization", "")
    if not payme_service.verify_callback(auth):
        return {"error": {"code": -32504, "message": "Insufficient privilege"}}

    body = await request.json()
    method  = body.get("method")
    params  = body.get("params", {})
    req_id  = body.get("id")

    order_id = int(params.get("account", {}).get("order_id", 0))
    result_dep = await db.execute(select(Deposit).where(Deposit.id == order_id))
    deposit = result_dep.scalar_one_or_none()

    if method == "CheckPerformTransaction":
        if not deposit or deposit.status == DepositStatus.REJECTED:
            return {"id": req_id, "error": {"code": -31050, "message": "Order not found"}}
        return {"id": req_id, "result": {"allow": True}}

    elif method == "CreateTransaction":
        if not deposit:
            return {"id": req_id, "error": {"code": -31050, "message": "Order not found"}}
        deposit.payme_order_id = params.get("id")
        deposit.status = DepositStatus.PROCESSING
        await db.commit()
        return {"id": req_id, "result": {
            "create_time": int(datetime.utcnow().timestamp() * 1000),
            "transaction": str(deposit.id),
            "state": 1,
        }}

    elif method == "PerformTransaction":
        if not deposit:
            return {"id": req_id, "error": {"code": -31003, "message": "Order not found"}}
        if deposit.status != DepositStatus.CONFIRMED:
            await credit_user(db, deposit)
        return {"id": req_id, "result": {
            "transaction": str(deposit.id),
            "perform_time": int(datetime.utcnow().timestamp() * 1000),
            "state": 2,
        }}

    elif method == "CancelTransaction":
        if deposit and deposit.status == DepositStatus.PROCESSING:
            deposit.status = DepositStatus.REJECTED
            await db.commit()
        return {"id": req_id, "result": {
            "transaction": str(deposit.id) if deposit else "0",
            "cancel_time": int(datetime.utcnow().timestamp() * 1000),
            "state": -1,
        }}

    elif method == "CheckTransaction":
        if not deposit:
            return {"id": req_id, "error": {"code": -31003, "message": "Not found"}}
        state_map = {
            DepositStatus.PENDING: 1,
            DepositStatus.PROCESSING: 1,
            DepositStatus.CONFIRMED: 2,
            DepositStatus.REJECTED: -2,
        }
        return {"id": req_id, "result": {
            "create_time": int(deposit.created_at.timestamp() * 1000),
            "perform_time": int(deposit.confirmed_at.timestamp() * 1000) if deposit.confirmed_at else 0,
            "cancel_time": 0,
            "transaction": str(deposit.id),
            "state": state_map.get(deposit.status, 1),
            "reason": None,
        }}

    return {"id": req_id, "error": {"code": -32601, "message": "Method not found"}}


# ── Click webhook ─────────────────────────────────────────────────────────────

@router.post("/webhook/click/prepare")
async def click_prepare(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    form = await request.form()
    data = dict(form)

    ok, err = click_service.verify_prepare(
        click_trans_id     = data.get("click_trans_id",""),
        service_id         = data.get("service_id",""),
        merchant_trans_id  = data.get("merchant_trans_id",""),
        amount             = data.get("amount",""),
        action             = data.get("action",""),
        sign_time          = data.get("sign_time",""),
        sign_string        = data.get("sign_string",""),
    )
    if not ok:
        return {"error": -1, "error_note": err}

    order_id = int(data.get("merchant_trans_id", 0))
    result   = await db.execute(select(Deposit).where(Deposit.id == order_id))
    deposit  = result.scalar_one_or_none()
    if not deposit:
        return {"error": -5, "error_note": "Order not found"}

    deposit.click_trans_id = data.get("click_trans_id")
    deposit.status = DepositStatus.PROCESSING
    await db.commit()

    return {
        "click_trans_id": data["click_trans_id"],
        "merchant_trans_id": str(order_id),
        "merchant_prepare_id": deposit.id,
        "error": 0,
        "error_note": "Success",
    }


@router.post("/webhook/click/complete")
async def click_complete(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    form = await request.form()
    data = dict(form)
    err_code = int(data.get("error", 0))

    ok, err = click_service.verify_complete(
        click_trans_id     = data.get("click_trans_id",""),
        merchant_trans_id  = data.get("merchant_trans_id",""),
        merchant_prepare_id = data.get("merchant_prepare_id",""),
        amount             = data.get("amount",""),
        action             = data.get("action",""),
        sign_time          = data.get("sign_time",""),
        sign_string        = data.get("sign_string",""),
    )
    if not ok:
        return {"error": -1, "error_note": err}

    order_id = int(data.get("merchant_prepare_id", 0))
    result   = await db.execute(select(Deposit).where(Deposit.id == order_id))
    deposit  = result.scalar_one_or_none()
    if not deposit:
        return {"error": -5, "error_note": "Order not found"}

    if err_code < 0:
        deposit.status = DepositStatus.REJECTED
        await db.commit()
        return {"error": err_code, "error_note": "Cancelled"}

    if deposit.status != DepositStatus.CONFIRMED:
        await credit_user(db, deposit)

    return {
        "click_trans_id": data["click_trans_id"],
        "merchant_trans_id": data["merchant_trans_id"],
        "error": 0,
        "error_note": "Success",
    }


# ── Uzum webhook ──────────────────────────────────────────────────────────────

@router.post("/webhook/uzum")
async def uzum_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    body      = await request.body()
    signature = request.headers.get("X-Signature", "")
    if not uzum_service.verify_webhook(signature, body):
        raise HTTPException(403, "Invalid signature")

    data     = json.loads(body)
    order_id = int(data.get("orderId", 0))
    status   = data.get("status")

    result  = await db.execute(select(Deposit).where(Deposit.id == order_id))
    deposit = result.scalar_one_or_none()
    if not deposit:
        return {"ok": False}

    if status == "CONFIRMED" and deposit.status != DepositStatus.CONFIRMED:
        await credit_user(db, deposit)
    elif status in ("CANCELLED", "DECLINED"):
        deposit.status = DepositStatus.REJECTED
        await db.commit()

    return {"ok": True}


# ── Admin deposit management ──────────────────────────────────────────────────

@router.get("/admin/all", dependencies=[Depends(require_admin)])
async def admin_deposits(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(Deposit, User)
        .join(User, Deposit.user_id == User.id)
        .order_by(Deposit.created_at.desc())
        .limit(limit).offset(offset)
    )
    if status:
        q = q.where(Deposit.status == status)
    result = await db.execute(q)
    rows   = result.all()
    return [
        {
            "id": d.id, "amount": d.amount, "method": d.method.value,
            "status": d.status.value, "transaction_id": d.transaction_id,
            "screenshot_url": d.screenshot_url,
            "user_id": u.id, "username": u.username, "first_name": u.first_name,
            "telegram_id": u.telegram_id,
            "created_at": d.created_at.isoformat(),
        }
        for d, u in rows
    ]


class AdminDepositAction(BaseModel):
    action: str  # "confirm" | "reject"
    note:   Optional[str] = None


@router.patch("/admin/{deposit_id}", dependencies=[Depends(require_admin)])
async def admin_deposit_action(
    deposit_id: int,
    body: AdminDepositAction,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result  = await db.execute(select(Deposit).where(Deposit.id == deposit_id))
    deposit = result.scalar_one_or_none()
    if not deposit:
        raise HTTPException(404, "Topilmadi")

    if body.action == "confirm":
        if deposit.status == DepositStatus.CONFIRMED:
            raise HTTPException(400, "Allaqachon tasdiqlangan")
        await credit_user(db, deposit)
        deposit.admin_id   = admin_user.id
        deposit.admin_note = body.note
        await db.commit()
        # Notify user via Telegram
        result2 = await db.execute(select(User).where(User.id == deposit.user_id))
        buyer = result2.scalar_one_or_none()
        if buyer and buyer.telegram_id:
            import httpx
            try:
                async with httpx.AsyncClient() as c:
                    await c.post(
                        f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage",
                        json={"chat_id": buyer.telegram_id, "parse_mode": "HTML",
                              "text": f"✅ <b>To'lov tasdiqlandi!</b>\n💰 +{deposit.amount:,} so'm"},
                        timeout=10,
                    )
            except Exception:
                pass
        return {"ok": True}

    elif body.action == "reject":
        deposit.status     = DepositStatus.REJECTED
        deposit.admin_note = body.note
        deposit.admin_id   = admin_user.id
        await db.commit()
        return {"ok": True}

    raise HTTPException(400, "Noto'g'ri action")


# ── User deposit history ──────────────────────────────────────────────────────

@router.get("/")
async def get_my_deposits(
    limit: int = 20,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db:   AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Deposit)
        .where(Deposit.user_id == user.id)
        .order_by(Deposit.created_at.desc())
        .limit(limit).offset(offset)
    )
    deps = result.scalars().all()
    return [
        {
            "id": d.id, "amount": d.amount,
            "method": d.method.value, "status": d.status.value,
            "transaction_id": d.transaction_id,
            "created_at": d.created_at.isoformat(),
        }
        for d in deps
    ]
