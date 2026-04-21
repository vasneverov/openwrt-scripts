# openwrt-scripts

Скрипты для автоматической прошивки и настройки роутеров Cudy на OpenWrt 25.12.
Делают всё: прошивка → шаблон → Podkop → Tailscale → авторизация.

---

## Структура

```
~/CLAUDECODE/
├── keys.conf                 ← ключи vless (не в репо, хранится локально)
├── WR3000H/setup-wr3000h.sh ← для Cudy WR3000H
├── WR3000S/setup-wr3000s.sh ← для Cudy WR3000S
└── fix-vasin-boss.sh        ← восстановление через AnyDesk (см. ниже)
```

## Восстановление роутера через AnyDesk

Если Tailscale не поднялся после ребута — подключайся через AnyDesk и выполни:

```bash
curl -s https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/fix-vasin-boss.sh | bash
```

Скрипт сам сделает всё:
- `fw_mode=none`
- `init.d/tailscale disable`
- `exclude_ntp=1`
- `rc.local` с tailscaled
- Watchdog скрипт + crontab
- Перезапуск Tailscale

## Предусловия

- Mac подключён кабелем к роутеру
- sshpass: `brew install sshpass`
- Файл `keys.conf` на уровень выше скрипта (см. формат ниже)
- Шаблоны конфигов: `~/Downloads/WR3000H/backup-wr3000h-template.tar.gz` и `~/Downloads/WR3000S V1/backup-wr3000s-template.tar.gz`

---

## setup-wr3000h.sh — Cudy WR3000H (OpenWrt 25.12)

**Запуск:**
```bash
./setup-wr3000h.sh 112   # 112 — номер роутера (z56-112)
```

**Предусловие:** роутер прошит OpenWrt 25.12, доступен на `192.168.1.1` без пароля.

### Шаги

| # | Что делает |
|---|-----------|
| 1 | Проверяет `192.168.1.1` |
| 2 | Заливает шаблон `backup-wr3000h-template.tar.gz`, ждёт ребута на `192.168.5.1` |
| 3 | Устанавливает Podkop, настраивает `main` (20 сервисов) + `yt` (YouTube) |
| 4 | Устанавливает Tailscale, фиксит два бага OpenWrt 25.12 |
| 5 | Запускает авторизацию, открывает браузер, **сам ждёт** пока нажмёшь |

---

## setup-wr3000s.sh — Cudy WR3000S (OpenWrt 25.12)

**Запуск:**
```bash
./setup-wr3000s.sh 112   # 112 — номер роутера (z56-112)
```

**Предусловие:** роутер на любой OpenWrt-прошивке, доступен на `192.168.1.1`.

### Шаги

| # | Что делает |
|---|-----------|
| 1 | Прошивает OpenWrt 25.12 через SSH (`sysupgrade -n`) |
| 2 | Заливает шаблон `backup-wr3000s-template.tar.gz`, ждёт ребута на `192.168.5.1` |
| 3 | Устанавливает Podkop, настраивает `main` (20 сервисов) + `yt` (YouTube) |
| 4 | Устанавливает Tailscale, фиксит два бага OpenWrt 25.12 |
| 5 | Запускает авторизацию, открывает браузер, **сам ждёт** пока нажмёшь |

---

## Два бага Tailscale в OpenWrt 25.12

В дефолтном пакете `/etc/init.d/tailscale` два бага:

**Баг 1 — `--statedir=/var/lib/tailscale` захардкожен**
`/var/lib/` — tmpfs (RAM), стирается при перезагрузке. После ребута: `Logged out`.
Фикс: убираем `--statedir`, остаётся `--state /etc/tailscale/tailscaled.state` (persistent).

**Баг 2 — `TS_DEBUG_FIREWALL_MODE="none"` захардкожен**
OpenWrt 25.12 не имеет `iptables`, только `nftables`. С `"none"` tailscaled падает через ~10 сек — зелёная точка тухнет.
Фикс: меняем `"none"` → `"$fw_mode"` (читает из UCI = `nftables`).

---

## Формат keys.conf

Хранится локально, **не в репо**:

```
108_main=vless://UUID@server:4190?...#Z56-108_hostFin
108_yt=vless://UUID@server:8853?...#Z56-108_bSPB
109_main=...
109_yt=...
```

---

## После настройки

- LAN: `192.168.5.1`, пароль SSH: `56756789`, WiFi: `@open` / `56756789`
- Tailscale: зелёная точка, выживает после перезагрузки (~35 сек на ребут)
- Podkop: 20 сервисов в `main` + `youtube` в отдельной секции `yt`
