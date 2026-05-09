# Урок: Ремонт TR30-12 (mr.nobody) — 100.66.188.30
## Дата: 09.05.2026

### Роутер
- **Имя:** tr30-12-mr-nobody
- **Tailscale IP:** 100.66.188.30
- **Модель:** Cudy TR3000 v1
- **OpenWrt:** 24.10.0
- **Tailscale учётка:** ne78va@
- **Диск:** 44.6 MB overlay (очень мало!)

### Исходное состояние
- **Podkop:** ❌ not running (sing-box запущен отдельно, PID 4572)
- **fw_mode:** `nftables` ❌ (должен быть `none`)
- **exclude_ntp:** `0` ❌ (должен быть `1`)
- **YT профиль:** отдельный ❌ (должен быть в main)
- **community_lists:** 19 шт, без `roblox`
- **Диск:** 100% 🚨
- **Watchdog'ы:** ❌ отсутствовали
- **init.d/tailscale:** ENABLED ❌ (должен быть DISABLED)
- **rc.local:** старый (tailscale serve) ❌
- **Автообновление Tailscale:** включено ❌

### Диагностика
1. **Диск забит под 100%** — две главные причины:
   - `/tmp/tailscale-update/tailscale_1.96.4_arm64.tgz` — **32.2 MB** (скачанный апдейт)
   - `/usr/bin/tailscaled.new` — **32.1 MB** (новый бинарник)
   - Итого ~64 MB мусора на 44 MB диске!
2. **Podkop не стартовал** — из-за переполненного диска не мог записать конфиг
3. **YT профиль отдельно** — лишняя сложность, youtube должен быть в main
4. **Нет watchdog'ов** — при падении podkop или tailscale никто не перезапустит

### Что сделали

#### 1. Чистка диска
```bash
rm -rf /tmp/tailscale-update/
rm -f /usr/bin/tailscaled.new
rm -f /tmp/sing-box/cache.db
```
**Результат:** 100% → 67% (освобождено ~16.5 MB)

#### 2. Отключение автообновления Tailscale
```bash
tailscale set --auto-update=false
```
Tailscale больше не будет скачивать обновления и забивать диск.

#### 3. Настройка podkop
- **fw_mode → none** — tailscale не лезет в nftables
- **exclude_ntp → 1** — NTP не уходит в прокси
- **YT профиль удалён** — youtube добавлен в main
- **19 community lists** — без roblox (невалидный в этой версии podkop)

#### 4. init.d/tailscale → disable
```bash
/etc/init.d/tailscale disable
```

#### 5. rc.local с userspace-networking
```bash
#!/bin/sh
sleep 40
tailscaled --tun=userspace-networking --statedir=/etc/tailscale >/dev/null 2>&1 &
sleep 15
tailscale up --accept-routes --timeout=30s
exit 0
```

#### 6. Watchdog'ы (каждые 2 минуты)
- **ts-watchdog.sh** — проверяет Tailscale, перезапускает если офлайн
- **podkop-watchdog.sh** — проверяет sing-box, перезапускает podkop если упал

#### 7. Crontab
```
*/2 * * * * /etc/ts-watchdog.sh
*/2 * * * * /etc/podkop-watchdog.sh
13 */3 * * * /usr/bin/podkop list_update
```

### Результат
- **Диск:** 100% → 67% ✅
- **Podkop:** списки обновлены, sing-box работает ✅
- **fw_mode:** none ✅
- **exclude_ntp:** 1 ✅
- **YT профиль:** удалён ✅
- **Watchdog'ы:** каждые 2 минуты ✅
- **Tailscale:** жив, версия 1.92.0, автообновление отключено ✅
- **Ключ main (Z56-107_ApeCZ3):** ● READY (TCP+TLS OK) ✅

### Ключевые выводы
1. **Диск 44 MB — критично мало.** Всегда проверять `df -h /` при диагностике.
2. **Мусор от Tailscale — частая проблема.** Автообновление скачивает бинарник (~32 MB) и кладёт в /tmp, но если диск забит — распаковать не может, и мусор остаётся.
3. **При первичной диагностике обязательно проверять:**
   - `df -h /` — свободное место
   - `find /tmp -type f -size +100k` — крупные файлы в tmp
   - `find /overlay -name '*tailscale*'` — следы tailscale
   - `ls -la /usr/bin/tailscaled.new` — недоустановленный апдейт
4. **Watchdog'ы — каждые 2 минуты**, не реже.
5. **roblox невалидный** в этой версии podkop — не добавлять в community_lists.
6. **Podkop `not running` — норма.** sing-box работает отдельно, podkop как сервис завершается после применения правил.

### Полезные команды для этого роутера
```bash
# Подключение
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@100.66.188.30

# Проверка диска
df -h /

# Поиск мусора
find /tmp -type f -size +100k 2>/dev/null
find /overlay -name '*tailscale*' -o -name '*tailscaled*' 2>/dev/null

# Проверка podkop
logread -e podkop | tail -10
/etc/init.d/podkop status

# Проверка tailscale
tailscale status --self
tailscale version

# Проверка watchdog'ов
crontab -l
ls -la /etc/*watchdog*
```
