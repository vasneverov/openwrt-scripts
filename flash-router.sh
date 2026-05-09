#!/bin/bash
# flash-router.sh — Universal router flashing with live progress
# Usage: bash ~/CLAUDECODE/flash-router.sh <ROUTER-NAME>
# e.g.:  bash ~/CLAUDECODE/flash-router.sh TR56-13
#        bash ~/CLAUDECODE/flash-router.sh z56-119
#        bash ~/CLAUDECODE/flash-router.sh M56-12

ROUTER="${1:-}"
[ -z "$ROUTER" ] && { echo "Usage: $0 <router-name>"; exit 1; }

SSHP="/opt/homebrew/bin/sshpass"
PASS="56756789"
SO="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -o PreferredAuthentications=password -o PubkeyAuthentication=no"
START=$(date +%s)

# ── ANSI colors ───────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# ── Series detection ──────────────────────────────────────────────────────────
RL=$(echo "$ROUTER" | tr '[:upper:]' '[:lower:]')
RU=$(echo "$ROUTER" | tr '[:lower:]' '[:upper:]')

case "$RL" in
  z56-*|h-01)
    SERIES="WR3000H"
    FW=~/Downloads/WR3000H/openwrt-25.12.0-mediatek-filogic-cudy_wr3000h-v1-squashfs-sysupgrade.bin
    TPL=~/Downloads/WR3000H/backup-wr3000h-template.tar.gz
    KMAIN=~/CLAUDECODE/ключи/vless_fin_rout_4190_108.md
    KYT=~/CLAUDECODE/ключи/vless_bSPB_direct_8853_108.html
    YT_UCI="yt"
    SCP_METHOD="scp"
    ;;
  tr56-*)
    SERIES="TR3000"
    FW=~/Downloads/TR3000\ V1\ 2/openwrt-25.12.0-mediatek-filogic-cudy_tr3000-v1-squashfs-sysupgrade.bin
    TPL=~/Downloads/TR3000\ V1\ 2/backup-tr3000-template.tar.gz
    NUM=$(echo "$RL" | sed 's/tr56-0*//' | sed 's/tr56-//')
    if [ "${NUM:-99}" -ge 7 ] 2>/dev/null; then
      KMAIN=~/CLAUDECODE/ключи/vless_italy_rout_2090_TR56.html
    else
      KMAIN=~/CLAUDECODE/ключи/vless_fin_rout_4190_TR56.md
    fi
    KYT=~/CLAUDECODE/ключи/vless_bSPB_direct_8853_TR56.md
    YT_UCI="YT"
    SCP_METHOD="scp"
    ;;
  m56-*)
    SERIES="M3000"
    FW=~/Downloads/M3000\ 1.0_2.0/openwrt-25.12.0-mediatek-filogic-cudy_m3000-v1-squashfs-sysupgrade.bin
    TPL=~/Downloads/M3000\ 1.0_2.0/backup-m3000-template.tar.gz
    KMAIN=~/CLAUDECODE/ключи/vless_cz2_rout_8448.md
    KYT=~/CLAUDECODE/ключи/vless_bSPB_direct_8853_M56.html
    YT_UCI="YT"
    SCP_METHOD="stdin"
    ;;
  *)
    echo -e "${RED}❌ Неизвестная серия: $ROUTER (ожидается z56-NNN, tr56-NN, m56-NN)${NC}"
    exit 1
    ;;
esac

# ── Extract VLESS keys ────────────────────────────────────────────────────────
KMAIN_EXP="${KMAIN/#\~/$HOME}"
KYT_EXP="${KYT/#\~/$HOME}"

VLESS_MAIN=$(grep "vless://" "$KMAIN_EXP" | grep -i "$RU" | head -1 \
  | sed 's/<[^>]*>//g' | tr -d '`"' | xargs)
VLESS_YT=$(grep "vless://" "$KYT_EXP" | grep -i "$RU" | head -1 \
  | sed 's/<[^>]*>//g' | tr -d '`"' | xargs)

[ -z "$VLESS_MAIN" ] && { echo -e "${RED}❌ main ключ не найден для $RU в $KMAIN_EXP${NC}"; exit 1; }
[ -z "$VLESS_YT"   ] && { echo -e "${RED}❌ yt ключ не найден для $RU в $KYT_EXP${NC}";   exit 1; }

# ── UI helpers ────────────────────────────────────────────────────────────────
elapsed() {
  local d=$(( $(date +%s) - START ))
  printf "+%d:%02d" $((d/60)) $((d%60))
}

