# План: olcRTC на DE2 (Германия) через WB Stream

## Проблема
Текущая схема (VLESS gRPC + Reality через bMSK relay) работает, но Wildberries детектит VPN и блокирует доступ. Нужна схема, где трафик неотличим от легитимного.

## Решение: olcRTC
**olcRTC** — туннель через WebRTC SFU легальных сервисов (Яндекс.Телемост, Салют Jazz, WB Stream). Трафик выглядит как обычный видеозвонок для ТСПУ и сайтов.

**Рекомендуемая комбинация:** `wbstream + datachannel` — макс. скорость, мин. пинг, без бана.

## Архитектура

```
Клиент (роутер) → SOCKS5 :8808 → olcrtc-cnc → WebRTC → SFU WB Stream → olcrtc-srv (DE2) → интернет
```

## План работ

### Шаг 1: Подготовка DE2 (сервер)
- [ ] Установить Go 1.26+ на DE2
- [ ] Установить mage
- [ ] Склонировать olcrtc: `git clone https://github.com/openlibrecommunity/olcrtc --recurse-submodules`
- [ ] Собрать: `mage build`
- [ ] Сгенерировать ключ: `openssl rand -hex 32`
- [ ] Сгенерировать Room ID: `./olcrtc -mode gen -carrier wbstream -dns 1.1.1.1:53 -amount 1 -data data`
- [ ] Запустить сервер: `./olcrtc -mode srv -carrier wbstream -transport datachannel -id <ROOM_ID> -client-id <CLIENT_ID> -key <KEY> -link direct -data data -dns 1.1.1.1:53`
- [ ] Создать systemd сервис для автозапуска

### Шаг 2: Настройка relay на bMSK
- [ ] Пробросить порт 8808 (SOCKS5) с bMSK на DE2 через socat/iptables
- [ ] Или поднять olcrtc-client на bMSK, который будет проксировать на роутеры

### Шаг 3: Тестирование
- [ ] Проверить через curl: `curl --socks5-hostname 127.0.0.1:8808 https://icanhazip.com`
- [ ] Проверить открытие wildberries.ru через прокси
- [ ] Проверить открытие yandex.ru через прокси
- [ ] Замерить скорость

### Шаг 4: Интеграция с роутерами
- [ ] Настроить роутер на использование SOCKS5 прокси (bMSK:8808)
- [ ] Или использовать redirect в xray/sing-box

## Важные заметки
- `client-id` должен совпадать на сервере и клиенте
- Один `client-id` может держать много соединений, но SFU ограничивает полосу на участника
- Рекомендуется 1 client-id = 1 пользователь
- Если VPS блокирует исходящий трафик — использовать `-socks-proxy`
- DNS можно сменить на `77.88.8.8` (Яндекс) если 1.1.1.1 не работает

## Ссылки
- Репозиторий: https://github.com/openlibrecommunity/olcrtc
- Документация: https://github.com/openlibrecommunity/olcrtc#readme
- Android клиент: https://github.com/alananisimov/olcbox
- Telegram: @openlibrecommunity
