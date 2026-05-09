# Урок: Ремонт 007-ufa (100.99.195.91)
## Дата: 09.05.2026

### Роутер
- **Имя:** 007-ufa
- **Tailscale IP:** 100.99.195.91
- **Модель:** Cudy WR3000E v1
- **OpenWrt:** 24.10.2 (opkg, не apk)
- **Провайдер:** Уфа, WAN IP 100.96.134.179 (CGNAT)
- **Tailscale учётка:** 56papezde@gmail.com

### Исходное состояние
- **2ip.ru:** 🇵🇱 Польша (91.92.46.229) — Main работал
- **YouTube:** ❌ 000 — не работал
- **Telegram:** ✅ 200 (FakeIP)
- **Остальные сайты:** ✅ все через FakeIP
- **Podkop:** YT профиль был отдельно, Main через bMSK:5323→PL5
- **fw4-fix:** ❌ не установлен
- **Лимит open files:** 4096 (дефолт)
- **Скрипты:** ❌ отсутствовали
- **/etc/hosts:** ❌ пустой
- **Tailscale:** ✅ Online, fw_mode=none, init.d DISABLED, rc.local есть, watchdog есть

### Диагностика
1. **YouTube не работал (000)** — YT профиль отдельно, как на tr56-04
2. **fw4 mangle_forward пустая** — forwarded трафик не маркировался
3. **Лимит open files 4096** — риск падения sing-box
4. **OpenWrt 24.10.2** — не 25.12, но fw4-fix всё равно нужен (nftables)

### Что сделали
1. **Удалили YT профиль**, добавили `youtube` в main (порядок: telegram, meta, youtube...)
2. **Скопировали 3 скрипта:** rescue_generic.sh, podkop-fw4-fix.sh, podkop-fix-lists.sh
3. **Установили podkop-fw4-fix** — правила в fw4 mangle_forward
4. **Исправили лимит open files** — добавили `procd_set_param limits "nofile=65536 65536"` в /etc/init.d/sing-box
5. **Добавили /etc/hosts** для raw.githubusercontent.com (4 IP)
6. **Добавили cron** для podkop-fix-lists.sh (0 3 * * *)
7. **Перезапустили sing-box и podkop**
8. **Обновили fw4** через `podkop-fw4-fix.sh update`

### Результат
- **YouTube:** 000 → **301 (FakeIP 198.18.0.239)** ✅
- **2ip.ru:** 🇵🇱 Польша (91.92.46.229) ✅
- **Все сайты:** работают через FakeIP ✅
- **Лимит open files:** 65536 ✅
- **fw4-fix:** установлен ✅
- **Tailscale:** стабилен, не перезагружался ✅

### Ключевые выводы
1. **Та же проблема, что на tr56-04** — YT профиль отдельно не работает. Решение то же: удалить YT, youtube в main.
2. **OpenWrt 24.10.2 тоже требует fw4-fix** — проблема не только в 25.12, а в nftables в целом.
3. **Порядок списков:** telegram, meta, youtube — запомнили.
4. **Tailscale уже был настроен правильно** — fw_mode=none, init.d disabled, rc.local. Спасительный скрипт не понадобился.

### Полезные команды для этого роутера
```bash
# Подключение
sshpass -p '56756789' ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no root@100.99.195.91

# Проверка YouTube
curl -s -o /dev/null -w '%{http_code} %{remote_ip}' --max-time 8 https://youtube.com

# Проверка IP
curl -s https://2ip.ru | head -3

# Проверка fw4-fix
nft list chain inet fw4 mangle_forward | grep podkop-fw4-fix

# Проверка лимита open files
cat /proc/$(pgrep sing-box)/limits | grep 'open files'
```
