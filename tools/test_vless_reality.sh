#!/bin/bash
# test_vless_reality.sh — тест VLESS Reality ключа через sing-box
# Использует sing-box как на роутере, а не OpenSSL
#
# Usage: ./test_vless_reality.sh <vless_url>
#   ./test_vless_reality.sh "vless://uuid@host:port?..."
#
# Требует: sing-box установлен локально (brew install sing-box)
# или использует ssh на роутер для теста

set -euo pipefail

VLESS_URL="${1:-}"
if [ -z "$VLESS_URL" ]; then
    echo "Usage: $0 <vless_url>"
    echo "  ./test_vless_reality.sh \"vless://uuid@host:port?...\""
    exit 1
fi

# Парсим URL
UUID=$(echo "$VLESS_URL" | sed 's|vless://\([^@]*\)@.*|\1|')
HOST=$(echo "$VLESS_URL" | sed 's|vless://[^@]*@\([^:]*\):.*|\1|')
PORT=$(echo "$VLESS_URL" | sed 's|vless://[^@]*@[^:]*:\([0-9]*\)?.*|\1|')
PBK=$(echo "$VLESS_URL" | grep -oP 'pbk=\K[^&]+')
SID=$(echo "$VLESS_URL" | grep -oP 'sid=\K[^&]+')
SNI=$(echo "$VLESS_URL" | grep -oP 'sni=\K[^&]+')

echo "=== VLESS Reality Test ==="
echo "UUID: $UUID"
echo "Host: $HOST:$PORT"
echo "PBK:  $PBK"
echo "SID:  $SID"
echo "SNI:  $SNI"
echo ""

# Проверка 1: TCP
echo "── [1/4] TCP check ──"
if timeout 5 bash -c "echo > /dev/tcp/$HOST/$PORT" 2>/dev/null; then
    echo "  ✅ TCP: port $PORT open"
else
    echo "  ❌ TCP: port $PORT unreachable"
    exit 1
fi

# Проверка 2: TLS handshake с правильным SNI
echo ""
echo "── [2/4] TLS handshake ──"
TLS_OUT=$(echo | timeout 5 openssl s_client -connect "$HOST:$PORT" -servername "$SNI" 2>&1 || true)
if echo "$TLS_OUT" | grep -q "CONNECTED"; then
    CERT_CN=$(echo "$TLS_OUT" | grep -oP 'subject=.*?CN\s*=\s*\K[^\n,/\\]+' | head -1)
    echo "  ✅ TLS: handshake OK (CN: ${CERT_CN:-unknown})"
else
    echo "  ❌ TLS: handshake failed"
    echo "$TLS_OUT" | tail -3
    exit 1
fi

# Проверка 3: Reality через sing-box (если установлен)
echo ""
echo "── [3/4] Reality check ──"
if command -v sing-box &>/dev/null; then
    TMPDIR=$(mktemp -d)
    cat > "$TMPDIR/config.json" << EOF
{
  "log": { "level": "error" },
  "dns": { "servers": [{"tag": "dns", "address": "1.1.1.1"}] },
  "inbounds": [{
    "type": "direct",
    "tag": "test-in",
    "listen": "127.0.0.1",
    "listen_port": 10800
  }],
  "outbounds": [{
    "type": "vless",
    "tag": "test-out",
    "server": "$HOST",
    "server_port": $PORT,
    "uuid": "$UUID",
    "flow": "",
    "tls": {
      "enabled": true,
      "server_name": "$SNI",
      "utls": { "enabled": true, "fingerprint": "chrome" },
      "reality": {
        "enabled": true,
        "public_key": "$PBK",
        "short_id": "$SID"
      }
    },
    "multiplex": {
      "enabled": false
    }
  }],
  "route": {
    "rules": [{"outbound": "test-out"}]
  }
}
EOF
    echo "  Testing Reality connection via sing-box..."
    timeout 10 sing-box check -c "$TMPDIR/config.json" 2>&1 && echo "  ✅ Config valid" || echo "  ⚠️ Config check issue"
    
    # Запускаем sing-box на 3 секунды и проверяем ошибки
    timeout 5 sing-box run -c "$TMPDIR/config.json" -D "$TMPDIR" 2>&1 | head -20 || true
    
    # Проверяем логи на ошибки Reality
    if [ -f "$TMPDIR/error.log" ]; then
        if grep -qi "reality" "$TMPDIR/error.log"; then
            echo "  ❌ Reality: verification failed!"
            grep -i "reality" "$TMPDIR/error.log"
        fi
    fi
    
    rm -rf "$TMPDIR"
else
    echo "  ⚠️ sing-box not installed locally"
    echo "  Install: brew install sing-box"
    echo "  Or test via router SSH"
fi

# Проверка 4: curl через proxy (если sing-box запущен)
echo ""
echo "── [4/4] curl test ──"
echo "  To test: start sing-box, then:"
echo "    curl -x socks5://127.0.0.1:10800 https://cloudflare.com/cdn-cgi/trace"
echo ""

echo "=== Done ==="
