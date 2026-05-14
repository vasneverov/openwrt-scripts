## 52-sfilin (100.91.163.17) — диагностика + rescue

**Date:** 2026-05-12
**Router:** 52-sfilin
**Tailscale IP:** 100.91.163.17
**SSH pass:** 56756789
**OpenWrt:** 24.10.1 (opkg)
**Tailscale:** 1.80.3
**Sing-box:** 1.12.22
**Podkop:** v0.7.14-r1 (свежий)
**Uptime:** 73 дня

### Что сделано
1. ✅ **rescue_generic.sh** — скопирован и применён
2. ✅ **/etc/hosts** — добавлены 4 IP raw.githubusercontent.com

### Состояние
| Параметр | Статус |
|----------|--------|
| Tailscale | ✅ Online, fw_mode=none, init.d DISABLED |
| Podkop | ✅ v0.7.14-r1, init.d ENABLED |
| Прокси | ✅ Чехия (85.137.164.179 — smartape.net) |
| Google | ✅ 301 (64.233.162.100) |
| YouTube | ❌ 000 |
| Telegram | ✅ 200 (149.154.167.99 — прямой) |
| Facebook | ✅ 301 (157.240.205.35 — прямой) |
| Instagram | ✅ 301 (157.240.205.174 — прямой) |
| nftables | ✅ есть |
| /etc/hosts | ✅ GitHub CDN добавлен |
| Скрипты | ✅ rescue_generic.sh |
| Память | 239MB |
| Диск | 58% (23.6M свободно) |

### Проблемы
- **YouTube 000** — не работает через podkop
- **Учётка vas.neverov** (не ne78va)
- **Uptime 73 дня** — давно не перезагружался
- **Память 239MB** — мало
- **cache-file timeout** — sing-box падает с `FATAL initialize cache-file: timeout` при старте
- **ulimit 4096** — procd не поддерживает `procd_set_param limits` на OpenWrt 24.10
- **Роутер потух** — после killall -9 sing-box перестал отвечать, нужна перезагрузка питанием

### План (после перезагрузки)
1. Полное удаление podkop + sing-box
2. Чистая установка через скрипт itdog
3. Настройка ключа
4. Проверка YouTube
