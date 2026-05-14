# lesson: z56-79-e-bondar (100.110.49.100) — repair 2026-05-13

## Роутер
- Модель: Cudy WR3000S v1
- OS: OpenWrt 24.10.5
- Tailscale: 100.110.49.100 (TS3 56papezde)
- Провайдер: Ростелеком, Москва
- Владелец: e-bondar

## Проблема
- fw4-fix rules = 0 (должно быть 4)
- Podkop не запущен (not running)

## Что сделано
1. Перезапущен podkop (`/etc/init.d/podkop restart`)
2. Применён fw4-fix (`/root/podkop-fw4-fix.sh update`)
3. Проверены сайты — все 10 отвечают

## Результат
- fw4-fix rules = 4 ✅
- Podkop зелёный, sing-box работает ✅
- Tailscale: 100.110.49.100, fw_mode=none ✅
- rc.local: правильный (sleep 40: NO, tailscaled: OK, timeout: YES, fw4-fix: OK) ✅
- Watchdog: 3 скрипта (ts, podkop, route) + list_update cron ✅
- Сайты: все 10 открываются ✅

## Статус
🟢 ОТРЕМОНТИРОВАН
