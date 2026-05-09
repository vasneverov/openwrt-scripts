# Универсальный скилл: Прошивка любого роутера OpenWrt

> **Автоопределение модели + live-лог в чат + итоговая таблица**
> Последнее обновление: 2026-05-08

---

## 1. Таблица роутеров

| Модель | Кодовое имя | Архитектура | Flash | Прошивка | Шаблон | Sing-box | Tailscale | Hostname |
|--------|-------------|-------------|-------|----------|--------|----------|-----------|----------|
| **Xiaomi AX3000T** | `xiaomi_mi-router-ax3000t` | aarch64_cortex-a53 | 128MB | `openwrt-25.12.2-mediatek-filogic-xiaomi_mi-router-ax3000t-squashfs-sysupgrade.bin` | `backup-ax3000t-template.tar.gz` | **толстый** (`sing-box`) | **толстый** (gunano) | `z56-NNN` |
| **Cudy M3000 v1** | `cudy_m3000-v1` | aarch64_cortex-a53 | 128MB | `openwrt-25.12.0-mediatek-filogic-cudy_m3000-v1-squashfs-sysupgrade.bin` | `backup-m3000-template.tar.gz` | **толстый** (`sing-box`) | **толстый** (gunano) | `z56-NNN` |
| **Cudy M3000 v2** | `cudy_m3000-v1` (force) | aarch64_cortex-a53 | 128MB | `openwrt-25.12.0-mediatek-filogic-cudy_m3000-v1-squashfs-sysupgrade.bin` (с `-F`) | `backup-m3000-template.tar.gz` | **толстый** (`sing-box`) | **толстый** (gunano) | `z56-NNN` |
| **Cudy WR3000H v1** | `cudy_wr3000h-v1` | aarch64_cortex-a53 | 128MB | `openwrt-25.12.0-mediatek-filogic-cudy_wr3000h-v1-squashfs-sysupgrade.bin` | `backup-wr3000h-template.tar.gz` | **толстый** (`sing-box`) | **UPX** (gunano) | `z56-NNN` |
| **Cudy WR3000S v1** | `cudy_wr3000s-v1` | aarch64_cortex-a53 | 128MB | `openwrt-25.12.0-mediatek-filogic-cudy_wr3000s-v1-squashfs-sysupgrade.bin` | `backup-wr3000s-template.tar.gz` | **толстый** (`sing-box`) | **UPX** (gunano) | `z56-NNN` |
| **Cudy TR3000 v1** | `cudy_tr3000-v1` | aarch64_cortex-a53 | 128MB | `openwrt-25.12.0-mediatek-filogic-cudy_tr3000-v1-squashfs-sysupgrade.bin` | `backup-tr3000-template.tar.gz` | **толстый** (`sing-box`) | **UPX** (gunano) | `z56-NNN` |

### 1.1 Пути к файлам

| Модель | Прошивка | Шаблон |
|--------|----------|--------|
| Xiaomi AX3000T | `~/Downloads/AX3000T/openwrt-25.12.2-mediatek-filogic-xiaomi_mi-router-ax3000t-squashfs-sysupgrade.bin` | `~/Downloads/AX3000T/backup-ax3000t-template.tar.gz` |
| Cudy M3000 | `~/Downloads/M3000/openwrt-25.12.0-mediatek-filogic-cudy_m3000-v1-squashfs-sysupgrade.bin` | `~/Downloads/M3000/backup-m3000-template.tar.gz` |
| Cudy WR3000H | `~/Downloads/WR3000H/openwrt-25.12.0-ramips-mt7628-cudy_wr3000h-v1-squashfs-sysupgrade.bin` | `~/Downloads/WR3000H/backup-wr3000h-template.tar.gz` |
| Cudy WR3000S | `~/Downloads/WR3000S V1/openwrt-25.12.0-ramips-mt7628-cudy_wr3000s-v1-squashfs-sysupgrade.bin` | `~/Downloads/WR3000S V1/backup-wr3000s-template.tar.gz` |

---

## 2. Алгоритм (12 шагов)

### Шаг 0: Подключение + автоопределение модели

```bash
# Подключиться кабелем к LAN порту
# Убедиться что IP 192.168.1.1 доступен
ping -c 2 -W 2 192.168.1.1

# Определить модель
MODEL=$(ssh -o StrictHostKeyChecking=no root@192.168.1.1 "cat /tmp/sysinfo/model" 2>/dev/null)
echo "Модель: $MODEL"

# Определить архитектуру
ARCH=$(ssh -o StrictHostKeyChecking=no root@192.168.1.1 "opkg print-architecture | head -1 | awk '{print \$2}'" 2>/dev/null)
echo "Архитектура: $ARCH"

# Определить версию OpenWrt
VER=$(ssh -o StrictHostKeyChecking=no root@192.168.1.1 "cat /etc/openwrt_release | grep RELEASE" 2>/dev/null)
echo "Версия: $VER"
```

