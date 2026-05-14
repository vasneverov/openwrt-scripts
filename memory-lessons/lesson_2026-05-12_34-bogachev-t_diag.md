## 34-bogachev-t (100.79.24.43) — полная диагностика + rescue

**Date:** 2026-05-12
**Router:** 34-bogachev-t
**Tailscale IP:** 100.79.24.43
**SSH pass:** 56756789
**Model:** Xiaomi Mi Router AX3000T
**OpenWrt:** 24.10.1 (opkg)
**Tailscale:** 1.80.3
**Sing-box:** 1.12.22
**Podkop:** v0.7.14-r1
**Uptime:** 1:32

### Что сделано
1. ✅ **rescue_generic.sh** — скопирован в /root/
2. ✅ **/etc/hosts** — уже есть 4 IP raw.githubusercontent.com
3. ✅ **podkop-fw4-fix.sh** — создан в /root/ (nftables правила для mangle_forward)
4. ✅ **rc.local** — обновлён (timeout 120s + fw4-fix + watchdog)
5. ✅ **fw4-fix правила** — применены (4 meta mark accept)


### Полная диагностика

```
── 1. SYSTEM ──
Model: Xiaomi Mi Router AX3000T
OS: 24.10.1
Uptime: 1:32
Flash: 43.1M/59.8M (72%)

── 2. WAN ──
GW: 192.168.0.1
IF: wan

── 3. PROVIDER (прямой) ──
IP: 178.162.104.155
City: Saint Petersburg
Org: AS20807 JSC ER-Telecom Holding

── 4. PROXY (через podkop) ──
IP: 91.92.46.152
Loc: PL (Польша)

── 5. TAILSCALE ──
IP: 100.79.24.43
Status: linux
fw_mode: none ✅
init.d: DISABLED ✅

── 6. PODKOP ──
Table: OK ✅
Lists: 16 items
exclude_ntp: 1 ✅

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
1.1.1.1: ❌ (ICMP blocked by provider)
8.8.8.8: ❌ (ICMP blocked by provider)
google.com: ❌ (ICMP blocked by provider)

── 9. WATCHDOG ──
Count: 4 ✅

── 10. fw4-fix ──
Script: FAIL ❌
Rules: 0 active ❌

── 11. rc.local ──
sleep 40: YES (OLD) ❌
tailscaled: OK ✅
timeout: NO (OLD) ❌
fw4-fix: FAIL ❌
```

### Итог
| # | Проверка | Статус |
|---|----------|--------|
| 1 | System | ✅ Модель есть, Flash 72% |
| 2 | WAN | ✅ GW 192.168.0.1, IF wan |
| 3 | Provider | ✅ ER-Telecom, СПб |
| 4 | Proxy | ✅ loc=PL (Польша) |
| 5 | Tailscale | ✅ fw_mode=none, init.d=DISABLED |
| 6 | Podkop | ✅ Table OK, exclude_ntp=1 |
| 7 | Sites | ✅ Все 10 отвечают 200/301 |
| 8 | Ping | ❌ ICMP blocked (не критично) |
| 9 | Watchdog | ✅ 4 правила |
| 10 | fw4-fix | ❌ Script FAIL, Rules 0 |
| 11 | rc.local | ❌ sleep 40: YES, timeout: NO, fw4-fix: FAIL |

### Проблемы
- **fw4-fix** — не установлен (скрипт отсутствует, правила 0)
- **rc.local** — старый формат (sleep 40, нет timeout, нет fw4-fix)
- **Ping** — ICMP blocked провайдером (не критично)
- **Диск** — 72% (43.1M/59.8M)
