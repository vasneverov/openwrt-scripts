#!/bin/sh
# install-modem-ui.sh — Modem UI for OpenWrt 25.12+
# Full dashboard with:
#   - USB device detection
#   - Network status (operator, IP, speeds)
#   - Signal quality (RSRP, RSRQ, RSSI, SINR) with color scales
#   - Modem info (model, FW, IMEI, IMSI, APN, traffic)
#   - Actions: refresh, firewall toggle, reboot
#
# Author: vasneverov
# Repo: https://github.com/vasneverov/openwrt-modem-ui
# License: MIT
#
# Usage: sh install-modem-ui.sh
#   or:  wget -qO- https://raw.githubusercontent.com/vasneverov/openwrt-modem-ui/main/install-modem-ui.sh | sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo "${CYAN}╔══════════════════════════════════════════════╗${NC}"
echo "${CYAN}║      Modem UI Installer — OpenWrt 25.12+    ║${NC}"
echo "${CYAN}║      https://github.com/vasneverov/openwrt-modem-ui  ║${NC}"
echo "${CYAN}╚══════════════════════════════════════════════╝${NC}"
echo ""

# ── Check OpenWrt ──
if ! grep -q 'OpenWrt' /etc/openwrt_release 2>/dev/null; then
    echo "${RED}✗ Not OpenWrt. Aborting.${NC}"
    exit 1
fi

RELEASE=$(grep 'DISTRIB_RELEASE' /etc/openwrt_release | cut -d"'" -f2)
echo "${GREEN}✓ OpenWrt $RELEASE detected${NC}"

# ── Check APK ──
if ! command -v apk >/dev/null 2>&1; then
    echo "${RED}✗ APK package manager not found (OpenWrt <25.12?)${NC}"
    echo "${YELLOW}  This script requires OpenWrt 25.12+ with APK.${NC}"
    exit 1
fi

ARCH=$(apk --print-arch 2>/dev/null || uname -m)
echo "${GREEN}✓ Architecture: $ARCH${NC}"

# ── Step 1: Install USB modem kernel modules ──
echo ""
echo "${YELLOW}[1/6] Installing USB modem drivers...${NC}"

KMOD_PKGS="kmod-usb-serial kmod-usb-serial-option kmod-usb-serial-wwan kmod-usb-acm"
KMOD_PKGS="$KMOD_PKGS kmod-wwan kmod-usb-wdm kmod-usb-net-qmi-wwan"
KMOD_PKGS="$KMOD_PKGS kmod-usb-net-cdc-mbim kmod-usb-net-cdc-ncm kmod-usb-serial-qualcomm"
KMOD_PKGS="$KMOD_PKGS kmod-usb-net kmod-usb-serial"

INSTALLED=0
FAILED=0
for pkg in $KMOD_PKGS; do
    if apk info --installed 2>/dev/null | grep -q "^${pkg}$"; then
        echo "  ${GREEN}✓${NC} $pkg (already installed)"
        INSTALLED=$((INSTALLED + 1))
        continue
    fi
    echo -n "  Installing $pkg ... "
    if apk add --force-broken-world --allow-untrusted "$pkg" 2>/dev/null; then
        echo "${GREEN}OK${NC}"
        INSTALLED=$((INSTALLED + 1))
    else
        echo "${YELLOW}not in repo (will try from built-in)${NC}"
        FAILED=$((FAILED + 1))
    fi
done
echo "${GREEN}  ✓ $INSTALLED packages installed/verified${NC}"

# ── Step 2: Load kernel modules ──
echo ""
echo "${YELLOW}[2/6] Loading kernel modules...${NC}"
for mod in usbserial usb_serial_option usb_serial_wwan cdc_acm qmi_wwan cdc_mbim cdc_ncm wwan; do
    if modprobe "$mod" 2>/dev/null; then
        echo "  ${GREEN}✓${NC} $mod loaded"
    fi
done

