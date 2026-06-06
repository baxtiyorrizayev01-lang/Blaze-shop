"""payments.py — Payment redirect helpers"""
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

router = APIRouter()

@router.get("/success")
async def payment_success():
    return {"status": "success", "message": "To'lov muvaffaqiyatli! Ilovaga qayting."}

@router.get("/fail")
async def payment_fail():
    return {"status": "fail", "message": "To'lov amalga oshmadi. Qaytadan urining."}
