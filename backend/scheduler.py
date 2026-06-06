"""
scheduler.py — Background tasks
- Aggregate daily stats
- Auto-end expired giveaways + pick winners
- Sync CS2 market prices from CSFloat/Skinport
Run as separate process: python scheduler.py
"""
import asyncio, random, logging
from datetime import datetime, timedelta

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.models import (
    AsyncSessionLocal, User, Order, Deposit, Skin, Giveaway,
    GiveawayParticipant, GiveawayStatus, OrderStatus, DepositStatus,
    DailyStats, Notification,
)
from steam.integrations import csfloat_api, skinport_api
from core.config import settings
import httpx

log = logging.getLogger("scheduler")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# ── Daily stats aggregation ───────────────────────────────────────────────────

async def aggregate_daily_stats():
    """Run at midnight — snapshot yesterday's stats into DailyStats table."""
    yesterday = (datetime.utcnow() - timedelta(days=1)).date()
    log.info(f"Aggregating stats for {yesterday}")

    async with AsyncSessionLocal() as db:
        # Check if already exists
        result = await db.execute(
            select(DailyStats).where(func.date(DailyStats.date) == yesterday)
        )
        if result.scalar_one_or_none():
            log.info("Stats already aggregated for this date")
            return

        async def count(model, *filters):
            q = select(func.count()).select_from(model)
            for f in filters: q = q.where(f)
            return (await db.execute(q)).scalar() or 0

        async def total(model, col, *filters):
            q = select(func.coalesce(func.sum(col), 0)).select_from(model)
            for f in filters: q = q.where(f)
            return (await db.execute(q)).scalar() or 0

        # Compute all stats
        since = datetime.combine(yesterday, datetime.min.time())
        until = since + timedelta(days=1)

        new_users = await count(User, User.created_at >= since, User.created_at < until)
        total_orders = await count(Order, Order.created_at >= since, Order.created_at < until)
        completed_orders = await count(Order, Order.created_at >= since, Order.created_at < until, Order.status == OrderStatus.DELIVERED)
        revenue = await total(Order, Order.price, Order.created_at >= since, Order.created_at < until, Order.status != OrderStatus.CANCELLED)
        total_deps = await total(Deposit, Deposit.amount, Deposit.created_at >= since, Deposit.created_at < until, Deposit.status == DepositStatus.CONFIRMED)
        dep_count = await count(Deposit, Deposit.created_at >= since, Deposit.created_at < until, Deposit.status == DepositStatus.CONFIRMED)

        stat = DailyStats(
            date=since,
            new_users=new_users,
            total_orders=total_orders,
            completed_orders=completed_orders,
            revenue=revenue,
            total_deposits=total_deps,
            deposit_count=dep_count,
        )
        db.add(stat)
        await db.commit()
        log.info(f"Stats saved: {new_users} users, {total_orders} orders, {revenue:,} revenue")


# ── Auto-end expired giveaways ────────────────────────────────────────────────

async def process_expired_giveaways():
    """Check giveaways that have passed their end_time and pick winners."""
    log.info("Checking expired giveaways...")

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Giveaway).where(
                Giveaway.status == GiveawayStatus.ACTIVE,
                Giveaway.end_time <= datetime.utcnow(),
            )
        )
        giveaways = result.scalars().all()

        for gw in giveaways:
            # Get all participants
            parts_result = await db.execute(
                select(GiveawayParticipant, User)
                .join(User, GiveawayParticipant.user_id == User.id)
                .where(GiveawayParticipant.giveaway_id == gw.id)
            )
            parts = parts_result.all()

            if not parts:
                gw.status = GiveawayStatus.CANCELLED
                log.info(f"Giveaway #{gw.id} cancelled (no participants)")
                await db.commit()
                continue

            # Pick random winner
            _, winner = random.choice(parts)
            gw.status    = GiveawayStatus.ENDED
            gw.winner_id = winner.id

            # Notify winner
            db.add(Notification(
                user_id=winner.id,
                title="🎉 Giveaway g'olibisiz!",
                message=f"'{gw.title}' giveaway'da g'olib bo'ldingiz! Sovg'a: {gw.prize_name}",
                type="success",
            ))
            await db.commit()

            log.info(f"Giveaway #{gw.id} ended. Winner: {winner.first_name} (@{winner.username})")

            # Telegram notification to winner
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage",
                        json={
                            "chat_id": winner.telegram_id,
                            "parse_mode": "HTML",
                            "text": (
                                f"🎉 <b>Tabriklaymiz, {winner.first_name}!</b>\n\n"
                                f"🏆 Siz <b>{gw.title}</b> giveaway'ining g'olibisiz!\n"
                                f"🎁 Sovrin: <b>{gw.prize_name}</b>\n\n"
                                f"Admin siz bilan tez orada bog'lanadi."
                            ),
                        },
                        timeout=10,
                    )
            except Exception as e:
                log.warning(f"Failed to notify giveaway winner: {e}")

            # Notify admins
            for admin_id in settings.admin_id_list:
                try:
                    async with httpx.AsyncClient() as client:
                        await client.post(
                            f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage",
                            json={
                                "chat_id": admin_id,
                                "parse_mode": "HTML",
                                "text": (
                                    f"🎁 <b>Giveaway #{gw.id} tugadi!</b>\n"
                                    f"🏆 G'olib: {winner.first_name} (@{winner.username or '—'})\n"
                                    f"Telegram ID: <code>{winner.telegram_id}</code>\n"
                                    f"Sovrin: {gw.prize_name}"
                                ),
                            },
                            timeout=10,
                        )
                except Exception:
                    pass


