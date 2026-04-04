# openwrt-scripts

Скрипты для автоматической настройки роутеров на OpenWrt с Podkop и Tailscale.

---

## setup-wr3000h.sh — Cudy WR3000H (OpenWrt 25.12)

Один скрипт делает всё с Mac по кабелю: hostname, Podkop, Tailscale.

### Предусловия

1. Прошит OpenWrt 25.12 через веб-интерфейс
2. Залит шаблон конфига → роутер на IP `192.168.5.1`, пароль `56756789`
3. Mac подключён к роутеру кабелем
4. Установлен `sshpass`: `brew install sshpass`

### Запуск

```bash
chmod +x setup-wr3000h.sh
./setup-wr3000h.sh 111   # где 111 — номер роутера (z56-111)
```

Скрипт попросит вставить два vless-ключа: main (обход РФ) и yt (YouTube).

---

### Что делает скрипт — по шагам

#### Шаг 1 — Проверка доступности
Пингует `192.168.5.1`. Если нет ответа — стоп с ошибкой.

#### Шаг 2 — Hostname + Podkop
- Переименовывает роутер в `z56-NNN` через UCI
- Устанавливает Podkop через официальный скрипт (всегда последняя версия):
  ```
  sh <(wget -O - https://raw.githubusercontent.com/itdoginfo/podkop/refs/heads/main/install.sh)
  ```
  На вопрос про русский язык автоматически отвечает `y`

#### Шаг 3 — Настройка Podkop

**Профиль `main`** — обход блокировок РФ:
- 20 community_lists: `telegram meta geoblock block porn news anime discord twitter hdrezka tiktok cloudflare google_ai google_play hodca roblox hetzner ovh digitalocean cloudfront`
- Ключ: вводится при запуске

**Профиль `yt`** — YouTube отдельным маршрутом:
- community_lists: только `youtube`
- Ключ: вводится при запуске

> **Критично:** секции Podkop должны иметь тип `section` (не `podkop`).
> `community_lists` — только через `uci add_list`, не `option`.

#### Шаг 4 — Фикс Tailscale (два бага OpenWrt 25.12)

В дефолтном пакете Tailscale для OpenWrt 25.12 два бага в `/etc/init.d/tailscale`:

**Баг 1 — `--statedir=/var/lib/tailscale` захардкожен**
`/var/lib/` — tmpfs (RAM), стирается при перезагрузке. После ребута: `Logged out`.
Фикс: убираем `--statedir`, остаётся `--state /etc/tailscale/tailscaled.state` (persistent overlay).

**Баг 2 — `TS_DEBUG_FIREWALL_MODE="none"` захардкожен**
OpenWrt 25.12 не имеет `iptables`, только `nftables`. С `"none"` tailscaled падает через ~10 сек — зелёная точка тухнет.
Фикс: меняем `"none"` → `"$fw_mode"` (читает из UCI → `nftables`).

UCI после фикса:
```
tailscale.settings.fw_mode='nftables'
tailscale.settings.state_file='/etc/tailscale/tailscaled.state'
```

#### Шаг 5 — Авторизация Tailscale
`tailscale up --accept-dns=false --accept-routes --reset` → ссылка → браузер открывается автоматически.
После авторизации зелёная точка горит и **не тухнет**.

---

### Выживание после перезагрузки

`/etc/rc.local` на роутере (из шаблона):
```sh
#!/bin/sh
(sleep 15
tailscale up --accept-dns=false --accept-routes
sleep 5
tailscale serve --bg --tcp 80  tcp://localhost:80
tailscale serve --bg --tcp 22  tcp://localhost:22
tailscale serve --bg --tcp 443 tcp://localhost:443) &
exit 0
```

---

## wr3000h-tailscale-setup.sh

Старый скрипт — только установка Tailscale на роутере (запускается прямо на роутере).

```sh
sh <(curl -L https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/wr3000h-tailscale-setup.sh)
```
