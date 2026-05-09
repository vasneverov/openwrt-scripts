Мне кажется, ты не там.#!/bin/sh
# Rescue script for Z56-117 (s-rogachev)
# One-shot fix for Tailscale + Podkop stability
# Run via AnyDesk terminal

echo "=========================================="
echo "RESCUE Z56-117 - $(date)"
echo "=========================================="

# 1. Fix Tailscale fw_mode
echo "[1/5] Setting fw_mode=none..."
uci set tailscale.settings.fw_mode='none'
uci commit tailscale
echo "✓ fw_mode=none"

# 2. Fix rc.local
echo "[2/5] Creating rc.local..."
cat > /etc/rc.local << 'EOF'
#!/bin/sh
(sleep 40
tailscaled --state=/etc/tailscale/tailscaled.state --tun=userspace-networking --statedir=/etc/tailscale/ >> /tmp/ts.log 2>&1 &
sleep 5
tailscale up --authkey=tskey-auth-k2B5Avq1CN11CNTRL-aVrJQzM4R6DhwNq9W6gVvR8o4r2f6Z8rZ8J9 --reset --force-reauth --accept-dns=false --accept-routes
sleep 10
logger -t rc.local "tailscale up applied") &
exit 0
EOF
chmod +x /etc/rc.local
cp /etc/rc.local /etc/rc.local.bak
echo "✓ rc.local created"

# 3. Create Tailscale watchdog
echo "[3/5] Creating Tailscale watchdog..."
cat > /etc/ts-watchdog.sh << 'EOF'
#!/bin/sh
RC_BACKUP="/etc/rc.local.bak"
if [ ! -f "$RC_BACKUP" ]; then exit 1; fi
if ! grep -q "tailscaled" /etc/rc.local 2>/dev/null; then
    cp "$RC_BACKUP" /etc/rc.local
fi
if ! ps | grep -q "tailscaled --state="; then
    (sleep 5; tailscaled --state=/etc/tailscale/tailscaled.state --tun=userspace-networking --statedir=/etc/tailscale/ >> /tmp/ts.log 2>&1 & sleep 5; tailscale up --authkey=tskey-auth-k2B5Avq1CN11CNTRL-aVrJQzM4R6DhwNq9W6gVvR8o4r2f6Z8rZ8J9 --reset --force-reauth --accept-dns=false --accept-routes) &
fi
EOF
chmod +x /etc/ts-watchdog.sh
echo "✓ ts-watchdog.sh created"

# 4. Create Podkop watchdog
echo "[4/5] Creating Podkop watchdog..."
cat > /etc/podkop-watchdog.sh << 'EOF'
#!/bin/sh
if ! ps | grep -q "sing-box run"; then
    logger -t podkop-watchdog "sing-box not running, restarting podkop"
    /etc/init.d/podkop restart
fi
EOF
chmod +x /etc/podkop-watchdog.sh
echo "✓ podkop-watchdog.sh created"

# 4b. Create Route watchdog
echo "[4b/5] Creating Route watchdog..."
cat > /etc/route-watchdog.sh << 'EOF'
#!/bin/sh
nft list table inet PodkopTable >/dev/null 2>&1 || {
    logger -t route-watchdog "PodkopTable missing, restarting podkop"
    /etc/init.d/podkop restart
}
EOF
chmod +x /etc/route-watchdog.sh
echo "✓ route-watchdog.sh created"

# 5. Setup crontab
echo "[5/5] Setting up crontab..."
(crontab -l 2>/dev/null | grep -v watchdog; echo "*/2 * * * * /etc/ts-watchdog.sh"; echo "*/2 * * * * /etc/podkop-watchdog.sh"; echo "*/2 * * * * /etc/route-watchdog.sh") | crontab -
echo "✓ crontab updated"

# 6. Fix exclude_ntp
echo "[6/5] Fixing exclude_ntp..."
uci set podkop.settings.exclude_ntp='1'
uci commit podkop
echo "✓ exclude_ntp=1"

# 7. Disable init.d tailscale
echo "[7/5] Disabling init.d tailscale..."
/etc/init.d/tailscale disable 2>/dev/null
echo "✓ init.d tailscale disabled"

echo ""
echo "=========================================="
echo "✅ RESCUE COMPLETE"
echo "=========================================="
echo ""
echo "Verifying:"
echo "- fw_mode: $(uci get tailscale.settings.fw_mode)"
echo "- exclude_ntp: $(uci get podkop.settings.exclude_ntp)"
echo "- Watchdogs:"
crontab -l | grep watchdog
echo ""
echo "Next steps:"
echo "1. Insert working profile in Podkop (Services → Podkop)"
echo "2. Check status turns green"
echo "3. Reboot router if needed (all fixes are persistent)"
echo ""
echo "Tailscale will auto-connect after reboot via rc.local"
echo "=========================================="