# ── Step 3: Install LuCI files ──
echo ""
echo "${YELLOW}[3/6] Installing LuCI Modem UI...${NC}"

mkdir -p /www/luci-static/resources/view/modem
mkdir -p /usr/share/luci/menu.d
mkdir -p /usr/share/rpcd/acl.d

# ── Dashboard JS (full version with signal quality) ──
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
						fs.read(base + '/idVendor').catch(nop),
						fs.read(base + '/idProduct').catch(nop),
						fs.read(base + '/manufacturer').catch(nop),
						fs.read(base + '/product').catch(nop),
						fs.read(base + '/serial').catch(nop),
						fs.read(base + '/speed').catch(nop),
						fs.read(base + '/bDeviceClass').catch(nop),
						fs.read(base + '/bNumConfigurations').catch(nop)
					]);
				}));
			}),
			fs.read('/tmp/modem_status.json').catch(function() { return '{}'; }).then(function(data) {
				try { return JSON.parse(data); } catch(e) { return {}; }
			})
		]);
	},

	render: function(data) {
		var devices = data[0];
		var m = data[1] || {};

		var view = E('div', { 'class': 'cbi-map' }, [
			E('h2', { 'class': 'cbi-page-title' }, [
				E('span', {}, [ '\uD83D\uDCE1 Modem Status / Состояние модема' ])
			])
		]);

		if (!devices || devices.length === 0) {
			view.appendChild(_empty());
			return view;
		}

		for (var d = 0; d < devices.length; d++) {
			var dev = devices[d];
			view.appendChild(_deviceCard(dev[0], dev[1], dev[2], dev[3], dev[4], dev[5], dev[6], dev[7], dev[8]));
		}

		view.appendChild(_signalCard(m));
		view.appendChild(_signalQualityCard(m));
		view.appendChild(_actionsCard());
		return view;
	}
});

function nop() { return null; }

function _empty() {
	return E('div', { 'class': 'cbi-section', style: 'padding:32px;text-align:center;color:#999' }, [
		E('span', {}, [ '\uD83D\uDD0C USB модем не обнаружен' ])
	]);
}

function _deviceCard(name, vendorId, prodId, manuf, prod, serial, speed, devClass, numCfg) {
	var isModem = /^(3566|12d1|2c7c|0bdb|1bbb|19d2|0f3d|413c)$/.test(vendorId);
	var ms = devClass === '08';
	var clr = ms ? '#FF9800' : '#4CAF50';
	var bg  = ms ? '#FFF3E0' : '#E8F5E9';
	return E('div', { 'class': 'cbi-section', style: 'margin-bottom:8px' }, [
		E('h3', { 'class': 'cbi-section-title' }, [ '\uD83D\uDCF1 USB устройство (' + (name || '?') + ')' ]),
		E('table', { 'class': 'cbi-section-table' }, [
			_tr('Производитель', manuf || '\u2014'),
			_tr('Модель', prod || '\u2014'),
			_tr('VID:PID', (vendorId||'?') + ' :' + (prodId||'?')),
		]),
		E('div', { style: 'background:'+bg+';border:2px solid '+clr+';border-radius:4px;padding:8px;margin:8px;text-align:center;font-weight:bold;color:'+clr }, [ ms ? '\u26A0\uFE0F Mass Storage (не переключён)' : '\u2705 Режим модема' ])
	]);
}

