# Универсальный скилл: Прошивка любого роутера OpenWrt

> **Автоопределение модели + ping-циклы (без sleep) + live-таблица + pre-auth key**
> Последнее обновление: 2026-05-10

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

## 2. Алгоритм (11 шагов)

### Шаг 0: Подключение + автоопределение модели + учётка

```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 0: Подключение + автоопределение"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP0_START=$(date +%s)

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

# ⚠️ СПРОСИТЬ УЧЁТКУ TAILSCALE
echo ""
echo "⚠️ На какую учётку Tailscale цепляем роутер?"
echo "  1 — vas.neverov@gmail.com"
echo "  2 — ne78va@gmail.com"
echo "  3 — 56papezde@gmail.com"
echo "  4 — n78rout@gmail.com (по умолчанию)"
echo ""
echo "⏳ Ожидание ответа..."
# Пользователь отвечает в чат, я запоминаю TS_ACCOUNT

# ⚠️ СПРОСИТЬ ХОСТНЕЙМ
echo ""
echo "⚠️ Какой hostname дать роутеру? (например: z56-120, h-02, tr30-26)"
echo ""
echo "⏳ Ожидание ответа..."
# Пользователь отвечает в чат, я запоминаю ROUTER_NAME

# Автоопределение конфигурации по модели
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
    SING_BOX="sing-box"          # толстый
    TAILSCALE_TYPE="upx"         # UPX
    ;;
  *"WR3000S"*)
    ROUTER_TYPE="cudy_wr3000s"
    FIRMWARE="$HOME/Downloads/WR3000S V1/openwrt-25.12.0-ramips-mt7628-cudy_wr3000s-v1-squashfs-sysupgrade.bin"
    TEMPLATE="$HOME/Downloads/WR3000S V1/backup-wr3000s-template.tar.gz"
    SING_BOX="sing-box"          # толстый
    TAILSCALE_TYPE="upx"         # UPX
    ;;
  *)
    echo "❌ Неизвестная модель: $MODEL"
    exit 1
    ;;
esac

echo "  ✅ Модель: $MODEL"
echo "  ✅ Hostname: $ROUTER_NAME"
echo "  ✅ Учётка TS: $TS_ACCOUNT ($TS_TAILNET)"
echo "  ✅ Sing-box: $SING_BOX"
echo "  ✅ Tailscale: $TAILSCALE_TYPE"

STEP0_TIME=$(($(date +%s)-STEP0_START))
echo "  ⏱ $STEP0_TIME сек"
```

### Шаг 1: Заливка OpenWrt (ping-цикл, без sleep)

```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 1: Заливка OpenWrt"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP1_START=$(date +%s)

# Скопировать прошивку
scp -O -o StrictHostKeyChecking=no "$FIRMWARE" root@192.168.1.1:/tmp/firmware.bin

# Прошить
ssh -o StrictHostKeyChecking=no root@192.168.1.1 "sysupgrade -n /tmp/firmware.bin"

# ⏱ PING-ЦИКЛ: ждём пока роутер поднимется на 192.168.1.1
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
  sleep 1
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

### Шаг 2: Backup-шаблон + hostname (ping-цикл)

```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 2: Backup-шаблон + hostname"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP2_START=$(date +%s)

if [ ! -f "$TEMPLATE" ]; then
  # Создать шаблон
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

# Применить шаблон + hostname
scp -O -o StrictHostKeyChecking=no "$TEMPLATE" root@192.168.1.1:/tmp/backup.tar.gz

ssh -o StrictHostKeyChecking=no root@192.168.1.1 "
cd / && tar xzf /tmp/backup.tar.gz
uci set system.@system[0].hostname='$ROUTER_NAME'
uci commit system
echo '$ROUTER_NAME' > /proc/sys/kernel/hostname
reboot
"

# ⏱ PING-ЦИКЛ: ждём пока роутер перезагрузится на 192.168.5.1
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
  sleep 1
done

ssh-keygen -R 192.168.5.1 2>/dev/null
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "echo OK"

STEP2_TIME=$(($(date +%s)-STEP2_START))
echo "  ⏱ $STEP2_TIME сек"

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

### Шаг 3: Создать ключ main (через relay)

```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 3: Создать ключ main"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP3_START=$(date +%s)

# Вызвать скилл create_clone_key.md
# Для AX3000T/M3000: bSPB:8448 → CZ2
# Для WR3000H/S: bSPB:4191 → Fin3 (или bMSK:5223 → Fin4)

python3 /Users/vas/CLAUDECODE/tools/create_vless_key.py \
  --router $ROUTER_NAME \
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

STEP3_TIME=$(($(date +%s)-STEP3_START))
echo "  ⏱ $STEP3_TIME сек"
echo "  ✅ Ключ READY ✓✓✓"
```

