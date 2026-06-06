"""
Blaze CS2 — Telegram Bot (aiogram 3.x)
Handles: /start referral, /balance, /orders, /help, /bonus
Mini App button, channel subscription check
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo, ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from core.config import settings
from models.models import AsyncSessionLocal, User, Referral, Notification
from sqlalchemy import select, update
import secrets, string

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("blaze_bot")

bot = Bot(token=settings.BOT_TOKEN, parse_mode="HTML")
dp  = Dispatcher()
router = Router()
dp.include_router(router)


# ── Keyboards ────────────────────────────────────────────────────────────────

def main_keyboard() -> ReplyKeyboardMarkup:
    """Main persistent keyboard with Web App button."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(
            text="🔫 Bozor",
            web_app=WebAppInfo(url=settings.WEBAPP_URL),
        )
    )
    builder.row(
        KeyboardButton(text="💰 Balans"),
        KeyboardButton(text="📦 Buyurtmalarim"),
    )
    builder.row(
        KeyboardButton(text="👥 Do'stlarni taklif et"),
        KeyboardButton(text="🎁 Kunlik bonus"),
    )
    return builder.as_markup(resize_keyboard=True)


def open_app_button(text="🔫 Bozorni ochish") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=text,
            web_app=WebAppInfo(url=settings.WEBAPP_URL),
        )
    ]])


# ── Helpers ──────────────────────────────────────────────────────────────────

def gen_referral_code() -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(8))


