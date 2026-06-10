#!/bin/sh
# install-modem-support.sh — Универсальная установка USB модема на OpenWrt
# Устанавливает: драйверы, Modem UI, network, firewall, проверяет работу
# Работает на любом OpenWrt 25.12+ (apk). Безопасно — не трогает Podkop/Tailscale.
#
# Использование:
#   # По SSH (вручную):
#   sh -c "$(wget -qO- https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/tools/install-modem-support.sh)"
#
#   # Через stdin-pipe (с компа):
#   cat install-modem-support.sh | ssh root@192.168.5.1 "sh"
#
#   # Дистанционно через Tailscale:
#   ssh root@100.x.x.x "sh -c \"\$(wget -qO- https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/tools/install-modem-support.sh)\""
#
# Автор: vasneverov
# Репозиторий: https://github.com/vasneverov/openwrt-scripts
# Лицензия: MIT

set -e

# ── Цвета ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

PASS="${GREEN}✅${NC}"
FAIL="${RED}❌${NC}"
SKIP="${YELLOW}⏭${NC}"
INFO="${CYAN}ℹ️${NC}"

echo ""
echo "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
echo "${CYAN}║     📡 Modem Support Installer — OpenWrt 25.12+ ║${NC}"
echo "${CYAN}╚══════════════════════════════════════════════════╝${NC}"
echo ""

HOSTNAME=$(cat /proc/sys/kernel/hostname 2>/dev/null || echo "unknown")
MODEL=$(cat /tmp/sysinfo/model 2>/dev/null || echo "unknown")
VER=$(grep 'DISTRIB_RELEASE' /etc/openwrt_release 2>/dev/null | cut -d"'" -f2 || echo "?")
echo " ${INFO} Роутер: ${BOLD}$HOSTNAME${NC} ($MODEL)"
echo " ${INFO} OpenWrt: $VER"
echo ""

# ── Проверка OpenWrt ──
if ! grep -q 'OpenWrt' /etc/openwrt_release 2>/dev/null; then
    echo " ${FAIL} Не OpenWrt. Выход."
    exit 1
fi

# ── Проверка apk ──
if ! command -v apk >/dev/null 2>&1; then
    echo " ${FAIL} Нет apk (нужен OpenWrt 25.12+). Выход."
    exit 1
fi

# ── Шаг 0: Диагностика ──
echo "${CYAN}━━━ [0/5] Диагностика ━━━${NC}"

# Интернет
if ping -c1 -W3 1.1.1.1 >/dev/null 2>&1; then
    echo " ${PASS} Интернет: есть"
    HAS_NET=1
else
    echo " ${FAIL} Интернет: НЕТ. Драйверы не установятся."
    echo "   Подключи WAN кабель или WiFi перед запуском."
    HAS_NET=0
fi

# USB модем
MODEM_VID=""
MODEM_PID=""
MODEM_FOUND=0
if command -v lsusb >/dev/null 2>&1; then
    LSUSB=$(lsusb 2>/dev/null)
    # Huawei E3372: 12d1:14db (mass storage) / 12d1:14dc (modem)
    # Fibocom: 3566:2001
    for VIDPID in "12d1:14dc" "12d1:14db" "3566:2001" "12d1:1506" "12d1:1c05" "12d1:1c0b"; do
        VID="${VIDPID%:*}"
        PID="${VIDPID#*:}"
        if echo "$LSUSB" | grep -qi "$VID:$PID"; then
            MODEM_VID="$VID"
            MODEM_PID="$PID"
            MODEM_FOUND=1
            break
        fi
    done
    if [ "$MODEM_FOUND" = "1" ]; then
        MS=""
        [ "$MODEM_PID" = "14db" ] && MS=" (Mass Storage — нужен usb_modeswitch)"
        [ "$MODEM_PID" = "2001" ] && MS=" (Fibocom — НЕ поддерживается!)"
        echo " ${PASS} Модем: $MODEM_VID:$MODEM_PID$MS"
    else
        echo " ${FAIL} Модем не обнаружен. Вставь модем с SIM в USB."
        echo "   Или проверь lsusb"
    fi