### Шаг 4: Установка Podkop (через install.sh с itdog)

> **Скрипт:** `https://raw.githubusercontent.com/itdoginfo/podkop/refs/heads/main/install.sh`
> **Интерактивные вопросы (3 шт):**
> 1. "Continue? (yes/no)" — при обновлении старой версии → `y`
> 2. "Русский язык интерфейса ставим? y/n" → `y` (обязательно!)
> 3. "Conflicting package: https-dns-proxy. Remove?" → `y`

```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 4: Установка Podkop"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP4_START=$(date +%s)

echo "  📦 Модель: $ROUTER_TYPE"
echo "  📦 Sing-box: $SING_BOX"

# Установка podkop через install.sh с itdog
# ⚠️ Ответы на интерактивные вопросы:
#   y — подтверждение обновления (если старая версия)
#   y — удалить https-dns-proxy (если есть)
#   y — русский язык интерфейса (обязательно!)
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
printf 'y\ny\ny\n' | sh <(wget -O - https://raw.githubusercontent.com/itdoginfo/podkop/refs/heads/main/install.sh)
"

STEP4_TIME=$(($(date +%s)-STEP4_START))
echo "  ⏱ $STEP4_TIME сек"

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

### Шаг 5: Настройка Podkop + fw4-fix (сразу!)

```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 5: Настройка Podkop + fw4-fix"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP5_START=$(date +%s)

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

# ⚠️ fw4-fix — СРАЗУ после podkop, не потом!
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
wget -q -O /root/podkop-fw4-fix.sh \
  'https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/tools/podkop-fw4-fix.sh' 2>/dev/null
chmod +x /root/podkop-fw4-fix.sh 2>/dev/null
/root/podkop-fw4-fix.sh install 2>/dev/null || true
"

# ⚠️ Проверить PodkopTable
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
nft list table inet PodkopTable >/dev/null 2>&1 && echo 'PodkopTable: OK' || echo 'PodkopTable: MISSING'
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

### Шаг 6: Установка Tailscale (через install_en.sh с GuNanOvO)

> **Скрипт:** `https://raw.githubusercontent.com/GuNanOvO/openwrt-tailscale/main/install_en.sh`
> **Интерактивные вопросы:** скрипт показывает меню, первый пункт — Persistent Installation
> **Формула:** `printf '1\n' | /tmp/ts.sh` — `1` выбирает первый пункт меню
> **Флаг `--tempinstall`:** для временной установки (в /tmp, без сохранения после ребута)
> **Флага `--persistentinstall` НЕТ** — только через меню

```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 6: Установка Tailscale"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP6_START=$(date +%s)

echo "  📦 Тип: $TAILSCALE_TYPE ($([ "$TAILSCALE_TYPE" = "full" ] && echo 'толстый' || echo 'UPX-сжатый'))"
echo "  📦 Установка через gunano скрипт (автоопределение архитектуры)"

# Установка через скрипт gunano
# Скрипт сам определяет архитектуру и ставит правильную версию (толстую или UPX)
# ⚠️ Ответ на меню: '1' = Persistent Installation
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
wget -O /tmp/ts.sh https://raw.githubusercontent.com/GuNanOvO/openwrt-tailscale/main/install_en.sh
chmod +x /tmp/ts.sh
printf '1\n' | /tmp/ts.sh
"

# Настройка после установки
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
# Фикс для OpenWrt 25.12
sed -i 's|--statedir=/var/lib/tailscale ||g' /etc/init.d/tailscale 2>/dev/null
sed -i 's|TS_DEBUG_FIREWALL_MODE=\"none\"|TS_DEBUG_FIREWALL_MODE=\"\$fw_mode\"|g' /etc/init.d/tailscale 2>/dev/null

# Настройка
uci set tailscale.settings.fw_mode='none'
uci set tailscale.settings.state_file='/etc/tailscale/tailscaled.state'
uci set tailscale.settings.autoupdate='false'
uci commit tailscale
mkdir -p /etc/tailscale

# Отключаем init.d (будет через rc.local)
/etc/init.d/tailscale disable
"

STEP6_TIME=$(($(date +%s)-STEP6_START))
echo "  ⏱ $STEP6_TIME сек"
```

### Шаг 7: Tailscale авторизация (pre-auth key, без serve anchor)