step_start() { echo -e "${YELLOW}⏳ $(elapsed)  $*${NC}"; }
step_ok()    { echo -e "${GREEN}✅ $(elapsed)  $*${NC}"; }
step_err()   { echo -e "${RED}❌ $(elapsed)  $*${NC}"; }
info()       { echo -e "${CYAN}   $*${NC}"; }

die() {
  step_err "$*"
  echo -e "${RED}${BOLD}   СТОП — требуется вмешательство${NC}"
  exit 1
}

# ── SSH helpers ───────────────────────────────────────────────────────────────
r1() { $SSHP -p ''     ssh $SO root@192.168.1.1 "$@" 2>/dev/null; }
r5() { $SSHP -p "$PASS" ssh $SO root@192.168.5.1 "$@" 2>/dev/null; }

copy_to_1() {
  local src="$1" dst="$2"
  if [ "$SCP_METHOD" = "stdin" ]; then
    $SSHP -p '' ssh $SO root@192.168.1.1 "cat > /tmp/$dst" < "$src" 2>/dev/null
  else
    $SSHP -p '' scp -O $SO "$src" root@192.168.1.1:/tmp/"$dst" 2>/dev/null
  fi
}

wait_1() {
  sleep 30
  while true; do
    ssh-keygen -R 192.168.1.1 2>/dev/null
    $SSHP -p '' ssh $SO -o ConnectTimeout=3 root@192.168.1.1 \
      "grep -q '25.12' /etc/openwrt_release" 2>/dev/null && return 0
    sleep 2
  done
}

wait_5() {
  sleep 30
  while true; do
    ssh-keygen -R 192.168.5.1 2>/dev/null
    $SSHP -p "$PASS" ssh $SO -o ConnectTimeout=3 root@192.168.5.1 \
      "echo UP" 2>/dev/null | grep -q UP && return 0
    sleep 2
  done
}

# ════════════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║  🔧 ПРОШИВКА: ${RU}  │  ${SERIES}  │  $(date '+%H:%M')  ║${NC}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════╝${NC}"
echo ""

# ── 0 Проверка ключей ─────────────────────────────────────────────────────────
step_start "Ключи          проверяем main + YT через check_vless.py..."
CHECK_MAIN=$(echo "$VLESS_MAIN" | python3 ~/CLAUDECODE/check_vless.py - 2>/dev/null)
CHECK_YT=$(echo "$VLESS_YT"     | python3 ~/CLAUDECODE/check_vless.py - 2>/dev/null)

echo "$CHECK_MAIN" | grep -q "READY" || die "main ключ не READY:\n$CHECK_MAIN"
echo "$CHECK_YT"   | grep -q "READY" || die "YT ключ не READY:\n$CHECK_YT"
step_ok "Ключи          оба READY ✓"

# ── 1 Проверка модели ─────────────────────────────────────────────────────────
step_start "Модель         проверяем на 192.168.1.1..."
ssh-keygen -R 192.168.1.1 2>/dev/null
MODEL=$(r1 "cat /tmp/sysinfo/model 2>/dev/null || cat /proc/device-tree/model 2>/dev/null")
[ -z "$MODEL" ] && die "нет ответа на 192.168.1.1 — роутер не подключён?"
step_ok "Модель         $MODEL"

# ── 2 OpenWrt flash ───────────────────────────────────────────────────────────
step_start "OpenWrt        заливаем прошивку 25.12.0..."
FW_EXP="${FW/#\~/$HOME}"
copy_to_1 "$FW_EXP" sysupgrade.bin || die "не удалось скопировать прошивку"
r1 "sysupgrade -n /tmp/sysupgrade.bin" || true
step_start "OpenWrt        ребут → ждём на 192.168.1.1..."
wait_1
step_ok "OpenWrt        25.12.0 поднялся"

# ── 3 Шаблон + hostname ───────────────────────────────────────────────────────
step_start "Шаблон         заливаем + hostname=$RU..."
ssh-keygen -R 192.168.1.1 2>/dev/null
TPL_EXP="${TPL/#\~/$HOME}"
copy_to_1 "$TPL_EXP" backup.tar.gz || die "не удалось скопировать шаблон"
r1 "
cd / && tar xzf /tmp/backup.tar.gz
uci set system.@system[0].hostname='$RU'
uci commit system
echo '$RU' > /proc/sys/kernel/hostname
uci set wireless.radio0.country='PA'
uci set wireless.radio1.country='PA'
uci commit wireless
reboot" || true
step_start "Шаблон         ребут → ждём на 192.168.5.1..."
wait_5
step_ok "Шаблон         192.168.5.1 UP  hostname=$RU"

