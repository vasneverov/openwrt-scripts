# Уроки сессии 30.04.2026 (вечер, часть 2)
# Роутеры: x001-borov1, z56-81, 32-ezhov-mama, GitHub rescue script

---

## УРОК 1 — КРАСНЫЕ КЛЮЧИ В ПОДКОПЕ = ТОЛЬКО ЗАМЕНА КЛЮЧЕЙ

**Симптом:** Ключи красные в LuCI подкопа, трафик не идёт.

**Неправильное действие (потеря времени):**
- Проверять логи sing-box
- Делать nc/curl тесты портов с роутера
- Перезапускать podkop вручную
- Смотреть nft таблицы

**Правильное действие — сразу:**
1. `ls ~/CLAUDECODE/tools/` — проверить скрипты
2. Создать нового клиента на нужном сервере (Fin4/bMSK/Fin3/bSPB)
3. `kill -9 $(pgrep xray)` на сервере
4. `grep -c 'UUID' /usr/local/x-ui/bin/config.json` → > 0
5. `check_vless.py → READY ✓✓✓`
6. `uci set podkop.main.proxy_string='...'` + `uci commit` + restart podkop

**Подтверждение:** x001-borov1 — заменили UUID, ключи сразу позеленели.

---

## УРОК 2 — X-UI ПАНЕЛЬ ПОРТ И BASEPATH

**bMSK и Fin4 панели:**
- Порт: `5050`
- webBasePath: `/5050/`
- Полный URL: `https://HOST:5050/5050/login`, `https://HOST:5050/5050/panel/api/inbounds/...`
- Узнать: `ssh root@HOST "/usr/local/x-ui/x-ui setting -show"`

**Не 54321 и не просто `/login`.**

---

## УРОК 3 — ПОСЛЕ GIT PUSH ВСЕГДА ПРОВЕРЯТЬ ЧЕРЕЗ CURL

**Неправильно:** сказать "запушено" после `git push ok`

**Правильно:**
```bash
git push origin main
sleep 5
curl -s "https://raw.githubusercontent.com/USER/REPO/main/FILE" | grep -c "СТРОКА_ИЗ_НОВЫХ_ИЗМЕНЕНИЙ"
# > 0 → теперь говорить "обновлено"
```

**Почему:** CDN raw.githubusercontent.com может кешировать старую версию. Push может сообщить "ok" локально, но контент ещё старый.

---

## УРОК 4 — community_lists: ТОЛЬКО list FORMAT, НЕ option

**Неправильно (создаёт одну строку с пробелами):**
```bash
uci set podkop.main.community_lists='telegram meta geoblock ...'
```

**Правильно (создаёт отдельные list элементы):**
```bash
uci del podkop.main.community_lists 2>/dev/null
uci add_list podkop.main.community_lists='telegram'
uci add_list podkop.main.community_lists='meta'
uci add_list podkop.main.community_lists='geoblock'
...
```

**Признак проблемы:** в `/etc/config/podkop` видно `option community_lists 'telegram meta geoblock...'` вместо отдельных `list community_lists 'telegram'`.

---

## УРОК 5 — BUSYBOX NC НЕ ПОДДЕРЖИВАЕТ -z

На OpenWrt `nc -z host port` → печатает usage и возвращает ненулевой exit code.

**Правильная проверка TCP-доступности с роутера:**
```bash
(echo '' | nc 159.194.198.172 8853); echo "exit: $?"
# exit: 0 = порт доступен
```

---

## УРОК 6 — АЛГОРИТМ СОЗДАНИЯ МОСКОВСКИХ КЛЮЧЕЙ (bMSK пакет)

| Секция | Сервер регистрации UUID | Ключ proxy_string |
|--------|------------------------|-------------------|
| main   | Fin4 inbound 1 (port 4191) | bMSK:5223 relay |
| YT     | bMSK inbound 1 (port 8853) | bMSK:8853 direct |

```python
# Fin4 inbound_id = 1, bMSK inbound_id = 1
# webBasePath /5050/ у обоих
# Fin4 SSH: duqwgjXiT4FRrc
# bMSK SSH: Ujkjdf56#
```

После создания: `kill -9 $(pgrep xray)` на обоих серверах.

---

## УРОК 7 — СПАСИТЕЛЬНЫЙ СКРИПТ НА GITHUB

URL: `sh <(wget -O - https://raw.githubusercontent.com/vasneverov/openwrt-fix/main/fix-tailscale-openwrt.sh)`

Репозиторий: `vasneverov/openwrt-fix` (НЕ openwrt-scripts!)
Локальный клон для пуша: `/tmp/openwrt-fix/`

**Что делает скрипт:**
1. fw_mode → none
2. podkop: exclude_ntp=1, mixed_proxy=0
3. rc.local → userspace-networking tailscaled
4. watchdog: ts-watchdog + podkop-watchdog в crontab
5. Tailscale → перезапуск
6. Итог с ✅/❌ по каждому пункту + "SSH готов"