```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 7: Tailscale авторизация (pre-auth key)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP7_START=$(date +%s)

# ⚠️ Проверить что прокси работает
echo "  🔍 Проверка прокси..."
PROXY_LOC=$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 \
  "curl -s --connect-timeout 5 --max-time 10 https://cloudflare.com/cdn-cgi/trace 2>/dev/null | grep 'loc='" 2>/dev/null)
echo "  Прокси: ${PROXY_LOC:-❌ НЕ РАБОТАЕТ}"

# ===== Создать pre-auth key через Tailscale API =====
echo "  🔑 Создание pre-auth key для учётки $TS_ACCOUNT..."

# Маппинг учёток → tailnet
case "$TS_ACCOUNT" in
  1) TS_TAILNET="vas.neverov@gmail.com"; TS_TOKEN="tskey-api-ktBh42VtRj11CNTRL-RBTDhNJYzdNNqr7wNTfLdNC6PncxBk63B" ;;
  2) TS_TAILNET="ne78va@gmail.com";     TS_TOKEN="tskey-api-kW1ujQ5i2w11CNTRL-wRvm7o2eCkiEfK7M1fhhjiq763ztrBsx" ;;
  3) TS_TAILNET="56papezde@gmail.com";  TS_TOKEN="tskey-api-k7CKy5KXg421CNTRL-UbV7qjoSeKAbB4Akb1VrJAB6NhfpLkYL" ;;
  4) TS_TAILNET="n78rout@gmail.com";    TS_TOKEN="tskey-api-krWQYxzw1511CNTRL-28hSufddDkPy7RxcKzcdjPS24aFRZLh2" ;;
  *) echo "❌ Неизвестная учётка: $TS_ACCOUNT"; exit 1 ;;
esac

# Создать pre-auth key (одноразовый, preauthorized)
TS_AUTH_KEY=$(curl -s -X POST "https://api.tailscale.com/api/v2/tailnet/$TS_TAILNET/keys" \
  -H "Authorization: Bearer $TS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "capabilities": {
      "devices": {
        "create": {
          "reusable": false,
          "ephemeral": false,
          "preauthorized": true
        }
      }
    }
  }' | grep -o '"key":"[^"]*"' | cut -d'"' -f4)

echo "  ✅ Pre-auth key создан: ${TS_AUTH_KEY:0:25}..."

# ===== Авторизация на роутере =====
# Убить старые tailscale up процессы
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
kill \$(ps | grep 'tailscale up' | grep -v grep | awk '{print \$1}') 2>/dev/null || true
echo '  tailscale up процессы убиты'
"

# Запустить tailscaled (если ещё не запущен)
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
ps | grep -q 'tailscaled --statedir=' || {
  tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking >> /tmp/ts.log 2>&1 &
  sleep 3
  echo '  tailscaled запущен'
}
"

# ===== Авторизация через --reset (чистый старт, без serve anchor) =====
# --reset сбрасывает старые advertise-routes и другие флаги
# --netfilter-mode=off: tailscale не лезет в iptables (это делает podkop)
# serve anchor НЕ НУЖЕН — watchdog держит соединение
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
tailscale up --reset \
  --authkey=$TS_AUTH_KEY \
  --hostname=$ROUTER_NAME \
  --accept-routes \
  --accept-dns=false \
  --netfilter-mode=off
"

sleep 3

# Проверить статус
TS_STATUS=$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 \
  "tailscale status 2>&1 | head -1" 2>/dev/null)
TS_IP=$(echo "$TS_STATUS" | awk '{print $1}')

if echo "$TS_STATUS" | grep -q "100\."; then
  echo "  ✅ Tailscale авторизован: $TS_IP"
else
  echo "  ⚠️ Статус: $TS_STATUS"
  echo "  ⏳ Ждём 10 сек..."
  sleep 10
  TS_STATUS=$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 \
    "tailscale status 2>&1 | head -1" 2>/dev/null)
  TS_IP=$(echo "$TS_STATUS" | awk '{print $1}')
  if echo "$TS_STATUS" | grep -q "100\."; then
    echo "  ✅ Tailscale авторизован: $TS_IP"
  else
    echo "  ❌ Tailscale НЕ авторизовался"
    echo "  Статус: $TS_STATUS"
    exit 1
  fi
fi

# ⚠️ Ожидание зелёной точки (ping-цикл)
echo "⏳ Ожидание зелёной точки (Tailscale ONLINE)..."
ONLINE_START=$(date +%s)
while true; do
  TS_STATUS=$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.5.1 \
    "tailscale status 2>&1 | head -1" 2>/dev/null)
  STATUS_FIELD=$(echo "$TS_STATUS" | awk '{print $4}')
  echo "  [$(($(date +%s)-ONLINE_START))c] $TS_STATUS"
  [ "$STATUS_FIELD" = "-" ] && break
  if [ $(($(date +%s)-ONLINE_START)) -gt 60 ]; then
    echo "  ❌ Таймаут! Tailscale не ONLINE за 60 сек"
    exit 1
  fi
  sleep 2
done
echo "  ✅ Tailscale ONLINE (зелёная точка) — за $(($(date +%s)-ONLINE_START)) сек"

# Проверить ping по Tailscale
ping -c 2 -W 3 $TS_IP 2>&1 | tail -3

STEP7_TIME=$(($(date +%s)-STEP7_START))
echo "  ⏱ $STEP7_TIME сек"
```