**Автоопределение конфигурации:**
```bash
# По модели выбираем параметры
case "$MODEL" in
  *"AX3000T"*|*"AX334T"*)
    ROUTER_TYPE="xiaomi_ax3000t"
    FIRMWARE="$HOME/Downloads/AX3000T/openwrt-25.12.2-mediatek-filogic-xiaomi_mi-router-ax3000t-squashfs-sysupgrade.bin"
    TEMPLATE="$HOME/Downloads/AX3000T/backup-ax3000t-template.tar.gz"
    SING_BOX="sing-box"          # толстый
    TAILSCALE_TYPE="full"        # толстый
    ;;
  *"M3000"*)
    ROUTER_TYPE="cudy_m3000"
    FIRMWARE="$HOME/Downloads/M3000/openwrt-25.12.0-mediatek-filogic-cudy_m3000-v1-squashfs-sysupgrade.bin"
    TEMPLATE="$HOME/Downloads/M3000/backup-m3000-template.tar.gz"
    SING_BOX="sing-box"          # толстый
    TAILSCALE_TYPE="full"        # толстый
    ;;
  *"WR3000H"*)
    ROUTER_TYPE="cudy_wr3000h"
    FIRMWARE="$HOME/Downloads/WR3000H/openwrt-25.12.0-ramips-mt7628-cudy_wr3000h-v1-squashfs-sysupgrade.bin"
    TEMPLATE="$HOME/Downloads/WR3000H/backup-wr3000h-template.tar.gz"
    SING_BOX="sing-box-tiny"     # тонкий UPX
    TAILSCALE_TYPE="upx"         # UPX
    ;;
  *"WR3000S"*)
    ROUTER_TYPE="cudy_wr3000s"
    FIRMWARE="$HOME/Downloads/WR3000S V1/openwrt-25.12.0-ramips-mt7628-cudy_wr3000s-v1-squashfs-sysupgrade.bin"
    TEMPLATE="$HOME/Downloads/WR3000S V1/backup-wr3000s-template.tar.gz"
    SING_BOX="sing-box-tiny"     # тонкий UPX
    TAILSCALE_TYPE="upx"         # UPX
    ;;
  *)
    echo "❌ Неизвестная модель: $MODEL"
    exit 1
    ;;
esac
```

### Шаг 1: Заливка OpenWrt

```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 1: Заливка OpenWrt"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP1_START=$(date +%s)

# Скопировать прошивку
scp -O -o StrictHostKeyChecking=no "$FIRMWARE" root@192.168.1.1:/tmp/firmware.bin

# Прошить
ssh -o StrictHostKeyChecking=no root@192.168.1.1 "sysupgrade -n /tmp/firmware.bin"

# ⏱ ЖИВОЙ МОНИТОРИНГ: ждём пока роутер поднимется на 192.168.1.1
echo "⏳ Ожидание перезагрузки на 192.168.1.1..."
WAIT_START=$(date +%s)
while true; do
  if ping -c 1 -W 1 192.168.1.1 >/dev/null 2>&1; then
    echo "  ✅ Роутер поднялся через $(($(date +%s)-WAIT_START)) сек"
    break
  fi
  if [ $(($(date +%s)-WAIT_START)) -gt 180 ]; then
    echo "  ❌ Таймаут! Роутер не поднялся за 180 сек"
    exit 1
  fi
  sleep 2
done

ssh-keygen -R 192.168.1.1 2>/dev/null

STEP1_TIME=$(($(date +%s)-STEP1_START))
echo "  ⏱ $STEP1_TIME сек"

# 🔍 ПРОВЕРКА WAN
echo "  🔍 Проверка WAN..."
ssh -o StrictHostKeyChecking=no root@192.168.1.1 "
WAN_IP=\$(ubus call network.interface.wan status 2>/dev/null | grep '\"address\"' | head -1 | grep -oP '\d+\.\d+\.\d+\.\d+')
PING_DNS=\$(ping -c 2 -W 3 1.1.1.1 2>&1 | grep -oP '\d+% packet loss')
PING_GOOGLE=\$(ping -c 2 -W 3 google.com 2>&1 | grep -oP '\d+% packet loss')
echo \"  WAN IP: \${WAN_IP:-❌ НЕТ IP}\"
echo \"  Пинг 1.1.1.1: \${PING_DNS:-❌}\"
echo \"  Пинг google.com: \${PING_GOOGLE:-❌}\"
"
```

### Шаг 2: Создание backup-шаблона (если нет)

