# Урок: sing-box "too many open files" — Сочи TR5608

**Дата:** 07.05.2026  
**Роутер:** TR5608 (Сочи, провайдер Ростелеком, Tailscale IP: 100.79.40.126)  
**Симптом:** YouTube, Instagram, Netflix не работают. Google, GitHub, Habr работают.

## Симптомы

1. YouTube не открывается (HTTP 000 или таймаут)
2. Google, GitHub, Habr работают нормально
3. ping до bMSK (159.194.198.172) — 25ms, до bSPB (5.35.84.151) — 35ms
4. В логах sing-box:
   ```
   ERROR inbound/tproxy[tproxy-in]: accept tcp ... accept4: too many open files
   ERROR connection: connection upload closed: too many open files
   ```

## Причина

**Лимит open files (4096) исчерпан.** Sing-box на OpenWrt по умолчанию имеет лимит 4096 файловых дескрипторов. При активном использовании (много community листов, много соединений) этот лимит быстро исчерпывается.

**Почему Google/GitHub работали, а YouTube/Netflix нет:**
- Google, GitHub идут через **direct-out** (напрямую, без прокси) — они не создают дополнительных соединений через relay
- YouTube, Netflix идут через **main-out** или **YT-out** (через bMSK relay) — каждое такое соединение требует дополнительных файловых дескрипторов для TLS/REALITY handshake

## Решение

Добавить `procd_set_param limits` в `/etc/init.d/sing-box`:

```bash
# В секцию start_service(), перед procd_set_param stdout 1:
procd_set_param limits "nofile=65536 65536"
```

После правки перезапустить sing-box:
```bash
/etc/init.d/sing-box restart
```

Проверить:
```bash
cat /proc/$(pgrep sing-box)/limits | grep "open files"
# Должно быть: Max open files 65536 65536 files
```

## Текущая конфигурация TR5608

**Main:** bMSK:9443 → PL6:5228 (Польша)
- pbk: `B13kRiGPLxYxU262OY53_DeuWJ3zn10wg1A_2O--qmQ`
- sid: `efab5678`

**YT:** bMSK:465 (прямой inbound на bMSK)
- pbk: `QfVJeoktRoCFJV6YdttWyGHMLnORut86toeStzTsUBk`
- sid: `a3f7b2c1`

**Community листы (20):** telegram, meta, geoblock, block, porn, news, anime, discord, twitter, hdrezka, tiktok, cloudflare, google_ai, google_play, hodca, roblox, hetzner, ovh, digitalocean, cloudfront

## Проверка доступности серверов из Сочи

| Сервер | Порт | Статус |
|--------|------|--------|
| bMSK (159.194.198.172) | 80 (HTTP) | ✅ HTTP 200 |
| bMSK (159.194.198.172) | 5050 (HTTPS, панель) | ✅ HTTP 404 |
| bMSK (159.194.198.172) | 8443 (HTTPS, relay PL6) | ✅ HTTP 400 |
| bMSK (159.194.198.172) | 8880 (HTTPS, relay PL6) | ✅ HTTP 400 |
| bMSK (159.194.198.172) | 9443 (HTTPS, relay PL6) | ✅ HTTP 400 |
| bMSK (159.194.198.172) | 465 (HTTPS, direct) | ✅ HTTP 400 |
| bMSK (159.194.198.172) | 8853 (HTTPS, direct) | ✅ HTTP 400 |
| bSPB (5.35.84.151) | 5050 (HTTPS, панель) | ✅ HTTP 404 |
| bSPB (5.35.84.151) | 80 (HTTP) | ❌ |
| bSPB (5.35.84.151) | 8853 (HTTPS) | ❌ |

**Вывод:** Все порты bMSK доступны из Сочи. Провайдер не блокирует Beget.
