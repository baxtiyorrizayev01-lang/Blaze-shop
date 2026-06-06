"""
Blaze CS2 Marketplace — FastAPI Main App
Production-ready: rate limiting, CORS, structured logging, health checks
"""
import time
import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from core.config import settings
from models.models import create_tables

# Route imports
from api.routes import auth, users, skins, orders, deposits, giveaways
from api.routes import admin, steam, payments, market, telegram

log = structlog.get_logger()

# ── Rate limiter ─────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


# ── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup", version=settings.APP_VERSION)
    await create_tables()
    log.info("database_ready")
    yield
    log.info("shutdown")


# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

# Rate limit error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = (time.time() - start) * 1000
    log.info(
        "request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        ms=round(duration, 1),
        ip=get_remote_address(request),
    )
    return response


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"]        = "DENY"
    response.headers["X-XSS-Protection"]       = "1; mode=block"
    response.headers["Referrer-Policy"]        = "strict-origin-when-cross-origin"
    return response


# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(auth.router,      prefix="/api/auth",      tags=["auth"])
app.include_router(users.router,     prefix="/api/users",     tags=["users"])
app.include_router(skins.router,     prefix="/api/skins",     tags=["skins"])
app.include_router(orders.router,    prefix="/api/orders",    tags=["orders"])
app.include_router(deposits.router,  prefix="/api/deposits",  tags=["deposits"])
app.include_router(giveaways.router, prefix="/api/giveaways", tags=["giveaways"])
app.include_router(admin.router,     prefix="/api/admin",     tags=["admin"])
app.include_router(steam.router,     prefix="/api/steam",     tags=["steam"])
app.include_router(payments.router,  prefix="/api/payments",  tags=["payments"])
app.include_router(market.router,    prefix="/api/market",    tags=["market"])
app.include_router(telegram.router,  prefix="/api/telegram",  tags=["telegram"])


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get("/")
async def root():
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION}