```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 2: Создание backup-шаблона"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP2_START=$(date +%s)

if [ ! -f "$TEMPLATE" ]; then
  ssh -o StrictHostKeyChecking=no root@192.168.1.1 "
  uci set system.@system[0].hostname='${ROUTER_TYPE^^}-TEMPLATE'
  uci set system.@system[0].timezone='MSK-3'
  uci set system.@system[0].zonename='Europe/Moscow'
  uci set wireless.radio0.country='PA'
  uci commit
  passwd root  # пароль: 56756789
  sysupgrade -b /tmp/backup-template.tar.gz
  "
  scp -O -o StrictHostKeyChecking=no root@192.168.1.1:/tmp/backup-template.tar.gz "$TEMPLATE"
  echo "  ✅ Шаблон создан: $TEMPLATE"
else
  echo "  ✅ Шаблон уже есть: $TEMPLATE"
fi

STEP2_TIME=$(($(date +%s)-STEP2_START))
echo "  ⏱ $STEP2_TIME сек"
```

### Шаг 3: Применить шаблон + hostname

```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 3: Применить шаблон + hostname"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP3_START=$(date +%s)

# Скопировать шаблон
scp -O -o StrictHostKeyChecking=no "$TEMPLATE" root@192.168.1.1:/tmp/backup.tar.gz

# Применить
ssh -o StrictHostKeyChecking=no root@192.168.1.1 "
cd / && tar xzf /tmp/backup.tar.gz
uci set system.@system[0].hostname='<ROUTER_NAME>'
uci commit system
echo '<ROUTER_NAME>' > /proc/sys/kernel/hostname
reboot
"

# ⏱ ЖИВОЙ МОНИТОРИНГ: ждём пока роутер перезагрузится на 192.168.5.1
echo "⏳ Ожидание перезагрузки на 192.168.5.1..."
WAIT_START=$(date +%s)
while true; do
  if ping -c 1 -W 1 192.168.5.1 >/dev/null 2>&1; then
    echo "  ✅ Роутер поднялся на 192.168.5.1 через $(($(date +%s)-WAIT_START)) сек"
    break
  fi
  if [ $(($(date +%s)-WAIT_START)) -gt 90 ]; then
    echo "  ❌ Таймаут! Роутер не поднялся за 90 сек"
    exit 1
  fi
  sleep 2
done

ssh-keygen -R 192.168.5.1 2>/dev/null
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "echo OK"

STEP3_TIME=$(($(date +%s)-STEP3_START))
echo "  ⏱ $STEP3_TIME сек"

# 🔍 ПРОВЕРКА WAN
echo "  🔍 Проверка WAN..."
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
WAN_IP=\$(ubus call network.interface.wan status 2>/dev/null | grep '\"address\"' | head -1 | grep -oP '\d+\.\d+\.\d+\.\d+')
PING_DNS=\$(ping -c 2 -W 3 1.1.1.1 2>&1 | grep -oP '\d+% packet loss')
PING_GOOGLE=\$(ping -c 2 -W 3 google.com 2>&1 | grep -oP '\d+% packet loss')
echo \"  WAN IP: \${WAN_IP:-❌ НЕТ IP}\"
echo \"  Пинг 1.1.1.1: \${PING_DNS:-❌}\"
echo \"  Пинг google.com: \${PING_GOOGLE:-❌}\"
"
```

### Шаг 4: Создать ключ main (через relay)

```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 4: Создать ключ main"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP4_START=$(date +%s)

# Вызвать скилл create_clone_key.md
# Для AX3000T/M3000: bSPB:8448 → CZ2
# Для WR3000H/S: bSPB:4191 → Fin3 (или bMSK:5223 → Fin4)

python3 /Users/vas/CLAUDECODE/tools/create_vless_key.py \
  --router <ROUTER_NAME> \
  --panel-ip <PANEL_IP> \
  --panel-port 5050 \
  --inbound-id <INBOUND_ID> \
  --relay-ip <RELAY_IP> \
  --relay-port <RELAY_PORT> \
  --pbk <PBK> \
  --sid <SID>

# Проверить ключ
python3 /Users/vas/CLAUDECODE/check_vless.py "vless://<NEW_UUID>@..."
# Должен быть: TCP OK + TLS OK → READY

STEP4_TIME=$(($(date +%s)-STEP4_START))
echo "  ⏱ $STEP4_TIME сек"
echo "  ✅ Ключ READY"
```

### Шаг 5: Установка Podkop

```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 5: Установка Podkop"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP5_START=$(date +%s)

echo "  📦 Модель: $ROUTER_TYPE"
echo "  📦 Sing-box: $SING_BOX ($([ "$SING_BOX" = "sing-box" ] && echo 'толстый' || echo 'тонкий UPX'))"

sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
# Установка podkop из itdoginfo
# Ответы: 'y' на всё, язык — русский (ru)
printf 'y\ny\nru\n' | sh <(wget -O - https://raw.githubusercontent.com/itdoginfo/podkop/refs/heads/main/install.sh)
"

STEP5_TIME=$(($(date +%s)-STEP5_START))
echo "  ⏱ $STEP5_TIME сек"

# 🔍 ПРОВЕРКА WAN
echo "  🔍 Проверка WAN..."
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
WAN_IP=\$(ubus call network.interface.wan status 2>/dev/null | grep '\"address\"' | head -1 | grep -oP '\d+\.\d+\.\d+\.\d+')
PING_DNS=\$(ping -c 2 -W 3 1.1.1.1 2>&1 | grep -oP '\d+% packet loss')
PING_GOOGLE=\$(ping -c 2 -W 3 google.com 2>&1 | grep -oP '\d+% packet loss')
echo \"  WAN IP: \${WAN_IP:-❌ НЕТ IP}\"
echo \"  Пинг 1.1.1.1: \${PING_DNS:-❌}\"
echo \"  Пинг google.com: \${PING_GOOGLE:-❌}\"
"
```