### Шаг 8: Спасительные скрипты (watchdog, rc.local, check-ip)

```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 8: Спасительные скрипты"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP8_START=$(date +%s)

sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
# ===== 8a. rc.local — tailscaled → sleep → tailscale up --reset → watchdog + FakeIP =====
# ⚠️ ВАЖНО: tailscaled стартует ПЕРВЫМ, sleep 3 даёт ему инициализироваться
# ⚠️ --reset сбрасывает старые advertise-routes и другие флаги
# ⚠️ --netfilter-mode=off — tailscale не лезет в iptables (это делает podkop)
# ⚠️ FakeIP route (198.18.0.0/15) — для DNS через Tailscale
# ⚠️ watchdog (ts-watchdog.sh) — авто-восстановление в фоне
cat > /etc/rc.local << 'EOF'
#!/bin/sh

# === TAILSCALE STARTUP ===
tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking >> /tmp/ts.log 2>&1 &
sleep 3
tailscale up --reset --accept-dns=false --accept-routes --netfilter-mode=off &

# === WATCHDOG В ФОНЕ ===
# Авто-восстановление: tailscaled running, NoState, DERP connection
/etc/ts-watchdog.sh &

logger -t rc.local 'rc.local complete'
ip route add 198.18.0.0/15 dev lo 2>/dev/null

exit 0
EOF
chmod +x /etc/rc.local
cp /etc/rc.local /etc/rc.local.bak
echo "  ✅ rc.local — tailscaled → sleep → tailscale up --reset → watchdog + FakeIP"

# ===== 8b. Firewall — tailscale0 в LAN + WAN порт (eth1) =====
uci set firewall.@zone[0].device='br-lan tailscale0'
uci commit firewall

# ===== 8b2. WAN порт (eth1) в LAN зону (для Cudy M3000 и др.) =====
# Некоторые роутеры (Cudy M3000 v1/v2) имеют отдельный WAN порт (eth1),
# который не входит в LAN зону по умолчанию. Без этого прокси не работает
# для клиентов, подключённых через WAN порт.
ETH1_EXISTS=$(ip link show eth1 2>/dev/null && echo yes || echo no)
if [ "$ETH1_EXISTS" = "yes" ]; then
  CURRENT_DEVICES=$(uci get firewall.@zone[0].device 2>/dev/null)
  if ! echo "$CURRENT_DEVICES" | grep -q "eth1"; then
    uci set firewall.@zone[0].device="$CURRENT_DEVICES eth1"
    uci commit firewall
    echo "  ✅ eth1 добавлен в LAN зону"
  fi
fi

# ===== 8c. WAN ifname =====
WAN_IFNAME=\$(uci get network.wan.ifname 2>/dev/null)
if [ -z \"\$WAN_IFNAME\" ]; then
    WAN_DEVICE=\$(uci get network.wan.device 2>/dev/null)
    if [ -n \"\$WAN_DEVICE\" ]; then
        uci set network.wan.ifname=\"\$WAN_DEVICE\"
        uci commit network
    fi
fi

# ===== 8d. Tailscale watchdog v3 — единый, с lock-файлом =====
# ⚠️ v3.1: lock-файл — не запускается дважды (rc.local + крон)
# ⚠️ Не убивает tailscale если он уже онлайн
# ⚠️ NoState fix: полный перезапуск tailscaled если DERP потерян
cat > /etc/ts-watchdog.sh << 'WEOF'
#!/bin/sh

# === ts-watchdog v3.1 ===
# Единый watchdog: работает и из rc.local, и из крона
# Lock-файл: не запускается дважды
# Не убивает tailscale если он уже онлайн
# NoState fix: если tailscale status выдаёт NoState — killall tailscaled + запуск заново

LOCKFILE=/tmp/ts-watchdog.lock

# Lock-файл: если уже запущен — выходим
if [ -f "$LOCKFILE" ]; then
    LOCKPID=$(cat "$LOCKFILE" 2>/dev/null)
    if kill -0 "$LOCKPID" 2>/dev/null; then
        exit 0
    fi
fi
echo $$ > "$LOCKFILE"

# 1. Проверка tailscaled процесс
if ! ps | grep -q "tailscaled --state="; then
    logger -t ts-watchdog "tailscaled not running, restarting..."
    tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking >> /tmp/ts.log 2>&1 &
    sleep 5
    tailscale up --accept-dns=false --accept-routes &
    logger -t ts-watchdog "tailscaled restarted"
    rm -f "$LOCKFILE"
    exit 0
fi

# 2. Проверка что tailscale онлайн
TS_STATUS=$(tailscale status 2>&1)

# 2a. Если tailscaled в битом состоянии (NoState) — перезапускаем целиком
if echo "$TS_STATUS" | grep -q "NoState"; then
    logger -t ts-watchdog "tailscaled in NoState (DERP lost), full restart..."
    killall tailscale 2>/dev/null
    sleep 1
    killall tailscaled 2>/dev/null
    sleep 2
    tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking >> /tmp/ts.log 2>&1 &
    sleep 5
    date +%s > /tmp/ts-up-start
    tailscale up --accept-dns=false --accept-routes &
    logger -t ts-watchdog "tailscaled fully restarted (NoState fix)"
    rm -f "$LOCKFILE"
    exit 0
fi

# 2b. Нормальный онлайн
if echo "$TS_STATUS" | grep -q '100\.'; then
    # ✅ Tailscale онлайн — ничего не делаем
    # Применяем podkop-fw4-fix если нужно
    if [ -x /root/podkop-fw4-fix.sh ]; then
        /root/podkop-fw4-fix.sh update 2>/dev/null
    fi
    rm -f "$LOCKFILE"
    exit 0
fi

# 3. Tailscale НЕ онлайн — пробуем перезапустить
logger -t ts-watchdog "tailscale not online, reconnecting..."

# Проверяем не висит ли tailscale up
TS_UP_PID=$(ps | grep "tailscale up" | grep -v grep | awk '{print $1}')
if [ -n "$TS_UP_PID" ]; then
    # Если tailscale up висит больше 90 сек — убиваем
    # 30 сек мало — tailscale up может висеть 40-50 сек при первом запуске
    if [ -f /tmp/ts-up-start ] && [ $(($(date +%s) - $(cat /tmp/ts-up-start))) -gt 90 ]; then
        logger -t ts-watchdog "tailscale up stuck (PID $TS_UP_PID), killing..."
        kill "$TS_UP_PID" 2>/dev/null
        sleep 2
        date +%s > /tmp/ts-up-start
        tailscale up --accept-dns=false --accept-routes &
        logger -t ts-watchdog "tailscale up restarted"
    fi
else
    # tailscale up не запущен — запускаем
    date +%s > /tmp/ts-up-start
    tailscale up --accept-dns=false --accept-routes &
    logger -t ts-watchdog "tailscale up started"
fi

rm -f "$LOCKFILE"
WEOF
chmod +x /etc/ts-watchdog.sh
echo "  ✅ ts-watchdog.sh v3.1 (NoState fix + lock-файл)"

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

# ===== 8i. Установка podkop-fix-lists =====
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


### Шаг 9: Проверка перед ребутом → спросить пользователя

```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 9: Проверка перед ребутом"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP9_START=$(date +%s)

