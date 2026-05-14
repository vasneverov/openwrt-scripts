# DE2 ROOM — olcRTC deploy (2026-05-13)

## Что сделано

### 1. xray-room (отдельный процесс, не через x-ui)
- Конфиг: `/usr/local/etc/xray-room.json`
- Порт: **2087** — VLESS Reality (те же pbk/sid/sni что на 2086)
- Outbound: SOCKS5 → `127.0.0.1:8808` (olcrtc-cnc)
- Systemd: `xray-room.service`
- Клиенты добавлять в `inbounds[0].settings.clients`

### 2. olcrtc-cnc (клиент)
- Systemd: `olcrtc-cnc.service`
- SOCKS5 на порту **8808**
- WebRTC → WB Stream → olcrtc-srv (тот же сервер)
- Room ID: `019e20bb-2553-7cde-9d48-95d7596a3654`
- Client ID: `de2-main`

### 3. olcrtc-srv (сервер)
- Systemd: `olcrtc.service` (уже был)
- Принимает WebRTC, отдаёт в интернет

### 4. DNAT на bMSK
- Порт **5091** → DE2:2087
- INPUT + FORWARD + DNAT правила добавлены
- Сохранены: `iptables-save > /etc/iptables/rules.v4`

### 5. Тестовый ключ
- Файл: `ключи/client-4826-DE2-ROOM.key`
- UUID: `C4ADAE04-390F-40AD-AC10-80D4E836E9AF`
- Префикс: `Client_4826_DE2_ROOM`

## Архитектура

```
Клиент → bMSK:5091 → DE2:2087 (xray-room, VLESS Reality)
  → SOCKS5:8808 (olcrtc-cnc)
  → WebRTC → WB Stream → olcrtc-srv (DE2)
  → интернет (🇩🇪 German IP)
```

## Команды

```bash
# Добавить клиента в room
ssh DE2
# править /usr/local/etc/xray-room.json → clients[]
systemctl restart xray-room

# Статус
systemctl status xray-room
systemctl status olcrtc-cnc
systemctl status olcrtc

# Логи
journalctl -u xray-room -n 20 --no-pager
journalctl -u olcrtc-cnc -n 20 --no-pager
```

## Формат ключа

```
vless://UUID@159.194.198.172:5091?type=grpc&security=reality&mode=gun&serviceName=&pbk=iR2cEt9NRvsSsuXR1f5cBgWZSkEzkmQjK5PX9YMt2Qo&sid=9fee82cd&sni=www.wildberries.ru&fp=chrome&spx=%2F#Client_XXXX_DE2_ROOM
```
