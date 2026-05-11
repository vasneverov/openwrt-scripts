# TR30_05-serebritsa — ремонт Tailscale + podkop

**Дата:** 2026-05-11
**Роутер:** TR30_05-serebritsa (100.69.174.52)
**OpenWrt:** 25.12.0
**Пароль:** 56756789
**Внешний IP:** 89.255.97.253 (Красногорск, РФ)
**Выход через podkop:** 91.92.46.152 (Польша, PL6)

## Исходное состояние
- Tailscale ONLINE, fw_mode=none, init.d DISABLED ✅
- rc.local — sleep 40 перед tailscaled (долго)
- ts-watchdog — старая версия (1087 байт, без NoState fix)
- direct_domains — НЕ установлены
- fw4-fix — НЕ установлен
- open files limit — 4096 (дефолт)
- YouTube — 000 (не работал)
- Google — 000 (ложная тревога, тест без -L)

## Что сделано
1. **direct_domains** — tailscale.com + controlplane + login
2. **ts-watchdog v3.1** — NoState fix, lock-файл
3. **rc.local** — убран sleep 40, watchdog в фоне
4. **podkop-fw4-fix** — правило в fw4 mangle_forward
5. **open files limit** — 4096 → 65536
6. **YouTube** — заработал (301, FakeIP) — youtube уже был в main (пользователь добавил)

## Важное
- Google показывает 000 в тесте без `-L` — это норма, Google работает (200 с -L)
- Google идёт через реальный IP (не через podkop) — это норма, Google нет в списках
- Диск не трогали (68% занято — норма)
- Ключ не проверяли — пользователь сказал что всё зелёное

## Конфигурация
- **Main:** bMSK:8443 → PL6 (Польша)
- **community_lists main:** telegram, meta, youtube, porn, news, anime, discord, twitter, hdrezka, tiktok, cloudflare, google_ai, google_play, hodca, roblox, hetzner, ovh, digitalocean, cloudfront
- **YT профиль:** удалён (youtube добавлен в main)
