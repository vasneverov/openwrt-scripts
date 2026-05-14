# check_vless.py — Reality bug: TCP+TLS OK, но ключ не работает

## Проблема
Ключ проходит TCP и TLS проверку, UUID есть в xray, но на роутере не работает.
Причина: Reality handshake через Python ssl не проверяет реальную валидность ключа.
OpenSSL s_client с Reality не работает — нужен sing-box.

## Решение
Добавлен `test_reality_via_router()` в `check_vless.py`:
- Использует SSH на роутер с sing-box (Italy router 100.86.250.119)
- Создаёт временный конфиг sing-box с тестируемым ключом
- Запускает sing-box на 4 сек, проверяет лог на "reality verification failed"
- Если ошибка — ключ не работает, несмотря на TCP+TLS OK

## Важно
- Для Reality теста нужен роутер с sing-box (не xray)
- Italy router (100.86.250.119) — pass `56756789`
- Если роутер недоступен — тест пропускается с предупреждением
- `timeout` на OpenWrt отсутствует — используется `sleep + kill %1`
- `base64 -d` на OpenWrt работает (BusyBox)

## TEST_ROUTERS
Список роутеров для Reality теста — в `check_vless.py`, переменная `TEST_ROUTERS`.
Формат: `[(ip, password), ...]`
