# Инструкции для Claude — прошивка роутеров серии 56

Эти инструкции описывают полную систему прошивки роутеров Cudy с OpenWrt + Podkop + Tailscale.
Читай этот файл целиком перед тем, как начинать любую работу с роутерами.

---

## Три модели роутеров и их серии

| Модель | Прозвище | Серия | Папка с прошивкой |
|--------|----------|-------|-------------------|
| Cudy WR3000H / WR3000S | "большой", "H" или "S" | z56-NNN | `~/Downloads/WR3000H/` или `~/Downloads/WR3000S V1/` |
| Cudy TR3000 | "маленький синий" | TR56-NN | `~/Downloads/TR3000 V1 2/` |
| Cudy M3000 | "банка" | M56-NN | `~/Downloads/M3000 1.0_2.0/` |

**Шаблоны настроек (tar.gz):**
- WR3000H: `~/Downloads/WR3000H/backup-wr3000h-template.tar.gz`
- WR3000S: `~/Downloads/WR3000S V1/backup-wr3000s-template.tar.gz`
- TR3000:  `~/Downloads/TR3000 V1 2/backup-tr3000-template.tar.gz`
- M3000:   `~/Downloads/M3000 1.0_2.0/backup-m3000-template.tar.gz`

После применения шаблона роутер всегда поднимается на **192.168.5.1**.
SSH пароль: `56756789`. WiFi: SSID `@open`, пароль `56756789`.

---

## VPN ключи

Ключи хранятся локально в папке `~/CLAUDECODE/ключи/`. Перед установкой на роутер ОБЯЗАТЕЛЬНО проверить:
```bash
python3 ~/CLAUDECODE/check_vless.py <ключ>
```
Только если статус `● READY` — ставить на роутер. Это железное правило.

### Файлы ключей

| Назначение | Файл |
|-----------|------|
| Main (Fin3, порт 4191) для z56 | `~/CLAUDECODE/ключи/vless_fin_rout_4190_108.md` |
| YT (bSPB, порт 8853) для z56 | `~/CLAUDECODE/ключи/vless_bSPB_direct_8853_108.html` |
| Main (Italy, порт 2090) для TR56 | `~/CLAUDECODE/КЛЮЧИ/vless_italy_rout_2090_TR56.html` |
| YT (bSPB, порт 8853) для TR56 | `~/CLAUDECODE/ключи/vless_bSPB_direct_8853_TR56.md` |
| Main (CZ2, порт 8448) для M56 | `~/CLAUDECODE/ключи/vless_cz2_rout_8448.md` |
| YT (bSPB, порт 8853) для M56 | `~/CLAUDECODE/ключи/vless_bSPB_direct_8853_M56.html` |

Все ключи проходят через relay `5.35.84.151`. Из файлов читай секцию по имени роутера (например, `Z56-121_hostFin2`).

---

## Универсальный скрипт (если есть)

```bash
bash ~/CLAUDECODE/flash-router.sh z56-NNN     # WR3000H/S
bash ~/CLAUDECODE/flash-router.sh TR56-NN     # TR3000
bash ~/CLAUDECODE/flash-router.sh M56-NN      # M3000
```

---

## Критические правила (нарушение = поломка сессии)

1. **USB LAN адаптер Mac не трогать** — Mac сам получает DHCP от роутера, ничего не переключать вручную.

2. **ssh-keygen -R перед каждым подключением:**
   ```bash
   ssh-keygen -R 192.168.1.1
   ssh-keygen -R 192.168.5.1
   ```
   Каждый новый роутер генерирует новый host key — без этого SSH падает молча.

3. **Два IP-адреса в процессе прошивки WR3000H/TR3000/M3000:**
   - Сразу после `sysupgrade` → роутер на `192.168.1.1`
   - После применения шаблона → роутер на `192.168.5.1`
   - Мониторить 5.1 сразу после sysupgrade = ошибка, гарантированный таймаут.

4. **Не делать больших sleep.** Поллинг каждые 2 сек, максимум 35–45 сек. Роутер часто поднимается быстрее.

5. **Tailscale autoupdate всегда отключать:**
   ```bash
   uci set tailscale.settings.autoupdate='false'
   ```

6. **Не перезагружать роутер без подтверждения пользователя**, если он за 1000 км.

---

## SSH-флаги для OpenWrt 25.12

Всегда добавлять к sshpass-командам:
```
-o PreferredAuthentications=password -o PubkeyAuthentication=no
```
Без этого sshpass падает exit 255 — pubkey пытается первым.

---

## Podkop — настройка

### Установка (на все роутеры одинаково):
```bash
sshpass -p '56756789' ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no \
  root@192.168.5.1 \
  "printf 'y\n' | sh <(wget -O - https://raw.githubusercontent.com/itdoginfo/podkop/refs/heads/main/install.sh)"
```
На вопрос про русский язык — `y`.

### Конфигурация community_lists (строго этот список):

