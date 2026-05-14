# SKILL: build_vless_key
## Создание VLESS-ключа под любого клиента (роутер)

### Вызов
```
python3 tools/build_vless_key.py <роутер> <город> <страна> [--port порт]
```

### Аргументы
| Аргумент | Описание | Пример |
|----------|----------|--------|
| роутер   | Имя роутера (label) | M56-24, TR56-13 |
| город    | Где стоит relay | spb, msk |
| страна   | Куда идёт трафик | finland, germany, poland, italy, czech |
| --port   | (опц) Порт relay | 5423, 4191 |

### Примеры
```
python3 tools/build_vless_key.py M56-24 msk germany
python3 tools/build_vless_key.py TR56-13 spb finland --port 4192
```

### Что делает скрипт
1. Читает `ключи/RELAY_REFERENCE.json` — схему relay/город/страна
2. Генерирует UUID
3. SSH на целевой сервер (DE2, Fin4, PL5...), добавляет клиента
4. Перезапускает xray
5. Собирает VLESS URL (pbk/sid/sni из справочника, не из панели!)
6. Запускает `check_vless.py` — проверка TCP+TLS+Reality+server checks
7. Сохраняет в `ключи/client-ROUTER-LABEL.key`
8. Выводит uci-команды для установки на роутер

### ⚠️ ВАЖНО: pbk должен быть правильным
- pbk берётся из `ключи/RELAY_REFERENCE.json`, **не из X-UI панели**
- На серверах с одним privateKey на все порты pbk одинаковый:
  - **DE2 (germany):** `iR2cEt9NRvsSsuXR1f5cBgWZSkEzkmQjK5PX9YMt2Qo`
  - **Fin4 (finland):** `HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI`
  - **PL5 (poland):** `4TCLYNy_kglu_bpE5n3Gx0yQ7L8TJQKRLATLgnXbtEw`
  - **Italy (italy):** `OBa4LZ0lL0j9RS52fgCw68jWqkvr_yakmpsolbiqgVI`
- Если pbk не совпадает — Reality handshake фейлится на конечном сервере
- `check_vless.py` покажет READY даже с неверным pbk (TCP+TLS идут через relay, relay не проверяет pbk)

### После создания
Клиент на роутере:
```
uci set podkop.main.proxy_string='<vless://url>'
uci commit podkop
/etc/init.d/podkop restart
```

Проверить глазами:
```
Попросить пользователя проверить зелёный ли ключ на роутере
```
