"""
Blaze CS2 Marketplace — PostgreSQL Models (SQLAlchemy 2.0 async)
"""
from datetime import datetime
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, UniqueConstraint, Index, Enum as SAEnum,
    Numeric, func
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.dialects.postgresql import JSONB
import enum

from core.config import settings


# ── Engine ──────────────────────────────────────────────────────────────────

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ── Enums ───────────────────────────────────────────────────────────────────

class OrderStatus(str, enum.Enum):
    PENDING   = "pending"
    CONFIRMED = "confirmed"
    SENT      = "sent"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED  = "refunded"

class DepositStatus(str, enum.Enum):
    PENDING   = "pending"
    PROCESSING = "processing"
    CONFIRMED = "confirmed"
    REJECTED  = "rejected"
    REFUNDED  = "refunded"

class DepositMethod(str, enum.Enum):
    PAYME   = "payme"
    CLICK   = "click"
    UZUM    = "uzum"
    UZCARD  = "uzcard"
    HUMO    = "humo"
    BALANCE = "balance"

class GiveawayStatus(str, enum.Enum):
    DRAFT   = "draft"
    ACTIVE  = "active"
    ENDED   = "ended"
    CANCELLED = "cancelled"

class UserRole(str, enum.Enum):
    USER  = "user"
    MOD   = "mod"
    ADMIN = "admin"
    OWNER = "owner"

class SkinExterior(str, enum.Enum):
    FN  = "Factory New"
    MW  = "Minimal Wear"
    FT  = "Field-Tested"
    WW  = "Well-Worn"
    BS  = "Battle-Scarred"

class MarketSource(str, enum.Enum):
    MANUAL   = "manual"
    CSFLOAT  = "csfloat"
    SKINPORT = "skinport"
    STEAM    = "steam_market"


# ── Models ──────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    telegram_id     = Column(BigInteger, unique=True, nullable=False, index=True)
    username        = Column(String(64))
    first_name      = Column(String(128))
    last_name       = Column(String(128))
    role            = Column(SAEnum(UserRole), default=UserRole.USER, nullable=False)
    is_banned       = Column(Boolean, default=False)
    ban_reason      = Column(Text)

    # Balance (stored in tiyin = som * 100 for precision)
    balance         = Column(BigInteger, default=0, nullable=False)
    total_spent     = Column(BigInteger, default=0, nullable=False)
    total_deposited = Column(BigInteger, default=0, nullable=False)

    # Steam
    steam_id        = Column(String(32), unique=True)
    steam_username  = Column(String(128))
    steam_avatar    = Column(Text)
    trade_url       = Column(Text)
    steam_linked_at = Column(DateTime(timezone=True))

    # Referral
    referral_code   = Column(String(16), unique=True, index=True)
    referred_by_id  = Column(Integer, ForeignKey("users.id"))
    referral_count  = Column(Integer, default=0)
    referral_earned = Column(BigInteger, default=0)

    # Bonuses
    last_daily_bonus = Column(DateTime(timezone=True))
    daily_streak     = Column(Integer, default=0)
    promo_used_count = Column(Integer, default=0)

    # Auth
    jwt_version     = Column(Integer, default=1)  # increment to invalidate tokens

    # Timestamps
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())
    last_seen_at    = Column(DateTime(timezone=True))

    # Relationships
    orders          = relationship("Order", back_populates="user", foreign_keys="Order.user_id")
    deposits        = relationship("Deposit", back_populates="user")
    favorites       = relationship("Favorite", back_populates="user")
    notifications   = relationship("Notification", back_populates="user")
    giveaway_entries = relationship("GiveawayParticipant", back_populates="user")
    referrals       = relationship("Referral", back_populates="referrer", foreign_keys="Referral.referrer_id")

    __table_args__ = (
        Index("ix_users_telegram_id", "telegram_id"),
        Index("ix_users_steam_id", "steam_id"),
        Index("ix_users_referral_code", "referral_code"),
    )


