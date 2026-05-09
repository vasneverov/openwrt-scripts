# Урок: Ремонт tr56-04-doc-dom (100.82.166.40)
## Дата: 09.05.2026

### Роутер
- **Имя:** tr56-04-doc-dom
- **Tailscale IP:** 100.82.166.40
- **Модель:** Cudy TR3000 v1
- **OpenWrt:** 25.12.0
- **Провайдер:** Дом.ru (СПб), WAN IP 88.210.8.246
- **Tailscale учётка:** TS3 (56papezde@gmail.com)

### Исходное состояние
- **2ip.ru:** 🇵🇱 Польша (91.92.46.229) — Main работал
- **YouTube:** ❌ 000 — не работал
- **Telegram:** ✅ 200 (FakeIP)
- **Остальные сайты:** ✅ все через FakeIP
- **Podkop:** YT профиль был отдельно (bSPB:8853), Main через bMSK:5323→PL5
- **fw4-fix:** ❌ не установлен
- **Лимит open files:** 4096 (дефолт)
- **Скрипты:** ❌ отсутствовали
- **/etc/hosts:** ❌ пустой

### Диагностика
1. **YouTube не работал** — YT профиль вёл на bSPB:8853, но сервер не отвечал (`connection refused`)
2. **Провайдер Дом.ru блокирует прямые TCP** — даже 1.1.1.1:53 и 8.8.8.8:53 недоступны
3. **fw4 mangle_forward пустая** — forwarded трафик не маркировался
4. **Лимит open files 4096** — риск падения sing-box при нагрузке

### Что сделали
1. **Удалили YT профиль**, добавили `youtube` в main (21 список)
2. **Скопировали 3 скрипта:** rescue_generic.sh, podkop-fw4-fix.sh, podkop-fix-lists.sh
3. **Установили podkop-fw4-fix** — правила в fw4 mangle_forward
4. **Исправили лимит open files** — добавили `procd_set_param limits "nofile=65536 65536"` в /etc/init.d/sing-box
5. **Добавили /etc/hosts** для raw.githubusercontent.com (4 IP)
6. **Добавили cron** для podkop-fix-lists.sh (0 3 * * *)
7. **Перезапустили sing-box и podkop**
8. **Обновили fw4** через `podkop-fw4-fix.sh update`

### Результат
- **YouTube:** 000 → **301 (FakeIP 198.18.2.73)** ✅
- **2ip.ru:** 🇵🇱 Польша (91.92.46.229) ✅
- **Все сайты:** работают через FakeIP ✅
- **Лимит open files:** 65536 ✅
- **fw4-fix:** установлен ✅
- **Tailscale:** стабилен, не перезагружался ✅

### Ключевые выводы
1. **YT профиль отдельно — зло.** bSPB:8853 часто падает. YouTube в main через bMSK:5323→PL5 работает стабильно.
2. **Дом.ru блокирует TCP** — но podkop через прокси это обходит, т.к. трафик идёт через sing-box туннель.
3. **Лимит open files — частая проблема.** Всегда проверять и фиксить.
4. **После перезапуска podkop — обязательно `podkop-fw4-fix.sh update`**, иначе fw4 остаётся со старыми сетами.
5. **Порядок лечения:** конфиг → скрипты → перезапуск → fw4 update. Без перезагрузки роутера.

### Полезные команды для этого роутера
```bash
# Подключение
sshpass -p '56756789' ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no root@100.82.166.40

# Проверка YouTube
curl -s -o /dev/null -w '%{http_code} %{remote_ip}' --max-time 8 https://youtube.com

# Проверка IP
curl -s https://2ip.ru | head -3

# Проверка fw4-fix
nft list chain inet fw4 mangle_forward | grep podkop-fw4-fix

# Проверка лимита open files
cat /proc/$(pgrep sing-box)/limits | grep 'open files'
```