function _signalCard(m) {
	var sig = parseInt(m.s) || 0;
	var n = Math.min(Math.max(sig,0),5);
	var connected = m.st === '901';
	var clr = connected ? '#4caf50' : '#999';
	var cols = ['#e74c3c','#e67e22','#f1c40f','#8bc34a','#4caf50'];
	var bars = E('div', { style: 'display:flex;align-items:flex-end;gap:3px;height:28px' });
	for (var i=0; i<5; i++) {
		var h = (i+1)*5;
		bars.appendChild(E('div', { style: 'width:16px;height:'+h+'px;background:'+(i<n?cols[i]:'#ddd')+';border-radius:2px 2px 0 0' }));
	}
	var fwOn = m.fw === '1';

	var left = E('table', { 'class': 'cbi-section-table' }, [
		_tr('Сигнал', bars),
		_tr('Регистрация', E('span', { style: 'color:'+clr+';font-weight:bold' }, [ connected ? (m.n||'?') : 'нет сети' ])),
		_tr('Оператор', E('span', { style: 'font-weight:bold' }, [ m.o || '\u2014' ])),
		_tr('IP', E('span', { style: 'font-family:monospace' }, [ m.i || '\u2014' ])),
		_tr('Скорость DL', (Math.round(parseInt(m.dr||0)/1024)) + ' KB/s'),
		_tr('Скорость UL', (Math.round(parseInt(m.ur||0)/1024)) + ' KB/s'),
		_tr('В соединении', _fmtTime(parseInt(m.ct||0))),
	]);

	var right = E('table', { 'class': 'cbi-section-table' }, [
		_tr('Модель', m.md || '\u2014'),
		_tr('FW', m.fv || '\u2014'),
		_tr('IMEI', m.im || '\u2014'),
		_tr('Номер', m.ms || '\u2014'),
		_tr('APN', m.ap || '\u2014'),
		_tr('Firewall', E('span', { style: 'font-weight:bold;color:'+(fwOn?'#e74c3c':'#4caf50') }, [ fwOn ? 'ВКЛ' : 'ВЫКЛ' ])),
		_tr('Скачано', (Math.round(parseInt(m.td||0)/1073741824*10)/10) + ' GB'),
		_tr('Отправлено', (Math.round(parseInt(m.tu||0)/1073741824*10)/10) + ' GB'),
	]);

	return E('div', { 'class': 'cbi-section', style: 'margin-bottom:8px' }, [
		E('h3', { 'class': 'cbi-section-title' }, [ '\uD83D\uDCF6 Сеть / Network' ]),
		E('div', { style: 'display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:4px 8px 8px' }, [ left, right ])
	]);
}

function _fmtTime(sec) {
	if (!sec) return '\u2014';
	var h = Math.floor(sec / 3600);
	var m = Math.floor((sec % 3600) / 60);
	return h + 'ч ' + m + 'м';
}

// ── Качество сигнала ── 2 колонки, белый ползунок ──
function _signalQualityCard(m) {
	var hasSignal = m.rsrp && m.rsrp !== '?';

	var section = E('div', { 'class': 'cbi-section', style: 'margin-bottom:8px' }, [
		E('h3', { 'class': 'cbi-section-title' }, [ '\uD83D\uDCA1 Качество сигнала / Signal Quality' ])
	]);

	if (!hasSignal) {
		section.appendChild(E('div', { style: 'padding:16px;text-align:center;color:#999' }, [ 'Нет данных сигнала' ]));
		return section;
	}

	var rsrp = parseInt(m.rsrp);
	var rsrq = parseInt(m.rsrq);
	var rssi = parseInt(m.rssi);
	var sinr = parseInt(m.sinr);

	var grid = E('div', { style: 'display:grid;grid-template-columns:1fr 1fr;gap:4px;padding:8px' });

	grid.appendChild(_sigBox('RSRP', 'Сила сигнала', rsrp, 'dBm', -130, -80,
		{ excellent: -90, good: -105, fair: -115, poor: -125 }));
	grid.appendChild(_sigBox('RSSI', 'Уровень сигнала', rssi, 'dBm', -120, -50,
		{ excellent: -65, good: -75, fair: -85, poor: -95 }));
	grid.appendChild(_sigBox('RSRQ', 'Качество', rsrq, 'dB', -25, -5,
		{ excellent: -9, good: -12, fair: -16, poor: -20 }));
	grid.appendChild(_sigBox('SINR', 'Шум/сигнал', sinr, 'dB', -10, 30,
		{ excellent: 20, good: 13, fair: 5, poor: 0 }));

	section.appendChild(grid);

	section.appendChild(E('div', { style: 'padding:6px 12px 10px;font-size:11px;color:#999;display:flex;gap:20px;border-top:1px solid #f0f0f0' }, [
		E('span', {}, [ 'Cell ID: ' + E('strong', { style: 'font-family:monospace;color:#666' }, [ m.cell_id || '\u2014' ]) ]),
		E('span', {}, [ 'PCI: ' + E('strong', { style: 'font-family:monospace;color:#666' }, [ m.pci || '\u2014' ]) ])
	]));

	return section;
}

