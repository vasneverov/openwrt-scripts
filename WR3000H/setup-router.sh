#!/bin/bash
# =============================================================================
# setup-router.sh — Автонастройка Cudy WR3000H (OpenWrt 25.12)
# =============================================================================
# Использование: ./setup-router.sh <NNN>
# Пример:        ./setup-router.sh 111
#
# Что делает:
#   1. Переименовывает роутер в z56-NNN
#   2. Устанавливает и настраивает Podkop (20 списков + секция YT)
#   3. Фиксит Tailscale init-скрипт (два бага OpenWrt 25.12)
#   4. Настраивает Tailscale UCI (nftables + persistent state)
#   5. Запускает tailscale up и выдаёт ссылку для авторизации в браузере
#
# Предусловия:
#   - Mac подключён кабелем к роутеру
#   - На роутере залит шаблон (backup-wr3000h-template.tar.gz) → IP 192.168.5.1
#   - Установлен sshpass: brew install sshpass
# =============================================================================

set -e

NNN="$1"
ROUTER="192.168.5.1"
PASS="56756789"
SSH="sshpass -p $PASS ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@$ROUTER"

# --- Цвета ---
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅ $1${NC}"; }
info() { echo -e "${YELLOW}➡  $1${NC}"; }
fail() { echo -e "${RED}❌ $1${NC}"; exit 1; }

# --- Проверка аргумента ---
[ -z "$NNN" ] && fail "Укажи номер роутера: ./setup-router.sh 111"

# --- Таблица vless-ключей hostFin (порт 4190, сервер Финляндия) ---
declare -A KEY_FIN
KEY_FIN[108]="vless://a7239128-3c89-40c3-b849-4fafea2de8c7@5.35.84.151:4190?type=grpc&security=reality&mode=gun&serviceName=&pbk=5alNn1i1ywQgTNJ96lFFU0EWKgwFJPCD9oR0JVBDcCM&sid=d9&sni=www.apple.com&fp=chrome&spx=%2F#Z56-108_hostFin"
KEY_FIN[109]="vless://32cb64aa-96d9-4ad7-9ff2-d0c1b560b2ee@5.35.84.151:4190?type=grpc&security=reality&mode=gun&serviceName=&pbk=5alNn1i1ywQgTNJ96lFFU0EWKgwFJPCD9oR0JVBDcCM&sid=d9&sni=www.apple.com&fp=chrome&spx=%2F#Z56-109_hostFin"
KEY_FIN[110]="vless://b43b2ed0-7fc5-45bf-9743-dd71825e7584@5.35.84.151:4190?type=grpc&security=reality&mode=gun&serviceName=&pbk=5alNn1i1ywQgTNJ96lFFU0EWKgwFJPCD9oR0JVBDcCM&sid=d9&sni=www.apple.com&fp=chrome&spx=%2F#Z56-110_hostFin"
KEY_FIN[111]="vless://65338526-00cf-4cd8-8f0c-d1b097bf2600@5.35.84.151:4190?type=grpc&security=reality&mode=gun&serviceName=&pbk=5alNn1i1ywQgTNJ96lFFU0EWKgwFJPCD9oR0JVBDcCM&sid=d9&sni=www.apple.com&fp=chrome&spx=%2F#Z56-111_hostFin"
KEY_FIN[112]="vless://97a0e57d-edf4-483b-b2c1-499507f860b2@5.35.84.151:4190?type=grpc&security=reality&mode=gun&serviceName=&pbk=5alNn1i1ywQgTNJ96lFFU0EWKgwFJPCD9oR0JVBDcCM&sid=d9&sni=www.apple.com&fp=chrome&spx=%2F#Z56-112_hostFin"
KEY_FIN[113]="vless://801fb255-aa20-42f0-913a-06128bf38ad6@5.35.84.151:4190?type=grpc&security=reality&mode=gun&serviceName=&pbk=5alNn1i1ywQgTNJ96lFFU0EWKgwFJPCD9oR0JVBDcCM&sid=d9&sni=www.apple.com&fp=chrome&spx=%2F#Z56-113_hostFin"
KEY_FIN[114]="vless://75e3bb6d-2be0-4d2f-8b2c-610c91d52f37@5.35.84.151:4190?type=grpc&security=reality&mode=gun&serviceName=&pbk=5alNn1i1ywQgTNJ96lFFU0EWKgwFJPCD9oR0JVBDcCM&sid=d9&sni=www.apple.com&fp=chrome&spx=%2F#Z56-114_hostFin"
KEY_FIN[115]="vless://cdf88074-e86b-4d60-b0e2-bb92148f2130@5.35.84.151:4190?type=grpc&security=reality&mode=gun&serviceName=&pbk=5alNn1i1ywQgTNJ96lFFU0EWKgwFJPCD9oR0JVBDcCM&sid=d9&sni=www.apple.com&fp=chrome&spx=%2F#Z56-115_hostFin"
KEY_FIN[116]="vless://c6236c55-4a89-463d-91c8-83add8fe1481@5.35.84.151:4190?type=grpc&security=reality&mode=gun&serviceName=&pbk=5alNn1i1ywQgTNJ96lFFU0EWKgwFJPCD9oR0JVBDcCM&sid=d9&sni=www.apple.com&fp=chrome&spx=%2F#Z56-116_hostFin"
KEY_FIN[117]="vless://ae87946b-7951-4c3f-8e26-8f00c43109a3@5.35.84.151:4190?type=grpc&security=reality&mode=gun&serviceName=&pbk=5alNn1i1ywQgTNJ96lFFU0EWKgwFJPCD9oR0JVBDcCM&sid=d9&sni=www.apple.com&fp=chrome&spx=%2F#Z56-117_hostFin"

