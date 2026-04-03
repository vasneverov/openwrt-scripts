# openwrt-scripts

Скрипты для настройки роутеров на OpenWrt.

---

## `wr3000h-tailscale-setup.sh`

Автоматическая установка и настройка Tailscale на роутере **Cudy WR3000H** под управлением **OpenWrt 25.12** (пакетный менеджер `apk`).

### Что делает скрипт

1. **Добавляет ключ репозитория** Gunanovo — неофициальная сборка Tailscale для OpenWrt с поддержкой `apk`.
2. **Подключает репозиторий** с пакетами Tailscale, автоматически определяя архитектуру роутера.
3. **Обновляет индекс пакетов** (`apk update`).
4. **Устанавливает** `tailscale`, `iptables`, `ip6tables`.
5. **Настраивает firewall-режим** `nftables` через `uci` — необходим для корректной работы Tailscale на OpenWrt 25.x.
6. **Прописывает автозапуск** в `/etc/rc.local`: через 15 секунд после старта роутера Tailscale автоматически открывает порты 80, 22 и 443 через `tailscale serve`.
7. **Включает службу** `tailscale` в автозагрузку и запускает её.
8. **Подключает роутер к сети Tailscale** с параметрами `--accept-dns=false --accept-routes`.

### Запуск на роутере

```sh
sh <(curl -L https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/wr3000h-tailscale-setup.sh)
```

### Требования

- Cudy WR3000H (или другой роутер на OpenWrt 25.12 с `apk`)
- Доступ в интернет с роутера
- Аккаунт на [tailscale.com](https://tailscale.com)

После выполнения скрипт попросит авторизоваться — откроется ссылка вида `https://login.tailscale.com/a/...`. Перейди по ней в браузере и подтверди подключение устройства.
