# Lesson: LAN роутер 192.168.5.1 — спасительный + Tailscale NoState

## Дата
2026-05-13, ~19:00

## Роутер
- IP: 192.168.5.1 (через WiFi)
- Внешний IP: 77.50.122.54 (Москва, RU)
- Uptime: 8ч33м

## Проблема
Роутер на LAN — Tailscale в NoState (не мог достучаться до координатора).
Прокси работал через Чехию (85.137.164.179, CZ).

## Что сделано

### 1. Спасительный скрипт
`rescue_generic.sh` — 11/11 шагов:
- fw_mode: nftables → none
- init.d/tailscale: DISABLED
- WAN ifname: добавлен из device
- ulimit + sysctl: fs.file-max 23945 → 65536
- exclude_ntp: 0 → 1
- enable_output_network_interface: 0 → 1
- direct_domains: tailscale.com, controlplane.tailscale.com, login.tailscale.com
- /root/podkop-fw4-fix.sh — nftables fix
- rc.local — новый (timeout + fw4-fix + watchdog)
- firewall — tailscale0 в LAN зону (конфиг, без перезагрузки)
- 3 watchdog'а: ts-watchdog v3.1, podkop-watchdog, route-watchdog
- crontab — watchdog'ы каждые 2 мин + list_update раз в 3ч
- /usr/bin/check-ip — скрипт диагностики

### 2. Tailscale NoState — починился сам
После спасительного Tailscale был в NoState. Через ~30-60 сек watchdog поднял — Tailscale стал зелёным.

### 3. Диагностика — зелёная
- Через прокси: 85.137.164.179 (Чехия)
- Напрямую: 77.50.122.54 (Москва)
- Все сайты: 200/301, тайминги 0.25-0.7с

## Что важно
- Спасительный льётся без перезагрузки — Tailscale и Podkop не трогает
- Watchdog сам чинит NoState на Tailscale (killall tailscaled + перезапуск)
- check-ip — удобная диагностика в один вызов
- Разные роутеры могут сидеть на одном LAN IP (192.168.5.1) — known_hosts чистить перед SSH