### Шаг 6: Настройка Podkop

```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 6: Настройка Podkop"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP6_START=$(date +%s)

sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
# Timezone
uci set system.@system[0].timezone='MSK-3'
uci set system.@system[0].zonename='Europe/Moscow'
uci commit system
/etc/init.d/sysntpd restart

# Podkop settings
uci set podkop.settings.dns_server='1.1.1.1'
uci set podkop.settings.bootstrap_dns_server='1.1.1.1'
uci set podkop.settings.dns_type='udp'
uci set podkop.settings.update_interval='3h'
uci set podkop.settings.exclude_ntp='1'
uci set podkop.settings.disable_quic='1'
uci set podkop.settings.download_lists_via_proxy='0'
uci set podkop.settings.download_community_lists_via_proxy='0'
uci set podkop.settings.enable_output_network_interface='1'

# Community lists — порядок: telegram, meta, youtube, потом остальные
uci del podkop.main.community_lists 2>/dev/null || true
uci add_list podkop.main.community_lists='telegram'
uci add_list podkop.main.community_lists='meta'
uci add_list podkop.main.community_lists='youtube'
for l in geoblock block porn news anime discord twitter hdrezka tiktok cloudflare google_ai google_play hodca roblox hetzner ovh digitalocean cloudfront; do
  uci add_list podkop.main.community_lists=\"\$l\"
done

# Main proxy
uci set podkop.main.proxy_string='<VLESS_MAIN_KEY>'
uci set podkop.main.proxy_config_type='url'
uci set podkop.main.mixed_proxy_enabled='0'

uci commit podkop
/etc/init.d/podkop restart
"

STEP6_TIME=$(($(date +%s)-STEP6_START))
echo "  ⏱ $STEP6_TIME сек"

# 🔍 ПРОВЕРКА WAN
echo "  🔍 Проверка WAN..."
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
WAN_IP=\$(ubus call network.interface.wan status 2>/dev/null | grep '\"address\"' | head -1 | grep -oP '\d+\.\d+\.\d+\.\d+')
PING_DNS=\$(ping -c 2 -W 3 1.1.1.1 2>&1 | grep -oP '\d+% packet loss')
PING_GOOGLE=\$(ping -c 2 -W 3 google.com 2>&1 | grep -oP '\d+% packet loss')
echo \"  WAN IP: \${WAN_IP:-❌ НЕТ IP}\"
echo \"  Пинг 1.1.1.1: \${PING_DNS:-❌}\"
echo \"  Пинг google.com: \${PING_GOOGLE:-❌}\"
"
```

### Шаг 7: Установка Tailscale (из gunano)

```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 7: Установка Tailscale"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP7_START=$(date +%s)

echo "  📦 Тип: $TAILSCALE_TYPE ($([ "$TAILSCALE_TYPE" = "full" ] && echo 'толстый' || echo 'UPX-сжатый'))"
echo "  📦 Репозиторий: gunano (автоопределение архитектуры)"

sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
# ===== Установка Tailscale из репозитория gunano =====
# Репозиторий сам определяет архитектуру и выбирает толстую/UPX версию

# Очистить дублирующиеся записи
grep -v 'openwrt-tailscale' /etc/opkg/customfeeds.conf > /tmp/feeds.tmp 2>/dev/null
mv /tmp/feeds.tmp /etc/opkg/customfeeds.conf 2>/dev/null

# Добавить ключ репозитория
wget -O /tmp/key-build.pub https://gunanovo.github.io/openwrt-tailscale/key-build.pub 2>/dev/null
opkg-key add /tmp/key-build.pub 2>/dev/null
rm /tmp/key-build.pub 2>/dev/null

# Добавить репозиторий с автоопределением архитектуры
echo \"src/gz openwrt-tailscale https://gunanovo.github.io/openwrt-tailscale/\$(opkg print-architecture | awk 'NF==3 && \\\$3~/^[0-9]+\$/ {print \\\$2}' | tail -1)\" >> /etc/opkg/customfeeds.conf

# Обновить и установить
opkg update
opkg install tailscale

# Фикс для OpenWrt 25.12
sed -i 's|--statedir=/var/lib/tailscale ||g' /etc/init.d/tailscale
sed -i 's|TS_DEBUG_FIREWALL_MODE=\"none\"|TS_DEBUG_FIREWALL_MODE=\"\$fw_mode\"|g' /etc/init.d/tailscale

# Настройка
uci set tailscale.settings.fw_mode='none'
uci set tailscale.settings.state_file='/etc/tailscale/tailscaled.state'
uci set tailscale.settings.autoupdate='false'
uci commit tailscale
mkdir -p /etc/tailscale

# Отключаем init.d (будет через rc.local)
/etc/init.d/tailscale disable
"

STEP7_TIME=$(($(date +%s)-STEP7_START))
echo "  ⏱ $STEP7_TIME сек"
```

