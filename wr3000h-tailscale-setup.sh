#!/bin/sh
# Tailscale setup for Cudy WR3000H on OpenWrt 25.12 (apk)
# Repo: https://github.com/vasneverov/openwrt-scripts

set -e

echo "==> [1/10] Adding Gunanovo repository key..."
wget -O /etc/apk/keys/gunanovo@github.io.pub \
  https://gunanovo.github.io/openwrt-tailscale/key-build.rsa.pub

echo "==> [2/10] Adding Tailscale repository..."
echo "https://gunanovo.github.io/openwrt-tailscale/$(cat /etc/apk/arch)/packages.adb" \
  >> /etc/apk/repositories.d/customfeeds.list

echo "==> [3/10] Updating package index..."
apk update

echo "==> [4/10] Installing tailscale, iptables, ip6tables..."
apk add tailscale iptables ip6tables
killall tailscaled 2>/dev/null; sleep 2

echo "==> [5/10] Setting fw_mode to nftables..."
uci set tailscale.settings.fw_mode='nftables'
uci commit tailscale

echo "==> [6/10] Writing /etc/rc.local..."
cat > /etc/rc.local << 'RCEOF'
#!/bin/sh
(sleep 10
tailscale serve --bg --tcp 80  tcp://localhost:80
tailscale serve --bg --tcp 22  tcp://localhost:22
tailscale serve --bg --tcp 443 tcp://localhost:443) &
exit 0
RCEOF
chmod +x /etc/rc.local

echo "==> [7/10] Enabling tailscale autostart..."
/etc/init.d/tailscale enable

echo "==> [8/10] Starting tailscaled daemon..."
tailscaled --state=/var/lib/tailscale/tailscaled.state \
           --socket=/var/run/tailscale/tailscaled.sock &
sleep 3

echo "==> [9/10] Configuring serve ports..."
tailscale serve --bg --tcp 80  tcp://localhost:80
tailscale serve --bg --tcp 443 tcp://localhost:443
tailscale serve --bg --tcp 22  tcp://localhost:22

echo "==> [10/10] Authenticating (open the link in browser)..."
tailscale up --accept-dns=false --accept-routes --reset

echo ""
tailscale serve status
echo ""
echo "Done! Tailscale is configured and running."
