import aiosqlite, os, secrets, string
from datetime import datetime

DB_PATH = os.getenv("DATABASE_URL", "blaze.db")

CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT, first_name TEXT, last_name TEXT,
    balance INTEGER DEFAULT 0,
    referral_code TEXT UNIQUE,
    referred_by INTEGER,
    is_banned INTEGER DEFAULT 0,
    is_admin INTEGER DEFAULT 0,
    trade_url TEXT,
    total_spent INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS skins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, weapon_type TEXT NOT NULL,
    collection TEXT, exterior TEXT NOT NULL,
    float_val REAL, pattern INTEGER, price INTEGER NOT NULL,
    image_url TEXT, is_active INTEGER DEFAULT 1,
    is_featured INTEGER DEFAULT 0, stock INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL, skin_id INTEGER NOT NULL,
    price INTEGER NOT NULL, status TEXT DEFAULT 'pending',
    trade_url TEXT, payment_method TEXT DEFAULT 'balance',
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS deposits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL, amount INTEGER NOT NULL,
    method TEXT NOT NULL, transaction_id TEXT,
    screenshot_url TEXT, status TEXT DEFAULT 'pending',
    admin_note TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS giveaways (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL, skin_id INTEGER,
    prize_name TEXT NOT NULL, prize_image TEXT,
    description TEXT, max_participants INTEGER DEFAULT 100,
    min_balance INTEGER DEFAULT 0, end_time TEXT NOT NULL,
    status TEXT DEFAULT 'active', winner_id INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS giveaway_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    giveaway_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
    joined_at TEXT DEFAULT (datetime('now')),
    UNIQUE(giveaway_id, user_id)
);
CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL, skin_id INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, skin_id)
);
CREATE TABLE IF NOT EXISTS referrals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER NOT NULL, referred_id INTEGER NOT NULL,
    bonus_paid INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS promo_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL, bonus_amount INTEGER NOT NULL,
    max_uses INTEGER DEFAULT 1, uses INTEGER DEFAULT 0,
    expires_at TEXT, is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS promo_uses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL, promo_id INTEGER NOT NULL,
    used_at TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, promo_id)
);
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL, title TEXT NOT NULL,
    message TEXT NOT NULL, is_read INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