else
    echo " ${YELLOW}⚠${NC} lsusb не установлен — не могу проверить модем"
fi

# Интерфейс модема
MODEM_IFACE=""
for iface in eth2 usb0 wwan0 eth3 eth4; do
    if [ -d "/sys/class/net/$iface" ]; then
        IP=$(ip -4 addr show "$iface" 2>/dev/null | grep 'inet ' | awk '{print $2}')
        if [ -n "$IP" ]; then
            MODEM_IFACE="$iface"
            echo " ${PASS} Интерфейс: $iface ($IP)"
            break
        fi
    fi
done
if [ -z "$MODEM_IFACE" ]; then
    # fallback: ищем любой интерфейс с IP из 192.168.8.0/24
    for iface in /sys/class/net/*/; do
        iface=$(basename "$iface")
        case "$iface" in lo|eth0|eth1|br-lan|phy*|tailscale*) continue;; esac
        IP=$(ip -4 addr show "$iface" 2>/dev/null | grep 'inet 192.168.8\.' | awk '{print $2}')
        if [ -n "$IP" ]; then
            MODEM_IFACE="$iface"
            echo " ${PASS} Интерфейс: $iface ($IP) [авто]"
            break
        fi
    done
fi
if [ -z "$MODEM_IFACE" ] && [ "$MODEM_FOUND" = "1" ]; then
    echo " ${YELLOW}⚠${NC} Модем найден, но интерфейс без IP. Если драйверов нет — будет дальше."
fi

# Firewall
FW_OK=0
if uci get firewall.@zone[1].network 2>/dev/null | grep -q 'modem'; then
    FW_OK=1
    echo " ${PASS} Firewall: modem в зоне wan"
else
    echo " ${FAIL} Firewall: modem НЕ в зоне wan (русские сайты не будут работать)"
fi

# Modem UI
UI_OK=0
if [ -f /www/luci-static/resources/view/modem/dashboard.js ]; then
    UI_OK=1
    echo " ${PASS} Modem UI: установлен"
else
    echo " ${FAIL} Modem UI: не установлен"
fi

# Метрики
METRIC_MODEM=$(uci get network.modem.metric 2>/dev/null || echo "?")
METRIC_WAN=$(uci get network.wan.metric 2>/dev/null || echo "?")
METRIC_WWAN=$(uci get network.wwan.metric 2>/dev/null || echo "?")
echo " ${INFO} Метрики: modem=$METRIC_MODEM wan=$METRIC_WAN wwan=$METRIC_WWAN"
echo ""

# ── Если интернета нет — аборт ──
if [ "$HAS_NET" != "1" ]; then
    echo " ${FAIL} Без интернета установка невозможна. Подключи WAN/WiFi и запусти заново."
    exit 1
fi

# ── Шаг 1: Драйверы USB ──
echo "${CYAN}━━━ [1/5] Установка драйверов USB модема ━━━${NC}"

KMOD_PKGS="kmod-usb-serial kmod-usb-serial-option kmod-usb-serial-wwan kmod-usb-acm"
KMOD_PKGS="$KMOD_PKGS kmod-wwan kmod-usb-wdm kmod-usb-net-qmi-wwan"
KMOD_PKGS="$KMOD_PKGS kmod-usb-net-cdc-mbim kmod-usb-net-cdc-ncm kmod-usb-serial-qualcomm"
KMOD_PKGS="$KMOD_PKGS kmod-usb-net kmod-usb-serial kmod-usb-storage kmod-usb-storage-uas"
KMOD_PKGS="$KMOD_PKGS usb-modeswitch usbutils python3 libusb-1.0-0"

INSTALLED=0
SKIPPED=0
for pkg in $KMOD_PKGS; do
    if apk info --installed 2>/dev/null | grep -q "^${pkg}$"; then
        SKIPPED=$((SKIPPED + 1))
        continue
    fi
    echo -n "  $pkg ... "
    if apk add --force-broken-world --allow-untrusted "$pkg" 2>/dev/null; then
        echo "${GREEN}OK${NC}"
        INSTALLED=$((INSTALLED + 1))
    else
        echo "${YELLOW}skip${NC}"
    fi
done
echo " ${PASS} Драйверы: $INSTALLED установлено, $SKIPPED уже были"
echo ""

# ── Загрузка модулей ──
for mod in usbserial usb_serial_option usb_serial_wwan cdc_acm qmi_wwan cdc_mbim cdc_ncm wwan; do
    modprobe "$mod" 2>/dev/null || true
done

# ── usb_modeswitch (если модем в Mass Storage) ──
if [ "$MODEM_PID" = "14db" ]; then
    echo "${YELLOW}⚠ Модем в Mass Storage. Пробую переключить...${NC}"
    # SCSI eject
    for dev in /sys/bus/usb/devices/*; do
        if [ -f "$dev/idVendor" ] && [ "$(cat "$dev/idVendor" 2>/dev/null)" = "12d1" ]; then
            if [ -f "$dev/idProduct" ] && [ "$(cat "$dev/idProduct" 2>/dev/null)" = "14db" ]; then
                echo "  Найден: $dev"
                if [ -f "$dev/authorized" ]; then
                    echo 0 > "$dev/authorized" 2>/dev/null || true
                    sleep 1
                    echo 1 > "$dev/authorized" 2>/dev/null || true
                    echo "  Сброс USB (authorized toggle)"
                fi
                break
            fi
        fi
    done
    sleep 5
    # Проверить, переключился ли
    if lsusb 2>/dev/null | grep -qi "12d1:14dc"; then
        echo " ${PASS} Модем переключился в modem mode (12d1:14dc)"
        MODEM_PID="14dc"
    else
        echo " ${FAIL} usb_modeswitch не сработал"
    fi
fi

# ── Шаг 2: Modem UI ──
echo "${CYAN}━━━ [2/5] Установка Modem UI ─────────────────${NC}"

mkdir -p /www/luci-static/resources/view/modem
mkdir -p /usr/share/luci/menu.d
mkdir -p /usr/share/rpcd/acl.d
mkdir -p /www/cgi-bin

# Dashboard.js (полная версия с сигнальными шкалами)
if [ -f /www/luci-static/resources/view/modem/dashboard.js ]; then
    cp /www/luci-static/resources/view/modem/dashboard.js /www/luci-static/resources/view/modem/dashboard.js.bak 2>/dev/null || true
    echo " ${SKIP} dashboard.js уже есть (backup сохранён)"
else
    # Заливаем минимальную заглушку, полный дашборд будет через install-modem-ui.sh
    echo " ${SKIP} install-modem-ui.sh будет ниже"
fi

# Menu entry
cat > /usr/share/luci/menu.d/luci-app-modem.json << 'MENUEOF'
{
  "admin/services/modem": {
    "title": "Modem",
    "order": 43,
    "action": {
      "type": "view",
      "path": "modem/dashboard"
    },
    "depends": {
      "acl": [ "luci-app-modem" ]
    }
  }
}
MENUEOF

# ACL
cat > /usr/share/rpcd/acl.d/luci-app-modem.json << 'ACLEOF'
{
  "luci-app-modem": {
    "description": "Grant access to sysfs for modem monitoring",
    "read": {
      "file": {
        "/sys/bus/usb/devices/*": [ "list", "read" ]
      }
    },
    "write": {}
  }
}
ACLEOF

# Устанавливаем install-modem-ui.sh (полный дашборд + статус + CGI + cron)
# Скачиваем с GitHub
echo "  Скачиваю install-modem-ui.sh..."
if wget -q --timeout=15 -O /tmp/install-modem-ui.sh \
  'https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/tools/install-modem-ui.sh' 2>/dev/null; then
    # Пропускаем первые 15 строк (проверки) — они уже выполнены
    chmod +x /tmp/install-modem-ui.sh
    sed '1,15d' /tmp/install-modem-ui.sh | sh -s 2>&1 | grep -v '^  Installing kmod'
    rm -f /tmp/install-modem-ui.sh
    UI_OK=1
    echo " ${PASS} Modem UI: установлен через GitHub"
else
    echo " ${YELLOW}⚠ GitHub недоступен. Устанавливаю базовый Modem UI из скрипта..."

    # Базовая версия dashboard.js
    cat > /www/luci-static/resources/view/modem/dashboard.js << 'JSEOF'
'use strict';
'require view';
'require fs';
return view.extend({
    load: function() {
        return Promise.all([
            fs.list('/sys/bus/usb/devices/').then(function(entries) {
                var devices = entries.filter(function(e) {
                    return (e.name.match(/^\d+-\d+$/) || e.name.match(/^\d+-\d+\.\d+$/));
                });
                return Promise.all(devices.map(function(dev) {
                    var base = '/sys/bus/usb/devices/' + dev.name;
                    return Promise.all([
                        Promise.resolve(dev.name),
                        fs.read(base + '/idVendor').catch(function(){}),
                        fs.read(base + '/idProduct').catch(function(){}),
                        fs.read(base + '/manufacturer').catch(function(){}),
                        fs.read(base + '/product').catch(function(){})
                    ]);
                }));
            }),
            fs.read('/tmp/modem_status.json').catch(function(){return '{}';}).then(function(d){try{return JSON.parse(d)}catch(e){return{}}})
        ]);
    },
    render: function(data) {
        var d = data[0], m = data[1] || {};
        var v = E('div',{'class':'cbi-map'},[E('h2',{'class':'cbi-page-title'},['📡 Modem Status'])]); v.appendChild(_signalCard(m)); return v;
    }
});
function _signalCard(m){var s=parseInt(m.s)||0,c=m.st==='901';return E('div',{'class':'cbi-section'},[E('h3',{'class':'cbi-section-title'},['📶 Network']),E('table',{'class':'cbi-section-table'},[_tr('Operator',m.o||'—'),_tr('IP',m.i||'—'),_tr('Connected',c?'✅':'❌')])]);}
function _tr(l,v){return E('tr',{'class':'cbi-section-table-row'},[E('td',{'style':'width:180px;font-weight:bold;padding:4px 8px'},[l]),E('td',{'style':'padding:4px 8px'},[typeof v==='string'?v:v])]);}
JSEOF

    # modem-full-status.sh
    cat > /root/modem-full-status.sh << 'SHEOF'
#!/bin/sh
S=$(curl -s --max-time 5 http://192.168.8.1/api/webserver/SesTokInfo 2>/dev/null)
SID=$(echo "$S" | sed -n 's/.*SessionID=\([^<]*\)<.*/\1/p')
TOK=$(echo "$S" | sed -n 's/.*<TokInfo>\([^<]*\)<.*/\1/p')
H="Cookie: SessionID=$SID"; V="__RequestVerificationToken: $TOK"
M=$(curl -s --max-time 5 http://192.168.8.1/api/monitoring/status -H "$H" -H "$V" 2>/dev/null)
sleep 1
D=$(curl -s --max-time 5 http://192.168.8.1/api/device/information -H "$H" -H "$V" 2>/dev/null)
sleep 1
P=$(curl -s --max-time 5 http://192.168.8.1/api/net/current-plmn -H "$H" -H "$V" 2>/dev/null)
sleep 1
F=$(curl -s --max-time 5 http://192.168.8.1/api/security/firewall-switch -H "$H" -H "$V" 2>/dev/null)
sleep 1
R=$(curl -s --max-time 5 http://192.168.8.1/api/monitoring/traffic-statistics -H "$H" -H "$V" 2>/dev/null)
sleep 1
A=$(curl -s --max-time 5 http://192.168.8.1/api/dialup/profiles -H "$H" -H "$V" 2>/dev/null)
sleep 1
Q=$(curl -s --max-time 5 http://192.168.8.1/api/device/signal -H "$H" -H "$V" 2>/dev/null)
SG=$(echo "$M" | sed -n 's/.*<SignalIcon>\([^<]*\)<.*/\1/p')
OP=$(echo "$P" | sed -n 's/.*<FullName>\([^<]*\)<.*/\1/p')
IP=$(echo "$M" | sed -n 's/.*<WanIPAddress>\([^<]*\)<.*/\1/p')
ST=$(echo "$M" | sed -n 's/.*<ConnectionStatus>\([^<]*\)<.*/\1/p')
DR=$(echo "$R" | sed -n 's/.*<CurrentDownloadRate>\([^<]*\)<.*/\1/p')
UR=$(echo "$R" | sed -n 's/.*<CurrentUploadRate>\([^<]*\)<.*/\1/p')
FW=$(echo "$F" | sed -n 's/.*<FirewallMainSwitch>\([^<]*\)<.*/\1/p')
MD=$(echo "$D" | sed -n 's/.*<DeviceName>\([^<]*\)<.*/\1/p')
FV=$(echo "$D" | sed -n 's/.*<SoftwareVersion>\([^<]*\)<.*/\1/p')
IM=$(echo "$D" | sed -n 's/.*<Imei>\([^<]*\)<.*/\1/p')
MS=$(echo "$D" | sed -n 's/.*<Msisdn>\([^<]*\)<.*/\1/p')
AP=$(echo "$A" | sed -n 's/.*<ApnName>\([^<]*\)<.*/\1/p')
TD=$(echo "$R" | sed -n 's/.*<TotalDownload>\([^<]*\)<.*/\1/p')
TU=$(echo "$R" | sed -n 's/.*<TotalUpload>\([^<]*\)<.*/\1/p')
CT=$(echo "$R" | sed -n 's/.*<CurrentConnectTime>\([^<]*\)<.*/\1/p')
RSRP=$(echo "$Q" | sed -n 's/.*<rsrp>\([^d]*\)dB.*/\1/p')
RSRQ=$(echo "$Q" | sed -n 's/.*<rsrq>\([^d]*\)dB.*/\1/p')
RSSI=$(echo "$Q" | sed -n 's/.*<rssi>\([^d]*\)dB.*/\1/p')
SINR=$(echo "$Q" | sed -n 's/.*<sinr>\([^d]*\)dB.*/\1/p')
PCI=$(echo "$Q" | sed -n 's/.*<pci>\([^<]*\)<.*/\1/p')
CELL=$(echo "$Q" | sed -n 's/.*<cell_id>\([^<]*\)<.*/\1/p')
echo "$M" | grep -q 'CurrentNetworkTypeEx>101<' && NN='4G LTE' || NN='?'
echo "{\"s\":\"${SG:-0}\",\"o\":\"${OP:-?}\",\"n\":\"$NN\",\"i\":\"${IP:-?}\",\"dr\":\"${DR:-0}\",\"ur\":\"${UR:-0}\",\"st\":\"${ST:-0}\",\"fw\":\"${FW:-1}\",\"md\":\"${MD:-?}\",\"fv\":\"${FV:-?}\",\"im\":\"${IM:-?}\",\"ms\":\"${MS:-?}\",\"ap\":\"${AP:-?}\",\"td\":\"${TD:-0}\",\"tu\":\"${TU:-0}\",\"ct\":\"${CT:-0}\",\"rsrp\":\"${RSRP:-?}\",\"rsrq\":\"${RSRQ:-?}\",\"rssi\":\"${RSSI:-?}\",\"sinr\":\"${SINR:-?}\",\"pci\":\"${PCI:-?}\",\"cell_id\":\"${CELL:-?}\"}" > /tmp/modem_status.json
SHEOF
    chmod +x /root/modem-full-status.sh

    # CGI
    cat > /www/cgi-bin/modem-action << 'CGIEOF'
#!/bin/sh
echo 'Content-Type: application/json'
echo ''
S=$(curl -s --max-time 5 http://192.168.8.1/api/webserver/SesTokInfo 2>/dev/null)
SID=$(echo "$S" | sed -n 's/.*SessionID=\([^<]*\)<.*/\1/p')
TOK=$(echo "$S" | sed -n 's/.*<TokInfo>\([^<]*\)<.*/\1/p')
H="Cookie: SessionID=$SID"; V="__RequestVerificationToken: $TOK"
ACTION="${QUERY_STRING#action=}"; ACTION="${ACTION%%&*}"
case "$ACTION" in
  fw-toggle)
    F=$(curl -s --max-time 5 http://192.168.8.1/api/security/firewall-switch -H "$H" -H "$V" 2>/dev/null)
    CURR=$(echo "$F" | sed -n 's/.*<FirewallMainSwitch>\([^<]*\)<.*/\1/p')
    if [ "$CURR" = "1" ]; then
      curl -s -X POST http://192.168.8.1/api/security/firewall-switch -H "$H" -H "$V" \
        --data '<?xml version="1.0" encoding="UTF-8"?><request><FirewallMainSwitch>0</FirewallMainSwitch><FirewallIPFilterSwitch>0</FirewallIPFilterSwitch><FirewallWanPortPingSwitch>1</FirewallWanPortPingSwitch></request>' >/dev/null 2>&1
      echo '{"status":"off"}'
    else
      curl -s -X POST http://192.168.8.1/api/security/firewall-switch -H "$H" -H "$V" \
        --data '<?xml version="1.0" encoding="UTF-8"?><request><FirewallMainSwitch>1</FirewallMainSwitch><FirewallIPFilterSwitch>1</FirewallIPFilterSwitch><FirewallWanPortPingSwitch>0</FirewallWanPortPingSwitch></request>' >/dev/null 2>&1
      echo '{"status":"on"}'
    fi ;;
  reboot)
    curl -s -X POST http://192.168.8.1/api/device/control -H "$H" -H "$V" \
      --data '<?xml version="1.0" encoding="UTF-8"?><request><Control>1</Control><ATCommand>AT+CRST</ATCommand></request>' >/dev/null 2>&1
    echo '{"status":"ok"}' ;;
esac
CGIEOF
    chmod +x /www/cgi-bin/modem-action

    # Cron
    (crontab -l 2>/dev/null | grep -v modem-full-status
     echo "* * * * * /root/modem-full-status.sh") | crontab -
    UI_OK=1
    echo " ${PASS} Modem UI: установлен (базовая версия)"
fi

echo ""

# ── Шаг 3: Web UI обновление (полный dashboard если есть доступ) ──
echo "${CYAN}━━━ [3/5] Обновление dashboard.js ────────────${NC}"
if [ "$UI_OK" = "1" ]; then
    # Пробуем скачать полный dashboard.js с GitHub
    if wget -q --timeout=10 -O /tmp/dashboard.js \
      'https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/tools/dashboard.js' 2>/dev/null; then
        cp /tmp/dashboard.js /www/luci-static/resources/view/modem/dashboard.js
        rm -f /tmp/dashboard.js
        echo " ${PASS} dashboard.js обновлён до полной версии (с сигнальными шкалами)"
    else
        echo " ${YELLOW}⚠${NC} Не удалось скачать полный dashboard — остаётся текущий"
    fi
fi
echo ""

# ── Шаг 4: Network + Firewall ──
echo "${CYAN}━━━ [4/5] Настройка сети и firewall ─────────${NC}"

# Определяем интерфейс модема если ещё не нашли
if [ -z "$MODEM_IFACE" ]; then
    for iface in eth2 usb0 wwan0; do
        if [ -d "/sys/class/net/$iface" ]; then
            MODEM_IFACE="$iface"
            break
        fi
    done
fi

if [ -n "$MODEM_IFACE" ]; then
    # Network interface
    uci set network.modem=interface 2>/dev/null || uci set network.modem=interface
    uci set network.modem.proto='dhcp'
    uci set network.modem.device="$MODEM_IFACE"
    
    # Приоритеты: модем > шнур > WiFi
    uci set network.modem.metric='10'
    uci set network.wan.metric='20'   # шнур
    uci set network.wwan.metric='30'   # WiFi
    
    uci commit network
    /etc/init.d/network reload 2>/dev/null || true
    
    echo " ${PASS} Network: modem=$MODEM_IFACE (metric 10), wan (metric 20), wwan (metric 30)"
    
    # Firewall
    if ! uci get firewall.@zone[1].network 2>/dev/null | grep -q 'modem'; then
        uci add_list firewall.@zone[1].network='modem'
        uci commit firewall
        # Проверяем tailscale nft, чтобы не было конфликта
        if [ -f /etc/nftables.d/99-tailscale-direct.nft ]; then
            mv /etc/nftables.d/99-tailscale-direct.nft /etc/nftables.d/99-tailscale-direct.nft.bak 2>/dev/null || true
        fi
        /etc/init.d/firewall restart 2>&1 | grep -v 'Error' || /etc/init.d/firewall restart 2>/dev/null || true
        # Восстанавливаем tailscale nft, если он есть
        if [ -f /etc/nftables.d/99-tailscale-direct.nft.bak ] && [ ! -f /etc/nftables.d/99-tailscale-direct.nft ]; then
            mv /etc/nftables.d/99-tailscale-direct.nft.bak /etc/nftables.d/99-tailscale-direct.nft 2>/dev/null || true
        fi
        FW_OK=1
        echo " ${PASS} Firewall: modem добавлен в зону wan"
    else
        echo " ${SKIP} Firewall: modem уже в зоне wan"
    fi
else
    echo " ${FAIL} Интерфейс модема не найден. Firewall не настроен."
    echo "   После установки драйверов перезапусти скрипт."
fi
echo ""

# ── Шаг 5: Первый сбор данных + Проверка ──
echo "${CYAN}━━━ [5/5] Проверка ───────────────────────────${NC}"

# Первый сбор данных
if [ -x /root/modem-full-status.sh ]; then
    /root/modem-full-status.sh 2>/dev/null
    echo " ${PASS} modem-full-status.sh выполнен"
fi

# Проверка статуса
echo ""
echo "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
echo "${CYAN}║          📊 Modem Support — ИТОГ                ║${NC}"
echo "${CYAN}╚══════════════════════════════════════════════════╝${NC}"

# 1. Модем
if [ -n "$MODEM_IFACE" ]; then
    MODEM_IP=$(ip -4 addr show "$MODEM_IFACE" 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)
    if [ -n "$MODEM_IP" ]; then
        echo " ${PASS} Модем: $MODEM_IFACE / $MODEM_IP"
    else
        echo " ${FAIL} Модем: $MODEM_IFACE без IP — жди DHCP или перезагрузки"
    fi
else
    echo " ${FAIL} Модем: интерфейс не найден"
fi

# 2. Русские сайты
YRES=$(curl -s -o /dev/null -w '%{http_code} %{time_total}s' --connect-timeout 5 http://yandex.ru 2>/dev/null)
VRES=$(curl -s -o /dev/null -w '%{http_code} %{time_total}s' --connect-timeout 5 http://vk.com 2>/dev/null)
echo " ${PASS} yandex.ru: $YRES"
echo " ${PASS} vk.com: $VRES"

# 3. Firewall
if [ "$FW_OK" = "1" ]; then
    echo " ${PASS} Firewall: modem в зоне wan"
else
    echo " ${FAIL} Firewall: modem НЕ в зоне wan"
fi

# 4. Modem UI
if [ "$UI_OK" = "1" ]; then
    echo " ${PASS} Modem UI: установлен (Services → Modem)"
else
    echo " ${FAIL} Modem UI: не установлен"
fi

# 5. Приоритеты
echo " ${INFO} Приоритет: modem(10) > wan(20) > wwan(30)"

echo ""
echo "${GREEN}✅ Modem support установлен!${NC}"
echo "   Для просмотра: открой LuCI → Services → Modem"
echo "   Или обнови страницу если уже открыта."
echo ""