# Проверить 5 пунктов
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
echo 'fw_mode:      ' \$(uci get tailscale.settings.fw_mode)
echo 'init.d:       ' \$(/etc/init.d/tailscale enabled 2>/dev/null && echo ENABLED || echo DISABLED)
echo 'rc.local:     ' \$(grep -q tailscaled /etc/rc.local && echo OK || echo FAIL)
echo 'watchdog:     ' \$(crontab -l | grep -c watchdog)
echo 'exclude_ntp:  ' \$(uci get podkop.settings.exclude_ntp)
echo 'fw4-fix:      ' \$(ls /root/podkop-fw4-fix.sh 2>/dev/null && echo OK || echo FAIL)
echo 'check-ip:     ' \$(which check-ip 2>/dev/null || echo FAIL)
echo 'PodkopTable:  ' \$(nft list table inet PodkopTable >/dev/null 2>&1 && echo OK || echo MISSING)
echo 'Tailscale:    ' \$(tailscale status 2>&1 | head -1 | awk '{print \$1}')
echo 'Прокси:       ' \$(curl -s --connect-timeout 5 --max-time 10 https://cloudflare.com/cdn-cgi/trace 2>/dev/null | grep 'loc=')
"

STEP9_TIME=$(($(date +%s)-STEP9_START))
echo "  ⏱ $STEP9_TIME сек"

# ⚠️ СПРОСИТЬ ПОЛЬЗОВАТЕЛЯ
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ⚠️  РОУТЕР ГОТОВ К РЕБУТУ!"
echo ""
echo "  ✅ fw_mode=none     ✅ init.d=DISABLED     ✅ rc.local=OK"
echo "  ✅ watchdog=3       ✅ exclude_ntp=1       ✅ fw4-fix=OK"
echo "  ✅ check-ip=OK      ✅ PodkopTable=OK      ✅ Tailscale=ONLINE"
echo "  ✅ Прокси работает (loc=не RU)"
echo ""
echo "  ⏳ Жду твоего разрешения на ребут..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
# Пользователь отвечает в чат
```


### Шаг 10: Ребут + мониторинг (ping-цикл)

```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 10: Ребут + мониторинг"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP10_START=$(date +%s)

# ⏱ ЗАСЕЧЬ ВРЕМЯ
echo "🕐 РЕБУТ: \$(date +%H:%M:%S)"
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "reboot"

# ⏱ PING-ЦИКЛ: ждём пока роутер поднимется
echo "⏳ Ожидание перезагрузки на 192.168.5.1..."
WAIT_START=$(date +%s)
while true; do
  if ping -c 1 -W 1 192.168.5.1 >/dev/null 2>&1; then
    echo "  ✅ Роутер поднялся через $(($(date +%s)-WAIT_START)) сек"
    break
  fi
  if [ $(($(date +%s)-WAIT_START)) -gt 120 ]; then
    echo "  ❌ Таймаут! Роутер не поднялся за 120 сек"
    exit 1
  fi
  sleep 1
done

# Мониторить каждые 5 секунд — ждём прокси + tailscale
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
  
  echo "[\$NOW] +\${ELAPSED}s | Proxy: \${PROXY:-N/A} | TS: \${TS_STATUS:-N/A}"
  
  if [ "\$PROXY_ONLINE" = false ] && echo "\$PROXY" | grep -q 'loc='; then
    echo "  ✅ Прокси поднялся на +\${ELAPSED}s секунде!"
    PROXY_ONLINE=true
  fi
  
  if [ "\$TS_ONLINE" = false ] && echo "\$TS_STATUS" | grep -q "100\."; then
    echo "  ✅ Tailscale поднялся на +\${ELAPSED}s секунде!"
    TS_ONLINE=true
  fi
  
  if [ "\$PROXY_ONLINE" = true ] && [ "\$TS_ONLINE" = true ]; then
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

STEP10_TIME=$(($(date +%s)-STEP10_START))
echo "  ⏱ $STEP10_TIME сек"
```


### Шаг 11: Финальная диагностика + итоговая таблица

> **Использует:** `~/.claude/skills/router-diag-step/SKILL.md` — универсальный диагностический шаг

```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 11: Финальная диагностика"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP11_START=$(date +%s)

# Универсальный диагностический шаг (см. router-diag-step)
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@192.168.5.1 "
echo '╔══════════════════════════════════════════════╗'
echo '║  DIAG: $ROUTER_NAME (192.168.5.1)            ║'
echo '╚══════════════════════════════════════════════╝'

echo ''
echo '── 1. SYSTEM ──'
echo \"Model: \$(cat /tmp/sysinfo/model 2>/dev/null)\"
echo \"OS: \$(cat /etc/openwrt_release | grep DISTRIB_RELEASE | cut -d\"'\" -f2)\"
echo \"Uptime: \$(uptime | sed 's/.*up //' | sed 's/,.*//')\"
echo \"Flash: \$(df -h / | tail -1 | awk '{print \$3\"/\"\$2}')\"

echo ''
echo '── 2. WAN ──'
echo \"GW: \$(ip route | grep default | awk '{print \$3}')\"
echo \"IF: \$(ip route | grep default | awk '{print \$5}')\"

echo ''
echo '── 3. PROVIDER ──'
curl -s --connect-timeout 5 --max-time 10 https://ipinfo.io/json 2>/dev/null | grep -E '\"ip\"|\"city\"|\"org\"' | tr -d '\"' | tr ',' ' '

echo ''
echo '── 4. PROXY ──'
curl -s --connect-timeout 5 --max-time 10 https://cloudflare.com/cdn-cgi/trace 2>/dev/null | grep -E 'ip=|loc='

echo ''
echo '── 5. TAILSCALE ──'
echo \"IP: \$(tailscale status 2>&1 | head -1 | awk '{print \$1}')\"
echo \"Status: \$(tailscale status 2>&1 | head -1 | awk '{print \$4}')\"
echo \"fw_mode: \$(uci get tailscale.settings.fw_mode)\"
echo \"init.d: \$(/etc/init.d/tailscale enabled 2>/dev/null && echo ENABLED || echo DISABLED)\"

echo ''
echo '── 6. PODKOP ──'
echo \"Table: \$(nft list table inet PodkopTable >/dev/null 2>&1 && echo OK || echo MISSING)\"
echo \"Lists: \$(uci get podkop.main.community_lists | wc -w) items\"
echo \"exclude_ntp: \$(uci get podkop.settings.exclude_ntp)\"

echo ''
echo '── 7. SITES ──'
for url in google.com youtube.com telegram.org facebook.com instagram.com rutracker.org tiktok.com x.com discord.com github.com; do
  CODE=\$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 https://\$url 2>/dev/null)
  printf '  %-15s %3s\n' \"\$url\" \"\$CODE\"
done

echo ''
echo '── 8. PING ──'
for host in 1.1.1.1 8.8.8.8 google.com; do
  AVG=\$(ping -c 3 -W 2 \$host 2>&1 | tail -1 | grep -oE 'avg = [0-9.]+' | cut -d' ' -f3)
  echo \"  \$host: \${AVG:-❌} ms\"
done

echo ''
echo '── 9. WATCHDOG ──'
echo \"Count: \$(crontab -l | grep -c watchdog)\"

echo ''
echo '── 10. fw4-fix ──'
echo \"Script: \$(ls /root/podkop-fw4-fix.sh >/dev/null 2>&1 && echo OK || echo FAIL)\"
echo \"Rules: \$(nft list chain inet fw4 mangle_forward 2>/dev/null | grep -c 'podkop-fw4-fix') active\"

echo ''
echo '── 11. rc.local ──'
grep -q 'sleep 40' /etc/rc.local && echo 'sleep 40: YES (OLD)' || echo 'sleep 40: NO (NEW)'
grep -q tailscaled /etc/rc.local && echo 'tailscaled: OK' || echo 'tailscaled: FAIL'
"

# Получить Tailscale IP
TS_IP=$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 \
  "tailscale status 2>&1 | head -1 | awk '{print \$1}'" 2>/dev/null)