"""

SEED_DATA = """
INSERT OR IGNORE INTO skins (name,weapon_type,collection,exterior,float_val,pattern,price,is_featured,stock) VALUES
('AK-47 | Redline','Rifle','The Phoenix Collection','Field-Tested',0.16,782,65000,1,3),
('AWP | Hyper Beast','Sniper Rifle','The Wildfire Collection','Minimal Wear',0.12,341,120000,1,2),
('M4A1-S | Night Terror','Rifle','The Dreams & Nightmares','Field-Tested',0.21,182,75000,0,5),
('Desert Eagle | Printstream','Pistol','The Fracture Collection','Factory New',0.03,654,85000,1,4),
('★ Karambit | Lore','Knife','The Breakout Collection','Factory New',0.01,921,2850000,1,1),
('Glock-18 | Neo-Noir','Pistol','The Gamma 2 Collection','Field-Tested',0.23,443,25000,0,8),
('M4A4 | Asiimov','Rifle','The Danger Zone Collection','Minimal Wear',0.14,555,95000,0,3),
('★ Butterfly Knife | Fade','Knife','The Breakout Collection','Factory New',0.02,879,4250000,1,1),
('USP-S | Kill Confirmed','Pistol','The Cobblestone Collection','Minimal Wear',0.09,212,40000,0,6),
('AK-47 | Bloodsport','Rifle','The Spectrum Collection','Field-Tested',0.19,332,85000,0,4),
('AWP | Asiimov','Sniper Rifle','The Breakout Collection','Field-Tested',0.28,111,70000,0,5),
('M4A1-S | Hyper Beast','Rifle','The Wildfire Collection','Minimal Wear',0.13,290,55000,0,7);
INSERT OR IGNORE INTO giveaways (title,prize_name,description,max_participants,end_time,status) VALUES
('Weekly AK-47 Giveaway','AK-47 | Redline (FT)','Like and share our channel!',200,datetime('now','+2 days'),'active'),
('AWP Hyper Beast Special','AWP | Hyper Beast (MW)','Subscribe and join!',150,datetime('now','+1 day'),'active'),
('Karambit Mega Giveaway','★ Karambit | Lore (FN)','Big giveaway for top members!',500,datetime('now','+5 days'),'active');
INSERT OR IGNORE INTO promo_codes (code,bonus_amount,max_uses) VALUES
('BLAZE2024',10000,100),('WELCOME',5000,500);
"""

def gen_ref(): return ''.join(secrets.choice(string.ascii_uppercase+string.digits) for _ in range(8))

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(CREATE_TABLES)
        await db.executescript(SEED_DATA)
        await db.commit()

async def get_or_create_user(tid, username=None, first_name=None, last_name=None, ref_code=None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE telegram_id=?", (tid,)) as c:
            u = await c.fetchone()
        if u:
            await db.execute("UPDATE users SET username=?,first_name=?,last_name=? WHERE telegram_id=?",
                             (username,first_name,last_name,tid))
            await db.commit()
            return dict(u), False
        ref_id = None
        if ref_code:
            async with db.execute("SELECT id FROM users WHERE referral_code=?", (ref_code,)) as c:
                r = await c.fetchone()
                if r: ref_id = r["id"]
        await db.execute(
            "INSERT INTO users (telegram_id,username,first_name,last_name,referral_code,referred_by) VALUES (?,?,?,?,?,?)",
            (tid, username, first_name, last_name, gen_ref(), ref_id))
        if ref_id:
            async with db.execute("SELECT id FROM users WHERE telegram_id=?", (tid,)) as c:
                new = await c.fetchone()
            await db.execute("INSERT INTO referrals (referrer_id,referred_id) VALUES (?,?)",(ref_id,new["id"]))
            await db.execute("UPDATE users SET balance=balance+5000 WHERE id=?",(ref_id,))
        await db.commit()
        async with db.execute("SELECT * FROM users WHERE telegram_id=?", (tid,)) as c:
            return dict(await c.fetchone()), True

async def get_user(tid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE telegram_id=?", (tid,)) as c:
            r = await c.fetchone(); return dict(r) if r else None

async def get_user_by_id(uid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE id=?", (uid,)) as c:
            r = await c.fetchone(); return dict(r) if r else None

async def update_user_balance(uid, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET balance=balance+? WHERE id=?", (amount,uid))
        await db.commit()

async def update_trade_url(tid, url):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET trade_url=? WHERE telegram_id=?", (url,tid))
        await db.commit()

async def ban_user(uid, ban=True):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_banned=? WHERE id=?", (1 if ban else 0, uid))
        await db.commit()

async def get_all_users(limit=50, offset=0):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",(limit,offset)) as c:
            return [dict(r) for r in await c.fetchall()]

async def get_user_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        res = {}
        for k,q in [("total","SELECT COUNT(*) as c FROM users"),
                    ("active","SELECT COUNT(*) as c FROM users WHERE is_banned=0"),
                    ("banned","SELECT COUNT(*) as c FROM users WHERE is_banned=1"),
                    ("today","SELECT COUNT(*) as c FROM users WHERE date(created_at)=date('now')"),
                    ("total_balance","SELECT COALESCE(SUM(balance),0) as c FROM users")]:
            async with db.execute(q) as cur: res[k] = (await cur.fetchone())["c"]
        return res

async def get_skins(weapon_type=None, search=None, sort="newest", limit=20, offset=0):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        where=["is_active=1","stock>0"]; params=[]
        if weapon_type: where.append("weapon_type=?"); params.append(weapon_type)
        if search: where.append("name LIKE ?"); params.append(f"%{search}%")
        order={"newest":"id DESC","price_asc":"price ASC","price_desc":"price DESC",
               "featured":"is_featured DESC,id DESC"}.get(sort,"id DESC")
        q=f"SELECT * FROM skins WHERE {' AND '.join(where)} ORDER BY {order} LIMIT ? OFFSET ?"
        async with db.execute(q, params+[limit,offset]) as c:
            return [dict(r) for r in await c.fetchall()]

async def get_skin(sid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM skins WHERE id=?", (sid,)) as c:
            r = await c.fetchone(); return dict(r) if r else None

async def add_skin(name,weapon_type,collection,exterior,float_val,pattern,price,image_url=None,is_featured=0,stock=1):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO skins (name,weapon_type,collection,exterior,float_val,pattern,price,image_url,is_featured,stock) VALUES (?,?,?,?,?,?,?,?,?,?)",
                         (name,weapon_type,collection,exterior,float_val,pattern,price,image_url,is_featured,stock))
        await db.commit()

async def update_skin(sid, **kw):
    fields=", ".join(f"{k}=?" for k in kw)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE skins SET {fields} WHERE id=?", list(kw.values())+[sid])
        await db.commit()

async def delete_skin(sid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE skins SET is_active=0 WHERE id=?", (sid,))
        await db.commit()

async def get_featured_skins(limit=6):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM skins WHERE is_featured=1 AND is_active=1 AND stock>0 LIMIT ?", (limit,)) as c:
            return [dict(r) for r in await c.fetchall()]

async def create_order(uid, sid, price, trade_url=None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT balance FROM users WHERE id=?", (uid,)) as c:
            u = await c.fetchone()
        if not u or u["balance"] < price: return None, "Balans yetarli emas"
        async with db.execute("SELECT stock FROM skins WHERE id=? AND is_active=1", (sid,)) as c:
            s = await c.fetchone()
        if not s or s["stock"] < 1: return None, "Skin mavjud emas"
        await db.execute("UPDATE users SET balance=balance-?,total_spent=total_spent+? WHERE id=?", (price,price,uid))
        await db.execute("UPDATE skins SET stock=stock-1 WHERE id=?", (sid,))
        await db.execute("INSERT INTO orders (user_id,skin_id,price,trade_url) VALUES (?,?,?,?)", (uid,sid,price,trade_url))
        async with db.execute("SELECT last_insert_rowid() as l") as c: oid=(await c.fetchone())["l"]
        await db.commit()
        return oid, None

async def get_orders(uid=None, status=None, limit=20, offset=0):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        where=["1=1"]; params=[]
        if uid: where.append("o.user_id=?"); params.append(uid)
        if status: where.append("o.status=?"); params.append(status)
        q=f"""SELECT o.*,s.name as skin_name,s.exterior,s.weapon_type,s.image_url,u.username,u.first_name
              FROM orders o JOIN skins s ON o.skin_id=s.id JOIN users u ON o.user_id=u.id
              WHERE {' AND '.join(where)} ORDER BY o.created_at DESC LIMIT ? OFFSET ?"""
        async with db.execute(q, params+[limit,offset]) as c:
            return [dict(r) for r in await c.fetchall()]

async def update_order_status(oid, status, notes=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE orders SET status=?,notes=?,updated_at=datetime('now') WHERE id=?", (status,notes,oid))
        await db.commit()

async def create_deposit(uid, amount, method, txid=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO deposits (user_id,amount,method,transaction_id) VALUES (?,?,?,?)", (uid,amount,method,txid))
        await db.commit()

async def get_deposits(uid=None, status=None, limit=20, offset=0):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        where=["1=1"]; params=[]
        if uid: where.append("d.user_id=?"); params.append(uid)
        if status: where.append("d.status=?"); params.append(status)
        q=f"""SELECT d.*,u.username,u.first_name,u.telegram_id
              FROM deposits d JOIN users u ON d.user_id=u.id
              WHERE {' AND '.join(where)} ORDER BY d.created_at DESC LIMIT ? OFFSET ?"""
        async with db.execute(q, params+[limit,offset]) as c:
            return [dict(r) for r in await c.fetchall()]

async def approve_deposit(did):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM deposits WHERE id=?", (did,)) as c: dep=await c.fetchone()
        if not dep or dep["status"]!="pending": return False
        await db.execute("UPDATE deposits SET status='confirmed',updated_at=datetime('now') WHERE id=?", (did,))
        await db.execute("UPDATE users SET balance=balance+? WHERE id=?", (dep["amount"],dep["user_id"]))
        await db.commit(); return True

async def reject_deposit(did, note=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE deposits SET status='rejected',admin_note=?,updated_at=datetime('now') WHERE id=?", (note,did))
        await db.commit()

async def get_giveaways(status="active", limit=10):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""SELECT g.*,(SELECT COUNT(*) FROM giveaway_participants WHERE giveaway_id=g.id) as participant_count
                                 FROM giveaways g WHERE g.status=? ORDER BY g.end_time ASC LIMIT ?""", (status,limit)) as c:
            return [dict(r) for r in await c.fetchall()]

