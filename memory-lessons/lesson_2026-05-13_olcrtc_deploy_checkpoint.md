# OLCRTC Deploy — Checkpoint 2026-05-13 02:44 MSK

## Что сделано до прерывания

### Сессия 1 (прервана — свет/инет отключили)
- Добавлен немецкий сервер DE2 (195.26.231.228) через московский релей bMSK
- Починен inbound 2086 (3x-ui баг с полем settings)
- Создан xray-direct.service (без x-ui)
- Проверен ключ напрямую и через bMSK relay
- Обновлён RELAY_REFERENCE.json
- Записан урок: `lesson_2026-05-13_de2_2086_fix.md`

### Сессия 2 (текущая) — OLCRTC deploy
**Задача:** Развернуть olcrtc (WebRTC relay) на DE2 (195.26.231.228)

**Проблема:** На VPS 2GB RAM/2 CPU сборка Go (pion WebRTC + LiveKit) идёт очень долго (>5 мин)

**Решение:** Собрать локально на Mac, залить готовый бинарник на DE2

**Статус:**
- [x] Go установлен на Mac (brew install go 1.26.3)
- [x] Репозиторий olcrtc склонирован в /tmp/olcrtc
- [x] Mage установлен
- [x] Сборка запущена: `mage build` — компилирует olcrtc-darwin-arm64
- [ ] Сборка НЕ ЗАВЕРШЕНА — всё ещё компилирует (pion/webrtc CGO)
- [ ] DE2 очищен от мусора (rm -rf /root/olcrtc /usr/local/go /root/go)

## Что осталось доделать

1. **Дождаться завершения сборки** на Mac — бинарник будет в `/tmp/olcrtc/build/olcrtc-darwin-arm64`
2. **Собрать linux/amd64 версию** кросс-компиляцией:
   ```
   GOOS=linux GOARCH=amd64 mage build
   ```
3. **Залить бинарник на DE2:**
   ```
   sshpass -p '24qbXK_EO-' scp /tmp/olcrtc/build/olcrtc-linux-amd64 root@195.26.231.228:/root/olcrtc/
   ```
4. **Настроить systemd сервис** на DE2 для olcrtc
5. **Настроить nginx reverse proxy** на DE2 (порт 443 -> olcrtc порт)
6. **Проверить работу** через bMSK relay

## Пароли/доступы
- DE2: root@195.26.231.228 / пароль: 24qbXK_EO-
- bMSK relay: 100.70.216.65 (tailscale)
- План деплоя: `/Users/vas/CLAUDECODE/PLAN_OLCRTC_DEPLOY.md`

## Файлы в /tmp/
- `/tmp/olcrtc/` — репозиторий с исходниками
- `/tmp/olcrtc/build/` — сюда собирается бинарник
- `/tmp/de2-config.json` — конфиг для olcrtc
- `/tmp/de2-fix-panel.py` — скрипт фикса панели
- `/tmp/add_ws_inbound.py` — скрипт добавления inbound
- `/tmp/Caddyfile`, `/tmp/nginx-ws.conf`, `/tmp/nginx-stream.conf`, `/tmp/socat-tls.service`, `/tmp/derper-config.json` — конфиги для relay

## Команда для продолжения
Сказать: "доделай olcrtc deploy на DE2"