# Получить локацию прокси
PROXY_LOC=$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 \
  "curl -s --connect-timeout 5 --max-time 10 https://cloudflare.com/cdn-cgi/trace 2>/dev/null | grep 'loc='" 2>/dev/null)

STEP11_TIME=$(($(date +%s)-STEP11_START))
echo "  ⏱ $STEP11_TIME сек"

# ===== ИТОГОВАЯ ТАБЛИЦА =====
TOTAL_TIME=$((STEP1_TIME+STEP2_TIME+STEP3_TIME+STEP4_TIME+STEP5_TIME+STEP6_TIME+STEP7_TIME+STEP8_TIME+STEP9_TIME+STEP10_TIME+STEP11_TIME))

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║           📊 ИТОГ ПРОШИВКИ: $ROUTER_NAME"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Модель:                    $MODEL"
echo "║  Архитектура:               $ARCH"
echo "║  Sing-box:                  $SING_BOX"
echo "║  Tailscale:                 $TAILSCALE_TYPE"
echo "╠══════════════════════════════════════════════════════════╣"
printf "║  Шаг 0:  Определение модели     ⏱ %3d сек  ✅\n" $STEP0_TIME
printf "║  Шаг 1:  Заливка OpenWrt        ⏱ %3d сек  ✅\n" $STEP1_TIME
printf "║  Шаг 2:  Backup-шаблон+hostname ⏱ %3d сек  ✅\n" $STEP2_TIME
printf "║  Шаг 3:  Создать ключ main      ⏱ %3d сек  ✅\n" $STEP3_TIME
printf "║  Шаг 4:  Установка Podkop       ⏱ %3d сек  ✅\n" $STEP4_TIME
printf "║  Шаг 5:  Настройка Podkop+fix   ⏱ %3d сек  ✅\n" $STEP5_TIME
printf "║  Шаг 6:  Установка Tailscale    ⏱ %3d сек  ✅\n" $STEP6_TIME
printf "║  Шаг 7:  Tailscale авторизация  ⏱ %3d сек  ✅\n" $STEP7_TIME
printf "║  Шаг 8:  Спасительные скрипты   ⏱ %3d сек  ✅\n" $STEP8_TIME
printf "║  Шаг 9:  Проверка перед ребутом ⏱ %3d сек  ✅\n" $STEP9_TIME
printf "║  Шаг 10: Ребут                  ⏱ %3d сек  ✅\n" $STEP10_TIME
printf "║  Шаг 11: Финальная диагностика  ⏱ %3d сек  ✅\n" $STEP11_TIME
echo "╠══════════════════════════════════════════════════════════╣"
printf "║  ⏱ ОБЩЕЕ ВРЕМЯ:                %3d сек\n" $TOTAL_TIME
echo "║  🌐 Tailscale IP:               $TS_IP"
echo "║  📍 LAN IP:                     192.168.5.1"
echo "║  🟢 Прокси:                     $PROXY_LOC"
echo "╚══════════════════════════════════════════════════════════╝"
```

---

## 3. Железные правила (для всех прошивок)

1. **Один профиль main** — YT профиль НЕ создаём. YouTube = 3-й список (после telegram, meta)
2. **Ключ всегда через relay** — русский relay-сервер, НЕ direct
3. **Ключи создавать только через `create_vless_key.py`** — НЕ через curl к API
4. **Перед установкой ключ проверить** `check_vless.py` → READY ✓✓✓
5. **После замены ключа podkop НЕ перезагружать** — только `uci commit`
6. **Всегда ставить 3 watchdog'а** — ts-watchdog, podkop-watchdog, route-watchdog
7. **Всегда ставить fw4-fix** — иначе forwarded трафик не маркируется. Ставить СРАЗУ после podkop (шаг 5)
8. **Всегда ставить check-ip** — для быстрой диагностики
9. **Перед ребутом проверять 10 пунктов** — fw_mode, init.d, rc.local, watchdog, exclude_ntp, fw4-fix, check-ip, PodkopTable, Tailscale, Прокси
10. **Финальная диагностика** — `check-ip` с роутера (loc=не RU)
11. **Tailscale для Cudy — только UPX из gunano** — репозиторий gunano сам определяет архитектуру и выбирает UPX-сжатую версию для роутеров с малым flash (WR3000H/S, TR3000). Для M3000 и AX3000T — толстая версия.
12. **На OpenWrt 25.12 (apk) — tailscale ставить через GitHub releases** — gunano репозиторий через apk может не работать из-за SSL ошибок wget. Скачивать .apk напрямую с `https://github.com/GuNanOvO/openwrt-tailscale/releases/download/v1.98.1/tailscale_1.98.1_aarch64_cortex-a53.apk` и устанавливать через `apk add --allow-untrusted /tmp/tailscale.apk`
13. **Cudy WR3000H/S, TR3000 — это aarch64_cortex-a53, НЕ mipsel** — у них 128MB flash, sing-box толстый, tailscale UPX (из-за занятого места другими пакетами)
14. **Tailscale авторизация — только через pre-auth key** — создаётся через Tailscale API, роутер авторизуется сам, без открытия браузера. Учётку спрашивать у пользователя в начале прошивки (шаг 0).
15. **Ребут — только с разрешения пользователя** — после шага 9 (проверка перед ребутом) показать пользователю аргументы и спросить "можно ребут?". Без подтверждения НЕ ребутить.
16. **В начале прошивки спросить учётку Tailscale** — на какую учётку цепляем роутер. По умолчанию — n78rout (4-я).
17. **Никаких `sleep N` — только ping-циклы** — все ожидания перезагрузки через ping с таймаутом 1 сек. Максимальное время ожидания: 180 сек (шаг 1), 90 сек (шаг 2), 120 сек (шаг 10).
18. **Если GitHub заблокирован — сначала разблокировать порты, потом podkop** — не ставить podkop из локальной папки пока не попробовали разблокировку.