function _sigBox(abbr, desc, value, unit, min, max, thresholds) {
	var v = Math.max(min, Math.min(max, value));
	var pct = ((v - min) / (max - min)) * 100;
	pct = Math.max(0, Math.min(100, pct));
	var rating = _signalRating(value, thresholds);

	var grad = 'linear-gradient(to right, #e74c3c 0%, #e67e22 25%, #f1c40f 50%, #8bc34a 75%, #2ecc71 100%)';

	var bar = E('div', { style: 'position:relative;height:20px;border-radius:10px;background:'+grad+';margin:4px 0' });
	var thumb = E('div', { style: 'position:absolute;left:calc('+pct+'% - 4px);top:0;width:8px;height:20px;background:#fff;border-radius:4px;box-shadow:0 1px 5px rgba(0,0,0,0.45);border:1px solid rgba(0,0,0,0.15);transition:left 0.25s;z-index:2' });
	bar.appendChild(thumb);

	var bottom = E('div', { style: 'display:flex;justify-content:space-between;align-items:center;font-size:11px' }, [
		E('span', { style: 'font-weight:bold;color:#444' }, [ (value > 0 ? '+' : '') + value + ' ' + unit ]),
		E('span', { style: 'font-weight:bold;color:'+rating.color }, [ rating.label ])
	]);

	return E('div', { style: 'padding:6px 8px;border:1px solid #e8e8e8;border-radius:6px;background:#fafafa' }, [
		E('div', { style: 'font-size:11px;font-weight:bold;color:#555;margin-bottom:2px' }, [ abbr + ' (' + desc + ')' ]),
		bar,
		bottom
	]);
}

function _signalRating(value, thresholds) {
	if (value >= thresholds.excellent) return { label: 'отлично', color: '#27ae60' };
	if (value >= thresholds.good)    return { label: 'хорошо', color: '#2ecc71' };
	if (value >= thresholds.fair)    return { label: 'норма', color: '#f39c12' };
	if (value >= thresholds.poor)    return { label: 'плохо', color: '#e67e22' };
	return { label: 'критично', color: '#e74c3c' };
}

function _actionsCard() {
	return E('div', { 'class': 'cbi-section', style: 'margin-bottom:8px' }, [
		E('h3', { 'class': 'cbi-section-title' }, [ '\u2699\uFE0F Действия / Actions' ]),
		E('div', { style: 'padding:8px;display:flex;gap:6px;flex-wrap:wrap' }, [
			E('button', { 'class': 'cbi-button cbi-button-reload', onclick: 'window.location.reload()' }, [ '\uD83D\uDD04 Обновить' ]),
			E('a', { 'class': 'cbi-button cbi-button-apply', href: '/cgi-bin/modem-action?action=fw-toggle' }, [ '\uD83D\uDD25 Firewall ВКЛ/ВЫКЛ' ]),
			E('a', { 'class': 'cbi-button cbi-button-apply', href: '/cgi-bin/modem-action?action=reboot', onclick: 'return confirm(\"Перезагрузить модем?\")' }, [ '\uD83D\uDD04 Перезагрузка модема' ]),
		])
	]);
}

