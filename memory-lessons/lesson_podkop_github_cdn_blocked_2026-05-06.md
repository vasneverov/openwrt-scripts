# Урок: Podkop + GitHub CDN блокировка — решение через локальные списки

**Дата:** 2026-05-06  
**Роутер:** S78-40 (100.118.37.35)  
**Проблема:** GitHub CDN заблокирован провайдером, community lists не скачиваются

## Симптомы

- В LuCI 7+ красных плашек "Cannot download telegram list", "Cannot download meta list"
- YouTube работает (туннель зелёный, профили active)
- Telegram/Instagram НЕ работают
- В логах podkop: `Failed to send request: Operation not permitted` при скачивании с raw.githubusercontent.com
- Таймаут 30 секунд на каждую попытку скачивания

## Диагностика

```bash
# Проверка доступности GitHub
logread | grep "github\|download" | tail -20
# Результат: Operation not permitted, таймауты на всех попытках

# mixed proxy не был включён
uci get podkop.main.mixed_proxy_enabled  # → 0
```

## Причина

sing-box 1.12+ скачивает ruleset (.srs файлы) с GitHub Releases:
- `https://github.com/itdoginfo/allow-domains/releases/latest/download/*.srs`

Провайдер (Ростелеком/ТТК в данном случае) блокирует GitHub CDN → скачивание падает → ruleset не создаются → трафик к Telegram/Meta не идёт через туннель.

## Решение

### 1. Включение mixed proxy

```bash
uci set podkop.main.mixed_proxy_enabled="1"
uci commit podkop
/etc/init.d/podkop restart
```

Создаёт `service-mixed-in` inbound на порту 4534.

### 2. Скачивание списков через туннель

```bash
mkdir -p /etc/sing-box/cache
for list in telegram meta geoblock block porn news anime discord twitter hdrezka tiktok cloudflare google_ai google_play hodca roblox hetzner ovh digitalocean cloudfront youtube; do
    curl -sL --proxy http://127.0.0.1:4534 \
        "https://github.com/itdoginfo/allow-domains/releases/latest/download/${list}.srs" \
        -o "/etc/sing-box/cache/${list}.srs"
done
```

**Важно:** флаг `-L` для следования редиректов GitHub Releases (302 → CDN).

### 3. Переключение на локальные файлы

```bash
# Замена URL
sed -i "s|https://github.com/itdoginfo/allow-domains/releases/latest/download/|file:///etc/sing-box/cache/|g" /etc/sing-box/config.json

# Удаление download_detour (не нужен для file://)
sed -i "/download_detour/d" /etc/sing-box/config.json
```

### 4. Перезапуск и проверка

```bash
killall sing-box; sleep 2; sing-box run -c /etc/sing-box/config.json &
curl -s -o /dev/null -w "%{http_code}" https://telegram.org  # → 200 ✅
```

### 5. Защита от перезаписи

При рестарте podkop перегенерирует конфиг. Создать защитный скрипт в cron:

```bash
cat > /etc/sing-box-protect.sh << 'EOF'
#!/bin/sh
if ! grep -q "file:///etc/sing-box/cache" /etc/sing-box/config.json 2>/dev/null; then
    logger -t sing-box-protect "Restoring local URLs"
    sed -i "s|https://github.com/itdoginfo/allow-domains/releases/latest/download/|file:///etc/sing-box/cache/|g" /etc/sing-box/config.json
    sed -i "/download_detour/d" /etc/sing-box/config.json
    /etc/init.d/podkop restart
fi
EOF
chmod +x /etc/sing-box-protect.sh

# Cron каждые 5 минут
echo "*/5 * * * * /etc/sing-box-protect.sh" | crontab -
```

## Итог

| Параметр | До | После |
|----------|-----|-------|
| Telegram | ❌ 000 | ✅ 200 |
| YouTube | ✅ 301 | ✅ 301 |
| Instagram | ❌ 000 | ✅ 301 |
| Плашки в LuCI | 7 красных | 0 |
| Размер кэша | — | 84KB (21 файл) |

## Нюансы

1. **file:// vs local:** sing-box 1.12 поддерживает `file://` URL в `url` поле ruleset, даже несмотря на название поля.

2. **download_detour:** для file:// URL не нужен download_detour, sing-box читает файл напрямую.

3. **Обновление:** списки не обновляются автоматически. Нужно периодически повторять Шаг 2.

4. **mixed proxy порт:** может меняться (обычно 4534). Проверять через `grep service-mixed-in /etc/sing-box/config.json`.

## Скилл создан

Полный скилл: `~/.claude/skills/podkop-lists-github-blocked/SKILL.md`

Триггеры: "плашки списков", "GitHub заблокирован", "не могу скачать community lists"
