#!/bin/bash
# =============================================================================
# setup-wr3000h.sh — Автонастройка Cudy WR3000H (OpenWrt 25.12)
# =============================================================================
# Использование: ./setup-wr3000h.sh <NNN>
# Пример:        ./setup-wr3000h.sh 111
#
# Предусловия:
#   - Mac подключён кабелем к роутеру
#   - На роутере залит шаблон → роутер на IP 192.168.5.1
#   - Установлен sshpass: brew install sshpass
# =============================================================================

set -e

NNN="$1"
ROUTER="192.168.5.1"
PASS="56756789"
SSH="sshpass -p $PASS ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@$ROUTER"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅ $1${NC}"; }
info() { echo -e "${YELLOW}➡  $1${NC}"; }
fail() { echo -e "${RED}❌ $1${NC}"; exit 1; }

[ -z "$NNN" ] && fail "Укажи номер роутера: ./setup-wr3000h.sh 111"

# --- Вводим ключи вручную ---
echo ""
echo "========================================"
echo "  Настройка роутера z56-${NNN}"
echo "========================================"
echo ""
echo "  Вставь vless-ключ MAIN (HostFin, порт 4190):"
read -r VLESS_MAIN
echo "  Вставь vless-ключ YT (bSPB, порт 8853):"
read -r VLESS_YT
echo ""

[ -z "$VLESS_MAIN" ] && fail "Ключ MAIN не введён"
[ -z "$VLESS_YT"   ] && fail "Ключ YT не введён"

# --- Шаг 1: Доступность ---
info "Шаг 1/5: Проверяю доступность роутера..."
ping -c 2 -W 2 "$ROUTER" > /dev/null 2>&1 || fail "Роутер $ROUTER недоступен. Проверь кабель."
ok "Роутер доступен"

# --- Шаг 2: Hostname + Podkop install ---
info "Шаг 2/5: Переименовываю роутер и устанавливаю Podkop..."
$SSH "
uci set system.@system[0].hostname='z56-${NNN}'
uci commit system
echo 'z56-${NNN}' > /proc/sys/kernel/hostname
printf 'y\n' | sh <(wget -O - https://raw.githubusercontent.com/itdoginfo/podkop/refs/heads/main/install.sh) 2>&1
"
ok "Hostname z56-${NNN} и Podkop установлены"

# --- Шаг 3: Настройка Podkop ---
info "Шаг 3/5: Настраиваю Podkop..."
$SSH "
uci set podkop.settings.dns_server='1.1.1.1'
uci set podkop.settings.bootstrap_dns_server='1.1.1.1'
uci set podkop.settings.dns_type='udp'
uci set podkop.settings.update_interval='3h'

uci del podkop.main.community_lists 2>/dev/null || true
for list in telegram meta geoblock block porn news anime discord twitter hdrezka tiktok cloudflare google_ai google_play hodca roblox hetzner ovh digitalocean cloudfront; do
  uci add_list podkop.main.community_lists=\"\$list\"
done
uci set podkop.main.proxy_string='${VLESS_MAIN}'

uci set podkop.yt=section
uci set podkop.yt.enabled='1'
uci set podkop.yt.connection_type='proxy'
uci set podkop.yt.proxy_config_type='url'
uci add_list podkop.yt.community_lists='youtube'
uci set podkop.yt.proxy_string='${VLESS_YT}'

uci commit podkop
/etc/init.d/podkop restart
"
ok "Podkop настроен (main: 20 списков, yt: youtube)"

# --- Шаг 4: Фикс Tailscale init (два бага OpenWrt 25.12) ---
info "Шаг 4/5: Фикс Tailscale для OpenWrt 25.12..."
$SSH "
sed -i 's|--statedir=/var/lib/tailscale ||g' /etc/init.d/tailscale
sed -i 's|TS_DEBUG_FIREWALL_MODE=\"none\"|TS_DEBUG_FIREWALL_MODE=\"\$fw_mode\"|g' /etc/init.d/tailscale
uci set tailscale.settings.fw_mode='nftables'
uci set tailscale.settings.state_file='/etc/tailscale/tailscaled.state'
uci commit tailscale
mkdir -p /etc/tailscale
"
ok "Tailscale пофикшен (nftables + persistent state)"

# --- Шаг 5: Авторизация Tailscale ---
info "Шаг 5/5: Запускаю Tailscale..."
$SSH "/etc/init.d/tailscale restart" 2>/dev/null || true
sleep 3

AUTH_URL=$($SSH 'tailscale up --accept-dns=false --accept-routes --reset 2>&1' 2>/dev/null \
  | grep 'https://login.tailscale.com' | head -1 | tr -d '[:space:]')

echo ""
echo "========================================"
echo "  z56-${NNN} — ОТКРОЙ В БРАУЗЕРЕ:"
echo "========================================"
echo ""
if [ -n "$AUTH_URL" ]; then
  echo "  $AUTH_URL"
  open "$AUTH_URL" 2>/dev/null || true
else
  echo "  Запусти вручную: tailscale up --accept-dns=false --accept-routes --reset"
fi
echo ""
echo "  После авторизации:"
echo "  ✅ Podkop: 20 сервисов + YouTube"
echo "  ✅ Tailscale: держится после перезагрузки"
echo "  ✅ Hostname: z56-${NNN}"
echo ""
