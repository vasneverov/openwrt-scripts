# Tailscale API Токены

> Источник: PL4 `/opt/router-monitor/.env`  
> Обновлено: 2026-04-28  
> Для мониторинга всегда брать отсюда — не искать на серверах

---

| # | Учётка | Tailnet | Токен |
|---|--------|---------|-------|
| 1 | vas.neverov@gmail.com | `vas.neverov@gmail.com` | `tskey-api-ktBh42VtRj11CNTRL-RBTDhNJYzdNNqr7wNTfLdNC6PncxBk63B` |
| 2 | ne78va@gmail.com | `ne78va@gmail.com` | `tskey-api-kW1ujQ5i2w11CNTRL-wRvm7o2eCkiEfK7M1fhhjiq763ztrBsx` |
| 3 | 56papezde@gmail.com | `56papezde@gmail.com` | `tskey-api-k7CKy5KXg421CNTRL-UbV7qjoSeKAbB4Akb1VrJAB6NhfpLkYL` |
| 4 | n78rout@gmail.com | `n78rout@gmail.com` | `tskey-api-krWQYxzw1511CNTRL-28hSufddDkPy7RxcKzcdjPS24aFRZLh2` |

---

## Использование

```bash
# Пример запроса (подставить нужный токен и tailnet)
curl -s "https://api.tailscale.com/api/v2/tailnet/56papezde@gmail.com/devices" \
  -H "Authorization: Bearer tskey-api-k7CKy5KXg421CNTRL-UbV7qjoSeKAbB4Akb1VrJAB6NhfpLkYL" \
  -o /tmp/ts3_devices.json
```

## Соответствие учёток и роутеров

| Учётка | Серии роутеров |
|--------|----------------|
| vas.neverov (TS1) | TR30, некоторые Z56, cudy |
| ne78va (TS2) | S78, M78, zXIA |
| 56papezde (TS3) | TR56, Z56 (большинство) |
| n78rout (TS4) | M56, Z56-124..126, TR56-08..10 |

## Обновление токенов

Если токен протух → новый берётся с PL4:
```bash
sshpass -p 'T-RUeIl9%+' ssh root@82.38.66.75 'cat /opt/router-monitor/.env'
```
