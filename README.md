# openwrt-scripts

Скрипты для автоматической прошивки, настройки и восстановления роутеров на OpenWrt с Podkop + Tailscale.

---

## Быстрый доступ

| Что нужно | Команда |
|-----------|---------|
| **Спасти роутер** (Tailscale слетел) | `sh <(wget -O - https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/fix-tailscale-openwrt.sh)` |
| **Проверить IP** | `check-ip` (на роутере) |

---

## fix-tailscale-openwrt.sh — универсальный спасительный скрипт

**Когда применять:** Роутер перезагрузился, Tailscale не поднялся, Podkop не работает, сайты не открываются.

**Запуск (через AnyDesk или локально):**
```bash
sh <(wget -O - https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/fix-tailscale-openwrt.sh)
```

**Или через SSH (если Tailscale ещё жив):**
```bash
ssh root@100.X.X.X "sh <(wget -O - https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/fix-tailscale-openwrt.sh)"
```

### Что делает скрипт (13 шагов)

| Шаг | Что делает | Зачем |
|-----|-----------|-------|
| **1** | `fw_mode=none` | Отключает встроенный firewall Tailscale — он конфликтует с nftables на OpenWrt 25.12 |
| **2** | `init.d/tailscale disable` | Отключает автозапуск tailscale через init.d — tailscaled запускается через rc.local (userspace-networking) |
| **3** | WAN ifname | Podkop требует `ifname`, а не `device`. Если в конфиге только `device` — добавляет `ifname` |
| **4** | Podkop настройки | Включает `exclude_ntp=1` (не ломать NTP), `enable_output=1` (вывод в сетевой интерфейс), отключает `mixed_proxy` |
| **5** | rc.local | Создаёт `/etc/rc.local` с tailscaled в userspace-networking режиме — запускается через 40 сек после загрузки |
| **6** | firewall LAN | Добавляет `tailscale0` в LAN зону firewall (без reload, чтобы не оборвать текущее соединение) |
| **7** | Watchdog'ы | 3 скрипта в `/etc/`: **ts-watchdog** (восстанавливает rc.local и tailscaled), **podkop-watchdog** (перезапускает sing-box если упал), **route-watchdog** (восстанавливает FakeIP маршруты и PodkopTable) |
| **8** | Crontab | Добавляет watchdog'ы в cron (каждые 2 минуты) + `podkop list_update` каждые 3 часа |
| **9** | check-ip | Устанавливает скрипт диагностики `/usr/bin/check-ip` — показывает IP через прокси и напрямую, тестирует сайты |
| **10** | podkop-fw4-fix | **Только для OpenWrt 25.12+ (fw4/nftables).** Исправляет баг: PodkopTable с hook prerouting НЕ ВИДИТ forwarded трафик от LAN-клиентов. Добавляет правила маркировки в `inet fw4 mangle_forward` (hook forward) |
| **11** | podkop-fix-lists | Чинит обновление community листов podkop — проверяет доступность raw.githubusercontent.com, добавляет рабочие IP в /etc/hosts |
| **12** | Проверка firewall | Проверяет что PodkopTable жива и fw4-fix правила установлены |
| **13** | Финальная диагностика | Показывает WAN статус, пинг, DNS, сводную таблицу |

**В конце:** автоматически запускается `check-ip` через 3 секунды — показывает IP через прокси, напрямую и тесты сайтов.

### Железные правила скрипта

| ❌ Не делает | Почему |
|-------------|--------|
| Не перезагружает Tailscale | Оборвётся SSH-соединение |
| Не рестартит Podkop | Может сломать маршрутизацию |
| Не делает `firewall reload` | Сбросит правила Tailscale |
| Не ребутит роутер | Очевидно |

---

## Два бага Tailscale в OpenWrt 25.12

В дефолтном пакете `/etc/init.d/tailscale` два бага:

**Баг 1 — `--statedir=/var/lib/tailscale` захардкожен**
`/var/lib/` — tmpfs (RAM), стирается при перезагрузке. После ребута: `Logged out`.
Фикс: tailscaled запускается через rc.local с `--statedir=/etc/tailscale/` (persistent flash).

**Баг 2 — `TS_DEBUG_FIREWALL_MODE="none"` захардкожен**
OpenWrt 25.12 не имеет `iptables`, только `nftables`. С `"none"` tailscaled падает через ~10 сек — зелёная точка тухнет.
Фикс: `fw_mode=none` в UCI + userspace-networking режим.

---

## Структура репозитория

```
openwrt-scripts/
├── fix-tailscale-openwrt.sh    ← универсальный спасительный скрипт
├── fix-vasin-boss.sh           ← старый скрипт восстановления
├── tools/
│   ├── podkop-fw4-fix.sh       ← фикс forwarded трафика для fw4/nftables
│   └── podkop-fix-lists.sh     ← фикс обновления community листов
├── WR3000H/setup-wr3000h.sh    ← прошивка Cudy WR3000H
├── WR3000S/setup-wr3000s.sh    ← прошивка Cudy WR3000S
└── README.md
```

---

## Прошивка новых роутеров

### Cudy WR3000H (OpenWrt 25.12)

```bash
./setup-wr3000h.sh 112   # 112 — номер роутера (z56-112)
```

**Предусловие:** роутер прошит OpenWrt 25.12, доступен на `192.168.1.1` без пароля.

### Cudy WR3000S (OpenWrt 25.12)

```bash
./setup-wr3000s.sh 112   # 112 — номер роутера (z56-112)
```

**Предусловие:** роутер на любой OpenWrt-прошивке, доступен на `192.168.1.1`.

### Шаги прошивки

| # | Что делает |
|---|-----------|
| 1 | Проверяет `192.168.1.1` |
| 2 | Заливает шаблон `backup-*-template.tar.gz`, ждёт ребута на `192.168.5.1` |
| 3 | Устанавливает Podkop, настраивает `main` (20 сервисов) + `yt` (YouTube) |
| 4 | Устанавливает Tailscale, фиксит два бага OpenWrt 25.12 |
| 5 | Запускает авторизацию, открывает браузер, ждёт пока нажмёшь |

---

## После настройки

- **LAN:** `192.168.5.1`, пароль SSH: `56756789`, WiFi: `@open` / `56756789`
- **Tailscale:** зелёная точка, выживает после перезагрузки (~35 сек на ребут)
- **Podkop:** 20 сервисов в `main` + `youtube` в отдельной секции `yt`
- **Диагностика:** `check-ip` на роутере
