# Руководство по диагностике и ремонту Podkop на OpenWrt 25.12

## Почему podkop перестал работать "из коробки"?

**Кратко:** OpenWrt 25.12 перешёл с `fw3`/`iptables` на `fw4`/`nftables`.
В новой системе `inet` таблицы с `hook prerouting` **не видят forwarded трафик** (с клиентов).

**Детали:**
- **OpenWrt < 25.12** (23.05, 24.10): `fw3` + `iptables` → `mangle PREROUTING` видел ВЕСЬ трафик
- **OpenWrt 25.12**: `fw4` + `nftables` → `inet PodkopTable prerouting` видит **только local** трафик
- **Решение:** Добавлять правила в `inet fw4 mangle_forward` (hook forward) — он видит forwarded трафик

## Быстрая диагностика

```bash
# 1. Статус podkop
/etc/init.d/podkop status

# 2. Статус sing-box
/etc/init.d/sing-box status

# 3. Проверка IP (должен показывать не Россию)
curl -s https://2ip.ru | head -3
curl -s https://myip.ipip.net

# 4. Проверка nftables (счётчики должны быть > 0)
nft list chain inet PodkopTable mangle 2>/dev/null | head -10

# 5. Проверка mangle_forward (должны быть podkop-fw4-fix правила)
nft list chain inet fw4 mangle_forward 2>/dev/null | grep "podkop-fw4-fix"
```

## Если podkop не работает

```bash
# 1. Перезапустить podkop
/etc/init.d/podkop restart

# 2. Подождать 30-40 секунд пока загрузятся списки
sleep 40

# 3. Обновить fw4-fix (если установлен)
/root/podkop-fw4-fix.sh update

# 4. Проверить
curl -s https://2ip.ru | head -3
```

## Установка podkop-fw4-fix на новый роутер

```bash
# 1. Загрузить скрипт
cat tools/podkop-fw4-fix.sh | ssh root@ROUTER_IP "cat > /root/podkop-fw4-fix.sh && chmod +x /root/podkop-fw4-fix.sh"

# 2. Установить
ssh root@ROUTER_IP "/root/podkop-fw4-fix.sh install"
```

## Важные моменты

1. **`podkop status` показывает `not running`** — это НОРМАЛЬНО для OpenWrt 25.12.
   Podkop — не демон, а одноразовый скрипт. Он запускается, загружает списки, создаёт nftables правила и завершается.

2. **После перезагрузки роутера** podkop запускается автоматически через `/etc/rc.d/S99podkop`.
   А podkop-fw4-fix запускается через `/etc/rc.d/S99podkop-fw4-fix`.

3. **Проверять работу нужно с клиента** (ноутбук/телефон за роутером), а не с самого роутера через SSH.
   С роутера трафик идёт через OUTPUT и может работать, даже если FORWARD сломан.

4. **Список роутеров, где установлены спящие агенты:**
   - z56-08 (100.79.40.126) — ✅ podkop-fw4-fix
   - z56-09 (100.116.130.9) — ✅ podkop-fw4-fix
   - m78-05 (100.75.8.100) — ✅ podkop-fw4-fix + podkop-fix-lists (cron)

## Полезные команды

```bash
# Проверить все nftables правила podkop
nft list table inet PodkopTable

# Проверить mangle_forward
nft list chain inet fw4 mangle_forward

# Посмотреть логи podkop
logread | grep -i podkop | tail -30

# Посмотреть логи sing-box
logread | grep -i sing-box | tail -30
```
