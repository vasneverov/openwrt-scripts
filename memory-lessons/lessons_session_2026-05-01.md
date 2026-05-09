# Уроки сессии 01.05.2026

## 1. СИСТЕМНАЯ ДЫРА: rescue скрипт не добавлял tailscale0 в firewall

**Симптом:** Tailscale онлайн (connectedToControl=True, lastSeen обновляется), но SSH и LuCI недоступны.
**Причина:** `fix-tailscale-openwrt.sh` не имел шага добавления tailscale0 в LAN зону firewall.
**Исправление:** Добавлен шаг [5/6]:
```sh
uci set firewall.@zone[0].device='br-lan tailscale0'
uci commit firewall
/etc/init.d/firewall reload
```
**Скрипт обновлён** в GitHub (vasneverov/openwrt-fix). Проверять через GitHub API, не raw CDN (кешируется).

---

## 2. GitHub push из CLAUDECODE блокируется большими файлами

CLAUDECODE репозиторий содержит большие файлы (MOV, chrome-headless-shell >100MB).
**Решение:** клонировать нужный репо в /tmp, скопировать файл, пушить оттуда.
```bash
cd /tmp && git clone https://github.com/vasneverov/openwrt-fix.git
cp ~/CLAUDECODE/tools/fix-tailscale-openwrt.sh /tmp/openwrt-fix/
cd /tmp/openwrt-fix && git add . && git commit -m "..." && git push
```

---

## 3. Всегда последняя учётка Tailscale = n78rout

Остальные учётки (vas.neverov, ne78va, 56papezde) полные.
При прошивке новых роутеров — всегда n78rout без вопросов.

---

## 4. WiFi клиент как временный WAN

Если у роутера нет проводного интернета — можно дать через WiFi клиент:
```bash
uci set network.wwan=interface
uci set network.wwan.proto='dhcp'
uci set network.wwan.metric='20'
uci commit network
uci set wireless.wwan=wifi-iface
uci set wireless.wwan.device='radio1'
uci set wireless.wwan.mode='sta'
uci set wireless.wwan.network='wwan'
uci set wireless.wwan.ssid='SSID'
uci set wireless.wwan.encryption='psk2'
uci set wireless.wwan.key='PASSWORD'
uci commit wireless
wifi up
```
После прошивки — удалить:
```bash
uci delete wireless.wwan
uci delete network.wwan
uci commit wireless && uci commit network && wifi reload
```

---

## 5. Серебрица (tr30-05-serebritsa)

- **IP LAN:** 192.168.3.1 (SSH работает с паролем 56756789)
- **SSID:** @RedHat
- **Пароль WiFi:** 56756789
- **Tailscale:** 100.69.174.52 (vas.neverov)

---

## 6. TR-08 — прошит сегодня

- **Модель:** Cudy TR3000 v1
- **OpenWrt:** 25.12.0
- **Tailscale:** 100.71.253.124 (n78rout)
- **Main:** Italy relay 5.35.84.151:2090
- **YT:** bSPB 5.35.84.151:8853
- **WAN при прошивке:** WiFi @RedHat (удалён после)

---

## 7. z56-110 и TR56-07 — ожидают AnyDesk

Оба роутера: Tailscale онлайн, но SSH/LuCI заблокированы (tailscale0 не в LAN firewall).
Исправление — rescue скрипт через AnyDesk.
- **z56-110:** 100.68.141.32 (56papezde)
- **TR56-07:** 100.115.89.110 (56papezde)

---

## 8. Tailscale API online=None ≠ offline

Поле `online` в API v2 может быть `null` даже когда роутер активен.
Реальный индикатор — `connectedToControl: true` + `lastSeen` обновляется в реальном времени.
