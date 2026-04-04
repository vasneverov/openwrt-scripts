#!/bin/bash
# =============================================================================
# setup-wr3000s.sh — Cudy WR3000S (OpenWrt 25.12)
# =============================================================================
# Использование: ./setup-wr3000s.sh <NNN>
# Пример:        ./setup-wr3000s.sh 112
#
# Предусловия:
#   - Роутер на OpenWrt (stock Cudy или свежая прошивка), IP 192.168.1.1
#   - Firmware 25.12 в ~/Downloads/WR3000S V1/
#   - Mac подключён кабелем (DHCP)
#   - sshpass: brew install sshpass
# =============================================================================

set -e
NNN="$1"
PASS="56756789"
FIRMWARE="$HOME/Downloads/WR3000S V1/openwrt-25.12.0-mediatek-filogic-cudy_wr3000s-v1-squashfs-sysupgrade.bin"
TEMPLATE="$HOME/Downloads/WR3000S V1/backup-wr3000s-template.tar.gz"
KEYS="$(dirname "$0")/../keys.conf"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅ $*${NC}"; }
info() { echo -e "${YELLOW}➡  $*${NC}"; }
step() { echo -e "${CYAN}════ $* ════${NC}"; }
fail() { echo -e "${RED}❌ $*${NC}"; exit 1; }

[ -z "$NNN" ] && fail "Укажи номер: ./setup-wr3000s.sh 112"
[ ! -f "$KEYS" ] && fail "Нет файла ключей: $KEYS"
[ ! -f "$FIRMWARE" ] && fail "Нет прошивки: $FIRMWARE"
[ ! -f "$TEMPLATE" ] && fail "Нет шаблона: $TEMPLATE"

VLESS_MAIN=$(grep "^${NNN}_main=" "$KEYS" | cut -d'=' -f2-)
VLESS_YT=$(grep "^${NNN}_yt=" "$KEYS" | cut -d'=' -f2-)
[ -z "$VLESS_MAIN" ] && fail "Нет main-ключа для роутера $NNN в keys.conf"
[ -z "$VLESS_YT"   ] && fail "Нет yt-ключа для роутера $NNN в keys.conf"

SSH1="ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@192.168.1.1"
SSHR="sshpass -p $PASS ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@192.168.5.1"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   Настройка z56-${NNN} (WR3000S)       ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── ШАГ 1: Прошивка OpenWrt 25.12 ────────────────────────────────────────────
step "1/5 Прошивка OpenWrt 25.12 через SSH"
ping -c 2 -W 2 192.168.1.1 > /dev/null 2>&1 || fail "192.168.1.1 недоступен"
ssh-keygen -R 192.168.1.1 2>/dev/null || true
VER=$($SSH1 'cat /etc/openwrt_release | grep RELEASE' 2>/dev/null || echo "unknown")
ok "Роутер: $VER"

info "Загружаю прошивку на роутер..."
scp -O -o StrictHostKeyChecking=no "$FIRMWARE" root@192.168.1.1:/tmp/sysupgrade.bin
info "Запускаю sysupgrade -n (роутер уйдёт в перезагрузку)..."
$SSH1 'sysupgrade -n /tmp/sysupgrade.bin' 2>/dev/null || true

info "Жду пока поднимется OpenWrt 25.12 на 192.168.1.1..."
sleep 20
for i in $(seq 1 30); do
  sleep 5
  result=$($SSH1 'cat /etc/openwrt_release | grep RELEASE' 2>/dev/null)
  if echo "$result" | grep -q "25.12"; then
    ok "OpenWrt 25.12 загрузился"
    break
  fi
  echo "  [$i/30] ещё не готов..."
done

# ── ШАГ 2: Шаблон → 192.168.5.1 ──────────────────────────────────────────────
step "2/5 Заливаю шаблон S, жду перезагрузки на 192.168.5.1"
scp -O -o StrictHostKeyChecking=no "$TEMPLATE" root@192.168.1.1:/tmp/backup.tar.gz
$SSH1 "cd / && tar xzf /tmp/backup.tar.gz && reboot" 2>/dev/null || true