### Шаг 8: Спасительные скрипты

```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 8: Спасительные скрипты"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP8_START=$(date +%s)

sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
# ===== 8a. rc.local =====
cat > /etc/rc.local << 'EOF'
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
cp /etc/rc.local /etc/rc.local.bak

# ===== 8b. Firewall — tailscale0 в LAN =====
uci set firewall.@zone[0].device='br-lan tailscale0'
uci commit firewall

# ===== 8c. WAN ifname =====
WAN_IFNAME=\$(uci get network.wan.ifname 2>/dev/null)
if [ -z \"\$WAN_IFNAME\" ]; then
    WAN_DEVICE=\$(uci get network.wan.device 2>/dev/null)
    if [ -n \"\$WAN_DEVICE\" ]; then
        uci set network.wan.ifname=\"\$WAN_DEVICE\"
        uci commit network
    fi
fi

# ===== 8d. Tailscale watchdog =====
cat > /etc/ts-watchdog.sh << 'WEOF'
#!/bin/sh
RC_BACKUP='/etc/rc.local.bak'
[ -f \"\$RC_BACKUP\" ] || exit 1
grep -q 'tailscaled' /etc/rc.local 2>/dev/null || cp \"\$RC_BACKUP\" /etc/rc.local
ps | grep -q 'tailscaled --statedir=' || {
  logger -t ts-watchdog 'tailscaled не найден, перезапуск'
  (sleep 5; tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking >> /tmp/ts.log 2>&1 &
   sleep 5; tailscale up --accept-dns=false --accept-routes) &
}
WEOF
chmod +x /etc/ts-watchdog.sh

# ===== 8e. Podkop watchdog =====
cat > /etc/podkop-watchdog.sh << 'PEOF'
#!/bin/sh
if ! ps | grep -q 'sing-box run'; then
    logger -t podkop-watchdog 'sing-box not running, restarting podkop'
    /etc/init.d/podkop restart
fi
PEOF
chmod +x /etc/podkop-watchdog.sh

# ===== 8f. Route watchdog =====
cat > /etc/route-watchdog.sh << 'REOF'
#!/bin/sh
nft list table inet PodkopTable >/dev/null 2>&1 || {
    logger -t route-watchdog 'PodkopTable missing, restarting podkop'
    /etc/init.d/podkop restart
}
REOF
chmod +x /etc/route-watchdog.sh

# ===== 8g. Crontab =====
(crontab -l 2>/dev/null | grep -v -E '(ts-watchdog|podkop-watchdog|route-watchdog|list_update)'
 echo '*/2 * * * * /etc/ts-watchdog.sh'
 echo '*/2 * * * * /etc/podkop-watchdog.sh'
 echo '*/2 * * * * /etc/route-watchdog.sh'
 echo '13 */3 * * * /usr/bin/podkop list_update'
) | crontab -

# ===== 8h. check-ip скрипт =====
cat > /usr/bin/check-ip << 'CIPEOF'
#!/bin/sh
echo '╔══════════════════════════════════════════════╗'
echo '║              CHECK-IP                        ║'
echo '╚══════════════════════════════════════════════╝'
echo ''
echo '=== ЧЕРЕЗ ПРОКСИ ==='
curl -s --connect-timeout 5 --max-time 10 https://cloudflare.com/cdn-cgi/trace 2>/dev/null | grep -E 'ip=|loc='
echo ''
echo '=== НАПРЯМУЮ ==='
curl -s --connect-timeout 5 --max-time 10 https://ipinfo.io/json 2>/dev/null | grep -E '\"ip\"|\"country\"|\"city\"'
echo ''
echo '=== ТЕСТЫ САЙТОВ ==='
for url in google.com youtube.com telegram.org facebook.com instagram.com rutracker.org tiktok.com x.com discord.com github.com; do
  CODE=\$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 https://\$url 2>/dev/null)
  printf '%-15s %3s\n' \"\$url\" \"\$CODE\"
done
CIPEOF
chmod +x /usr/bin/check-ip

# ===== 8i. Установка podkop-fw4-fix =====
wget -q -O /root/podkop-fw4-fix.sh \
  'https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/tools/podkop-fw4-fix.sh' 2>/dev/null
chmod +x /root/podkop-fw4-fix.sh 2>/dev/null
/root/podkop-fw4-fix.sh install 2>/dev/null || true

# ===== 8j. Установка podkop-fix-lists =====
wget -q -O /root/podkop-fix-lists.sh \
  'https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/tools/podkop-fix-lists.sh' 2>/dev/null
chmod +x /root/podkop-fix-lists.sh 2>/dev/null
sh /root/podkop-fix-lists.sh 2>/dev/null || true
"

STEP8_TIME=$(($(date +%s)-STEP8_START))
echo "  ⏱ $STEP8_TIME сек"

# 🔍 ПРОВЕРКА WAN
echo "  🔍 Проверка WAN..."
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
WAN_IP=\$(ubus call network.interface.wan status 2>/dev/null | grep '\"address\"' | head -1 | grep -oP '\d+\.\d+\.\d+\.\d+')
PING_DNS=\$(ping -c 2 -W 3 1.1.1.1 2>&1 | grep -oP '\d+% packet loss')
PING_GOOGLE=\$(ping -c 2 -W 3 google.com 2>&1 | grep -oP '\d+% packet loss')
echo \"  WAN IP: \${WAN_IP:-❌ НЕТ IP}\"
echo \"  Пинг 1.1.1.1: \${PING_DNS:-❌}\"
echo \"  Пинг google.com: \${PING_GOOGLE:-❌}\"
"
```

