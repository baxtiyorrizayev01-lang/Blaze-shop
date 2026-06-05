import asyncio, logging, os
from aiogram import Bot, Dispatcher, F
from aiogram.types import (Message, CallbackQuery, InlineKeyboardMarkup,
                            InlineKeyboardButton, WebAppInfo, MenuButtonWebApp,
                            ReplyKeyboardMarkup, KeyboardButton)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import database as db

load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN  = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
ADMIN_IDS  = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-app.netlify.app")
CHANNEL_ID = os.getenv("CHANNEL_ID", "")

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp  = Dispatcher(storage=MemoryStorage())


class DepositState(StatesGroup):
    amount   = State()
    method   = State()
    txid     = State()

class PromoState(StatesGroup):
    code = State()


def is_admin(uid): return uid in ADMIN_IDS

def main_kb(webapp_url):
    return ReplyKeyboardMarkup(keyboard=[[
        KeyboardButton(text="🎮 Blaze Shop ni ochish",
                       web_app=WebAppInfo(url=webapp_url))
    ]], resize_keyboard=True)

def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika", callback_data="adm_stats")],
        [InlineKeyboardButton(text="📦 Kutayotgan buyurtmalar", callback_data="adm_orders_pending"),
         InlineKeyboardButton(text="💳 Kutayotgan to'lovlar", callback_data="adm_deposits_pending")],
        [InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="adm_users"),
         InlineKeyboardButton(text="🎁 Giveawaylar", callback_data="adm_giveaways")],
    ])


# ─── /start ─────────────────────────────────────────────────────────────────

@dp.message(CommandStart())
async def cmd_start(msg: Message, command: CommandStart):
    ref_code = None
    if command.args:
        ref_code = command.args.replace("ref_", "")

    user, is_new = await db.get_or_create_user(
        msg.from_user.id,
        username=msg.from_user.username,
        first_name=msg.from_user.first_name,
        last_name=msg.from_user.last_name,
        ref_code=ref_code
    )

    name = msg.from_user.first_name or "Do'st"
    welcome = (
        f"🔥 <b>Blaze CS2 Skin Shop ga xush kelibsiz!</b>\n\n"
        f"Salom, <b>{name}</b>! 👋\n\n"
        f"Bu yerda siz:\n"
        f"✅ CS2 skinlarini sotib olishingiz\n"
        f"🎁 Giveawaylarda qatnashishingiz\n"
        f"💰 Balansni to'ldirishingiz mumkin\n\n"
        f"📱 Mini ilovani ochish uchun tugmani bosing:"
    )
    if is_new:
        welcome += "\n\n🎉 <b>Ro'yxatdan o'tganingiz uchun tabriklaymiz!</b>"
        if ref_code:
            welcome += "\n✨ Referal bonusi qo'shildi: <b>+5,000 so'm</b>"

    await msg.answer(welcome, reply_markup=main_kb(WEBAPP_URL))
    await bot.set_chat_menu_button(
        msg.chat.id,
        MenuButtonWebApp(text="🎮 Blaze Shop", web_app=WebAppInfo(url=WEBAPP_URL))
    )

    if is_new and CHANNEL_ID:
        try:
            await bot.send_message(
                CHANNEL_ID,
                f"👤 Yangi foydalanuvchi: <b>{msg.from_user.first_name}</b>"
                f" (@{msg.from_user.username or 'noaniq'})"
            )
        except Exception: pass


# ─── /admin ─────────────────────────────────────────────────────────────────

@dp.message(Command("admin"))
async def cmd_admin(msg: Message):
    if not is_admin(msg.from_user.id):
        return await msg.answer("❌ Siz admin emassiz.")
    await msg.answer("🔧 <b>Admin Panel</b>", reply_markup=admin_kb())


