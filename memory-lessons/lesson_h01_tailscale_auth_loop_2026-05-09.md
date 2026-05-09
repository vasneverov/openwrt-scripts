# Урок: H-01 Tailscale — бесконечный цикл авторизации и почему Podkop роняет Tailscale

## Дата: 2026-05-09
## Роутер: H-01 (WR3000H, OpenWrt 25.12.0)
## Проблема: Tailscale авторизуется, через 2 минуты отваливается

## Симптомы
1. `tailscale up` выдаёт ссылку
2. Пользователь нажимает Connect в браузере
3. В логе `machineAuthorized=true`, `health=ok`
4. Через ~2 минуты: `map response long-poll timed out`
5. `tailscale status` снова показывает `Logged out`
6. State файл есть, но маленький (119 байт вместо 2600+)

## Корневая причина
**Podkop (sing-box) перехватывает long-poll соединение Tailscale к controlplane.tailscale.com**

Tailscale использует long-poll HTTP соединение к `controlplane.tailscale.com` для получения обновлений карты сети. Это соединение идёт через прокси (Podkop/sing-box), который:
- Либо обрывает long-poll по таймауту (2 минуты)
- Либо не может корректно пробросить длинное соединение

После обрыва long-poll Tailscale теряет связь с контрол-сервером и переходит в состояние `Logged out`.

## Почему убивали полчаса
1. **tailscale up висит в фоне** — после `tailscale up` процесс не завершается, он ждёт. При повторном `killall tailscale` и новом `tailscale up` генерируется **новый nodekey**, и старая авторизация становится недействительной.
2. **Цикл:** убиваем tailscale → новый nodekey → новая ссылка → пользователь нажимает → авторизация проходит → через 2 минуты long-poll обрывается → logged out → убиваем tailscale → новый nodekey → ...
3. **Podkop не добавлял tailscale.com в direct_domains** — трафик к controlplane.tailscale.com шёл через прокси, который обрывал long-poll.

## Решение
1. Добавить Tailscale домены в direct_domains Podkop (чтобы трафик шёл напрямую, минуя прокси):
   ```
   uci add_list podkop.main.direct_domains='tailscale.com'
   uci add_list podkop.main.direct_domains='controlplane.tailscale.com'
   uci add_list podkop.main.direct_domains='login.tailscale.com'
   uci commit podkop
   /etc/init.d/podkop restart
   ```
2. **НЕ убивать `tailscale up`** после получения ссылки. Дождаться когда он сам подхватит авторизацию.
3. Если `tailscale up` уже убит и nodekey пересоздан — чистить state и начинать заново:
   ```
   killall tailscaled
   rm -f /etc/tailscale/tailscaled.state
   tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking >> /tmp/ts.log 2>&1 &
   sleep 4
   tailscale up --accept-dns=false --accept-routes
   ```

## Проверка что всё работает
- `tailscale status` — показывает IP (100.117.186.39) и список устройств
- `tailscale ip -4` — возвращает IP
- State файл: `ls -la /etc/tailscale/tailscaled.state` — должен быть > 2KB
- В логе: `Switching ipn state Starting -> Running (WantRunning=true, nm=true)`
- DERP соединение: `derp-4 connected`

## Статус H-01 на момент урока
- ✅ Tailscale: 100.117.186.39, Running
- ✅ Прокси: работает (CZ, 92.61.71.14)
- ✅ Все сайты открываются (google, youtube, github, instagram, tiktok, twitter, discord, telegram, roblox, steam)
- ⚠️ ChatGPT: HTTP 403 (блокировка на стороне OpenAI, не проблема роутера)
- ⚠️ Netflix: HTTP 302 (редирект, может не работать из-за гео)
- ❌ Podkop: not running (sing-box работает, но init.d podkop не активен)
- ❌ LAN4, LAN3, LAN2: NO-CARRIER (не подключены кабели)
- ❌ phy1-ap0: DOWN (вторая WiFi антенна выключена)

## Проблема с Cline (VS Code extension)
Каждые ~30 секунд контекстное окно Cline "засыпает" — новые выводы команд не приходят, пока не пройдёт авто-proв. Это не баг Tailscale, это ограничение архитектуры Cline:
- Команды с долгим выводом (>30 сек) обрезаются
- Мониторинг в цикле while true не видит изменений, пока не завершится текущий блок вывода
- Решение: разбивать мониторинг на короткие шаги (каждый шаг < 30 сек), или использовать фоновые процессы с отдельными проверками