# ── Price sync from market APIs ───────────────────────────────────────────────

async def sync_market_prices():
    """
    Fetch latest prices from Skinport (bulk endpoint, cached 5 min)
    and update market_price field on our skins.
    """
    log.info("Syncing market prices from Skinport...")
    try:
        items = await skinport_api.get_items()
        if not items:
            log.warning("Skinport returned no data")
            return

        # Build price map: market_hash_name → min_price (USD cents → convert to som)
        # Using a rough exchange rate — ideally fetch from CBU API
        USD_TO_SOM = 12_700  # Update this regularly or fetch from API

        price_map = {}
        for item in items:
            name = item.get("market_hash_name", "")
            min_price = item.get("min_price")  # USD
            if name and min_price:
                price_map[name] = int(min_price * USD_TO_SOM / 100)  # cents to som

        if not price_map:
            log.warning("No prices extracted from Skinport")
            return

        updated = 0
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Skin).where(Skin.is_active == True))
            skins = result.scalars().all()

            for skin in skins:
                market_price = price_map.get(skin.name)
                if market_price and market_price != skin.market_price:
                    skin.market_price = market_price
                    updated += 1

            await db.commit()
        log.info(f"Updated market prices for {updated} skins")

    except Exception as e:
        log.error(f"Price sync failed: {e}")


# ── Cleanup old notifications ─────────────────────────────────────────────────

async def cleanup_old_notifications():
    """Delete notifications older than 30 days."""
    cutoff = datetime.utcnow() - timedelta(days=30)
    async with AsyncSessionLocal() as db:
        from sqlalchemy import delete
        result = await db.execute(
            delete(Notification).where(
                Notification.created_at < cutoff,
                Notification.is_read == True,
            )
        )
        await db.commit()
        log.info(f"Cleaned up {result.rowcount} old notifications")


# ── Stale order cleanup ───────────────────────────────────────────────────────

async def cancel_stale_orders():
    """Cancel pending orders older than 48 hours and refund balance."""
    cutoff = datetime.utcnow() - timedelta(hours=48)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Order).where(
                Order.status == OrderStatus.PENDING,
                Order.created_at < cutoff,
            )
        )
        stale = result.scalars().all()

        for order in stale:
            order.status = OrderStatus.CANCELLED
            order.admin_notes = "Avtomatik bekor qilindi (48s javob yo'q)"

            # Refund
            await db.execute(
                update(User).where(User.id == order.user_id).values(
                    balance=User.balance + order.price,
                    total_spent=User.total_spent - order.price,
                )
            )
            # Restore stock
            await db.execute(
                update(Skin).where(Skin.id == order.skin_id).values(
                    stock=Skin.stock + 1
                )
            )
            db.add(Notification(
                user_id=order.user_id,
                title="Buyurtma bekor qilindi",
                message=f"#{order.id} buyurtma 48 soat ichida tasdiqlanmadi. {order.price:,} so'm qaytarildi.",
                type="warning",
            ))

        await db.commit()
        if stale:
            log.info(f"Cancelled {len(stale)} stale orders")


# ── Scheduler loop ────────────────────────────────────────────────────────────

async def run_scheduler():
    log.info("Scheduler started")

    # Task intervals in seconds
    TASKS = [
        (process_expired_giveaways, 60),       # Every minute
        (cancel_stale_orders,       3600),      # Every hour
        (sync_market_prices,        300),       # Every 5 minutes
        (cleanup_old_notifications, 86400),     # Daily
        (aggregate_daily_stats,     86400),     # Daily
    ]

    last_run = {task: 0 for task, _ in TASKS}

    while True:
        now = asyncio.get_event_loop().time()

        for task_fn, interval in TASKS:
            if now - last_run[task_fn] >= interval:
                try:
                    await task_fn()
                    last_run[task_fn] = now
                except Exception as e:
                    log.error(f"Task {task_fn.__name__} failed: {e}")

        await asyncio.sleep(30)  # Check every 30 seconds


if __name__ == "__main__":
    asyncio.run(run_scheduler())
