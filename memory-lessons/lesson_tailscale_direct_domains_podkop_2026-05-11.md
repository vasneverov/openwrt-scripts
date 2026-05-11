# Урок: Tailscale + podkop — direct_domains для стабильности long-poll

**Дата:** 2026-05-11
**Роутеры:** H-01, zakhar16, tr56-16
**Проблема:** Tailscale точка серая, хотя tailscaled запущен

---

## Симптом

- Tailscale в админке показывает **серую точку** (offline)
- SSH через Tailscale **не работает** (таймаут)
- Но по проводу (192.168.5.1) зайти можно
- tailscaled запущен, tailscale status показывает `offline`
- В логе `/tmp/ts.log`:
  ```
  control: lite map update error after 2m0.003s: Post "https://controlplane.tailscale.com/machine/map": context canceled
  Received error: PollNetMap: context canceled
  health(warnable=mapresponse-timeout): error: Tailscale hasn't received a network map from the coordination server in 2m8s.
  ```

## Корень

Podkop перехватывает трафик к `controlplane.tailscale.com` через tproxy. Long-poll соединение (которое Tailscale держит постоянно с control plane) обрывается через ~2 мин, потому что podkop не умеет корректно проксировать долгие WebSocket/long-poll соединения.

## Решение

Добавить `direct_domains` в podkop — трафик к tailscale.com идёт напрямую, минуя прокси:

```bash
uci add_list podkop.settings.direct_domains='tailscale.com'
uci add_list podkop.settings.direct_domains='controlplane.tailscale.com'
uci add_list podkop.settings.direct_domains='login.tailscale.com'
uci commit podkop
/etc/init.d/podkop restart
```

После этого:
1. Перезапустить tailscaled: `killall tailscaled; sleep 2; tailscaled ... &`
2. Поднять: `tailscale up --reset --accept-dns=false --accept-routes --hostname=... --netfilter-mode=off`

## Проверка

```bash
# Статус — должен быть прочерк (не offline)
tailscale status | head -1

# Лог — должно быть "derp-XX connected"
tail -5 /tmp/ts.log | grep 'derp.*connected'
```

## Где добавлять

- **rescue_generic.sh** — добавить direct_domains в секцию podkop
- **fix-tailscale-openwrt.sh** — добавить direct_domains
- **flash_router_universal.md** — добавить шаг проверки direct_domains
- **groom-routers** — добавить проверку direct_domains

## Затронутые роутеры

| Роутер | IP | Дата фикса |
|--------|----|-----------|
| H-01 | 100.117.186.39 | 09.05.2026 |
| zakhar16 | 100.108.52.26 | 11.05.2026 |
| tr56-16 | 100.68.181.47 | 11.05.2026 |

## Важно

- Без direct_domains Tailscale работает ~2 мин, потом точка серая
- Watchdog с NoState fix чинит, но цикл повторяется
- direct_domains решают проблему полностью — проверено 10/10 за 5 мин
