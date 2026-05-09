# Урок: M78-11 — замена чужого ключа на свой

**Дата:** 09.05.2026  
**Роутер:** M78-11  
**Tailscale IP:** 100.89.171.119  
**Пароль:** 56756789

## Проблема
На роутере M78-11 стоял чужой ключ **M56-07_CZ2_rout_8448** (UUID: `3f688db9-1e31-48a1-9f8d-54750dd7a979`). Это ключ от другого роутера (M56-07).

## Решение
1. Определён текущий ключ через `uci get podkop.main.proxy_string`
2. Создан новый клиент **M78-11_CZ2** на CZ2 сервере (92.61.71.14) в inbound **CZ2_rout_8448** (ID=18, порт 8448)
3. Новый UUID: `ea7dea75-dc77-4f12-88e9-fe77dfa7aac1`
4. VLESS ссылка установлена на роутер через `uci set podkop.main.proxy_string`
5. Podkop перезапущен

## Результат
- Google: HTTP 200
- YouTube: HTTP 200
- Telegram: HTTP 200

## Ключ
```
vless://ea7dea75-dc77-4f12-88e9-fe77dfa7aac1@5.35.84.151:8448?type=grpc&security=reality&mode=gun&serviceName=&pbk=FyCxYT4Ku_RyR7r2dZYofYxcAOm5xJtgP-T_xjgVnCQ&sid=dcaa&sni=www.apple.com&fp=chrome&spx=%2F#M78-11_CZ2_rout_8448
```

## Как создавать клиента на CZ2 через API
```bash
# Логин в панель
curl -s -c /tmp/cz2_cookies.txt -X POST 'https://cz2.theredhat.su:5050/5050/login' \
  -H 'Content-Type: application/json' \
  -d '{"username":"ad","password":"56"}'

# Получить inbound 18
curl -s -b /tmp/cz2_cookies.txt 'https://cz2.theredhat.su:5050/5050/panel/api/inbounds/get/18'

# Обновить — добавить клиента через API (POST /panel/api/inbounds/update/18)
```
