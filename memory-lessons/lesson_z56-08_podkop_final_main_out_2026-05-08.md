# Урок: z56-08 — Podkop заработал после перезапуска

**Дата:** 08.05.2026
**Роутер:** z56-08 (Сочи, 100.79.40.126)
**OpenWrt:** 25.12.0

## Проблема
Роутер показывал Россию на проверялках (2ip.ru, myip.ipip.net) вместо Польши.

## Диагностика
1. `podkop status` → `not running`
2. `sing-box status` → `running`
3. nftables `PodkopTable chain mangle` — счётчики 0 (трафик не маркируется)
4. `podkop-fw4-fix` добавил правила в `inet fw4 mangle_forward`, но счётчики тоже 0

## Решение
1. Перезапустить podkop: `/etc/init.d/podkop restart`
2. Подождать 30-40 секунд пока загрузятся списки
3. Обновить fw4: `/root/podkop-fw4-fix.sh update`

## Результат
- **2ip.ru** → 🇵🇱 Польша (91.92.46.152) ✅
- **myip.ipip.net** → 🇵🇱 Польша (Варшава) ✅
- **ipinfo.io** → 🇷🇺 Россия (185.15.62.83) — не в списках

## Важно
- `podkop status` показывает `not running` даже когда всё работает — это нормально для podkop на OpenWrt 25.12
- После перезагрузки роутера нужно запускать podkop и podkop-fw4-fix
- Настроены сервисы автозапуска: `S99podkop`, `S99podkop-fix-final`, `S99podkop-fw4-fix`

## Сравнение с эталонным роутером (TR-Boss_00)
- На TR-Boss_00 podkop тоже `not running`, но всё работает
- Разница: на TR-Boss_00 podkop создаёт цепочку `mangle` с хуком `prerouting` и счётчики показывают 171K пакетов
- На z56-08 после перезапуска podkop создал такую же цепочку, но счётчики 0 — трафик идёт через OUTPUT (с роутера), а FORWARD (с клиентов) не маркируется
- **Решение для клиентского трафика:** podkop-fw4-fix.sh добавляет правила в `inet fw4 mangle_forward`
