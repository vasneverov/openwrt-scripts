## tr30-25-volosach (100.67.0.52) — диагностика + rescue

**Date:** 2026-05-12
**Router:** tr30-25-volosach
**Tailscale IP:** 100.67.0.52
**SSH pass:** 56756789
**OpenWrt:** 24.10.4 (opkg)
**Tailscale:** 1.94.0-1
**Sing-box:** 1.12.12-extended-1.5.1
**Podkop:** v0.7.10-r1 (устарел, последний v0.7.14)

### Что сделано
1. **Диагностика** — полная (Фаза 1)
2. **rescue_generic.sh** — скопирован и применён
3. **/etc/hosts** — добавлены 4 IP raw.githubusercontent.com

### Состояние
| Параметр | Статус |
|----------|--------|
| Tailscale | ✅ Online, fw_mode=none, init.d DISABLED |
| Podkop | ✅ init.d ENABLED, списки загружены |
| fw4-fix | ❌ Не установлен (OpenWrt 24.10.4 — может не нужно) |
| Прокси | ✅ Италия (151.243.198.86) — relay Italy |
| YouTube | ✅ 301 (FakeIP 198.18.0.25) |
| Telegram | ✅ 200 (FakeIP 198.18.0.26) |
| Google | ❌ 000 — не открывается |
| nftables | ✅ 7 podkop цепочек, счётчики > 0 |
| /etc/hosts | ✅ GitHub CDN добавлен |
| Скрипты | ✅ rescue_generic.sh (остальных нет) |
| Crontab | ✅ 3 watchdog'а + list_update |
| Память | 497MB — норм |
| Диск | 75% (10.7M свободно) — маловато |

### Особенности
- Учётка ne78va (пароль 56756789)
- youtube в main (нет отдельного YT профиля)
- Google 000 — возможно блокировка провайдера
- Podkop v0.7.10 — не последний, но трогать не стали
