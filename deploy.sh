#!/bin/bash
# deploy.sh — Full deployment script for Blaze CS2 Marketplace
# Run as root on Ubuntu 22.04 VPS
# Usage: chmod +x deploy.sh && ./deploy.sh

set -e
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

info "🔥 Blaze CS2 Marketplace — Deployment Script"
info "============================================="

# ── System deps ──────────────────────────────────────────────────────────────
info "Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq docker.io docker-compose curl git certbot ufw

# Enable firewall
ufw allow ssh
ufw allow 80
ufw allow 443
ufw --force enable

# Start Docker
systemctl enable docker
systemctl start docker

# ── Clone / update repo ───────────────────────────────────────────────────────
if [ ! -d "/opt/blaze" ]; then
    info "Cloning repository..."
    git clone https://github.com/yourname/blaze-cs2 /opt/blaze
else
    info "Updating repository..."
    cd /opt/blaze && git pull
fi

cd /opt/blaze

# ── Environment check ─────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
    cp .env.example .env
    error ".env file created from template. Please fill in all values and re-run!"
fi

source .env
[ -z "$BOT_TOKEN" ]         && error "BOT_TOKEN is not set in .env"
[ -z "$DATABASE_URL" ]      && error "DATABASE_URL is not set in .env"
[ -z "$SECRET_KEY" ]        && error "SECRET_KEY is not set in .env"
[ -z "$POSTGRES_PASSWORD" ] && error "POSTGRES_PASSWORD is not set in .env"

info "✅ Environment variables validated"

# ── SSL Certificate ───────────────────────────────────────────────────────────
DOMAIN=$(grep WEBAPP_URL .env | cut -d'/' -f3)
if [ -n "$DOMAIN" ] && [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    info "Getting SSL certificate for $DOMAIN..."
    certbot certonly --standalone \
        --non-interactive \
        --agree-tos \
        --email admin@$DOMAIN \
        -d $DOMAIN || warn "SSL cert failed — continuing without HTTPS"
fi

# ── Update domain in nginx config ─────────────────────────────────────────────
if [ -n "$DOMAIN" ]; then
    sed -i "s/your-domain.com/$DOMAIN/g" deploy/nginx.conf
fi

# ── Update API URL in frontend ────────────────────────────────────────────────
API_URL="https://$DOMAIN"
sed -i "s|https://your-backend.railway.app|$API_URL|g" frontend/index.html
sed -i "s|https://your-backend.railway.app|$API_URL|g" admin/index.html

# ── Build and start ───────────────────────────────────────────────────────────
info "Building and starting containers..."
docker-compose pull
docker-compose up -d --build

# Wait for backend
info "Waiting for backend to start..."
for i in {1..30}; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        info "✅ Backend is healthy"
        break
    fi
    sleep 2
    if [ $i -eq 30 ]; then
        error "Backend failed to start. Check: docker-compose logs backend"
    fi
done

# ── Run migrations ────────────────────────────────────────────────────────────
info "Running database migrations..."
docker-compose exec -T backend alembic upgrade head 2>/dev/null || \
    docker-compose exec -T backend python -c "from models.models import create_tables; import asyncio; asyncio.run(create_tables())"

# ── Seed database ─────────────────────────────────────────────────────────────
info "Seeding database with sample skins..."
docker-compose exec -T backend python seed.py

# ── Register Telegram webhook ─────────────────────────────────────────────────
WEBHOOK_SECRET=$(openssl rand -hex 16)
info "Registering Telegram webhook..."
curl -sf "https://$DOMAIN/api/telegram/set-webhook?secret=$WEBHOOK_SECRET" || \
    warn "Webhook registration failed — do it manually"

# ── Health check ──────────────────────────────────────────────────────────────
info ""
info "🔥 Deployment complete!"
info "================================="
info "Frontend:   https://$DOMAIN"
info "Admin:      https://$DOMAIN/admin/"
info "API docs:   (disabled in production)"
info "Health:     https://$DOMAIN/health"
info ""
info "📱 Set Mini App URL in BotFather:"
info "   /mybots → Your Bot → Menu Button → https://$DOMAIN"
info ""
info "Container status:"
docker-compose ps
info ""
info "View logs: docker-compose logs -f backend"