class Skin(Base):
    __tablename__ = "skins"

    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(String(256), nullable=False)
    weapon_type  = Column(String(64), nullable=False)
    collection   = Column(String(128))
    exterior     = Column(String(32), nullable=False)
    rarity       = Column(String(32))
    float_val    = Column(Float)
    pattern      = Column(Integer)
    stickers     = Column(JSONB, default=list)
    price        = Column(BigInteger, nullable=False)      # som
    market_price = Column(BigInteger)                      # reference price from APIs
    image_url    = Column(Text)
    inspect_url  = Column(Text)
    is_active    = Column(Boolean, default=True)
    is_featured  = Column(Boolean, default=False)
    stock        = Column(Integer, default=1, nullable=False)
    market_source = Column(SAEnum(MarketSource), default=MarketSource.MANUAL)
    market_id    = Column(String(128))    # CSFloat listing ID, etc.
    wear_min     = Column(Float)
    wear_max     = Column(Float)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())

    orders       = relationship("Order", back_populates="skin")
    favorites    = relationship("Favorite", back_populates="skin")

    __table_args__ = (
        Index("ix_skins_weapon_type", "weapon_type"),
        Index("ix_skins_is_active", "is_active"),
        Index("ix_skins_price", "price"),
    )


class Order(Base):
    __tablename__ = "orders"

    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    skin_id        = Column(Integer, ForeignKey("skins.id"), nullable=False, index=True)
    price          = Column(BigInteger, nullable=False)
    status         = Column(SAEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    trade_url      = Column(Text)
    trade_offer_id = Column(String(32))     # Steam trade offer
    payment_method = Column(SAEnum(DepositMethod), default=DepositMethod.BALANCE)
    admin_id       = Column(Integer, ForeignKey("users.id"))
    notes          = Column(Text)
    admin_notes    = Column(Text)
    metadata       = Column(JSONB, default=dict)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    updated_at     = Column(DateTime(timezone=True), onupdate=func.now())
    confirmed_at   = Column(DateTime(timezone=True))
    delivered_at   = Column(DateTime(timezone=True))

    user  = relationship("User", back_populates="orders", foreign_keys=[user_id])
    skin  = relationship("Skin", back_populates="orders")
    admin = relationship("User", foreign_keys=[admin_id])

    __table_args__ = (
        Index("ix_orders_status", "status"),
        Index("ix_orders_user_status", "user_id", "status"),
    )


class Deposit(Base):
    __tablename__ = "deposits"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount          = Column(BigInteger, nullable=False)
    method          = Column(SAEnum(DepositMethod), nullable=False)
    status          = Column(SAEnum(DepositStatus), default=DepositStatus.PENDING)

    # Payment gateway fields
    transaction_id  = Column(String(128), unique=True)
    provider_txid   = Column(String(256))   # Gateway's own transaction ID
    provider_data   = Column(JSONB, default=dict)

    # Payme specific
    payme_order_id  = Column(String(64))

    # Click specific
    click_trans_id  = Column(String(64))

    # Uzum specific
    uzum_order_id   = Column(String(64))

    admin_id        = Column(Integer, ForeignKey("users.id"))
    admin_note      = Column(Text)
    screenshot_url  = Column(Text)

    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())
    confirmed_at    = Column(DateTime(timezone=True))

    user  = relationship("User", back_populates="deposits", foreign_keys=[user_id])
    admin = relationship("User", foreign_keys=[admin_id])

    __table_args__ = (
        Index("ix_deposits_status", "status"),
        Index("ix_deposits_method", "method"),
    )


class Giveaway(Base):
    __tablename__ = "giveaways"

    id               = Column(Integer, primary_key=True, index=True)
    title            = Column(String(256), nullable=False)
    description      = Column(Text)
    skin_id          = Column(Integer, ForeignKey("skins.id"))
    prize_name       = Column(String(256), nullable=False)
    prize_image      = Column(Text)
    max_participants = Column(Integer, default=100)
    min_balance      = Column(BigInteger, default=0)
    require_channel  = Column(Boolean, default=False)
    channel_id       = Column(String(64))
    status           = Column(SAEnum(GiveawayStatus), default=GiveawayStatus.DRAFT)
    winner_id        = Column(Integer, ForeignKey("users.id"))
    end_time         = Column(DateTime(timezone=True), nullable=False)
    created_by       = Column(Integer, ForeignKey("users.id"))
    created_at       = Column(DateTime(timezone=True), server_default=func.now())

    prize_skin  = relationship("Skin", foreign_keys=[skin_id])
    winner      = relationship("User", foreign_keys=[winner_id])
    creator     = relationship("User", foreign_keys=[created_by])
    participants = relationship("GiveawayParticipant", back_populates="giveaway")


