# AX3000T (100.103.185.16) — CZ2 через bSPB relay

Создан: 2026-05-10

## VLESS Key (Relay)

```
vless://B566E29B-103A-4E43-9EB8-6F91CC667035@5.35.84.151:8448?type=grpc&security=reality&mode=gun&serviceName=&pbk=FyCxYT4Ku_RyR7r2dZYofYxcAOm5xJtgP-T_xjgVnCQ&sid=dcaa&sni=www.apple.com&fp=chrome&spx=%2F#AX3000T_100.103.185.16_CZ2_relay
```

## Параметры

| Параметр | Значение |
|----------|----------|
| UUID | `B566E29B-103A-4E43-9EB8-6F91CC667035` |
| Релей | `5.35.84.151:8448` (bSPB) |
| Конечный сервер | `92.61.71.14:8448` (CZ2, инбаунд 18) |
| pbk | `FyCxYT4Ku_RyR7r2dZYofYxcAOm5xJtgP-T_xjgVnCQ` |
| sid | `dcaa` |
| SNI | `www.apple.com` |
| fp | `chrome` |

## Проверка

```bash
echo 'vless://B566E29B-103A-4E43-9EB8-6F91CC667035@5.35.84.151:8448?type=grpc&security=reality&mode=gun&serviceName=&pbk=FyCxYT4Ku_RyR7r2dZYofYxcAOm5xJtgP-T_xjgVnCQ&sid=dcaa&sni=www.apple.com&fp=chrome&spx=%2F#AX3000T_100.103.185.16_CZ2_relay' | python3 ~/CLAUDECODE/check_vless.py -
```

**Результат:** ● READY ✓✓ (TCP+TLS OK)
