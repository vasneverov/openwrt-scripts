---
name: Tailscale OpenWrt 25.12 Init.d Fix
description: Критическое исправление init.d для Tailscale в OpenWrt 25.12 - state persistence
type: feedback
originSessionId: 99678cb6-b45e-407e-acd9-1020996c496b
---
## Проблема

В OpenWrt 25.12 Tailscale 1.94.1 из репозитория Гунанова имеет **hardcoded `--statedir=/var/lib/tailscale`** (расположен в RAM/tmpfs). После перезагрузки state стирается и Tailscale теряет авторизацию (серая точка).

## Решение

Патч `/etc/init.d/tailscale` для добавления `--statedir /etc/tailscale`:

```sh
#!/bin/sh /etc/rc.common

START=80
USE_PROCD=1

start_service() {
    local state_file
    config_load tailscale
    config_get state_file "settings" state_file "/etc/tailscale/tailscaled.state"
    
    mkdir -p /etc/tailscale
    
    procd_open_instance
    procd_set_param command /usr/sbin/tailscaled
    procd_append_param command --port 41641
    procd_append_param command --state "$state_file"
    procd_append_param command --statedir /etc/tailscale  # <-- КРИТИЧЕСКИ
    procd_set_param respawn
    procd_set_param stdout 1
    procd_set_param stderr 1
    procd_close_instance
}

stop_service() {
    /usr/sbin/tailscaled --cleanup 2>/dev/null || true
}

reload_service() {
    stop
    start
}
```

## Проверка

```bash
# Должно показать --statedir /etc/tailscale
cat /proc/$(pgrep tailscaled)/cmdline | tr '\0' ' '

# State файл должен быть в /etc/tailscale/
ls -la /etc/tailscale/tailscaled.state
```

## Применение

**Why:** Без этого исправления Tailscale теряет авторизацию после каждой перезагрузки роутера.

**How to apply:**
1. После установки Tailscale через `apk add tailscale`
2. Перед первой авторизацией `tailscale up`
3. Обязательно для всех роутеров OpenWrt 25.12

**История:** Обнаружено на H_02-Algor (WR3000H) 2026-04-24. Потрачено 3 попытки авторизации пока не найдена причина.
