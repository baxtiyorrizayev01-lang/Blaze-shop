# 🔥 Blaze CS2 Marketplace — Production v2.0

> CS2 skin marketplace optimized for 10,000+ concurrent users  
> Built for Uzbek market: Payme · Click · Uzum Bank · UzCard/Humo

---

## 📦 Project Structure

```
blaze-pro/
├── backend/                    # FastAPI backend
│   ├── api/
│   │   ├── middleware/
│   │   │   └── auth.py         # JWT + Telegram initData auth
│   │   └── routes/
│   │       ├── auth.py         # Telegram + Steam OpenID login
│   │       ├── users.py        # Profile, referrals, bonus, promo
│   │       ├── skins.py        # Skin listing, search, favorites
│   │       ├── orders.py       # Buy + order management
│   │       ├── deposits.py     # Payme/Click/Uzum/UzCard webhooks
│   │       ├── giveaways.py    # Giveaway system
│   │       ├── admin.py        # Full admin API + analytics
│   │       ├── steam.py        # Steam inventory sync
│   │       ├── market.py       # CSFloat + Skinport price feeds
│   │       ├── telegram.py     # Bot webhook + channel check
│   │       └── payments.py     # Payment redirect pages
│   ├── core/
│   │   └── config.py           # All environment settings
│   ├── models/
│   │   └── models.py           # PostgreSQL schema (SQLAlchemy 2.0 async)
│   ├── payments/
│   │   └── gateways.py         # Payme, Click, Uzum, UzCard/Humo
│   ├── steam/
│   │   └── integrations.py     # Steam API, CSFloat, Skinport
│   ├── migrations/             # Alembic async migrations
│   ├── main.py                 # FastAPI app + middleware
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── index.html              # Complete Telegram Mini App
│   └── src/
│       └── store/
│           └── useStore.js     # Zustand store (React version)
├── admin/
│   └── index.html              # Responsive admin panel (standalone)
├── deploy/
│   └── nginx.conf              # Production nginx config
├── docker-compose.yml          # Full stack deployment
├── .env.example                # All required environment variables
└── README.md
```

---

## 🚀 Quick Deploy (VPS)

### Prerequisites
- Ubuntu 22.04 VPS (4GB+ RAM recommended)
- Domain name with DNS pointing to your VPS
- Docker + Docker Compose installed

### Step 1: Clone & Configure
```bash
git clone https://github.com/yourname/blaze-cs2
cd blaze-cs2

# Copy and fill environment variables
cp .env.example .env
nano .env   # Fill ALL values
```

### Step 2: SSL Certificate
```bash
# Install certbot
apt install certbot

# Get certificate
certbot certonly --standalone -d your-domain.com

# Update nginx.conf with your domain
sed -i 's/your-domain.com/youractualdomain.com/g' deploy/nginx.conf
```

### Step 3: Update Frontend URL
```bash
# Update API URL in frontend
sed -i "s|https://your-backend.railway.app|https://your-domain.com|g" frontend/index.html

# Update API URL in admin panel
sed -i "s|https://your-backend.railway.app|https://your-domain.com|g" admin/index.html
```

### Step 4: Run
```bash
docker compose up -d --build

# Verify all containers are healthy
docker compose ps

# View logs
docker compose logs -f backend
```

### Step 5: Register Telegram Webhook
```bash
# Set bot webhook (replace YOUR_SECRET with a random string)
curl -X POST "https://your-domain.com/api/telegram/set-webhook?secret=YOUR_RANDOM_SECRET"
```

### Step 6: Create first admin skin
```bash
# Get JWT token first (from Telegram login)
# Then call admin API to add first skin:
curl -X POST "https://your-domain.com/api/admin/skins" \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{"name":"AK-47 | Redline","weapon_type":"Rifle","exterior":"Field-Tested","price":65000,"stock":1}'
```

---

## 🏦 Payment Setup

### Payme
1. Register at https://payme.uz/
2. Get Merchant ID and keys
3. Set webhook URL: `https://your-domain.com/api/deposits/webhook/payme`
4. Fill `PAYME_*` vars in `.env`
5. Set `PAYME_TEST_MODE=False` for production