### Шаг 9: Запуск Tailscale + авторизация

```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 9: Tailscale авторизация"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP9_START=$(date +%s)

# ⚠️ Проверить что прокси работает
echo "  🔍 Проверка прокси..."
PROXY_LOC=$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 \
  "curl -s --connect-timeout 5 --max-time 10 https://cloudflare.com/cdn-cgi/trace 2>/dev/null | grep 'loc='" 2>/dev/null)
echo "  Прокси: ${PROXY_LOC:-❌ НЕ РАБОТАЕТ}"

# Запустить tailscaled
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking >> /tmp/ts.log 2>&1 &
"
sleep 3

# Получить ссылку авторизации
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
setsid tailscale up --accept-dns=false --accept-routes --reset > /tmp/tsup.log 2>&1 &
"
sleep 6

TS_URL=$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 \
  "grep -o 'https://login.tailscale.com[^ ]*' /tmp/tsup.log 2>/dev/null" | head -1)

echo "🔗 АВТОРИЗУЙ В TAILSCALE (учётка n78rout@gmail.com):"
echo "   $TS_URL"
open "$TS_URL" 2>/dev/null || true

# Ждать авторизации — мониторить каждые 3 секунды
echo "⏳ Ожидание авторизации Tailscale..."
AUTH_START=$(date +%s)
while true; do
  TS_STATUS=$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.5.1 \
    "tailscale status 2>&1 | head -1" 2>/dev/null)
  echo "  [$(($(date +%s)-AUTH_START))c] $TS_STATUS"
  echo "$TS_STATUS" | grep -q "100\." && break
  sleep 3
done

TS_IP=$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 \
  "tailscale status 2>&1 | head -1" | awk '{print $1}')
echo "  ✅ Tailscale авторизован: $TS_IP (за $(($(date +%s)-AUTH_START)) сек)"

# ⚠️ Ожидание зелёной точки
echo "⏳ Ожидание зелёной точки (Tailscale ONLINE)..."
ONLINE_START=$(date +%s)
while true; do
  TS_STATUS=$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.5.1 \
    "tailscale status 2>&1 | head -1" 2>/dev/null)
  STATUS_FIELD=$(echo "$TS_STATUS" | awk '{print $4}')
  echo "  [$(($(date +%s)-ONLINE_START))c] $TS_STATUS"
  [ "$STATUS_FIELD" = "-" ] && break
  sleep 3
done
echo "  ✅ Tailscale ONLINE (зелёная точка) — за $(($(date +%s)-ONLINE_START)) сек"

# Проверить ping по Tailscale
ping -c 2 -W 3 $TS_IP 2>&1 | tail -3

STEP9_TIME=$(($(date +%s)-STEP9_START))
echo "  ⏱ $STEP9_TIME сек"
```

### Шаг 10: Проверка перед ребутом (5 пунктов)

```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 10: Проверка перед ребутом"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP10_START=$(date +%s)

sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
echo 'fw_mode:      ' \$(uci get tailscale.settings.fw_mode)
echo 'init.d:       ' \$(/etc/init.d/tailscale enabled 2>/dev/null && echo ENABLED || echo DISABLED)
echo 'rc.local:     ' \$(grep -q tailscaled /etc/rc.local && echo OK || echo FAIL)
echo 'watchdog:     ' \$(crontab -l | grep -c watchdog)
echo 'exclude_ntp:  ' \$(uci get podkop.settings.exclude_ntp)
echo 'fw4-fix:      ' \$(ls /root/podkop-fw4-fix.sh 2>/dev/null && echo OK || echo FAIL)
echo 'check-ip:     ' \$(which check-ip 2>/dev/null || echo FAIL)
"

STEP10_TIME=$(($(date +%s)-STEP10_START))
echo "  ⏱ $STEP10_TIME сек"
```