async def get_or_create_user(tg_user: types.User, ref_code: str | None = None) -> tuple[User, bool]:
    """Get existing user or create new one. Returns (user, is_new)."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.telegram_id == tg_user.id)
        )
        user = result.scalar_one_or_none()

        if user:
            user.username   = tg_user.username
            user.first_name = tg_user.first_name
            user.last_name  = tg_user.last_name
            await db.commit()
            return user, False

        # New user
        from models.models import UserRole
        role = UserRole.ADMIN if tg_user.id in settings.admin_id_list else UserRole.USER
        user = User(
            telegram_id   = tg_user.id,
            username      = tg_user.username,
            first_name    = tg_user.first_name,
            last_name     = tg_user.last_name,
            role          = role,
            referral_code = gen_referral_code(),
        )
        db.add(user)
        await db.flush()  # Get user.id

        # Handle referral
        if ref_code:
            ref_result = await db.execute(
                select(User).where(
                    User.referral_code == ref_code,
                    User.telegram_id != tg_user.id,
                )
            )
            referrer = ref_result.scalar_one_or_none()
            if referrer and not user.referred_by_id:
                user.referred_by_id      = referrer.id
                referrer.balance         += settings.REFERRAL_BONUS
                referrer.referral_count  += 1
                referrer.referral_earned += settings.REFERRAL_BONUS

                db.add(Referral(
                    referrer_id=referrer.id,
                    referred_id=user.id,
                    bonus_paid=settings.REFERRAL_BONUS,
                ))
                db.add(Notification(
                    user_id=referrer.id,
                    title="Yangi referal! 👥",
                    message=(
                        f"{tg_user.first_name} sizning havolangiz orqali "
                        f"ro'yxatdan o'tdi! +{settings.REFERRAL_BONUS:,} so'm"
                    ),
                    type="success",
                ))

                # Notify referrer via Telegram
                try:
                    await bot.send_message(
                        referrer.telegram_id,
                        f"🎉 <b>Yangi referal!</b>\n"
                        f"👤 {tg_user.first_name} sizning havolangiz orqali qo'shildi!\n"
                        f"💰 <b>+{settings.REFERRAL_BONUS:,} so'm</b> balansga qo'shildi!",
                    )
                except Exception:
                    pass

        await db.commit()
        await db.refresh(user)
        return user, True


# ── /start ───────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    args = message.text.split(maxsplit=1)
    ref_code = None

    if len(args) > 1:
        arg = args[1].strip()
        if arg.startswith("ref_"):
            ref_code = arg[4:]

    user, is_new = await get_or_create_user(message.from_user, ref_code)

    name = message.from_user.first_name

    if is_new:
        welcome = (
            f"👋 Salom, <b>{name}</b>! Blaze CS2 Marketga xush kelibsiz!\n\n"
            f"🔫 <b>Blaze CS2 Market</b> — eng qulay va xavfsiz CS2 skin bozori.\n\n"
            f"✅ Xavfsiz to'lov (Payme, Click, Uzum, UzCard)\n"
            f"⚡ Tez yetkazish (Steam Trade)\n"
            f"🎁 Kunlik bonuslar va giveawaylar\n"
            f"👥 Do'stlarni taklif qilib pul ishlang\n\n"
            f"Balans: <b>{user.balance:,} so'm</b>"
        )
        if ref_code:
            welcome += f"\n\n🎁 Referal havolasi orqali kelgansiz!"
    else:
        welcome = (
            f"🔥 Salom yana, <b>{name}</b>!\n\n"
            f"💰 Balansingiz: <b>{user.balance:,} so'm</b>\n"
            f"📦 Buyurtmalar: /orders\n"
            f"👥 Referal: /referral"
        )

    await message.answer(welcome, reply_markup=main_keyboard())
    await message.answer(
        "🛒 Bozorni ochish uchun quyidagi tugmani bosing:",
        reply_markup=open_app_button(),
    )


# ── /balance ──────────────────────────────────────────────────────────────────

@router.message(Command("balance"))
@router.message(F.text == "💰 Balans")
async def cmd_balance(message: types.Message):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

    if not user:
        await message.answer("Ro'yxatdan o'tish uchun /start")
        return

    text = (
        f"💰 <b>Balans ma'lumotlari</b>\n\n"
        f"💵 Joriy balans: <b>{user.balance:,} so'm</b>\n"
        f"🛒 Jami sarflangan: <b>{user.total_spent:,} so'm</b>\n"
        f"📥 Jami to'langan: <b>{user.total_deposited:,} so'm</b>\n\n"
        f"Balans to'ldirish uchun ilovani oching:"
    )
    await message.answer(text, reply_markup=open_app_button("💳 Balans to'ldirish"))


# ── /orders ───────────────────────────────────────────────────────────────────

@router.message(Command("orders"))
@router.message(F.text == "📦 Buyurtmalarim")
async def cmd_orders(message: types.Message):
    from models.models import Order, Skin, OrderStatus
    async with AsyncSessionLocal() as db:
        user_r = await db.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = user_r.scalar_one_or_none()
        if not user:
            await message.answer("/start orqali ro'yxatdan o'ting")
            return

        orders_r = await db.execute(
            select(Order, Skin)
            .join(Skin, Order.skin_id == Skin.id)
            .where(Order.user_id == user.id)
            .order_by(Order.created_at.desc())
            .limit(5)
        )
        rows = orders_r.all()

    if not rows:
        await message.answer(
            "📦 Sizda hali buyurtma yo'q.\nBozorga kirish:",
            reply_markup=open_app_button(),
        )
        return

    status_icons = {
        "pending":   "⏳",
        "confirmed": "✅",
        "sent":      "📤",
        "delivered": "🎉",
        "cancelled": "❌",
    }

    lines = ["📦 <b>So'nggi buyurtmalar:</b>\n"]
    for order, skin in rows:
        icon = status_icons.get(order.status.value, "❓")
        lines.append(
            f"{icon} <b>{skin.name}</b> ({skin.exterior})\n"
            f"   💰 {order.price:,} so'm  |  #{order.id}\n"
            f"   Holat: <i>{order.status.value}</i>\n"
        )

    await message.answer("\n".join(lines), reply_markup=open_app_button("📦 Barchasini ko'rish"))


# ── /referral ─────────────────────────────────────────────────────────────────

@router.message(Command("referral"))
@router.message(F.text == "👥 Do'stlarni taklif et")
async def cmd_referral(message: types.Message):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

    if not user:
        await message.answer("/start orqali ro'yxatdan o'ting")
        return

    ref_link = f"https://t.me/{settings.BOT_USERNAME}?start=ref_{user.referral_code}"
    text = (
        f"👥 <b>Referal dasturi</b>\n\n"
        f"Do'stingizni taklif qilib, har bir yangi foydalanuvchi uchun\n"
        f"💰 <b>+{settings.REFERRAL_BONUS:,} so'm</b> oling!\n\n"
        f"📊 Statistika:\n"
        f"   👤 Taklif qilinganlar: <b>{user.referral_count}</b> kishi\n"
        f"   💵 Jami daromad: <b>{user.referral_earned:,} so'm</b>\n\n"
        f"🔗 Sizning havolangiz:\n"
        f"<code>{ref_link}</code>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📤 Do'stlarga yuborish", url=f"https://t.me/share/url?url={ref_link}&text=Blaze+CS2+Marketga+qo%27shiling!")
    ]])
    await message.answer(text, reply_markup=kb)


# ── /bonus ────────────────────────────────────────────────────────────────────

@router.message(Command("bonus"))
@router.message(F.text == "🎁 Kunlik bonus")
async def cmd_bonus(message: types.Message):
    from datetime import datetime, timedelta
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await message.answer("/start orqali ro'yxatdan o'ting")
            return

        now = datetime.utcnow()
        if user.last_daily_bonus:
            diff = now - user.last_daily_bonus
            if diff.total_seconds() < 86400:
                next_in = 86400 - diff.total_seconds()
                hours = int(next_in // 3600)
                mins  = int((next_in % 3600) // 60)
                await message.answer(
                    f"⏰ Keyingi bonus: <b>{hours}s {mins}m</b> dan keyin\n"
                    f"💰 Joriy balans: <b>{user.balance:,} so'm</b>"
                )
                return
            streak = user.daily_streak + 1 if diff.total_seconds() < 172800 else 1
        else:
            streak = 1

        bonus = settings.DAILY_BONUS_AMOUNT + min(streak * 500, 5000)
        user.balance          += bonus
        user.last_daily_bonus  = now
        user.daily_streak      = streak

        db.add(Notification(
            user_id=user.id, title="Kunlik bonus! 🎁",
            message=f"+{bonus:,} so'm olindi! ({streak} kun ketma-ket)",
            type="success",
        ))
        await db.commit()

    await message.answer(
        f"🎁 <b>Kunlik bonus olindi!</b>\n\n"
        f"💰 +<b>{bonus:,} so'm</b>\n"
        f"🔥 Ketma-ket: <b>{streak}</b> kun\n"
        f"💵 Yangi balans: <b>{user.balance:,} so'm</b>"
    )


# ── /help ─────────────────────────────────────────────────────────────────────

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "🔥 <b>Blaze CS2 Market — Buyruqlar</b>\n\n"
        "/start — Botni ishga tushirish\n"
        "/balance — Balansni ko'rish\n"
        "/orders — Buyurtmalarim\n"
        "/referral — Referal dastur\n"
        "/bonus — Kunlik bonus olish\n"
        "/help — Yordam\n\n"
        "❓ Savollar uchun: @BlazeSupportBot",
        reply_markup=open_app_button(),
    )


# ── Admin commands ─────────────────────────────────────────────────────────────

@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if message.from_user.id not in settings.admin_id_list:
        return

    from models.models import Order, Deposit, DepositStatus, OrderStatus
    from sqlalchemy import func
    from datetime import datetime, timedelta

    async with AsyncSessionLocal() as db:
        today = datetime.utcnow().date()

        async def count(model, *filters):
            q = select(func.count()).select_from(model)
            for f in filters: q = q.where(f)
            r = await db.execute(q)
            return r.scalar() or 0

        async def total(model, col, *filters):
            q = select(func.coalesce(func.sum(col), 0)).select_from(model)
            for f in filters: q = q.where(f)
            r = await db.execute(q)
            return r.scalar() or 0

        total_users     = await count(User)
        new_today       = await count(User, func.date(User.created_at) == today)
        pending_orders  = await count(Order, Order.status == OrderStatus.PENDING)
        pending_deps    = await count(Deposit, Deposit.status == DepositStatus.PENDING)
        rev_today       = await total(Order, Order.price, func.date(Order.created_at)==today, Order.status!=OrderStatus.CANCELLED)
        rev_total       = await total(Order, Order.price, Order.status!=OrderStatus.CANCELLED)

    await message.answer(
        f"📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{total_users:,}</b> (bugun +{new_today})\n"
        f"⏳ Kutayotgan buyurtmalar: <b>{pending_orders}</b>\n"
        f"💳 Kutayotgan to'lovlar: <b>{pending_deps}</b>\n"
        f"💰 Bugungi daromad: <b>{rev_today:,}</b> so'm\n"
        f"📈 Jami daromad: <b>{rev_total:,}</b> so'm"
    )


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    log.info("Bot starting...")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