### Click
1. Register at https://my.click.uz/
2. Set prepare URL: `https://your-domain.com/api/deposits/webhook/click/prepare`
3. Set complete URL: `https://your-domain.com/api/deposits/webhook/click/complete`
4. Fill `CLICK_*` vars in `.env`

### Uzum Bank
1. Register at https://uzumbank.uz/business
2. Set webhook URL: `https://your-domain.com/api/deposits/webhook/uzum`
3. Fill `UZUM_*` vars in `.env`

### UzCard/Humo (Manual + OCTO)
- For manual: Users submit their transaction ID, admin confirms
- For OCTO gateway: Register at https://octo.uz/, fill `UZCARD_*` vars

---

## 🎮 Steam Setup

1. Get Steam API key: https://steamcommunity.com/dev/apikey
2. Set `STEAM_API_KEY` in `.env`
3. Set `STEAM_REALM=https://your-domain.com`
4. Set `STEAM_RETURN_URL=/api/auth/steam/callback`

---

## 📈 CS2 Market APIs

### CSFloat
1. Register at https://csfloat.com/
2. Get API key from profile settings
3. Set `CSFLOAT_API_KEY` in `.env`

### Skinport
1. Register at https://skinport.com/
2. Get API credentials from account → API
3. Set `SKINPORT_API_KEY` and `SKINPORT_SECRET` in `.env`

---

## ⚡ Performance for 10,000+ Users

The stack is configured for high load:

| Component | Configuration |
|-----------|---------------|
| FastAPI   | 4 Gunicorn workers + async I/O |
| PostgreSQL | Pool size: 20 connections |
| Redis     | 256MB, LRU eviction |
| Nginx     | Rate limiting, gzip, HTTP/2 |
| DB indexes | All query fields indexed |

**Scaling tip:** For 50,000+ users, add:
```yaml
# docker-compose.yml
backend:
  deploy:
    replicas: 4
```

---

## 🔒 Security Features

- ✅ JWT tokens with version invalidation (ban = instant logout)
- ✅ Telegram initData HMAC verification
- ✅ Rate limiting per IP (60 req/min API, 10/min auth)
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ HTTPS only (HTTP → HTTPS redirect)
- ✅ Security headers (HSTS, XSS, etc.)
- ✅ Admin role verification on every admin endpoint
- ✅ Webhook signature verification (Payme, Click, Uzum)
- ✅ Audit log for all admin actions

---

## 📱 Telegram Mini App

Open in Telegram by setting your bot's Menu Button URL to:
```
https://your-domain.com
```

Or create a direct link:
```
https://t.me/YourBotUsername/app
```

---

## 🛠 Database Migrations

```bash
# Initialize migrations
cd backend
alembic init migrations

# Create a migration
alembic revision --autogenerate -m "initial schema"

# Apply migrations
alembic upgrade head
```

---

## 📊 Admin Panel

Access at: `https://your-domain.com/admin/`

First time setup:
1. Open admin panel
2. Click "⚙️ API Sozlash" button
3. Enter backend URL and your JWT token

Features:
- 📊 Real-time dashboard with revenue charts
- 🛒 Order management with instant confirm/send/deliver
- 💳 Deposit approval workflow
- 👥 User management + ban/unban
- 🔫 Skin catalog management
- 🎁 Giveaway creation + winner selection
- 🎟 Promo code management
- 📢 Broadcast notifications to all/selected users
- 📈 Analytics: revenue, users, deposits, top skins

---

## 🔧 Troubleshooting

```bash
# Check backend health
curl https://your-domain.com/health

# View backend logs
docker compose logs backend --tail=100 -f

# Restart all services
docker compose restart

# Force rebuild
docker compose up -d --build --force-recreate

# Check PostgreSQL
docker compose exec postgres psql -U blaze -d blaze -c "\dt"

# Run DB migrations manually
docker compose exec backend alembic upgrade head
```

---

## 📞 Support

- Telegram: @BlazeFalcon
- Platform: Blaze CS2 Marketplace v2.0
