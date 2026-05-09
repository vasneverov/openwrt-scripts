# Урок: Низкие порты 465 и 993 работают на bMSK и bSPB

**Дата:** 05.05.2026
**Статус:** ✅ ПРОВЕРЕНО И РАБОТАЕТ

## Суть
Низкие порты (ниже 1024) для VLESS+REALITY+gRPC успешно работают на обоих серверах.
Обходят DPI, так как выглядят как легитимный почтовый трафик.

## Проверенные порты

### bMSK (Москва) — 159.194.198.172
| Порт | Протокол | Статус | Клиент |
|------|----------|--------|--------|
| **465** | SMTP SSL | ✅ РАБОТАЕТ | TR30-25 |
| **993** | IMAPS | ✅ РАБОТАЕТ | VasyaOnline YT |
| **631** | IPP | ✅ РАБОТАЕТ | test |

### bSPB (Питер) — 5.35.84.151
| Порт | Протокол | Статус | Клиент |
|------|----------|--------|--------|
| **993** | IMAPS | ✅ РАБОТАЕТ | (подтверждено) |

## Ключевые правила создания низких портов

1. **Генерация REALITY ключей**: Только через `/usr/local/x-ui/bin/xray x25519`
   - ❌ openssl генерирует НЕВЕРНЫЕ ключи → xray падает с `invalid "privateKey"`
   - ✅ xray x25519 даёт правильные ключи

2. **Формат VLESS ключа**:
   ```
   vless://{uuid}@{server_ip}:{port}?type=grpc&security=reality&mode=gun&serviceName=&pbk={public_key}&sid={short_id}&sni=www.apple.com&fp=chrome&spx=%2F#{email}
   ```

3. **gRPC Reality**: поле `flow` должно быть ПУСТЫМ (не xtls-rprx-vision)

4. **Перезапуск xray**: `/usr/local/x-ui/x-ui.sh restart`

5. **Проверка**: `ss -tlnp | grep xray` — порт должен быть в LISTEN

## Доступные низкие порты на bMSK (свободны)
- 110 (POP3)
- 143 (IMAP)
- 2086 (Cloudflare HTTP)
- 2087 (Cloudflare HTTPS)
- 2095 (Cloudflare HTTP)

## Готовые ключи
- **YouTube (993)**: `/Users/vas/Desktop/vless_key_993.txt`
- **TR30-25 (465)**: `/Users/vas/Desktop/vless_bMSK_465_TR30-25.txt`
