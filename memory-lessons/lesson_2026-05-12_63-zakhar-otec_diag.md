## 63-zakhar-otec (100.75.45.59) — полная диагностика + rescue

**Date:** 2026-05-12
**Router:** 63-zakhar-otec
**Tailscale IP:** 100.75.45.59
**SSH pass:** 56756789
**Model:** OpenWrt 24.10.1
**Uptime:** 6 days
**Flash:** 28.5M/59.8M (50%)
**Podkop:** v0.5.8
**Tailscale:** 1.80.3

### Что сделано
1. ✅ **fix-tailscale-openwrt.sh** — закинут (спасительный скрипт)
2. ✅ **fw4-fix** — создан и применён (4 правила)
3. ✅ **rc.local** — новый формат (timeout 120s + fw4-fix + watchdog)
4. ✅ **ulimit** — добавлен в podkop + sing-box init.d
5. ✅ **fs.file-max** — 23897 → 65536
6. ✅ **WAN ifname** — wan (был device, добавлен ifname)
7. ✅ **Watchdog'ы** — 3 шт (ts + podkop + route)
8. ✅ **Crontab** — обновлён

### Полная диагностика

```
── 1. SYSTEM ──
OpenWrt 24.10.1
Uptime: 6 days
Flash: 28.5M/59.8M (50%)

── 2. WAN ──
GW: 87.240.49.1
IF: wan

── 3. PROVIDER (прямой) ──
IP: 87.240.49.212
City: Moscow
Org: AS42610 PJSC Rostelecom

── 4. PROXY (через podkop) ──
IP: 91.92.46.152
Loc: PL (Польша)

── 5. TAILSCALE ──
IP: 100.75.45.59
Status: linux
fw_mode: none ✅
init.d: DISABLED ✅

── 6. PODKOP ──
Table: OK ✅
Lists: 0 (v0.5.8 — community_lists не поддерживается)

── 7. SITES (все через прокси) ──
google.com      301 ✅
youtube.com     301 ✅
telegram.org    200 ✅
facebook.com    301 ✅
instagram.com   301 ✅
rutracker.org   301 ✅
tiktok.com      301 ✅
x.com           200 ✅
discord.com     200 ✅
github.com      200 ✅

── 8. PING ──
1.1.1.1: OK ✅
8.8.8.8: OK ✅
google.com: OK ✅

── 9. WATCHDOG ──
Count: 3 ✅

── 10. fw4-fix ──
Script: OK ✅
Rules: 4 ✅

── 11. rc.local ──
timeout: YES ✅
tailscaled: OK ✅
fw4-fix: OK ✅
```

### Итог
| # | Проверка | Статус |
|---|----------|--------|
| 1 | System | ✅ OpenWrt 24.10.1, Flash 50% |
| 2 | WAN | ✅ GW 87.240.49.1, IF wan |
| 3 | Provider | ✅ Rostelecom, Москва |
| 4 | Proxy | ✅ loc=PL (Польша) |
| 5 | Tailscale | ✅ fw_mode=none, init.d=DISABLED |
| 6 | Podkop | ✅ Table OK, v0.5.8 |
| 7 | Sites | ✅ Все 10 отвечают 200/301 |
| 8 | Ping | ✅ Все 3 OK |
| 9 | Watchdog | ✅ 3 правила |
| 10 | fw4-fix | ✅ Script OK, Rules 4 |
| 11 | rc.local | ✅ timeout YES, fw4-fix OK |

### Проблемы
- **Нет** — все проверки зелёные
- Podkop v0.5.8 — старая версия, community_lists не поддерживается (0 списков)
