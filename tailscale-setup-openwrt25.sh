#!/bin/sh

wget -O /etc/apk/keys/gunanovo@github.io.pub https://gunanovo.github.io/openwrt-tailscale/key-build.rsa.pub
echo "https://gunanovo.github.io/openwrt-tailscale/$(cat /etc/apk/arch)/packages.adb" >> /etc/apk/repositories.d/customfeeds.list
apk update
apk add tailscale iptables ip6tables
pkill -f tailscaled 2>/dev/null; sleep 1

uci set tailscale.settings.fw_mode='nftables'
uci commit tailscale

/etc/init.d/tailscale enable
/etc/init.d/tailscale stop 2>/dev/null
tailscaled --state=/var/lib/tailscale/tailscaled.state \
           --socket=/var/run/tailscale/tailscaled.sock &
sleep 3

cat >/etc/rc.local <<'EOF'
#!/bin/sh
(sleep 10
tailscale serve --bg --tcp 80  tcp://localhost:80
tailscale serve --bg --tcp 22  tcp://localhost:22
tailscale serve --bg --tcp 443 tcp://localhost:443) &
exit 0
EOF
chmod +x /etc/rc.local

tailscale serve --bg --tcp 80  tcp://localhost:80
tailscale serve --bg --tcp 443 tcp://localhost:443
tailscale serve --bg --tcp 22  tcp://localhost:22
tailscale up --accept-dns=false --accept-routes --reset
tailscale serve status
