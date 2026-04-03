#!/bin/sh
# Tailscale setup for Cudy WR3000H on OpenWrt 25.12 (apk)
# Repo: https://github.com/vasneverov/openwrt-scripts

set -e

echo "==> [1/9] Adding Gunanovo repository key..."
wget -O /etc/apk/keys/gunanovo@github.io.pub \
  https://gunanovo.github.io/openwrt-tailscale/key-build.rsa.pub

echo "==> [2/9] Adding Tailscale repository..."
echo "https://gunanovo.github.io/openwrt-tailscale/$(cat /etc/apk/arch)/packages.adb" \
  >> /etc/apk/repositories.d/customfeeds.list

echo "==> [3/9] Updating package index..."
apk update

echo "==> [4/9] Installing tailscale, iptables, ip6tables..."
apk add tailscale iptables ip6tables

echo "==> [5/9] Setting fw_mode to nftables..."
uci set tailscale.settings.fw_mode='nftables'
uci commit tailscale

echo "==> [6/9] Writing /etc/rc.local..."
cat > /etc/rc.local << 'RCEOF'
#!/bin/sh
(sleep 15
tailscale serve --bg --tcp 80 tcp://localhost:80
tailscale serve --bg --tcp 22 tcp://localhost:22
tailscale serve --bg --tcp 443 tcp://localhost:443) &
exit 0
RCEOF

echo "==> [7/9] chmod +x /etc/rc.local..."
chmod +x /etc/rc.local

echo "==> [8/9] Enabling and restarting tailscale..."
/etc/init.d/tailscale enable
/etc/init.d/tailscale restart

echo "==> [9/9] Waiting 5s, then running tailscale up..."
sleep 5
tailscale up --accept-dns=false --accept-routes

echo ""
echo "Done! Tailscale is configured and running."
