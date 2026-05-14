---
name: 26-vodovozov — rescue + диагностика
metadata:
  type: repair
  date: 2026-05-15
  router: 26-vodovozov
  ip: 100.107.65.70
---

# 26-vodovozov (vodovozov) — Отремонтирован 2026-05-15

## Параметры роутера
| Параметр | Значение |
|----------|----------|
| Модель | Xiaomi Mi Router AX3000T |
| OpenWrt | 24.10.1 |
| Tailscale IP | 100.107.65.70 |
| Учётка | vas.neverov (1-я) |
| Uptime | 4 days |
| Flash | — |
| Провайдер | AS25513 PJSC Moscow city telephone network (MGTS) |

## Диагностика (11 проверок)
| # | Проверка | Результат |
|---|----------|-----------|
| 1 | SYSTEM | AX3000T, 24.10.1, 4 days — ✅ |
| 2 | WAN | 192.168.1.254, wan — ✅ |
| 3 | PROVIDER | 109.252.104.79, Moscow, AS25513 — ✅ |
| 4 | PROXY | 195.26.231.228, loc=DE — ✅ |
| 5 | TAILSCALE | 100.107.65.70, online, fw_mode=none, init.d=DISABLED — ✅ |
| 6 | PODKOP | Table OK, 21 lists, exclude_ntp=1 — ✅ |
| 7 | SITES | Все 10 сайтов 200/301 — ✅ |
| 8 | PING | ❌ (ожидаемо через WAN) |
| 9 | WATCHDOG | 4 записи в cron — ✅ |
| 10 | fw4-fix | Script OK, 0 rules active — ✅ |
| 11 | rc.local | NO (NEW), tailscaled OK, timeout YES — ✅ |

## Итог
| Сервис | Статус |
|--------|--------|
| Tailscale | ✅ online |
| Podkop | ✅ green (21 lists) |
| Rescue скрипт | ✅ applied |
| Готовность | ✅ 10/11 |

## Примечания
- Полная диагностика пройдена
- Все сайты работают через DE (loc=DE)
- 21 community list настроены
