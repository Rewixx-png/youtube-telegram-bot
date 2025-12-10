#!/bin/bash

# ==========================================
# 🛡️  YOUTUBE BOT INSTALLER v4.1
#    "Lazy Admin Edition"
# ==========================================

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
MAGENTA='\033[1;35m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${MAGENTA}   _______________________________________________   ${NC}"
echo -e "${MAGENTA}  |                                               |  ${NC}"
echo -e "${MAGENTA}  |    🤖 YOUTUBE BOT SETUP: LAZY MODE 🤖         |  ${NC}"
echo -e "${MAGENTA}  |_______________________________________________|  ${NC}"

# --- 1. CLEANUP & TOOLS ---
echo -e "\n${YELLOW}🧹 Чистка хвостов...${NC}"
if [ -f "docker-compose.yml" ]; then
    docker-compose down --remove-orphans > /dev/null 2>&1
fi

install_tools() {
    if ! command -v lsof &> /dev/null; then
        echo -e "${YELLOW}🛠️  Stalling lsof...${NC}"
        if [ -x "$(command -v apt-get)" ]; then apt-get update -qq && apt-get install -y lsof -qq;
        elif [ -x "$(command -v yum)" ]; then yum install -y lsof;
        elif [ -x "$(command -v apk)" ]; then apk add lsof; fi
    fi
}

resolve_port() {
    local port=$1
    local pid=$(lsof -i :$port -sTCP:LISTEN -t | head -n 1)
    if [[ -n "$pid" ]]; then
        local proc_name=$(ps -p $pid -o comm=)
        echo -e "\n${RED}⛔️ ПОРТ $port ЗАНЯТ: $proc_name (PID: $pid)${NC}"
        
        if [[ "$proc_name" == "docker-proxy" ]]; then
             echo -e "${YELLOW}⚠️  Это Docker. Останавливаю контейнеры...${NC}"
             docker stop $(docker ps -q) 2>/dev/null
             sleep 2
        fi

        if lsof -i :$port -sTCP:LISTEN > /dev/null; then
            echo -e "${YELLOW}💀 Убиваю процесс $pid...${NC}"
            kill -15 $pid 2>/dev/null; sleep 1; kill -9 $pid 2>/dev/null
            if lsof -i :$port -sTCP:LISTEN > /dev/null; then
                echo -e "${RED}❌ Не могу освободить порт $port. Разберись вручную.${NC}"; exit 1
            fi
        fi
        echo -e "${GREEN}✅ Порт $port освобожден.${NC}"
    fi
}

# --- MAIN CHECKS ---
if [ "$EUID" -ne 0 ]; then echo -e "${RED}❌ Run as root!${NC}"; exit 1; fi
install_tools
resolve_port 80
resolve_port 443
resolve_port 8081

# --- 2. CONFIGURATION (WITH DEFAULTS) ---
echo -e "\n${BLUE}[Конфигурация]${NC}"

# Загрузка из кэша
LOADED_FROM_ENV=0
if [ -f .env ]; then
    echo -e "${CYAN}📂 Найден файл .env! Читаю настройки...${NC}"
    export $(grep -v '^#' .env | xargs)
    
    echo -e "   🔹 Домен: $API_DOMAIN"
    echo -e "   🔹 Email: $ADMIN_EMAIL"
    echo -e "   🔹 Token: ${BOT_TOKEN:0:5}..."
    
    read -p "♻️  Использовать эти данные? (Y/n): " use_cache
    if [[ "$use_cache" == "n" || "$use_cache" == "N" ]]; then
        LOADED_FROM_ENV=0
    else
        LOADED_FROM_ENV=1
        DOMAIN=$API_DOMAIN
        EMAIL=$ADMIN_EMAIL
        TG_API_ID=$TELEGRAM_API_ID
        TG_API_HASH=$TELEGRAM_API_HASH
    fi
fi