@dp.callback_query(F.data == "adm_stats")
async def adm_stats(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return
    stats = await db.get_dashboard_stats()
    u_stats = await db.get_user_stats()
    text = (
        f"📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{u_stats['total']}</b> (bugun +{u_stats['today']})\n"
        f"🚫 Bloklangan: <b>{u_stats['banned']}</b>\n\n"
        f"🛒 Buyurtmalar: <b>{stats['total_orders']}</b>\n"
        f"⏳ Kutayotgan: <b>{stats['pending_orders']}</b>\n"
        f"📅 Bugungi sotuv: <b>{stats['today_sales']}</b> ta\n\n"
        f"💰 Bugungi daromad: <b>{stats['today_revenue']:,} so'm</b>\n"
        f"💎 Jami daromad: <b>{stats['total_revenue']:,} so'm</b>\n\n"
        f"💳 Kutayotgan to'lovlar: <b>{stats['pending_deposits']}</b>\n"
        f"🎁 Faol giveawaylar: <b>{stats['active_giveaways']}</b>"
    )
    await cb.message.edit_text(text, reply_markup=admin_kb())


@dp.callback_query(F.data == "adm_orders_pending")
async def adm_orders(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return
    orders = await db.get_orders(status="pending", limit=10)
    if not orders:
        return await cb.answer("Kutayotgan buyurtmalar yo'q", show_alert=True)
    text = "📦 <b>Kutayotgan buyurtmalar:</b>\n\n"
    btns = []
    for o in orders:
        text += (f"#{o['id']} — {o['skin_name']} ({o['exterior']})\n"
                 f"👤 {o['first_name']} | 💰 {o['price']:,} so'm\n"
                 f"📅 {o['created_at'][:16]}\n\n")
        btns.append([
            InlineKeyboardButton(text=f"✅ #{o['id']} Tasdiqlash",
                                 callback_data=f"order_confirm_{o['id']}"),
            InlineKeyboardButton(text=f"❌ Bekor",
                                 callback_data=f"order_cancel_{o['id']}"),
        ])
    btns.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_back")])
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))