# --- Таблица vless-ключей bSPB (порт 8853, YouTube) ---
declare -A KEY_YT
KEY_YT[108]="vless://caf13374-7725-4421-a4e1-c2ca4ed9008f@5.35.84.151:8853?type=grpc&security=reality&mode=gun&serviceName=&pbk=me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM&sid=ddcb53b3&sni=www.apple.com&fp=chrome&spx=%2F#Z56-108_bSPB"
KEY_YT[109]="vless://d2e36ee2-8928-417a-a6be-d942188636e1@5.35.84.151:8853?type=grpc&security=reality&mode=gun&serviceName=&pbk=me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM&sid=ddcb53b3&sni=www.apple.com&fp=chrome&spx=%2F#Z56-109_bSPB"
KEY_YT[110]="vless://1545a0ca-7bcd-4b63-a608-5558ac33b1ff@5.35.84.151:8853?type=grpc&security=reality&mode=gun&serviceName=&pbk=me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM&sid=ddcb53b3&sni=www.apple.com&fp=chrome&spx=%2F#Z56-110_bSPB"
KEY_YT[111]="vless://4d9c6419-94d5-4cd3-af11-ee53b28c4610@5.35.84.151:8853?type=grpc&security=reality&mode=gun&serviceName=&pbk=me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM&sid=ddcb53b3&sni=www.apple.com&fp=chrome&spx=%2F#Z56-111_bSPB"
KEY_YT[112]="vless://34220d6f-209e-4c3c-8f07-58ca8bf2c3ef@5.35.84.151:8853?type=grpc&security=reality&mode=gun&serviceName=&pbk=me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM&sid=ddcb53b3&sni=www.apple.com&fp=chrome&spx=%2F#Z56-112_bSPB"
KEY_YT[113]="vless://d3dfa773-54f1-4bad-b36f-fe16ef98a553@5.35.84.151:8853?type=grpc&security=reality&mode=gun&serviceName=&pbk=me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM&sid=ddcb53b3&sni=www.apple.com&fp=chrome&spx=%2F#Z56-113_bSPB"
KEY_YT[114]="vless://f0ed919f-e0d6-4d0d-944c-d37eabc75cdf@5.35.84.151:8853?type=grpc&security=reality&mode=gun&serviceName=&pbk=me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM&sid=ddcb53b3&sni=www.apple.com&fp=chrome&spx=%2F#Z56-114_bSPB"
KEY_YT[115]="vless://7097dc13-2dfd-407a-8f4c-791cbbcfaa53@5.35.84.151:8853?type=grpc&security=reality&mode=gun&serviceName=&pbk=me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM&sid=ddcb53b3&sni=www.apple.com&fp=chrome&spx=%2F#Z56-115_bSPB"
KEY_YT[116]="vless://818ec880-de66-4c65-b55b-9657db799d8f@5.35.84.151:8853?type=grpc&security=reality&mode=gun&serviceName=&pbk=me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM&sid=ddcb53b3&sni=www.apple.com&fp=chrome&spx=%2F#Z56-116_bSPB"
KEY_YT[117]="vless://2f14b0ec-5c54-4af6-be26-5e46db353bbc@5.35.84.151:8853?type=grpc&security=reality&mode=gun&serviceName=&pbk=me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM&sid=ddcb53b3&sni=www.apple.com&fp=chrome&spx=%2F#Z56-117_bSPB"