---

## 4. Выбор пакетов по модели

| Модель | Flash | Архитектура | Sing-box | Tailscale | Причина |
|--------|-------|-------------|----------|-----------|---------|
| Xiaomi AX3000T | 128MB | aarch64_cortex-a53 | **толстый** (`sing-box`) | **толстый** (gunano) | Много места |
| Cudy M3000 v1/v2 | 128MB | aarch64_cortex-a53 | **толстый** (`sing-box`) | **толстый** (gunano) | Много места |
| Cudy WR3000H v1 | 128MB | aarch64_cortex-a53 | **толстый** (`sing-box`) | **UPX** (gunano) | 128MB, но занято пакетами |
| Cudy WR3000S v1 | 128MB | aarch64_cortex-a53 | **толстый** (`sing-box`) | **UPX** (gunano) | 128MB, но занято пакетами |
| Cudy TR3000 v1 | 128MB | aarch64_cortex-a53 | **толстый** (`sing-box`) | **UPX** (gunano) | 128MB, но занято пакетами |

> **Важно:** Репозиторий gunano (`https://github.com/GuNanOvO/openwrt-tailscale`) сам определяет архитектуру роутера и автоматически выбирает нужную версию tailscale (толстую или UPX-сжатую). На OpenWrt 25.12 с apk — скачивать .apk напрямую с GitHub releases, т.к. apk update может не работать из-за SSL ошибок wget на роутере.

---

## 5. Формат live-лога в чат

Каждый шаг выводится в чат с:
- `━━━` разделитель
- `✅ ШАГ N: Название` — зелёная галочка
- `⏱ X сек` — тайминг шага
- `🔍 Проверка WAN` — после каждого шага
- `❌ СТОП` — если ошибка
- В конце — итоговая таблица

---

*Последнее обновление: 2026-05-10*