class GiveawayParticipant(Base):
    __tablename__ = "giveaway_participants"

    id          = Column(Integer, primary_key=True)
    giveaway_id = Column(Integer, ForeignKey("giveaways.id"), nullable=False)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    joined_at   = Column(DateTime(timezone=True), server_default=func.now())

    giveaway = relationship("Giveaway", back_populates="participants")
    user     = relationship("User", back_populates="giveaway_entries")

    __table_args__ = (UniqueConstraint("giveaway_id", "user_id"),)


class Favorite(Base):
    __tablename__ = "favorites"

    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    skin_id    = Column(Integer, ForeignKey("skins.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="favorites")
    skin = relationship("Skin", back_populates="favorites")

    __table_args__ = (UniqueConstraint("user_id", "skin_id"),)


class Referral(Base):
    __tablename__ = "referrals"

    id          = Column(Integer, primary_key=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    referred_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    bonus_paid  = Column(BigInteger, default=0)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    referrer = relationship("User", back_populates="referrals", foreign_keys=[referrer_id])
    referred = relationship("User", foreign_keys=[referred_id])


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id            = Column(Integer, primary_key=True)
    code          = Column(String(32), unique=True, nullable=False, index=True)
    bonus_amount  = Column(BigInteger, nullable=False)
    max_uses      = Column(Integer, default=1)
    uses          = Column(Integer, default=0)
    expires_at    = Column(DateTime(timezone=True))
    is_active     = Column(Boolean, default=True)
    created_by    = Column(Integer, ForeignKey("users.id"))
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    uses_list     = relationship("PromoUse", back_populates="promo")


class PromoUse(Base):
    __tablename__ = "promo_uses"

    id       = Column(Integer, primary_key=True)
    user_id  = Column(Integer, ForeignKey("users.id"), nullable=False)
    promo_id = Column(Integer, ForeignKey("promo_codes.id"), nullable=False)
    used_at  = Column(DateTime(timezone=True), server_default=func.now())

    user  = relationship("User")
    promo = relationship("PromoCode", back_populates="uses_list")

    __table_args__ = (UniqueConstraint("user_id", "promo_id"),)


class Notification(Base):
    __tablename__ = "notifications"

    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title      = Column(String(256), nullable=False)
    message    = Column(Text, nullable=False)
    type       = Column(String(32), default="info")   # info, success, warning, error
    is_read    = Column(Boolean, default=False)
    link       = Column(String(512))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notifications")

    __table_args__ = (Index("ix_notifications_user_unread", "user_id", "is_read"),)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id         = Column(Integer, primary_key=True)
    admin_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    action     = Column(String(128), nullable=False)
    target_id  = Column(Integer)
    target_type = Column(String(64))
    details    = Column(JSONB, default=dict)
    ip_address = Column(String(64))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    admin = relationship("User", foreign_keys=[admin_id])


class DailyStats(Base):
    """Pre-aggregated stats for the analytics dashboard"""
    __tablename__ = "daily_stats"

    id                = Column(Integer, primary_key=True)
    date              = Column(DateTime(timezone=True), unique=True, nullable=False)
    new_users         = Column(Integer, default=0)
    active_users      = Column(Integer, default=0)
    total_orders      = Column(Integer, default=0)
    completed_orders  = Column(Integer, default=0)
    revenue           = Column(BigInteger, default=0)
    total_deposits    = Column(BigInteger, default=0)
    deposit_count     = Column(Integer, default=0)
    new_referrals     = Column(Integer, default=0)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