### Шаг 11: Ребут + мониторинг

```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 11: Ребут + мониторинг"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP11_START=$(date +%s)

# ⏱ ЗАСЕЧЬ ВРЕМЯ
echo "🕐 РЕБУТ: \$(date +%H:%M:%S)"
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "reboot"

# Ждать 30 сек пока роутер загрузится
sleep 30

# Мониторить каждые 5 секунд
REBOOT_START=$(date +%s)
TS_ONLINE=false
PROXY_ONLINE=false

for i in \$(seq 1 30); do
  NOW=\$(date +%H:%M:%S)
  ELAPSED=\$((\$(date +%s)-REBOOT_START))
  
  PROXY=\$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.5.1 \
    "curl -s --connect-timeout 3 --max-time 5 https://cloudflare.com/cdn-cgi/trace 2>/dev/null | grep -E 'ip=|loc='" 2>/dev/null)
  
  TS_STATUS=\$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.5.1 \
    "tailscale status 2>&1 | head -1" 2>/dev/null)
  
  TS_PING=\$(ping -c 1 -W 2 $TS_IP 2>/dev/null | grep -o 'time=.*' | cut -d= -f2)
  
  echo "[\$NOW] +\${ELAPSED}s | Proxy: \${PROXY:-N/A} | TS: \${TS_STATUS:-N/A} | Ping: \${TS_PING:-N/A}"
  
  if [ "\$PROXY_ONLINE" = false ] && echo "\$PROXY" | grep -q 'loc='; then
    echo "  ✅ Прокси поднялся на +\${ELAPSED}s секунде!"
    PROXY_ONLINE=true
  fi
  
  if [ "\$TS_ONLINE" = false ] && echo "\$TS_STATUS" | grep -q "100\."; then
    echo "  ✅ Tailscale поднялся на +\${ELAPSED}s секунде!"
    TS_ONLINE=true
  fi
  
  if [ "\$PROXY_ONLINE" = true ] && [ "\$TS_ONLINE" = true ] && [ -n "\$TS_PING" ]; then
    echo "  ✅ ВСЁ РАБОТАЕТ! Выход из мониторинга."
    break
  fi
  
  sleep 5
done

# Финальная проверка
echo ""
echo "=== ФИНАЛЬНАЯ ПРОВЕРКА ПОСЛЕ РЕБУТА ==="
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.5.1 "
echo '--- Время работы ---'
uptime
echo ''
echo '--- Podkop ---'
echo \"Ключ: \$(uci get podkop.main.proxy_string | cut -c1-40)...\"
echo \"PodkopTable: \$(nft list table inet PodkopTable >/dev/null 2>&1 && echo OK || echo MISSING)\"
echo ''
echo '--- Tailscale ---'
tailscale status 2>&1 | head -3
echo ''
echo '--- Прокси ---'
curl -s --connect-timeout 5 --max-time 10 https://cloudflare.com/cdn-cgi/trace 2>/dev/null | grep -E 'ip=|loc='
echo ''
echo '--- Сайты ---'
for url in google.com youtube.com telegram.org github.com; do
  CODE=\$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 https://\$url 2>/dev/null)
  echo \"  \$url: \$CODE\"
done
echo ''
echo '--- Watchdog ---'
crontab -l | grep -c watchdog
echo ''
echo '--- fw4-fix ---'
/root/podkop-fw4-fix.sh update 2>&1 | tail -2
"
echo ""
echo "✅ РЕБУТ ЗАВЕРШЁН: +\$((\$(date +%s)-REBOOT_START)) секунд"

STEP11_TIME=$(($(date +%s)-STEP11_START))
echo "  ⏱ $STEP11_TIME сек"
```

### Шаг 12: Финальная диагностика

```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 12: Финальная диагностика"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP12_START=$(date +%s)

sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "check-ip"

STEP12_TIME=$(($(date +%s)-STEP12_START))
echo "  ⏱ $STEP12_TIME сек"
```

---

## 3. Итоговая таблица

После завершения всех 12 шагов выводится таблица:

```
╔══════════════════════════════════════════════════════════╗
║           📊 ИТОГ ПРОШИВКИ: <ROUTER_NAME>               ║
╠══════════════════════════════════════════════════════════╣
║  Модель:                    <MODEL>                     ║
║  Архитектура:               <ARCH>                      ║
║  Sing-box:                  <SING_BOX>                  ║
║  Tailscale:                 <TAILSCALE_TYPE>            ║
╠══════════════════════════════════════════════════════════╣
║  Шаг 0:  Определение модели     ⏱ 0:10  ✅            ║
║  Шаг 1:  Заливка OpenWrt        ⏱ <T1>  ✅            ║
║  Шаг 2:  Backup-шаблон          ⏱ <T2>  ✅            ║
║  Шаг 3:  Применить шаблон       ⏱ <T3>  ✅            ║
║  Шаг 4:  Создать ключ main      ⏱ <T4>  ✅            ║
║  Шаг 5:  Установка Podkop       ⏱ <T5>  ✅            ║
║  Шаг 6:  Настройка Podkop       ⏱ <T6>  ✅            ║
║  Шаг 7:  Установка Tailscale    ⏱ <T7>  ✅            ║
║  Шаг 8:  Спасительные скрипты   ⏱ <T8>  ✅            ║
║  Шаг 9:  Tailscale авторизация  ⏱ <T9>  ✅            ║
║  Шаг 10: Проверка перед ребутом ⏱ <T10> ✅            ║
║  Шаг 11: Ребут                  ⏱ <T11> ✅            ║
║  Шаг 12: Финальная диагностика  ⏱ <T12> ✅            ║
╠══════════════════════════════════════════════════════════╣
║  ⏱ ОБЩЕЕ ВРЕМЯ:                <TOTAL>                 ║
║  🌐 Tailscale IP:               <TS_IP>                 ║
║  📍 LAN IP:                     192.168.5.1             ║
║  🟢 check-ip:                   loc=<COUNTRY>           ║
╚══════════════════════════════════════════════════════════╝
```

---

## 4. Железные правила (для всех прошивок)

1. **Один профиль main** — YT профиль НЕ создаём. YouTube = 3-й список (после telegram, meta)
2. **Ключ всегда через relay** — русский relay-сервер, НЕ direct
3. **Ключи создавать только через `create_vless_key.py`** — НЕ через curl к API
4. **Перед установкой ключ проверить** `check_vless.py` → READY
5. **После замены ключа podkop НЕ перезагружать** — только `uci commit`
6. **Всегда ставить 3 watchdog'а** — ts-watchdog, podkop-watchdog, route-watchdog
7. **Всегда ставить fw4-fix** — иначе forwarded трафик не маркируется
8. **Всегда ставить check-ip** — для быстрой диагностики
9. **Перед ребутом проверять 5 пунктов** — fw_mode, init.d, rc.local, watchdog, exclude_ntp
10. **Финальная диагностика** — `check-ip` с роутера (loc=не RU)
11. **Tailscale для Cudy — только UPX из gunano** — репозиторий gunano сам определяет архитектуру и выбирает UPX-сжатую версию для роутеров с малым flash (WR3000H/S, TR3000). Для M3000 и AX3000T — толстая версия.
12. **На OpenWrt 25.12 (apk) — tailscale ставить через GitHub releases** — gunano репозиторий через apk может не работать из-за SSL ошибок wget. Скачивать .apk напрямую с `https://github.com/GuNanOvO/openwrt-tailscale/releases/download/v1.98.1/tailscale_1.98.1_aarch64_cortex-a53.apk` и устанавливать через `apk add --allow-untrusted /tmp/tailscale.apk`
13. **Cudy WR3000H/S, TR3000 — это aarch64_cortex-a53, НЕ mipsel** — у них 128MB flash, sing-box толстый, tailscale UPX (из-за занятого места другими пакетами)

---

## 5. Выбор пакетов по модели

| Модель | Flash | Архитектура | Sing-box | Tailscale | Причина |
|--------|-------|-------------|----------|-----------|---------|
| Xiaomi AX3000T | 128MB | aarch64_cortex-a53 | **толстый** (`sing-box`) | **толстый** (gunano) | Много места |
| Cudy M3000 v1/v2 | 128MB | aarch64_cortex-a53 | **толстый** (`sing-box`) | **толстый** (gunano) | Много места |
| Cudy WR3000H v1 | 128MB | aarch64_cortex-a53 | **толстый** (`sing-box`) | **UPX** (gunano) | 128MB, но занято пакетами |
| Cudy WR3000S v1 | 128MB | aarch64_cortex-a53 | **толстый** (`sing-box`) | **UPX** (gunano) | 128MB, но занято пакетами |
| Cudy TR3000 v1 | 128MB | aarch64_cortex-a53 | **толстый** (`sing-box`) | **UPX** (gunano) | 128MB, но занято пакетами |

> **Важно:** Репозиторий gunano (`https://github.com/GuNanOvO/openwrt-tailscale`) сам определяет архитектуру роутера и автоматически выбирает нужную версию tailscale (толстую или UPX-сжатую). На OpenWrt 25.12 с apk — скачивать .apk напрямую с GitHub releases, т.к. apk update может не работать из-за SSL ошибок wget на роутере.

---

## 6. Формат live-лога в чат

Каждый шаг выводится в чат с:
- `━━━` разделитель
- `✅ ШАГ N: Название` — зелёная галочка
- `⏱ X сек` — тайминг шага
- `🔍 Проверка WAN` — после каждого шага
- `❌ СТОП` — если ошибка
- В конце — итоговая таблица

---

*Последнее обновление: 2026-05-08*
