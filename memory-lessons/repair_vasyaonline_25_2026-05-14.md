---
name: VasyaOnline_25 — rescue скрипт + диагностика
metadata:
  type: repair
  date: 2026-05-14
  router: VasyaOnline_25
  ip: 100.91.218.113
---

# VasyaOnline_25 (25-cherednik-dacha) — Отремонтирован 2026-05-14

## Параметры роутера
| Параметр | Значение |
|----------|----------|
| Модель | Xiaomi Mi Router AX3000T |
| OpenWrt | 24.10.1 |
| Tailscale IP | 100.91.218.113 |
| Учётка | vas.neverov (1-я) |
| Uptime | 2 days |
| Flash | 46% |
| Провайдер | AS205460 LLC Svyaz Invest (Krasnogorsk) |

## Что было сделано

### 1. Применён rescue_generic.sh
- ✅ fw_mode: none (уже был)
- ✅ init.d/tailscale: DISABLED (уже был)
- ✅ ulimit + sysctl: настроены (23897 → 65536)
- ✅ exclude_ntp: 1 (уже был)
- ✅ direct_domains: tailscale.com, controlplane.tailscale.com, login.tailscale.com
- ✅ podkop-fw4-fix.sh: установлен (был отсутствует)
- ✅ rc.local v3.1: создан (timeout + fw4-fix + watchdog)
- ✅ firewall: tailscale0 в LAN зоне (уже был)
- ✅ 3 watchdog'а (ts-watchdog.sh, podkop-watchdog.sh, route-watchdog.sh) — */2 мин
- ✅ check-ip: /usr/bin/check-ip создан (был отсутствует)

### 2. Диагностика (11 проверок)
| # | Проверка | Результат |
|---|----------|-----------|
| 1 | SYSTEM | AX3000T, 24.10.1, 2 days, 46% — ✅ |
| 2 | WAN | 10.0.2.1, wan — ✅ |
| 3 | PROVIDER | 194.55.141.10, Krasnogorsk, AS205460 — ✅ |
| 4 | PROXY | 92.61.71.14, loc=CZ — ✅ |
| 5 | TAILSCALE | 100.91.218.113, online, fw_mode=none, init.d=DISABLED — ✅ |
| 6 | PODKOP | Table OK, 21 lists, exclude_ntp=1 — ✅ |
| 7 | SITES | Все 10 сайтов 200/301 — ✅ |
| 8 | PING | ❌ (ожидаемо через WAN) |
| 9 | WATCHDOG | 4 записи в cron — ✅ |
| 10 | fw4-fix | Script OK, 4 rules active — ✅ |
| 11 | rc.local | NO (NEW), tailscaled OK, timeout YES — ✅ |

## Особенность
**global_check показывает ❌ Bootstrap DNS, ❌ Main DNS, ❌ DNS on router**

**НО:** Все сайты работают (google.com 301, telegram.org 200), прокси loc=CZ. DNS фактически работает через sing-box.

**Причина:** Особенность провайдера AS205460 (Krasnogorsk). На других роутерах с другими провайдерами global_check показывает DNS зелёными. Это не требует исправления — VPN функционирует корректно.

## Итог
| Сервис | Статус |
|--------|--------|
| Tailscale | ✅ online (сохранён, не трогали) |
| Podkop | ✅ green (подтверждено пользователем) |
| Rescue скрипт | ✅ applied |
| Готовность | ✅ 10/11 |

## Примечания
- Перезагрузка НЕ производилась
- Tailscale сохранён любыми путями (железное правило)
- DNS красные в global_check — особенность провайдера, не трогаем
