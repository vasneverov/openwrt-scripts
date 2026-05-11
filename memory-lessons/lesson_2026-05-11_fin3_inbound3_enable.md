# Fin3 inbound 3 enable + key check

## Проблема
Inbound 3 на Fin3 (144.31.66.115) был выключен: enable=false, port=0, streamSettings пустой. 40 клиентов добавлены, но не работали.

## Диагностика
- `ss -tlnp` — порт 4191 не слушается
- `cat /usr/local/x-ui/bin/config.json | python3 -c '...'` — в конфиге только 2 inbounds (62789 api, 2083 личный)
- xray запущен через x-ui: `bin/xray-linux-amd64 -c bin/config.json` из `/usr/local/x-ui/`

## Решение
Прямая запись в config.json не работает — x-ui перезаписывает его при старте xray.

**Правильный путь — через API X-UI:**
1. `POST /login` — получить cookie
2. `POST /panel/api/inbounds/update/3` — обновить inbound с полным JSON:
   - id: 3, port: 4191, enable: true
   - protocol: vless
   - settings: JSON-строка с clients (все 40 клиентов)
   - streamSettings: JSON-строка с Reality (grpc, privateKey, shortIds, serverNames)
   - tag: "inbound-4191"
   - sniffing: JSON-строка
3. `POST /panel/api/server/restartXrayService` — перезапустить xray

## Проверка
- `ss -tlnp | grep 4191` — порт слушается
- `python3 check_vless.py <vless_url>` — READY ✓✓✓

## Ключевые параметры
- Panel URL: `https://144.31.66.115:5050/5050`
- Логин: ad / 56
- Inbound 3: port 4191, Reality, shortId=932e706c, pbk=XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw
- Relay: bSPB 5.35.84.151:4191 → DNAT → Fin3 144.31.66.115:4191
