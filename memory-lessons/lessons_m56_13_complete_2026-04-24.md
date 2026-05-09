---
name: Уроки M56-13 — полный цикл отладки
description: Все уроки из 3+ часов работы с M56-13: Motorcomm PHY, firewall, rc.local, DNS
date: 2026-04-24
type: feedback
originSessionId: de229e55-1495-45ad-81f8-f1e14c05362a
---
# Уроки M56-13 (Cudy M3000 v2) — полный цикл

## 1. M3000 v2 — Motorcomm YT8821 PHY

**Признак:** Серийный номер начинается на "25" (например 250512...)

**Прошивка:**
- Файл: `openwrt-25.12.2-mediatek-filogic-cudy_m3000-v2-yt8821-squashfs-sysupgrade.bin`
- После factory прошивки — **force upgrade**:
```bash
sysupgrade -F /tmp/firmware.bin
```

## 2. Tailscale — НИКОГДА не добавлять tailscale0 в firewall

**Ошибка:**
```bash
uci set firewall.@zone[0].device='br-lan tailscale0'  # ❌ ЛОМАЕТ Tailscale
```

**Правильно:**
```bash
uci set firewall.@zone[0].device='br-lan'  # ✅ Tailscale и так работает через userspace-networking
```

**Почему:** При добавлении tailscale0 в LAN зону firewall, Tailscale не может достучаться до controlplane.tailscale.com через podkop.

## 3. rc.local — правильный тайминг для M-серии

**Вариант 1 (рабочий на M56-13):**
```bash
#!/bin/sh
sleep 25
tailscaled --tun=userspace-networking --statedir=/etc/tailscale >/dev/null 2>&1 &
sleep 15
tailscale up --accept-routes --timeout=30s
exit 0
```

**Важно:** Без `--state=` (только `--statedir`), с полным путем `/usr/sbin/tailscaled`.

## 4. Проверка перед ребутом — смотреть в скилл

**Недостаточно:** 7-пунктовая проверка
**Нужно:** Открыть скилл `flashing-openwrt-router` и свериться с Шагом 5 и Шагом 7

**Особенно проверить:**
- rc.local (нет ли `--state=`)
- firewall (нет ли tailscale0)
- Все 5 пунктов готовности

## 5. DNS + podkop + Tailscale

**Проблема:** Когда podkop запущен, DNS через 127.0.0.1 может не резолвить controlplane.tailscale.com.

**Решение:** Временно остановить podkop, дать Tailscale подключиться, потом запустить podkop.

## 6. Стабильность Tailscale

**Факторы стабильности:**
1. Правильный rc.local (тайминг, параметры)
2. Без tailscale0 в firewall
3. exclude_ntp='1' в podkop
4. fw_mode='none' в tailscale
5. init.d/tailscale disabled

## 7. Диагностика

**Если точка серая:**
1. Проверить `tailscale status` — что показывает
2. Проверить `ps | grep tailscaled` — работает ли процесс
3. Проверить DNS: `nslookup controlplane.tailscale.com`
4. Проверить firewall: `uci get firewall.@zone[0].device`
5. Проверить лог: `tail -20 /tmp/ts.log`

## Сводная таблица M3000

| Параметр | M3000 v1 | M3000 v2 (Motorcomm) |
|----------|----------|----------------------|
| Серийник | 24xxxx | 25xxxx |
| Прошивка | m3000-v1 | m3000-v2-yt8821 |
| Force upgrade | Не нужен | Нужен (-F) |

## Итог

**M56-13:**
- ✅ Прошивка: OpenWrt 25.12.2 v2-yt8821
- ✅ Tailscale: 100.76.253.51 (стабильно)
- ✅ Podkop: запущен
- ✅ Firewall: только br-lan (без tailscale0)

**Why:** Каждая ошибка (tailscale0 в firewall, неправильный rc.local) приводила к падению Tailscale через 30-40 секунд.
**How to apply:** Всегда проверять серийник для M3000, никогда не добавлять tailscale0 в firewall, перед ребутом сверяться со скиллом.