# ── 4 Podkop install ──────────────────────────────────────────────────────────
step_start "Podkop         устанавливаем..."
r5 "printf 'y\n' | sh <(wget -O - https://raw.githubusercontent.com/itdoginfo/podkop/refs/heads/main/install.sh)" 2>/dev/null
PVER=$(r5 "/usr/bin/podkop show_version 2>/dev/null" | tr -d '[:space:]')
[ -z "$PVER" ] && die "Podkop не установился"
step_ok "Podkop         v${PVER} установлен"

# ── 5 Podkop config ───────────────────────────────────────────────────────────
step_start "Podkop         настраиваем main + $YT_UCI + timezone..."
r5 "
uci set system.@system[0].timezone='MSK-3'
uci set system.@system[0].zonename='Europe/Moscow'
uci commit system
/etc/init.d/sysntpd restart
uci set podkop.settings.dns_server='1.1.1.1'
uci set podkop.settings.bootstrap_dns_server='1.1.1.1'
uci set podkop.settings.dns_type='udp'
uci set podkop.settings.update_interval='3h'
uci set podkop.settings.exclude_ntp='1'
uci set podkop.settings.disable_quic='1'
uci del podkop.main.community_lists 2>/dev/null || true
for l in telegram meta geoblock block porn news anime discord twitter hdrezka tiktok cloudflare google_ai google_play hodca roblox hetzner ovh digitalocean cloudfront; do
  uci add_list podkop.main.community_lists=\"\$l\"
done
uci set podkop.main.proxy_string='${VLESS_MAIN}'
uci set podkop.main.proxy_config_type='url'
uci set podkop.main.mixed_proxy_enabled='0'
uci set podkop.${YT_UCI}=section
uci set podkop.${YT_UCI}.enabled='1'
uci set podkop.${YT_UCI}.connection_type='proxy'
uci set podkop.${YT_UCI}.proxy_config_type='url'
uci del podkop.${YT_UCI}.community_lists 2>/dev/null || true
uci add_list podkop.${YT_UCI}.community_lists='youtube'
uci set podkop.${YT_UCI}.proxy_string='${VLESS_YT}'
uci set podkop.${YT_UCI}.mixed_proxy_enabled='0'
uci commit podkop
/etc/init.d/podkop restart"

# Самопроверка podkop
EX=$(r5 "uci get podkop.settings.exclude_ntp")
MM=$(r5 "uci get podkop.main.mixed_proxy_enabled")
CT=$(r5 "uci get podkop.main.proxy_config_type")
[ "$EX" = "1" ] && [ "$MM" = "0" ] && [ "$CT" = "url" ] \
  && step_ok "Podkop         exclude_ntp=1 mixed=0 type=url ✓" \
  || die "Podkop конфиг проверка провалилась: ntp=$EX mixed=$MM type=$CT"

sleep 5
SB=$(r5 "ps | grep sing-box | grep -v grep")
[ -n "$SB" ] && step_ok "sing-box       запущен ✓" || step_err "sing-box       не запущен (watchdog поднимет)"

# ── 5.1 Podkop watchdog ───────────────────────────────────────────────────────
step_start "Podkop WD      добавляем crontab watchdog..."
r5 "(crontab -l 2>/dev/null | grep -v 'podkop restart'; echo '*/10 * * * * netstat -tlnp | grep -q \":1602\" || /etc/init.d/podkop restart') | crontab -"
step_ok "Podkop WD      каждые 10 мин ✓"

# ── 6 Tailscale install + фикс ────────────────────────────────────────────────
step_start "Tailscale      устанавливаем 1.96.5 + фикс fw_mode..."
r5 "wget -q -O /tmp/tailscale.apk 'https://gunanovo.github.io/openwrt-tailscale/aarch64_cortex-a53/tailscale-1.96.5-r1.apk' \
  && apk add --allow-untrusted /tmp/tailscale.apk && rm -f /tmp/tailscale.apk
sed -i 's|--statedir=/var/lib/tailscale ||g' /etc/init.d/tailscale
/etc/init.d/tailscale disable
rm -f /etc/nftables.d/tailscale*.nft 2>/dev/null
uci set tailscale.settings.fw_mode='none'
uci set tailscale.settings.state_file='/etc/tailscale/tailscaled.state'
uci set tailscale.settings.autoupdate='false'
uci commit tailscale
mkdir -p /etc/tailscale"
step_ok "Tailscale      1.96.5 установлен  fw_mode=none  init.d=disabled"