function _tr(l, v) {
	return E('tr', { 'class': 'cbi-section-table-row' }, [
		E('td', { 'class': 'cbi-value-field', style: 'width:180px;font-weight:bold;padding:4px 8px' }, [ E('span', {}, [ l ]) ]),
		E('td', { 'class': 'cbi-value-field', style: 'padding:4px 8px' }, [ typeof v === 'string' ? E('span', {}, [ v ]) : v ])
	]);
}
JSEOF
echo "  ${GREEN}✓${NC} dashboard.js (full) written"

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
echo "  ${GREEN}✓${NC} menu entry written"

# ACL
cat > /usr/share/rpcd/acl.d/luci-app-modem.json << 'ACLEOF'
{
  "luci-app-modem": {
    "description": "Grant access to sysfs for modem monitoring",
    "read": {
      "file": {
        "/sys/bus/usb/devices/*": [ "list", "read" ],
        "/tmp/modem_status.json": [ "read" ]
      }
    },
    "write": {}
  }
}
ACLEOF
echo "  ${GREEN}✓${NC} ACL written"

# ── Step 4: Install modem status collector + cron ──
echo ""
echo "${YELLOW}[4/6] Installing modem status collector...${NC}"

mkdir -p /www/cgi-bin

# modem-full-status.sh — collects all modem data every minute
cat > /root/modem-full-status.sh << 'SHEOF'
#!/bin/sh
S=$(curl -s --max-time 5 http://192.168.8.1/api/webserver/SesTokInfo 2>/dev/null)
SID=$(echo "$S" | sed -n 's/.*SessionID=\([^<]*\)<.*/\1/p')
TOK=$(echo "$S" | sed -n 's/.*<TokInfo>\([^<]*\)<.*/\1/p')
H="Cookie: SessionID=$SID"
V="__RequestVerificationToken: $TOK"

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
echo "  ${GREEN}✓${NC} modem-full-status.sh written"

# Cron job — every minute
(crontab -l 2>/dev/null | grep -v modem-full-status
 echo "* * * * * /root/modem-full-status.sh") | crontab -
echo "  ${GREEN}✓${NC} cron: /root/modem-full-status.sh every minute"

# ── Step 5: Install CGI actions ──
echo ""
echo "${YELLOW}[5/6] Installing CGI actions...${NC}"

cat > /www/cgi-bin/modem-action << 'CGIEOF'
#!/bin/sh
echo 'Content-Type: application/json'
echo ''
S=$(curl -s --max-time 5 http://192.168.8.1/api/webserver/SesTokInfo 2>/dev/null)
SID=$(echo "$S" | sed -n 's/.*SessionID=\([^<]*\)<.*/\1/p')
TOK=$(echo "$S" | sed -n 's/.*<TokInfo>\([^<]*\)<.*/\1/p')
H="Cookie: SessionID=$SID"
V="__RequestVerificationToken: $TOK"
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
echo "  ${GREEN}✓${NC} CGI actions written"

# ── Step 6: Restart services ──
echo ""
echo "${YELLOW}[6/6] Restarting LuCI services...${NC}"
/etc/init.d/rpcd restart 2>/dev/null
/etc/init.d/uhttpd restart 2>/dev/null
rm -rf /tmp/luci-* 2>/dev/null
echo "  ${GREEN}✓${NC} Services restarted"

# ── Verification ──
echo ""
echo "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "${CYAN}  Installation complete!${NC}"
echo "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  ${GREEN}▶${NC} Log out of LuCI and log back in"
echo "  ${GREEN}▶${NC} Open Services → Modem"
echo "  ${GREEN}▶${NC} First run: /root/modem-full-status.sh"
echo "  ${GREEN}▶${NC} Then refresh browser"
echo ""
echo "  ${YELLOW}Note: Modem API at 192.168.8.1.${NC}"
echo "  ${YELLOW}If your modem is on a different IP, edit${NC}"
echo "  ${YELLOW}/root/modem-full-status.sh before first run.${NC}"
echo ""
