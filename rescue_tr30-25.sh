#!/bin/sh
# Rescue script for TR30-25 (волосач) - WWAN version
# One-shot fix for Tailscale + Podkop via WiFi
# Usage: sh <(wget -O - https://raw.githubusercontent.com/vasneverov/openwrt-fix/main/rescue-tr30-25.sh)

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   TR30-25 Rescue Tool (WWAN/WiFi Version)      ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

echo "[1/8] Checking network..."
# Ждем сеть
for i in 1 2 3 4 5; do
    if ping -c 1 -W 3 8.8.8.8 >/dev/null 2>&1; then
        echo "  ✓ Network OK"
        break
    fi
    echo "  Waiting for network... ($i/5)"
    sleep 5
done

echo ""
echo "[2/8] Setting Tailscale fw_mode → none"
uci set tailscale.settings.fw_mode='none'
uci commit tailscale
echo "  ✓ fw_mode = none"

echo ""
echo "[3/8] Disabling init.d/tailscale"
/etc/init.d/tailscale disable 2>/dev/null
echo "  ✓ init.d/tailscale disabled"

echo ""
echo "[4/8] Setting podkop exclude_ntp → 1"
uci set podkop.settings.exclude_ntp='1'
uci commit podkop
echo "  ✓ exclude_ntp = 1"

echo ""
echo "[5/8] Deleting Calls profile"
uci delete podkop.Calls 2>/dev/null
uci commit podkop
echo "  ✓ Calls deleted"

echo ""
echo "[6/8] Setting community_lists (telegram+meta first)"
uci set podkop.main.community_lists='telegram meta google_ai geoblock block porn news anime discord twitter hdrezka tiktok cloudflare google_play hodca hetzner ovh digitalocean cloudfront'
uci commit podkop
echo "  ✓ community_lists updated"

echo ""
echo "[7/8] Setting Moscow keys (bMSK relay)"
# Main key (bMSK:5223 → Fin4)
uci set podkop.main.proxy_string='vless://9c509a4c-4381-4c5e-8407-c7bb76b11d37@159.194.198.172:5223?type=grpc&security=reality&mode=gun&serviceName=&pbk=HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI&sid=4b929012&sni=www.apple.com&fp=chrome&spx=%2F#TR30-25-main'
uci set podkop.main.enabled='1'

# YT key (bMSK:8853 direct)
uci set podkop.YT=section 2>/dev/null
uci set podkop.YT.connection_type='proxy'
uci set podkop.YT.proxy_config_type='url'
uci set podkop.YT.community_lists='youtube'
uci set podkop.YT.proxy_string='vless://0890eac2-6e0e-46dc-83e7-621057d0d986@159.194.198.172:8853?type=grpc&security=reality&mode=gun&serviceName=&pbk=g5eg_BKQJLVbPxryppyE0AGpQB_HKHPGkOJN9I6bSzI&sid=1cbf0359&sni=www.apple.com&fp=chrome&spx=%2F#TR30-25-yt'
uci set podkop.YT.enabled='1'
uci commit podkop
echo "  ✓ Keys configured"

echo ""
echo "[8/8] Creating watchdog scripts..."

# Tailscale watchdog
cat > /etc/ts-watchdog.sh << 'WEOF'
#!/bin/sh
RC_BACKUP="/etc/rc.local.bak"
if [ ! -f "$RC_BACKUP" ]; then exit 1; fi
if ! grep -q "tailscaled" /etc/rc.local 2>/dev/null; then
    cp "$RC_BACKUP" /etc/rc.local
fi
if ! ps | grep -q "tailscaled --tun"; then
    (sleep 5; tailscaled --tun=userspace-networking --statedir=/etc/tailscale/ >> /tmp/ts.log 2>&1 & sleep 5; tailscale up --accept-dns=false --accept-routes) &
fi
WEOF
chmod +x /etc/ts-watchdog.sh

# Podkop watchdog
cat > /etc/podkop-watchdog.sh << 'WEOF'
#!/bin/sh
if ! ps | grep -q "sing-box run"; then
    logger -t podkop-watchdog "sing-box not running, restarting podkop"
    /etc/init.d/podkop restart
fi
WEOF
chmod +x /etc/podkop-watchdog.sh

# Setup crontab
echo "*/2 * * * * /etc/ts-watchdog.sh" > /etc/crontabs/root
echo "*/2 * * * * /etc/podkop-watchdog.sh" >> /etc/crontabs/root
echo "*/2 * * * * /etc/route-watchdog.sh" >> /etc/crontabs/root
echo "13 */3 * * * /usr/bin/podkop list_update" >> /etc/crontabs/root

echo "  ✓ Watchdog created"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║         RESTARTING SERVICES...                   ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

/etc/init.d/podkop restart
echo "  ✓ Podkop restarted"

echo ""
echo "Waiting 10 seconds for services to start..."
sleep 10

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║         FINAL STATUS                             ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Check status
echo "Tailscale fw_mode: $(uci get tailscale.settings.fw_mode)"
echo "exclude_ntp: $(uci get podkop.settings.exclude_ntp)"
echo ""

if ps | grep -q "sing-box run"; then
    echo "  ✅ sing-box RUNNING"
else
    echo "  ❌ sing-box NOT running"
fi

if tailscale status 2>/dev/null | grep -q "100\."; then
    echo "  ✅ Tailscale ONLINE"
    tailscale status | head -1
else
    echo "  ⏳ Tailscale connecting..."
fi

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  🎉 RESCUE COMPLETE!                             ║"
echo "║                                                  ║"
echo "║  Tests after 30 seconds:                         ║"
echo "║  - curl https://www.google.com                     ║"
echo "║  - curl https://www.youtube.com                    ║"
echo "║  - curl https://telegram.org                       ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
