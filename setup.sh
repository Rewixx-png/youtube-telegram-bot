#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN}   🚀 YOUTUBE BOT INSTALLER (NO-VENV EDITION) 🚀    ${NC}"
echo -e "${CYAN}======================================================${NC}"

# 1. Проверки
if ! command -v docker &> /dev/null; then echo -e "${RED}Docker не найден!${NC}"; exit 1; fi
if ! command -v python3 &> /dev/null; then echo -e "${RED}Python3 не найден!${NC}"; exit 1; fi

# 2. Данные
echo -e "\n${YELLOW}[1/6] Сбор конфигурации...${NC}"

read -p "Домен API (напр. api.mydomain.com): " DOMAIN
read -p "Email для SSL: " EMAIL
read -p "Telegram API_ID: " TG_API_ID
read -p "Telegram API_HASH: " TG_API_HASH
read -p "Bot Token: " BOT_TOKEN

if [[ -z "$DOMAIN" || -z "$BOT_TOKEN" ]]; then echo -e "${RED}Обязательные поля пусты!${NC}"; exit 1; fi

# Генерируем .env файл
echo -e "\n${YELLOW}[2/6] Создание .env файла...${NC}"
cat > .env <<EOF
BOT_TOKEN=${BOT_TOKEN}
TELEGRAM_API_ID=${TG_API_ID}
TELEGRAM_API_HASH=${TG_API_HASH}
API_DOMAIN=${DOMAIN}
ADMIN_EMAIL=${EMAIL}
EOF
echo -e "${GREEN}✅ .env создан.${NC}"

# 3. Cookies
echo -e "\n${YELLOW}[3/6] Вставка Cookies (Netscape format)...${NC}"
echo -e "${CYAN}Скопируй текст куков, вставь ниже, нажми ENTER, затем Ctrl+D.${NC}"
cat > cookies.txt
if [ ! -s cookies.txt ]; then echo -e "${RED}Пустые куки!${NC}"; exit 1; fi

# 4. Установка библиотек (ГЛОБАЛЬНО)
echo -e "\n${YELLOW}[4/6] Установка Python библиотек (Global)...${NC}"
pip install -r requirements.txt

# 5. Docker Configs
echo -e "\n${YELLOW}[5/6] Настройка Docker/Nginx...${NC}"
mkdir -p nginx_conf certbot/conf certbot/www

cat > docker-compose.yml <<EOF
version: '3.8'
services:
  telegram-bot-api:
    image: aiogram/telegram-bot-api:latest
    container_name: telegram-bot-api
    restart: unless-stopped
    environment:
      - TELEGRAM_API_ID=${TG_API_ID}
      - TELEGRAM_API_HASH=${TG_API_HASH}
      - TELEGRAM_LOCAL=true
      - TELEGRAM_HTTP_PORT=8081
    volumes:
      - ./telegram-bot-api-data:/var/lib/telegram-bot-api
    ports:
      - "8081:8081"
  nginx:
    image: nginx:alpine
    container_name: nginx-proxy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx_conf:/etc/nginx/conf.d
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    depends_on:
      - telegram-bot-api
    command: "/bin/sh -c 'while :; do sleep 6h & wait \$\${!}; nginx -s reload; done & nginx -g \"daemon off;\"'"
  certbot:
    image: certbot/certbot
    container_name: certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait \$\${!}; done;'"
EOF

# Nginx HTTP Only first
cat > nginx_conf/nginx.conf <<EOF
server {
    listen 80;
    server_name ${DOMAIN};
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 301 https://\$host\$request_uri; }
}
EOF

# 6. SSL Init
echo -e "\n${YELLOW}[6/6] Получение SSL...${NC}"
docker-compose up -d nginx
sleep 5
docker-compose run --rm certbot certonly --webroot --webroot-path /var/www/certbot -d ${DOMAIN} --email ${EMAIL} --agree-tos --no-eff-email

if [ ! -d "./certbot/conf/live/${DOMAIN}" ]; then
    echo -e "${RED}❌ SSL Fail.${NC}"
    exit 1
fi

# Nginx Full Config
cat > nginx_conf/nginx.conf <<EOF
server {
    listen 80;
    server_name ${DOMAIN};
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 301 https://\$host\$request_uri; }
}
server {
    listen 443 ssl;
    server_name ${DOMAIN};
    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    client_max_body_size 2000M;
    location / {
        proxy_pass http://telegram-bot-api:8081;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

docker-compose restart nginx
docker-compose up -d telegram-bot-api

echo -e "\n${GREEN}🎉 ВСЕ ГОТОВО!${NC}"
echo -e "Запуск: ${YELLOW}python3 bot.py${NC}"