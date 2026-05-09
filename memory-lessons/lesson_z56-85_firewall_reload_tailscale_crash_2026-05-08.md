# Урок: z56-85 (100.79.216.88) — firewall reload сломал Tailscale

## Дата: 2026-05-08

## Проблема
Применил rescue_generic.sh на z56-85, затем установил fw4-fix и перезапустил podkop.
После этого роутер пропал из Tailscale.

## Корень
**`/etc/init.d/firewall reload`** в rescue_generic.sh (шаг 6) перезаписал nftables.
Tailscale использует nftables для своей маршрутизации — после reload все его правила сброшены.
Tailscale потерял связь и не может восстановиться без перезагрузки роутера.

## Что было сделано
1. ✅ Диагностика — все проблемы выявлены
2. ✅ rescue_generic.sh — применён (все 9 шагов)
3. ✅ Community lists — обновлены
4. ✅ fw4-fix — установлен
5. ❌ firewall reload — сломал Tailscale

## Исправление
- **rescue_generic.sh:** убран `/etc/init.d/firewall reload` из шага 6
- **IRON_RULES.md:** добавлено правило 25 — НИКОГДА не reload firewall
- **fw4-fix:** убран `nft flush table inet PodkopTable` — он сносит всё

## Статус
- ❌ Роутер пропал — ждём перезагрузки питания
- ✅ rescue_generic.sh исправлен — больше не reload'ит firewall
- ✅ IRON_RULES.md обновлён

## Вывод
**Никогда не делать `/etc/init.d/firewall reload` на роутере с работающим Tailscale.**
Только `uci commit firewall` — tailscale0 добавится в зону LAN при следующей перезагрузке.