# --- Проверяем, что ключ есть для этого номера ---
VLESS_MAIN="${KEY_FIN[$NNN]}"
VLESS_YT="${KEY_YT[$NNN]}"
[ -z "$VLESS_MAIN" ] && fail "Нет ключа hostFin для роутера $NNN (диапазон 108-117)"
[ -z "$VLESS_YT"   ] && fail "Нет ключа bSPB для роутера $NNN (диапазон 108-117)"

echo ""
echo "========================================"
echo "  Настройка роутера z56-${NNN}"
echo "  Роутер: ${ROUTER} | Пароль: ${PASS}"
echo "========================================"
echo ""

# --- Шаг 1: Проверить доступность ---
info "Шаг 1/5: Проверяю доступность роутера..."
ping -c 2 -W 2 "$ROUTER" > /dev/null 2>&1 || fail "Роутер $ROUTER недоступен. Проверь кабель и IP."
ok "Роутер доступен"

# --- Шаг 2: Hostname + Podkop install ---
info "Шаг 2/5: Переименовываю роутер и устанавливаю Podkop..."
$SSH "
uci set system.@system[0].hostname='z56-${NNN}'
uci commit system
echo 'z56-${NNN}' > /proc/sys/kernel/hostname
echo '>>> Hostname: z56-${NNN}'
printf 'y\n' | sh <(wget -O - https://raw.githubusercontent.com/itdoginfo/podkop/refs/heads/main/install.sh) 2>&1
echo '>>> Podkop установлен'
"
ok "Hostname и Podkop готовы"

# --- Шаг 3: Настроить Podkop ---
info "Шаг 3/5: Настраиваю Podkop (main + yt)..."
$SSH "
# Settings
uci set podkop.settings.dns_server='1.1.1.1'
uci set podkop.settings.bootstrap_dns_server='1.1.1.1'
uci set podkop.settings.dns_type='udp'
uci set podkop.settings.update_interval='3h'

# Main — очищаем дефолт, добавляем 20 списков
uci del podkop.main.community_lists 2>/dev/null || true
uci add_list podkop.main.community_lists='telegram'
uci add_list podkop.main.community_lists='meta'
uci add_list podkop.main.community_lists='geoblock'
uci add_list podkop.main.community_lists='block'
uci add_list podkop.main.community_lists='porn'
uci add_list podkop.main.community_lists='news'
uci add_list podkop.main.community_lists='anime'
uci add_list podkop.main.community_lists='discord'
uci add_list podkop.main.community_lists='twitter'
uci add_list podkop.main.community_lists='hdrezka'
uci add_list podkop.main.community_lists='tiktok'
uci add_list podkop.main.community_lists='cloudflare'
uci add_list podkop.main.community_lists='google_ai'
uci add_list podkop.main.community_lists='google_play'
uci add_list podkop.main.community_lists='hodca'
uci add_list podkop.main.community_lists='roblox'
uci add_list podkop.main.community_lists='hetzner'
uci add_list podkop.main.community_lists='ovh'
uci add_list podkop.main.community_lists='digitalocean'
uci add_list podkop.main.community_lists='cloudfront'
uci set podkop.main.proxy_string='${VLESS_MAIN}'

# YT секция — тип SECTION (не podkop!)
uci set podkop.yt=section
uci set podkop.yt.enabled='1'
uci set podkop.yt.connection_type='proxy'
uci set podkop.yt.proxy_config_type='url'
uci add_list podkop.yt.community_lists='youtube'
uci set podkop.yt.proxy_string='${VLESS_YT}'

uci commit podkop
/etc/init.d/podkop restart
echo '>>> Podkop настроен'
"
ok "Podkop настроен"

# --- Шаг 4: Фикс Tailscale init-скрипта (два бага OpenWrt 25.12) ---
info "Шаг 4/5: Фикс Tailscale для OpenWrt 25.12..."
$SSH "
# БАГ 1: --statedir=/var/lib/tailscale захардкожен (RAM, стирается при ребуте)
# Убираем его — останется только --state из UCI (/etc/tailscale/tailscaled.state)
sed -i 's|--statedir=/var/lib/tailscale ||g' /etc/init.d/tailscale

# БАГ 2: TS_DEBUG_FIREWALL_MODE=none захардкожен
# OpenWrt 25.12 не имеет iptables, только nftables → нужно читать из UCI (fw_mode=nftables)
sed -i 's|TS_DEBUG_FIREWALL_MODE=\"none\"|TS_DEBUG_FIREWALL_MODE=\"\$fw_mode\"|g' /etc/init.d/tailscale

# UCI: убеждаемся что fw_mode=nftables и state_file правильный
uci set tailscale.settings.fw_mode='nftables'
uci set tailscale.settings.state_file='/etc/tailscale/tailscaled.state'
uci commit tailscale

# Создаём папку для persistent state
mkdir -p /etc/tailscale

echo '>>> Tailscale init пофикшен'
grep -n 'FIREWALL\|statedir' /etc/init.d/tailscale || true
"
ok "Tailscale init-скрипт пофикшен"

# --- Шаг 5: Запустить Tailscale и получить ссылку авторизации ---
info "Шаг 5/5: Запускаю Tailscale, получаю ссылку авторизации..."
/etc/init.d/tailscale restart 2>/dev/null || true
sleep 3

AUTH_URL=$($SSH 'tailscale up --accept-dns=false --accept-routes --reset 2>&1' 2>/dev/null | grep 'https://login.tailscale.com' | head -1 | tr -d '[:space:]')

echo ""
echo "========================================"
echo "  z56-${NNN} — ГОТОВ К АВТОРИЗАЦИИ"
echo "========================================"
echo ""
if [ -n "$AUTH_URL" ]; then
  echo "  Открой в браузере:"
  echo ""
  echo "  $AUTH_URL"
  echo ""
  echo "  После авторизации — зелёная точка в Tailscale"
  echo "  Имя устройства: z56-${NNN}"
  # Открываем браузер автоматически (macOS)
  open "$AUTH_URL" 2>/dev/null || true
else
  echo "  Не удалось получить ссылку автоматически."
  echo "  Запусти вручную на роутере: tailscale up --accept-dns=false --accept-routes --reset"
fi
echo ""
echo "  После авторизации роутер будет:"
echo "  ✅ Подкоп: обход РФ-блокировок (20 сервисов) + YouTube отдельно"
echo "  ✅ Tailscale: выживает после перезагрузки"
echo "  ✅ Hostname: z56-${NNN}"
echo ""
