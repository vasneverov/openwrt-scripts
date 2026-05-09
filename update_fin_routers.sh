#!/bin/bash
# Обновляет Finland proxy_string на всех онлайн-роутерах

NEW_PBK="P4Sgrnue93n5EMGm_eQITiGhIUmCRWozPgGvm0P_NUU"
NEW_SID="f9d5b916"
RELAY_IP="5.35.84.151"
PORT="4190"
SSH_PASS="56756789"
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=8 -o PreferredAuthentications=password -o PubkeyAuthentication=no"

# IP|NAME пары
ROUTERS=(
  "100.90.90.89|tr56-01"
  "100.76.46.100|tr56-03"
  "100.99.249.51|z56-47"
  "100.77.107.55|z56-48"
  "100.100.29.16|z56-49"
  "100.76.47.77|z56-50"
  "100.99.179.1|z56-51"
  "100.105.115.52|z56-53"
  "100.108.19.117|z56-55"
  "100.89.162.72|z56-56"
  "100.105.207.78|z56-57"
  "100.67.244.64|z56-58"
  "100.85.219.70|z56-59"
  "100.100.235.94|z56-61"
  "100.109.58.91|z56-62"
  "100.72.239.25|z56-64"
  "100.93.208.96|z56-67"
  "100.97.48.79|z56-71"
  "100.79.200.8|z56-72"
  "100.70.111.10|z56-74"
  "100.108.160.54|z56-76"
  "100.110.49.100|z56-79"
  "100.104.77.100|z56-81"
  "100.88.231.2|z56-83"
  "100.79.216.88|z56-85"
  "100.105.78.4|z56-87"
  "100.95.193.21|z56-89"
  "100.113.155.97|z56-90"
  "100.125.186.51|z56-91"
  "100.106.95.11|z56-94"
  "100.100.61.75|z56-97"
  "100.108.28.93|z56-101"
  "100.125.3.5|z56-105"
  "100.68.141.32|z56-110"
  "100.79.169.64|z56-113"
  "100.87.130.63|z56-114"
  "100.119.177.78|z56-115"
)

UUIDS_FILE="/tmp/fin_router_uuids.txt"
> "$UUIDS_FILE"

echo "=== Сбор UUID и обновление proxy_string ==="
echo ""

for ENTRY in "${ROUTERS[@]}"; do
  IP="${ENTRY%%|*}"
  NAME="${ENTRY##*|}"

  CURRENT=$(sshpass -p "$SSH_PASS" ssh $SSH_OPTS root@$IP \
    "grep proxy_string /etc/config/podkop | grep -E '4190|5alNn1i1'" 2>/dev/null | head -1)

  if [ -z "$CURRENT" ]; then
    echo "❌ $NAME ($IP): нет Finland конфига — пропуск"
    continue
  fi

  UUID=$(echo "$CURRENT" | grep -oE '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')

  if [ -z "$UUID" ]; then
    echo "❌ $NAME ($IP): UUID не найден"
    continue
  fi

  echo "$NAME $UUID" >> "$UUIDS_FILE"

  LABEL="${NAME}_fin2"
  NEW_PROXY="vless://${UUID}@${RELAY_IP}:${PORT}?type=grpc&security=reality&mode=gun&serviceName=&pbk=${NEW_PBK}&sid=${NEW_SID}&sni=www.apple.com&fp=chrome&spx=%2F#${LABEL}"

  RESULT=$(sshpass -p "$SSH_PASS" ssh $SSH_OPTS root@$IP "
    uci set podkop.main.proxy_string='$NEW_PROXY'
    uci commit podkop
    /etc/init.d/podkop restart >/dev/null 2>&1
    echo OK
  " 2>/dev/null)

  if [ "$RESULT" = "OK" ]; then
    echo "✅ $NAME ($IP): UUID=$UUID"
  else
    echo "⚠️  $NAME ($IP): UUID=$UUID — ошибка"
  fi
done

echo ""
echo "=== UUID для добавления в Finland панель ==="
cat "$UUIDS_FILE"
echo ""
echo "Всего: $(wc -l < $UUIDS_FILE)"