@dp.callback_query(F.data.startswith("order_confirm_"))
async def confirm_order(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return
    oid = int(cb.data.split("_")[-1])
    await db.update_order_status(oid, "delivered", "Admin tomonidan tasdiqlandi")
    orders = await db.get_orders(limit=1)
    if orders:
        o = orders[0]
        uid = o["user_id"]
        u = await db.get_user_by_id(uid)
        if u:
            await db.create_notification(uid, "Buyurtma tasdiqlandi",
                f"#{oid} buyurtmangiz jo'natildi! Trade URL ni tekshiring.")
            try:
                await bot.send_message(u["telegram_id"],
                    f"✅ <b>Buyurtma #{oid} tasdiqlandi!</b>\n"
                    f"Skinni qabul qilish uchun Trade URL ni tekshiring.")
            except Exception: pass
    await cb.answer("✅ Buyurtma tasdiqlandi!")
    await cb.message.edit_text("✅ Buyurtma tasdiqlandi!", reply_markup=admin_kb())


@dp.callback_query(F.data.startswith("order_cancel_"))
async def cancel_order(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return
    oid = int(cb.data.split("_")[-1])
    orders_list = await db.get_orders(limit=100)
    order = next((o for o in orders_list if o["id"] == oid), None)
    if order:
        await db.update_order_status(oid, "cancelled", "Admin tomonidan bekor qilindi")
        await db.update_user_balance(order["user_id"], order["price"])
        u = await db.get_user_by_id(order["user_id"])
        if u:
            await db.create_notification(order["user_id"], "Buyurtma bekor qilindi",
                f"#{oid} buyurtmangiz bekor qilindi. Pul balansga qaytarildi.")
            try:
                await bot.send_message(u["telegram_id"],
                    f"❌ <b>Buyurtma #{oid} bekor qilindi.</b>\n"
                    f"Mablag' balansga qaytarildi: <b>+{order['price']:,} so'm</b>")
            except Exception: pass
    await cb.answer("Bekor qilindi!")
    await cb.message.edit_text("❌ Buyurtma bekor qilindi.", reply_markup=admin_kb())


@dp.callback_query(F.data == "adm_deposits_pending")
async def adm_deposits(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return
    deps = await db.get_deposits(status="pending", limit=10)
    if not deps:
        return await cb.answer("Kutayotgan to'lovlar yo'q", show_alert=True)
    text = "💳 <b>Kutayotgan to'lovlar:</b>\n\n"
    btns = []
    for d in deps:
        text += (f"#{d['id']} — {d['first_name']} (@{d['username'] or '-'})\n"
                 f"💰 {d['amount']:,} so'm | {d['method']}\n"
                 f"🆔 {d.get('transaction_id','—')}\n"
                 f"📅 {d['created_at'][:16]}\n\n")
        btns.append([
            InlineKeyboardButton(text=f"✅ #{d['id']} Tasdiqlash",
                                 callback_data=f"dep_confirm_{d['id']}"),
            InlineKeyboardButton(text=f"❌ Rad",
                                 callback_data=f"dep_reject_{d['id']}"),
        ])
    btns.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_back")])
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))


@dp.callback_query(F.data.startswith("dep_confirm_"))
async def confirm_deposit(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return
    did = int(cb.data.split("_")[-1])
    deps = await db.get_deposits(limit=200)
    dep = next((d for d in deps if d["id"] == did), None)
    ok = await db.approve_deposit(did)
    if ok and dep:
        u = await db.get_user_by_id(dep["user_id"])
        if u:
            await db.create_notification(dep["user_id"], "To'lov tasdiqlandi",
                f"{dep['amount']:,} so'm balansga qo'shildi!")
            try:
                await bot.send_message(u["telegram_id"],
                    f"✅ <b>To'lov tasdiqlandi!</b>\n"
                    f"Balansga qo'shildi: <b>+{dep['amount']:,} so'm</b> 🎉")
            except Exception: pass
    await cb.answer("✅ To'lov tasdiqlandi!")
    await cb.message.edit_text("✅ To'lov tasdiqlandi!", reply_markup=admin_kb())


@dp.callback_query(F.data.startswith("dep_reject_"))
async def reject_deposit(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return
    did = int(cb.data.split("_")[-1])
    await db.reject_deposit(did, "Admin tomonidan rad etildi")
    await cb.answer("Rad etildi!")
    await cb.message.edit_text("❌ To'lov rad etildi.", reply_markup=admin_kb())


@dp.callback_query(F.data == "adm_users")
async def adm_users(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return
    users = await db.get_all_users(limit=10)
    text = "👥 <b>So'nggi foydalanuvchilar:</b>\n\n"
    for u in users:
        status = "🚫" if u["is_banned"] else "✅"
        text += (f"{status} {u['first_name']} (@{u['username'] or '-'})\n"
                 f"   💰 {u['balance']:,} so'm | ID: {u['telegram_id']}\n\n")
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_back")]
    ]))


@dp.callback_query(F.data == "adm_giveaways")
async def adm_giveaways(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return
    gws = await db.get_giveaways(status="active", limit=10)
    text = "🎁 <b>Faol giveawaylar:</b>\n\n"
    btns = []
    for g in gws:
        text += (f"#{g['id']} — {g['title']}\n"
                 f"🏆 {g['prize_name']}\n"
                 f"👥 {g['participant_count']}/{g['max_participants']}\n"
                 f"⏰ {g['end_time'][:16]}\n\n")
        btns.append([InlineKeyboardButton(
            text=f"🎲 #{g['id']} G'olibni tanlash",
            callback_data=f"gw_pick_{g['id']}"
        )])
    btns.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_back")])
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))


