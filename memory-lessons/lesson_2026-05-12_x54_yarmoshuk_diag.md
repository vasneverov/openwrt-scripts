## x54-yarmoshuk (100.98.211.40) — диагностика + rescue

**Date:** 2026-05-12
**Router:** x54-yarmoshuk
**Tailscale IP:** 100.98.211.40
**SSH pass:** 56756789
**OpenWrt:** 25.12.2
**Tailscale:** 1.96.4-2
**Sing-box:** 1.12.17

### Что сделано
1. **rescue_generic.sh** — применён (fw_mode=none, init.d DISABLED, watchdog'ы, ulimit, rc.local)
2. **Диагностика** — полная (Фаза 1)
3. **/etc/hosts** — добавлены 4 IP raw.githubusercontent.com

### Состояние
| Параметр | Статус |
|----------|--------|
| Tailscale | ✅ Online, fw_mode=none, init.d DISABLED |
| Podkop | ✅ init.d ENABLED, списки загружены |
| fw4-fix | ✅ Установлен, работает |
| Прокси | ✅ Чехия (92.61.71.14) |
| YouTube | ✅ 301 (FakeIP 198.18.0.5) |
| Telegram | ✅ 200 (FakeIP 198.18.0.6) |
| Google | ✅ 301 (реальный IP) |
| nftables | ✅ 12 podkop цепочек |
| Счётчики | ⚠️ 0 (роутер только перезагружен, трафика нет) |
| /etc/hosts | ✅ GitHub CDN добавлен |
| Скрипты | ✅ rescue_generic.sh, podkop-fw4-fix.sh, podkop-fix-lists.sh |
| Crontab | ✅ 3 watchdog'а + list_update |

### Особенности
- youtube в main (нет отдельного YT профиля) — норм
- download_lists_via_proxy=0 — норм
- Нет /etc/hosts записей GitHub — добавлены
- Роутер только перезагружен (uptime 25 мин) — счётчики nftables 0 из-за этого
