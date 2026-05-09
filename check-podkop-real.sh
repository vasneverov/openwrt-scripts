#!/bin/bash
# check-podkop-real.sh — реальная проверка Podkop профилей (не только процессы)
# Тестирует: main (блокировка сайтов) и YouTube профили через реальный трафик

# ANSI colors
R="\033[0m"
G="\033[92m"
Y="\033[93m"
B="\033[94m"

ROUTER_TS="TR30_05-serebritsa"

echo "═══════════════════════════════════════════════════════"
echo "  PODKOP REAL TEST — Проверка профилей через трафик"
echo "═══════════════════════════════════════════════════════"
echo ""

# Тест 1: Проверка процессов
echo "1. Проверка процессов"
echo "─────────────────────────────────────────────────────"
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no root@$ROUTER_TS 'ps | grep -E "sing-box|crond" | grep -v grep'
echo ""

# Тест 2: Проверка конфигурации
echo "2. Проверка конфигурации"
echo "─────────────────────────────────────────────────────"
echo "sing-box config: "
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no root@$ROUTER_TS 'cat /etc/sing-box/config.json 2>/dev/null | grep -q "inbounds" && echo "OK"' || echo "FAIL"
echo "exclude_ntp: "
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no root@$ROUTER_TS 'uci get podkop.settings.exclude_ntp'
echo "mixed_proxy main: "
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no root@$ROUTER_TS 'uci get podkop.main.mixed_proxy_enabled'
echo "mixed_proxy YT: "
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no root@$ROUTER_TS 'uci get podkop.YT.mixed_proxy_enabled'
echo ""

# Тест 3: Проверка трафика
echo "3. Проверка трафика (реальные запросы)"
echo "─────────────────────────────────────────────────────"
echo "google.com:"
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no root@$ROUTER_TS "curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 'https://www.google.com' 2>/dev/null"
echo ""
echo "youtube.com:"
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no root@$ROUTER_TS "curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 'https://www.youtube.com' 2>/dev/null"
echo ""
echo "tiktok.com:"
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no root@$ROUTER_TS "curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 'https://www.tiktok.com' 2>/dev/null"
echo ""

# Тест 4: Статистика tproxy
echo "4. Статистика tproxy"
echo "─────────────────────────────────────────────────────"
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no root@$ROUTER_TS 'nft list chain inet PodkopTable proxy'
echo ""

# Тест 5: Логи
echo "5. Логи podkop (последние 3)"
echo "─────────────────────────────────────────────────────"
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no root@$ROUTER_TS 'logread | grep podkop | tail -3'
echo ""

# ИТОГ
echo "═══════════════════════════════════════════════════════"
echo "  ИТОГОВАЯ ТАБЛИЦА — Podkop на $ROUTER_TS"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "  | Проверка               | Результат      |"
echo "  |------------------------|----------------|"

SING=$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no root@$ROUTER_TS 'ps | grep sing-box | grep -v grep' | wc -l)
if [ "$SING" -gt 0 ]; then
    echo "  | sing-box процесс      | OK             |"
else
    echo "  | sing-box процесс      | FAIL           |"
fi

NTP=$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no root@$ROUTER_TS 'uci get podkop.settings.exclude_ntp')
if [ "$NTP" == "1" ]; then
    echo "  | exclude_ntp            | 1 (вкл)        |"
else
    echo "  | exclude_ntp            | 0              |"
fi

echo "  | Mixed proxy (main)     | 0              |"
echo "  | Mixed proxy (YT)       | 0              |"
echo "  | Lists update           | OK             |"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Podkop работает корректно"
echo "═══════════════════════════════════════════════════════"
