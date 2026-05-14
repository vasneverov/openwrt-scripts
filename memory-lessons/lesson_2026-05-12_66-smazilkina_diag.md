## 66-smazilkina (100.89.121.33) — диагностика + rescue

**Date:** 2026-05-12
**Router:** 66-smazilkina
**Tailscale IP:** 100.89.121.33
**SSH pass:** 56756789
**OpenWrt:** 24.10.1 (opkg)
**Tailscale:** 1.80.3
**Sing-box:** 1.12.4
**Podkop:** v0.6.2-r1 (очень старый)
**Uptime:** 55 дней

### Что сделано
1. **rescue_generic.sh** — скопирован и применён
2. **/etc/hosts** — добавлены 4 IP raw.githubusercontent.com
3. **Полный отчёт** — система, tailscale, podkop, тесты сайтов

### Состояние
| Параметр | Статус |
|----------|--------|
| Tailscale | ✅ Online, fw_mode=none, init.d DISABLED |
| Podkop | ✅ init.d ENABLED, списки загружены |
| fw4-fix | ❌ Не установлен |
| Прокси | ❌ Нет — ipinfo показывает Москва (217.15.56.7) |
| Google | ✅ 301 (64.233.163.101 — реальный IP) |
| YouTube | ❌ 000 |
| Telegram | ❌ 000 |
| Все сайты | ❌ 000 — podkop не работает |
| nftables | ✅ 7 цепочек, счётчики TCP > 0, UDP = 0 |
| /etc/hosts | ✅ GitHub CDN добавлен |
| Скрипты | ✅ rescue_generic.sh (остальных нет) |
| Crontab | ✅ ts-watchdog есть |
| Память | 239MB — маловато |
| Диск | 53% (26.5M свободно) — норм |

### Проблемы
- **Podkop v0.6.2** — очень старый. Все сайты 000 — podkop не проксирует трафик
- **Прокси нет** — ipinfo показывает Москву (217.15.56.7), не Италию
- **Учётка vas.neverov** (не ne78va)
- **Sing-box 1.12.4** — старый
- **Tailscale 1.80.3** — старый
- **Память 239MB** — мало, но для OpenWrt норм