async def get_giveaway(gid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""SELECT g.*,(SELECT COUNT(*) FROM giveaway_participants WHERE giveaway_id=g.id) as participant_count
                                 FROM giveaways g WHERE g.id=?""", (gid,)) as c:
            r=await c.fetchone(); return dict(r) if r else None

async def join_giveaway(gid, uid):
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute("INSERT INTO giveaway_participants (giveaway_id,user_id) VALUES (?,?)", (gid,uid))
            await db.commit(); return True,None
        except aiosqlite.IntegrityError: return False,"Siz allaqachon qatnashyapsiz"

async def is_participating(gid, uid):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM giveaway_participants WHERE giveaway_id=? AND user_id=?", (gid,uid)) as c:
            return bool(await c.fetchone())

async def pick_winner(gid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""SELECT u.* FROM giveaway_participants gp JOIN users u ON gp.user_id=u.id
                                 WHERE gp.giveaway_id=? ORDER BY RANDOM() LIMIT 1""", (gid,)) as c:
            w=await c.fetchone()
        if w:
            await db.execute("UPDATE giveaways SET status='ended',winner_id=? WHERE id=?", (w["id"],gid))
            await db.commit()
        return dict(w) if w else None

async def create_giveaway(title,prize_name,description,max_participants,end_time,skin_id=None,prize_image=None,min_balance=0):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO giveaways (title,skin_id,prize_name,prize_image,description,max_participants,min_balance,end_time) VALUES (?,?,?,?,?,?,?,?)",
                         (title,skin_id,prize_name,prize_image,description,max_participants,min_balance,end_time))
        await db.commit()

