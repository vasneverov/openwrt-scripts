# Урок: Ремонт e-008-tvoy-oblik (100.83.104.61)
## Дата: 09.05.2026

### Роутер
- **Имя:** e-008-tvoy-oblik
- **Tailscale IP:** 100.83.104.61
- **Модель:** Cudy WR3000E v1
- **OpenWrt:** 24.10.5 (opkg)
- **Провайдер:** неизвестно
- **Tailscale учётка:** 56papezde@gmail.com

### Исходное состояние
- **2ip.ru:** 🇵🇱 Польша (91.92.46.229) — Main работал
- **YouTube:** ❌ 000 — не работал
- **Tailscale:** ✅ fw_mode=none, init.d DISABLED, rc.local есть (настроено ранее)
- **Podkop:** YT профиль отдельно, Main через bMSK:5323→PL5
- **fw4-fix:** ❌ не установлен
- **Лимит open files:** 4096
- **Скрипты:** ❌ отсутствовали
- **/etc/hosts:** ❌ пустой

### Диагностика
1. **YouTube не работал (000)** — YT профиль отдельно, та же проблема
2. **fw4 mangle_forward пустая** — forwarded трафик не маркировался
3. **Лимит open files 4096** — риск падения sing-box
4. **Tailscale уже настроен правильно** — спасительный скрипт не нужен

### Что сделали (быстрый прогон, ~2 минуты)
1. Скопировали podkop-fw4-fix.sh и podkop-fix-lists.sh
2. Удалили YT профиль, youtube в main (telegram, meta, youtube...)
3. fw4-fix install
4. Лимит open files 65536
5. /etc/hosts для GitHub CDN
6. Cron 0 3 * * *
7. Перезапуск sing-box и podkop
8. fw4 update

### Результат
- **YouTube:** 000 → **301 (FakeIP 198.18.0.4)** ✅
- **2ip.ru:** 🇵🇱 Польша ✅
- **Telegram:** 200 (FakeIP) ✅
- **Google:** 301 (прямой) ✅
- **fw4-fix:** 4 правила ✅
- **Лимит open files:** 65536 ✅

### Ключевые выводы
1. **Tailscale уже был настроен** — fw_mode=none, init.d disabled, rc.local. Спасительный скрипт не нужен. Это значит, что роутер уже лечили раньше.
2. **Быстрый ремонт занял ~2 минуты** — потому что Tailscale не трогали, только podkop.
3. **Проблема та же** — YT профиль отдельно не работает. Решение: удалить YT, youtube в main.
4. **Роутер перезагружался несколько раз** — Tailscale падал при первом подключении. После настройки fw4-fix и лимитов — стабилен.

### Полезные команды
```bash
# Подключение
sshpass -p '56756789' ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no root@100.83.104.61

# Проверка YouTube
curl -s -o /dev/null -w '%{http_code} %{remote_ip}' --max-time 8 https://youtube.com

# Проверка IP
curl -s https://2ip.ru | head -3

# Проверка fw4-fix
nft list chain inet fw4 mangle_forward | grep podkop-fw4-fix

# Проверка лимита open files
cat /proc/$(pgrep sing-box)/limits | grep 'open files'
```
