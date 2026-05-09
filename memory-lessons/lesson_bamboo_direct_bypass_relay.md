---
name: Bamboo Lab и другие IP-whitelist сервисы — обход через прямой ключ
description: Когда relay даёт российский IP — добавлять отдельную podkop секцию с прямым европейским ключом
date: 2026-04-26
type: pattern
critical: false
---

# Паттерн: IP-чувствительные сервисы в podkop

## Проблема

Стандартный main-ключ в podkop обычно идёт через **relay на bSPB** (5.35.84.151, Санкт-Петербург).
Relay нужен для:
- Telegram-звонков (из российской подсети проходят без проблем)
- Обхода российских белых списков

**Но:** сервисы вроде Bamboo Lab (3D-принтеры), MakerWorld и другие с IP-whitelist видят **российский IP** из relay и могут ограничивать функционал.

## Решение — отдельная секция с прямым европейским ключом

Добавить в podkop секцию (например `bamboo`) с прямым ключом на Fin3/Fin4/другой европейский сервер.

### Пример реализации (M56-13)

```bash
# VLESS_DIRECT = прямой ключ на Fin3 (5.35.84.151:4191 → DNAT → 144.31.66.115, Finnish IP)
VLESS_DIRECT="vless://UUID@5.35.84.151:4191?type=grpc&security=reality&mode=gun&serviceName=&pbk=XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw&sid=932e706c&sni=www.apple.com&fp=chrome&spx=%2F#M56-XX_bamboo_Fin3"

uci set podkop.bamboo=section
uci set podkop.bamboo.enabled='1'
uci set podkop.bamboo.connection_type='proxy'
uci set podkop.bamboo.proxy_config_type='url'
uci set podkop.bamboo.proxy_string="$VLESS_DIRECT"
uci set podkop.bamboo.mixed_proxy_enabled='0'
uci set podkop.bamboo.user_domain_list_type='text'
uci set podkop.bamboo.user_subnet_list_type='disabled'
uci set podkop.bamboo.user_domains_text='us.mqtt.bambulab.com
makerworld.com'
uci commit podkop
/etc/init.d/podkop restart
```

### UCI имя секции
- Для M56/TR56/S78: использовать **lowercase** (`bamboo`, не `BAMBOO`)
- YT секция — uppercase `YT` на M56/TR56, lowercase `yt` на z56 — это только для YT

## Как понять что нужна прямая секция

**Симптомы:** сервис работает, но урезанный функционал / не авторизует аккаунт / EU-только фичи

**Диагностика:**
```bash
# Через какой IP выходит трафик к проблемному домену?
# На роутере (если есть curl):
curl -s --max-time 5 https://api.ipify.org  # без proxy = WAN IP
```

Если WAN IP российский, а сервис требует EU — нужна прямая секция.

## Какие ключи использовать

| Сервер | Выход | Когда использовать |
|--------|-------|--------------------|
| Fin3 relay (5.35.84.151:4191 → 144.31.66.115) | 🇫🇮 Finnish | Bamboo Lab, EU-only сервисы |
| Italy relay (5.35.84.151:2090 → 151.243.198.86) | 🇮🇹 Italian | Альтернатива |
| bSPB direct (5.35.84.151:8853) | 🇷🇺 Russian | YT, Telegram (уже настроено) |

UUID для роутера берётся из `~/CLAUDECODE/ключи/new_m56/vless_m56_13-22_VERIFIED.md`

## Практика сессии 2026-04-26

- Роутер: M56-13 (100.76.253.51, n78rout)
- Домены: `us.mqtt.bambulab.com`, `makerworld.com`
- Ключ: M56-13 Fin3 UUID `3914029b-148d-4554-b6b0-95cfe6bf7964`
- Результат: sing-box создал `bamboo-out` и `bamboo-user-domains-ruleset`, принтер видит финский IP ✅