**main** (20 списков, russia_inside НЕ добавлять):
```
telegram meta geoblock block porn news anime discord twitter hdrezka tiktok cloudflare google_ai google_play hodca roblox hetzner ovh digitalocean cloudfront
```

**yt** (только одно значение, строчными):
```
youtube
```

### Критично для Podkop 0.7.x:
- Обязательное поле: `connection_type='proxy'` (в 0.4.x не было)
- `proxy_string` обязателен — без него "Outbound section not found"
- Всегда `uci add_list` для community_lists (не `uci set`)
- Секция YT: `uci set podkop.YT=section` (заглавные для M56/TR56)
- Секция yt: `uci set podkop.yt=section` (строчные для z56)

### Баг: del перед add_list
```bash
uci del podkop.main.community_lists 2>/dev/null || true
# затем add_list
```
Podkop install создаёт дефолтный main с russia_inside — del обязателен.

---

## Tailscale — установка и фикс

Официальный пакет OpenWrt устарел. Ставить UPX-версию:
```bash
wget -qO /tmp/tailscale.apk 'https://gunanovo.github.io/openwrt-tailscale/aarch64_cortex-a53/tailscale-1.96.5-r1.apk'
apk add --allow-untrusted /tmp/tailscale.apk
rm -f /tmp/tailscale.apk
```

### Два бага в /etc/init.d/tailscale (OpenWrt 25.12) — фикс обязателен:
```bash
sed -i 's|--statedir=/var/lib/tailscale ||g' /etc/init.d/tailscale
sed -i 's|TS_DEBUG_FIREWALL_MODE="none"|TS_DEBUG_FIREWALL_MODE="$fw_mode"|g' /etc/init.d/tailscale
uci set tailscale.settings.fw_mode='nftables'
uci set tailscale.settings.state_file='/etc/tailscale/tailscaled.state'
uci set tailscale.settings.autoupdate='false'
uci commit tailscale
mkdir -p /etc/tailscale
```

### Авторизация Tailscale — делает пользователь:
```bash
tailscale up --accept-dns=false --accept-routes --reset
```
Появится ссылка → открыть в браузере → Connect → дождаться Success. **Не закрывать терминал до Success!**

Проверка что state записался:
```bash
wc -c < /etc/tailscale/tailscaled.state   # должно быть ~2800+
```

### rc.local (уже в шаблоне, sleep разный по моделям):
- WR3000H/TR3000: sleep **40** сек
- M3000: sleep **25** сек

---

## Финальная проверка Podkop после ребута

```bash
sshpass -p '56756789' ssh root@192.168.5.1 "
MAIN=\$(wget -qO- 'http://192.168.5.1:9090/proxies/main-out/delay?timeout=5000&url=http%3A%2F%2Fgstatic.com%2Fgenerate_204' 2>/dev/null)
YT=\$(wget -qO- 'http://192.168.5.1:9090/proxies/yt-out/delay?timeout=5000&url=http%3A%2F%2Fgstatic.com%2Fgenerate_204' 2>/dev/null)
echo \"main-out: \$(echo \$MAIN | jq -r 'if .delay then \"OK (\(.delay)ms)\" else \"FAIL\" end')\"
echo \"yt-out:   \$(echo \$YT   | jq -r 'if .delay then \"OK (\(.delay)ms)\" else \"FAIL\" end')\"
"
```
Ожидаем: `main-out: OK (XXXms)` и `yt-out: OK (XXXms)`.

Финальный отчёт всегда содержит:
- Tailscale ✅ IP 100.x.x.x
- Podkop main ✅
- Podkop YT ✅

---

## VPN серверы (relay)

Все ключи работают через relay `5.35.84.151` (Beget SPB):
- Fin3 (основной, Финляндия): порт 4191 → реальный сервер 144.31.66.115
- Italy (Италия): порт 2090 → реальный сервер 151.243.198.86
- bSPB (YouTube, Россия/Beget): порт 8853 → прямой (российский CDN, не блокируется)
- CZ2 (Чехия): порт 8448 → реальный сервер 92.61.71.14

**Правило:** если claude.ai показывает "unavailable" через Польшу — переключить main на Italy.

---

## Tailscale учётки

Роутеры разбиты по учётным записям Tailscale:
- `vas.neverov` — учётка 1 (z56, M56, часть TR56)
- `56papezde` — учётка 2 (TR56, часть z56)
- `ne78va` — учётка 3 (S78, TR-boss и др.)

---

## Алгоритм работы при команде "прошиваем роутер NNN"

1. Определить серию (z56/TR56/M56) → выбрать workflow
2. Убедиться что роутер подключён по LAN и доступен на 192.168.1.1
3. Прочитать ключи из соответствующих файлов
4. Проверить ключи через `check_vless.py` → все READY
5. Выполнить шаги: sysupgrade → шаблон → podkop → tailscale → финальная проверка
6. Не перезагружать без подтверждения пользователя
7. Итоговый отчёт: Tailscale ✅, Podkop main ✅, Podkop YT ✅