async def toggle_favorite(uid, sid):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM favorites WHERE user_id=? AND skin_id=?", (uid,sid)) as c: e=await c.fetchone()
        if e:
            await db.execute("DELETE FROM favorites WHERE user_id=? AND skin_id=?", (uid,sid)); await db.commit(); return False
        await db.execute("INSERT INTO favorites (user_id,skin_id) VALUES (?,?)", (uid,sid)); await db.commit(); return True

async def get_favorites(uid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT s.* FROM favorites f JOIN skins s ON f.skin_id=s.id WHERE f.user_id=? ORDER BY f.created_at DESC", (uid,)) as c:
            return [dict(r) for r in await c.fetchall()]

async def use_promo(uid, code):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM promo_codes WHERE code=? AND is_active=1", (code,)) as c: p=await c.fetchone()
        if not p: return None,"Promo kod topilmadi"
        if p["uses"]>=p["max_uses"]: return None,"Promo kod tugagan"
        async with db.execute("SELECT 1 FROM promo_uses WHERE user_id=? AND promo_id=?", (uid,p["id"])) as c:
            if await c.fetchone(): return None,"Siz bu kodni allaqachon ishlatgansiz"
        await db.execute("INSERT INTO promo_uses (user_id,promo_id) VALUES (?,?)", (uid,p["id"]))
        await db.execute("UPDATE promo_codes SET uses=uses+1 WHERE id=?", (p["id"],))
        await db.execute("UPDATE users SET balance=balance+? WHERE id=?", (p["bonus_amount"],uid))
        await db.commit(); return p["bonus_amount"],None

async def create_notification(uid, title, message):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO notifications (user_id,title,message) VALUES (?,?,?)", (uid,title,message))
        await db.commit()

async def get_notifications(uid, limit=20):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT ?", (uid,limit)) as c:
            return [dict(r) for r in await c.fetchall()]

async def get_referrals(uid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""SELECT u.username,u.first_name,u.created_at,u.total_spent
                                 FROM referrals r JOIN users u ON r.referred_id=u.id
                                 WHERE r.referrer_id=? ORDER BY r.created_at DESC""", (uid,)) as c:
            return [dict(r) for r in await c.fetchall()]

async def get_dashboard_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        stats={}
        for k,q in [("total_users","SELECT COUNT(*) as c FROM users"),
                    ("total_skins","SELECT COUNT(*) as c FROM skins WHERE is_active=1"),
                    ("total_orders","SELECT COUNT(*) as c FROM orders"),
                    ("pending_orders","SELECT COUNT(*) as c FROM orders WHERE status='pending'"),
                    ("pending_deposits","SELECT COUNT(*) as c FROM deposits WHERE status='pending'"),
                    ("active_giveaways","SELECT COUNT(*) as c FROM giveaways WHERE status='active'"),
                    ("today_sales","SELECT COUNT(*) as c FROM orders WHERE date(created_at)=date('now')"),
                    ("today_revenue","SELECT COALESCE(SUM(price),0) as c FROM orders WHERE date(created_at)=date('now') AND status!='cancelled'"),
                    ("total_revenue","SELECT COALESCE(SUM(price),0) as c FROM orders WHERE status!='cancelled'")]:
            async with db.execute(q) as cur: stats[k]=(await cur.fetchone())["c"]
        return stats