# Функция ввода с дефолтным значением
ask_var() {
    local prompt="$1"
    local var_name="$2"
    local default_val="$3"
    local current_val="${!var_name}"
    
    if [[ "$LOADED_FROM_ENV" -eq 1 && -n "$current_val" ]]; then
        return
    fi
    
    while true; do
        if [[ -n "$default_val" ]]; then
            read -p "$prompt [$default_val]: " input
        else
            read -p "$prompt: " input
        fi

        if [[ -z "$input" && -n "$default_val" ]]; then
            input="$default_val"
        fi

        if [[ -n "$input" ]]; then
            eval $var_name=\"$input\"
            break
        fi
        echo -e "${RED}❌ Это поле обязательно!${NC}"
    done
}

ask_var "🌍 Домен (напр. api.mysite.com)" DOMAIN
# Генерируем фейковый емаил для ленивых
DEFAULT_EMAIL="admin@$DOMAIN"
ask_var "📧 Email (для SSL)" EMAIL "$DEFAULT_EMAIL"

ask_var "🆔 Telegram API_ID" TG_API_ID
ask_var "🔑 Telegram API_HASH" TG_API_HASH
ask_var "🤖 Bot Token" BOT_TOKEN

# Сохраняем .env
cat > .env <<EOF
BOT_TOKEN=${BOT_TOKEN}
TELEGRAM_API_ID=${TG_API_ID}
TELEGRAM_API_HASH=${TG_API_HASH}
API_DOMAIN=${DOMAIN}
ADMIN_EMAIL=${EMAIL}
EOF

# --- 3. COOKIES ---
echo -e "\n${BLUE}[Cookies]${NC}"
if [[ -s cookies.txt ]]; then
    echo -e "${GREEN}✅ Файл cookies.txt найден и не пуст.${NC}"
    read -p "Перезаписать куки? (y/N): " rewrite_cookies
else
    rewrite_cookies="y"
fi

if [[ "$rewrite_cookies" == "y" || "$rewrite_cookies" == "Y" ]]; then
    echo -e "${YELLOW}🍪 Вставь Cookies (Netscape) + ENTER + Ctrl+D:${NC}"
    cat > cookies.txt
    if [ ! -s cookies.txt ]; then echo -e "${RED}❌ Куки пустые!${NC}"; exit 1; fi
fi

# --- 4. INSTALLATION ---
echo -e "\n${BLUE}[Установка]${NC}"
pip install -r requirements.txt > /dev/null 2>&1
echo -e "✅ Python libs installed."

# --- 5. DOCKER SETUP ---
echo -e "\n${BLUE}[Docker & Nginx]${NC}"
rm -rf nginx_conf telegram-bot-api-data certbot
mkdir -p nginx_conf certbot/conf certbot/www telegram-bot-api-data

cat > docker-compose.yml <<EOF
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
      - TELEGRAM_VERBOSITY=1
    volumes:
      - ./telegram-bot-api-data:/var/lib/telegram-bot-api
    ports:
      - "8081:8081"
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

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

cat > nginx_conf/nginx.conf <<EOF
server {
    listen 80;
    server_name ${DOMAIN};
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 301 https://\$host\$request_uri; }
}
EOF

echo -e "${MAGENTA}🚀 Запуск Nginx для SSL...${NC}"
docker-compose up -d nginx
echo "⏳ Жду Nginx (5 сек)..."
sleep 5

# --- SSL GENERATION ---
echo -e "${MAGENTA}🔐 Генерация SSL...${NC}"
# Если EMAIL пустой (вдруг что-то сломалось), ставим заглушку
if [[ -z "$EMAIL" ]]; then EMAIL="admin@${DOMAIN}"; fi

docker-compose run --rm --entrypoint certbot certbot certonly --webroot --webroot-path /var/www/certbot -d "${DOMAIN}" --email "${EMAIL}" --agree-tos --no-eff-email

if [ ! -d "./certbot/conf/live/${DOMAIN}" ]; then
    echo -e "${RED}❌ SSL ОШИБКА!${NC}"
    echo -e "Проверь домен и DNS."
    exit 1
fi

# --- FINAL CONFIG ---
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
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    client_max_body_size 2000M;
    proxy_read_timeout 600s;
    location / {
        proxy_pass http://telegram-bot-api:8081;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

echo "🔄 Перезагрузка..."
docker-compose restart nginx
docker-compose up -d telegram-bot-api

echo -e "\n${GREEN}🎉 ВСЁ ГОТОВО!${NC}"
echo -e "Запуск бота: ${YELLOW}python3 bot.py${NC}"