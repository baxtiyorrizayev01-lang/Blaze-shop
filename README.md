# 🔥 Blaze CS2 Skin Shop — Telegram Mini App

Premium CS2 skin marketplace as a Telegram Mini App.

## 📁 Project Structure

```
blaze/
├── bot/                    # Python Aiogram bot + REST API
│   ├── main.py             # Bot handlers + aiohttp API server
│   ├── database.py         # SQLite async database layer
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile
│   └── .env.example
├── frontend/               # React + Vite Mini App
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── index.css       # TailwindCSS + custom styles
│   │   ├── store/
│   │   │   └── useStore.js # Zustand global state + API calls
│   │   ├── components/
│   │   │   ├── BottomNav.jsx
│   │   │   ├── SkinCard.jsx
│   │   │   └── Toast.jsx
│   │   └── pages/
│   │       ├── HomePage.jsx      # 🏠 Home with balance, featured, giveaways
│   │       ├── ShopPage.jsx      # 🛒 Catalog + search + filter + skin detail
│   │       ├── GiveawayPage.jsx  # 🎁 Active & ended giveaways + join
│   │       ├── BalancePage.jsx   # 💰 Deposit (3-step) + history + promo
│   │       └── ProfilePage.jsx   # 👤 Profile, orders, favorites, referrals
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── netlify.toml        # Deploy to Netlify
└── admin/
    └── index.html          # 🔧 Standalone admin panel (password: blaze2024)
```

## 🚀 Quick Start

### 1. Bot (Backend)

```bash
cd bot
cp .env.example .env
# Edit .env with your BOT_TOKEN and settings

pip install -r requirements.txt
python main.py
```

### 2. Frontend (Mini App)

```bash
cd frontend
npm install
cp .env.example .env
# Set VITE_API_URL=http://your-server:8080/api

npm run dev          # Development
npm run build        # Production build
```

### 3. BotFather Setup

1. Open [@BotFather](https://t.me/botfather)
2. `/newbot` — create your bot
3. `/setmenubutton` — set Mini App button
4. URL: `https://your-frontend.netlify.app`

### 4. Deploy Frontend → Netlify

```bash
cd frontend
npm run build
# Drag `dist/` folder to netlify.com
# OR connect GitHub repo → auto deploy
```

### 5. Deploy Bot → Railway/VPS

```bash
# Railway (free tier)
railway login
railway new
railway up

# Or Docker
docker-compose up -d
```

## 🌐 Environment Variables

### Bot (.env)
```
BOT_TOKEN=1234567890:AAGxxxxxxxxxxxxxxxx
ADMIN_IDS=123456789,987654321
WEBAPP_URL=https://your-app.netlify.app
DATABASE_URL=blaze.db
CHANNEL_ID=@your_channel
PORT=8080
```

### Frontend (.env)
```
VITE_API_URL=https://your-bot-server.railway.app/api
```

## 🔧 Admin Panel

Open `admin/index.html` in browser.
Default password: `blaze2024`

**Features:**
- 📊 Dashboard with revenue chart
- 🛒 Skin management (add/edit/delete)
- 📦 Order management (confirm/cancel)
- 💳 Deposit approval (confirm/reject)
- 🎁 Giveaway management + pick winner
- 👥 User management + balance control
- ⚙️ Settings

## 📱 Mini App Features

| Feature | Status |
|---------|--------|
| 🏠 Home page with balance | ✅ |
| 🛒 Skin catalog with filters | ✅ |
| 🔍 Search skins | ✅ |
| 🛒 Buy skin (balance deduct) | ✅ |
| ❤️ Favorites | ✅ |
| 🎁 Giveaway join | ✅ |
| ⏱ Countdown timer | ✅ |
| 💰 3-step deposit flow | ✅ |
| 💳 Uzcard/Humo/Click/Payme | ✅ |
| 📋 Transaction history | ✅ |
| 🎟 Promo codes | ✅ |
| 👤 Profile page | ✅ |
| 📦 Order history | ✅ |
| 👥 Referral system | ✅ |
| 🔔 Notifications | ✅ |
| 🔗 Trade URL | ✅ |
| 📳 Haptic feedback | ✅ |
| 🌙 Telegram theme | ✅ |

## 🤖 Bot Commands

```
/start [ref_CODE] — Start bot + open Mini App
/balance          — Check balance
/profile          — View profile + referral link
/promo            — Enter promo code
/admin            — Admin panel (admins only)
/help             — Help
```

## 🗄️ Database Schema

- `users` — Telegram users with balance
- `skins` — CS2 skin listings
- `orders` — Purchase orders
- `deposits` — Balance top-up requests
- `giveaways` — Giveaway events
- `giveaway_participants` — Who joined what
- `favorites` — User favorites
- `referrals` — Referral tracking
- `promo_codes` — Discount/bonus codes
- `notifications` — In-app notifications

## 🔌 API Endpoints

POST `/api` with JSON body:

| Action | Description |
|--------|-------------|
| `get_user` | Get user data |
| `get_skins` | Get skin catalog |
| `get_featured` | Featured skins |
| `buy_skin` | Purchase skin |
| `get_orders` | User orders |
| `deposit` | Create deposit |
| `get_deposits` | Deposit history |
| `get_giveaways` | Active giveaways |
| `join_giveaway` | Join giveaway |
| `toggle_favorite` | Add/remove favorite |
| `use_promo` | Apply promo code |
| `get_referrals` | Referral list |
| `update_trade_url` | Set Steam trade URL |
| `get_notifications` | User notifications |

## 🎨 Design System

- Background: `#0B0F17`
- Accent: `#FF6B00`
- Success: `#00d084`
- Error: `#e74c3c`
- Font: Barlow (Google Fonts)
- Glassmorphism cards
- Mobile-first, Telegram-native UX