# ── 6.1 rc.local ─────────────────────────────────────────────────────────────
step_start "rc.local       настраиваем userspace-networking автостарт..."
r5 "cat > /etc/rc.local << 'EOF'
#!/bin/sh
(sleep 40
tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking >> /tmp/ts.log 2>&1 &
sleep 5
tailscale up --accept-dns=false --accept-routes
sleep 10
logger -t rc.local 'tailscale up applied') &
exit 0
EOF
chmod +x /etc/rc.local
cp /etc/rc.local /etc/rc.local.bak"
step_ok "rc.local       создан + бэкап ✓"

# ── 6.2 Tailscale firewall ────────────────────────────────────────────────────
step_start "Firewall       добавляем tailscale0 в LAN зону..."
r5 "uci set firewall.@zone[0].device='br-lan tailscale0'
uci commit firewall
/etc/init.d/firewall reload"
step_ok "Firewall       tailscale0 в LAN ✓"

# ── 6.3 Tailscale watchdog ────────────────────────────────────────────────────
step_start "Tailscale WD   создаём ts-watchdog.sh + crontab..."
r5 "cat > /etc/ts-watchdog.sh << 'EOF'
#!/bin/sh
RC_BACKUP='/etc/rc.local.bak'
[ -f \"\$RC_BACKUP\" ] || exit 1
grep -q 'tailscaled' /etc/rc.local 2>/dev/null || cp \"\$RC_BACKUP\" /etc/rc.local
ps | grep -q 'tailscaled --statedir=' || {
  logger -t ts-watchdog 'tailscaled не найден, перезапуск'
  (sleep 5; tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking >> /tmp/ts.log 2>&1 &
   sleep 5; tailscale up --accept-dns=false --accept-routes) &
}
EOF
chmod +x /etc/ts-watchdog.sh
(crontab -l 2>/dev/null | grep -v ts-watchdog; echo '*/3 * * * * /etc/ts-watchdog.sh') | crontab -"
step_ok "Tailscale WD   каждые 3 мин ✓"

# ── 6.4 hotplug podkop after tailscale0 ──────────────────────────────────────
step_start "Hotplug        podkop restart при подъёме tailscale0..."
r5 "cat > /etc/hotplug.d/net/99-podkop-tailscale << 'EOF'
#!/bin/sh
[ \"\$ACTION\" = 'add' ] || exit 0
[ \"\$INTERFACE\" = 'tailscale0' ] || exit 0
(sleep 30; /etc/init.d/podkop restart; logger -t podkop-tailscale 'podkop restarted') &
EOF
chmod +x /etc/hotplug.d/net/99-podkop-tailscale"
step_ok "Hotplug        99-podkop-tailscale ✓"

# ── 7 Запускаем tailscaled вручную ───────────────────────────────────────────
step_start "Tailscale      запускаем tailscaled (userspace)..."
r5 "tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking >> /tmp/ts.log 2>&1 &"
sleep 3
step_ok "Tailscale      tailscaled запущен"

# ── 8 Auth URL ────────────────────────────────────────────────────────────────
step_start "Tailscale      получаем ссылку авторизации..."
r5 "setsid tailscale up --accept-dns=false --accept-routes --reset > /tmp/tsup.log 2>&1 &"
TS_URL=""
for i in $(seq 1 20); do
  TS_URL=$(r5 "grep -o 'https://login.tailscale.com[^ ]*' /tmp/tsup.log 2>/dev/null" | head -1)
  [ -n "$TS_URL" ] && break
  sleep 2
done
[ -z "$TS_URL" ] && die "ссылка авторизации не появилась"

echo ""
echo -e "${BOLD}${BLUE}🔗 АВТОРИЗУЙ В TAILSCALE (учётка n78rout@gmail.com):${NC}"
echo -e "${BOLD}   $TS_URL${NC}"
echo ""

# Ждём авторизации
until r5 "tailscale status 2>&1 | head -1" | grep -q "100\."; do sleep 3; done
TS_IP=$(r5 "tailscale status 2>&1 | head -1" | awk '{print $1}')
STATE=$(r5 "wc -c < /etc/tailscale/tailscaled.state 2>/dev/null" | xargs)
step_ok "Tailscale      авторизован  IP=$TS_IP  state=${STATE}b"

# ── 8.1 tailscale serve reset ─────────────────────────────────────────────────
r5 "tailscale serve reset 2>/dev/null; true"

# ── 9 Проверка перед ребутом (5 пунктов) ─────────────────────────────────────
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}   ✔ ПРОВЕРКА ГОТОВНОСТИ К РЕБУТУ${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

REBOOT_OK=true
FM=$(r5 "uci get tailscale.settings.fw_mode")
ID=$(r5 "/etc/init.d/tailscale enabled && echo ENABLED || echo DISABLED")
RC=$(r5 "grep -q tailscaled /etc/rc.local && echo OK || echo FAIL")
WD=$(r5 "crontab -l | grep -q ts-watchdog && echo OK || echo FAIL")
EN=$(r5 "uci get podkop.settings.exclude_ntp")

[ "$FM" = "none"     ] && echo -e "${GREEN}   ✅ fw_mode=none${NC}"     || { echo -e "${RED}   ❌ fw_mode=$FM${NC}";     REBOOT_OK=false; }
[ "$ID" = "DISABLED" ] && echo -e "${GREEN}   ✅ init.d DISABLED${NC}"  || { echo -e "${RED}   ❌ init.d ENABLED${NC}";  REBOOT_OK=false; }
[ "$RC" = "OK"       ] && echo -e "${GREEN}   ✅ rc.local OK${NC}"      || { echo -e "${RED}   ❌ rc.local FAIL${NC}";   REBOOT_OK=false; }
[ "$WD" = "OK"       ] && echo -e "${GREEN}   ✅ watchdog OK${NC}"      || { echo -e "${RED}   ❌ watchdog FAIL${NC}";   REBOOT_OK=false; }
[ "$EN" = "1"        ] && echo -e "${GREEN}   ✅ exclude_ntp=1${NC}"    || { echo -e "${RED}   ❌ exclude_ntp=$EN${NC}"; REBOOT_OK=false; }

$REBOOT_OK || die "5-пунктовая проверка провалилась — ребут отменён"
echo ""

# ── 10 Ребут ─────────────────────────────────────────────────────────────────
step_start "Ребут          перезагружаем..."
r5 "reboot" || true
sleep 50
step_start "Ребут          ждём Tailscale online после ребута..."
for i in $(seq 1 40); do
  ssh-keygen -R 192.168.5.1 2>/dev/null
  TS_REBOOT=$(r5 "tailscale status 2>&1 | head -1" 2>/dev/null)
  echo "$TS_REBOOT" | grep -q "100\." && break
  sleep 3
done
TS_REBOOT_IP=$(echo "$TS_REBOOT" | awk '{print $1}')
[ -z "$TS_REBOOT_IP" ] && die "Tailscale не поднялся после ребута"
step_ok "Ребут          Tailscale держится: $TS_REBOOT_IP ✓"

# ── 11 Финальный тест трафика ─────────────────────────────────────────────────
step_start "Тест трафика   google / youtube / telegram / chatgpt..."
sleep 5
G=$(r5 "curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 https://www.google.com")
Y=$(r5 "curl -s -o /dev/null -w '%{http_code}' --connect-timeout 8 https://www.youtube.com")
T=$(r5 "curl -s -o /dev/null -w '%{http_code}' --connect-timeout 8 https://web.telegram.org")
C=$(r5 "curl -s -o /dev/null -w '%{http_code}' --connect-timeout 8 https://chatgpt.com")

TRAFFIC_OK=true
[ "$G" = "200" ] && echo -e "${GREEN}   ✅ google:   200${NC}" || { echo -e "${RED}   ❌ google:   $G${NC}";   TRAFFIC_OK=false; }
[ "$Y" = "200" ] && echo -e "${GREEN}   ✅ youtube:  200${NC}" || { echo -e "${RED}   ❌ youtube:  $Y${NC}";  TRAFFIC_OK=false; }
[ "$T" = "200" ] && echo -e "${GREEN}   ✅ telegram: 200${NC}" || { echo -e "${RED}   ❌ telegram: $T${NC}"; TRAFFIC_OK=false; }
[ "$C" = "200" ] && echo -e "${GREEN}   ✅ chatgpt:  200${NC}" || { echo -e "${RED}   ❌ chatgpt:  $C${NC}"; TRAFFIC_OK=false; }

# ── Footer ────────────────────────────────────────────────────────────────────
TOTAL=$(( $(date +%s) - START ))
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if $TRAFFIC_OK; then
  echo -e "${BOLD}${GREEN}   ✅ ${RU} — ГОТОВ | Итого: $((TOTAL/60)):$(printf '%02d' $((TOTAL%60)))${NC}"
else
  echo -e "${BOLD}${YELLOW}   ⚠️  ${RU} — ГОТОВ с предупреждениями | Итого: $((TOTAL/60)):$(printf '%02d' $((TOTAL%60)))${NC}"
fi
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