info "Жду пока роутер поднимется на 192.168.5.1..."
sleep 15
for i in $(seq 1 30); do
  sleep 5
  result=$(sshpass -p "$PASS" ssh -o ConnectTimeout=3 -o StrictHostKeyChecking=no root@192.168.5.1 'echo ok' 2>/dev/null)
  [ "$result" = "ok" ] && break
  echo "  [$i/30] ещё не готов..."
done
ssh-keygen -R 192.168.5.1 2>/dev/null || true
$SSHR 'echo ok' > /dev/null 2>&1 || fail "192.168.5.1 не отвечает"
ok "Роутер на 192.168.5.1"

# ── ШАГ 3: Hostname + Podkop ──────────────────────────────────────────────────
step "3/5 Hostname z56-${NNN} + Podkop"
$SSHR "
uci set system.@system[0].hostname='z56-${NNN}'
uci commit system
echo 'z56-${NNN}' > /proc/sys/kernel/hostname
printf 'y\n' | sh <(wget -O - https://raw.githubusercontent.com/itdoginfo/podkop/refs/heads/main/install.sh) 2>&1

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
ok "Hostname и Podkop готовы"

# ── ШАГ 4: Tailscale ─────────────────────────────────────────────────────────
step "4/5 Tailscale (установка + фикс OpenWrt 25.12)"
$SSHR "
apk update -q 2>/dev/null; apk add tailscale 2>&1 | tail -3

# Баг 1: убираем --statedir=/var/lib (RAM → стирается при ребуте)
sed -i 's|--statedir=/var/lib/tailscale ||g' /etc/init.d/tailscale
# Баг 2: TS_DEBUG_FIREWALL_MODE=none → nftables (iptables нет в 25.12)
sed -i 's|TS_DEBUG_FIREWALL_MODE=\"none\"|TS_DEBUG_FIREWALL_MODE=\"\$fw_mode\"|g' /etc/init.d/tailscale

uci set tailscale.settings.fw_mode='nftables'
uci set tailscale.settings.state_file='/etc/tailscale/tailscaled.state'
uci commit tailscale
mkdir -p /etc/tailscale
/etc/init.d/tailscale enable
/etc/init.d/tailscale restart
"
ok "Tailscale установлен и пофикшен"

# ── ШАГ 5: Авторизация Tailscale ─────────────────────────────────────────────
step "5/5 Авторизация Tailscale"
info "Запускаю tailscale up..."

$SSHR 'setsid tailscale up --accept-dns=false --accept-routes --reset > /tmp/tsup.log 2>&1 &'
sleep 6

AUTH_URL=$($SSHR 'cat /tmp/tsup.log 2>/dev/null' | grep 'https://login.tailscale.com' | head -1 | tr -d '[:space:]')

if [ -z "$AUTH_URL" ]; then
  fail "Не удалось получить ссылку авторизации"
fi

echo ""
echo "  Открываю браузер — АВТОРИЗУЙСЯ:"
echo "  $AUTH_URL"
open "$AUTH_URL" 2>/dev/null || true
echo ""
info "Жду авторизацию (слежу за state-файлом)..."

# Ждём пока state-файл вырастет > 500 байт (признак успешной авторизации)
for i in $(seq 1 60); do
  sleep 3
  size=$($SSHR 'wc -c < /etc/tailscale/tailscaled.state 2>/dev/null' 2>/dev/null | tr -d ' ')
  if [ -n "$size" ] && [ "$size" -gt 500 ]; then
    TS_IP=$($SSHR 'tailscale ip 2>/dev/null' 2>/dev/null | head -1)
    echo ""
    ok "Авторизован! Tailscale IP: $TS_IP"
    break
  fi
  echo "  [$i/60] ожидание авторизации... (state: ${size:-?} байт)"
done

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   z56-${NNN} ГОТОВ ✅                  ║"
echo "║   Podkop: 20 сервисов + YouTube      ║"
echo "║   Tailscale: держится после ребута   ║"
echo "╚══════════════════════════════════════╝"
echo ""