@dp.callback_query(F.data.startswith("gw_pick_"))
async def pick_winner(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return
    gid = int(cb.data.split("_")[-1])
    winner = await db.pick_winner(gid)
    giveaway = await db.get_giveaway(gid)
    if not winner:
        return await cb.answer("Ishtirokchilar yo'q!", show_alert=True)
    text = (f"🎉 <b>G'olib tanlandi!</b>\n\n"
            f"🏆 {giveaway['prize_name']}\n\n"
            f"🥇 G'olib: <b>{winner['first_name']}</b> "
            f"(@{winner['username'] or 'noaniq'})\n"
            f"🆔 Telegram ID: <code>{winner['telegram_id']}</code>")
    try:
        await bot.send_message(winner["telegram_id"],
            f"🎉 <b>Tabriklaymiz! Siz g'olib bo'ldingiz!</b>\n\n"
            f"🏆 Sovg'a: <b>{giveaway['prize_name']}</b>\n\n"
            f"Sovg'ani olish uchun adminlar bilan bog'laning.")
    except Exception: pass
    await db.create_notification(winner["id"], "Giveaway g'olibisiz!",
        f"Siz '{giveaway['title']}' da g'olib bo'ldingiz! 🎉")
    await cb.message.edit_text(text, reply_markup=admin_kb())


@dp.callback_query(F.data == "adm_back")
async def adm_back(cb: CallbackQuery):
    await cb.message.edit_text("🔧 <b>Admin Panel</b>", reply_markup=admin_kb())


# ─── /balance ───────────────────────────────────────────────────────────────

@dp.message(Command("balance"))
async def cmd_balance(msg: Message):
    user = await db.get_user(msg.from_user.id)
    if not user:
        return await msg.answer("Avval /start bosing")
    await msg.answer(
        f"💰 <b>Balansingiz: {user['balance']:,} so'm</b>\n\n"
        f"📱 To'ldirish uchun mini ilovani oching:",
        reply_markup=main_kb(WEBAPP_URL)
    )


@dp.message(Command("profile"))
async def cmd_profile(msg: Message):
    user = await db.get_user(msg.from_user.id)
    if not user: return await msg.answer("Avval /start bosing")
    refs = await db.get_referrals(user["id"])
    orders = await db.get_orders(uid=user["id"], limit=5)
    text = (
        f"👤 <b>Profilingiz</b>\n\n"
        f"📛 Ism: <b>{user['first_name'] or '—'}</b>\n"
        f"🔗 Username: @{user['username'] or '—'}\n"
        f"🆔 ID: <code>{user['telegram_id']}</code>\n\n"
        f"💰 Balans: <b>{user['balance']:,} so'm</b>\n"
        f"💸 Jami sarflangan: <b>{user['total_spent']:,} so'm</b>\n\n"
        f"👥 Referallar: <b>{len(refs)}</b> ta\n"
        f"🛒 Buyurtmalar: <b>{len(orders)}</b> ta\n\n"
        f"🔗 Referal havolangiz:\n"
        f"<code>https://t.me/blazecs2bot?start=ref_{user['referral_code']}</code>"
    )
    await msg.answer(text)


@dp.message(Command("promo"))
async def cmd_promo(msg: Message, state: FSMContext):
    await state.set_state(PromoState.code)
    await msg.answer("🎟 <b>Promo kodingizni kiriting:</b>")


@dp.message(PromoState.code)
async def process_promo(msg: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(msg.from_user.id)
    if not user: return
    amount, err = await db.use_promo(user["id"], msg.text.strip().upper())
    if err:
        await msg.answer(f"❌ {err}")
    else:
        await msg.answer(f"🎉 <b>Promo kod qabul qilindi!</b>\n💰 Balansga qo'shildi: <b>+{amount:,} so'm</b>")


@dp.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.answer(
        "📚 <b>Buyruqlar:</b>\n\n"
        "/start — Botni ishga tushirish\n"
        "/balance — Balansni ko'rish\n"
        "/profile — Profilni ko'rish\n"
        "/promo — Promo kod kiritish\n"
        "/help — Yordam\n\n"
        "❓ Savollar bo'lsa admin bilan bog'laning: @blazecs2admin"
    )


# ─── WEBHOOK / API (for Mini App) ───────────────────────────────────────────

from aiohttp import web

async def handle_api(request: web.Request):
    """Simple REST API for Mini App"""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    action = data.get("action")
    tid = data.get("telegram_id")

    if not action or not tid:
        return web.json_response({"error": "Missing fields"}, status=400)

    tid = int(tid)

    if action == "get_user":
        user = await db.get_user(tid)
        return web.json_response({"user": user})

    elif action == "get_skins":
        skins = await db.get_skins(
            weapon_type=data.get("weapon_type"),
            search=data.get("search"),
            sort=data.get("sort", "newest"),
            limit=data.get("limit", 20),
            offset=data.get("offset", 0)
        )
        return web.json_response({"skins": skins})

    elif action == "get_skin":
        skin = await db.get_skin(data.get("skin_id"))
        return web.json_response({"skin": skin})

    elif action == "get_featured":
        skins = await db.get_featured_skins()
        return web.json_response({"skins": skins})

    elif action == "get_giveaways":
        gws = await db.get_giveaways(status=data.get("status","active"))
        return web.json_response({"giveaways": gws})

    elif action == "join_giveaway":
        user = await db.get_user(tid)
        if not user: return web.json_response({"error": "User not found"})
        ok, err = await db.join_giveaway(data.get("giveaway_id"), user["id"])
        return web.json_response({"ok": ok, "error": err})

    elif action == "buy_skin":
        user = await db.get_user(tid)
        if not user: return web.json_response({"error": "User not found"})
        skin = await db.get_skin(data.get("skin_id"))
        if not skin: return web.json_response({"error": "Skin not found"})
        oid, err = await db.create_order(user["id"], skin["id"], skin["price"], user.get("trade_url"))
        if err: return web.json_response({"error": err})
        for aid in ADMIN_IDS:
            try:
                await bot.send_message(aid,
                    f"🛒 <b>Yangi buyurtma #{oid}!</b>\n"
                    f"👤 {user.get('first_name','?')} (@{user.get('username','?')})\n"
                    f"🔫 {skin['name']} ({skin['exterior']})\n"
                    f"💰 {skin['price']:,} so'm")
            except Exception: pass
        return web.json_response({"ok": True, "order_id": oid})

    elif action == "deposit":
        user = await db.get_user(tid)
        if not user: return web.json_response({"error": "User not found"})
        amount = int(data.get("amount", 0))
        method = data.get("method", "")
        txid   = data.get("transaction_id", "")
        if amount < 10000:
            return web.json_response({"error": "Minimal summa 10,000 so'm"})
        await db.create_deposit(user["id"], amount, method, txid)
        for aid in ADMIN_IDS:
            try:
                await bot.send_message(aid,
                    f"💳 <b>Yangi to'lov so'rovi!</b>\n"
                    f"👤 {user.get('first_name','?')} (@{user.get('username','?')})\n"
                    f"💰 {amount:,} so'm | {method}\n"
                    f"🆔 {txid}")
            except Exception: pass
        return web.json_response({"ok": True})

    elif action == "get_orders":
        user = await db.get_user(tid)
        if not user: return web.json_response({"error": "User not found"})
        orders = await db.get_orders(uid=user["id"], limit=20)
        return web.json_response({"orders": orders})

    elif action == "get_deposits":
        user = await db.get_user(tid)
        if not user: return web.json_response({"error": "User not found"})
        deps = await db.get_deposits(uid=user["id"], limit=20)
        return web.json_response({"deposits": deps})

    elif action == "get_favorites":
        user = await db.get_user(tid)
        if not user: return web.json_response({"error": "User not found"})
        favs = await db.get_favorites(user["id"])
        return web.json_response({"favorites": favs})

    elif action == "toggle_favorite":
        user = await db.get_user(tid)
        if not user: return web.json_response({"error": "User not found"})
        is_fav = await db.toggle_favorite(user["id"], data.get("skin_id"))
        return web.json_response({"is_favorite": is_fav})

    elif action == "use_promo":
        user = await db.get_user(tid)
        if not user: return web.json_response({"error": "User not found"})
        amount, err = await db.use_promo(user["id"], data.get("code","").upper())
        if err: return web.json_response({"error": err})
        return web.json_response({"ok": True, "amount": amount})

    elif action == "get_referrals":
        user = await db.get_user(tid)
        if not user: return web.json_response({"error": "User not found"})
        refs = await db.get_referrals(user["id"])
        return web.json_response({"referrals": refs, "code": user["referral_code"]})

    elif action == "get_notifications":
        user = await db.get_user(tid)
        if not user: return web.json_response({"error": "User not found"})
        notifs = await db.get_notifications(user["id"])
        return web.json_response({"notifications": notifs})

    elif action == "update_trade_url":
        await db.update_trade_url(tid, data.get("trade_url",""))
        return web.json_response({"ok": True})

    elif action == "admin_stats":
        user = await db.get_user(tid)
        if not user or not user["is_admin"] and tid not in ADMIN_IDS:
            return web.json_response({"error": "Unauthorized"}, status=403)
        stats = await db.get_dashboard_stats()
        return web.json_response({"stats": stats})

    return web.json_response({"error": "Unknown action"}, status=400)


async def main():
    await db.init_db()
    app = web.Application()
    app.router.add_post("/api", handle_api)
    app.router.add_options("/api", lambda r: web.Response(headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }))

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080)))
    await site.start()
    logging.info("API server started on port 8080")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
