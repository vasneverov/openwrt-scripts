# DE2 M56-24 Relay Key — Checkpoint 2026-05-13 15:13

## Задача
Создать соседний ключ для M56-24 на DE2 (Германия) через московский relay bMSK:5090.
Образец: TR56-06_italy через bSPB:2090 → Italy:2086.

## Что сделано

### DE2 сервер (195.26.231.228, пароль: 24qbXK_EO-)
- **Порт 2086**: добавлен Reality (скопирован streamSettings с порта 4191)
- **privateKey** на 2086: `aJA2j_6MaXqyXEISPNkQ90M8ptnMOIxUJ27x-9hstWY`
- **pbk** из этого privateKey: `iR2cEt9NRvsSsuXR1f5cBgWZSkEzkmQjK5PX9YMt2Qo` (совпадает с RELAY_REFERENCE)
- **shortIds** на 2086: `['25fbd6cb', '9fee82cd']`
- **Клиент M56-24-de2-2086** добавлен на порт 2086 с UUID `0C318E8A-6683-42EE-B4E7-B5B6B8CFD782`
- Xray перезапущен (PID 50996), порты слушают: 2086, 2087, 4191, 4192

### Проблема
Ключ через bMSK:5090 не работает — TLS падает (SSL: None).
Даже напрямую на DE2:2086 не работает (с любым sid).
При этом напрямую на DE2:4191 — работает (TCP 52ms, TLS 207ms).

### Гипотеза
Проблема не в privateKey/pbk (совпадают). Возможно:
1. Relay bMSK:5090 — это socat/nginx, который не пропускает gRPC Reality трафик
2. Или relay форвардит не на DE2:2086, а на другой порт
3. Или на bMSK стоит iptables DNAT, но есть блокировка

### Что не проверено
- Доступ к bMSK (159.194.198.172) — пароль `Ujkjdf56#` не подошёл
- Доступ к bSPB (5.35.84.151) — пароль `Ujkjdf56` не подошёл

### Рабочий ключ (прямое подключение, без relay)
```
vless://0C318E8A-6683-42EE-B4E7-B5B6B8CFD782@195.26.231.228:4191?type=grpc&security=reality&mode=gun&serviceName=&pbk=tJQ2sg1fJJjKoy9blRGL8yKKqpDnoHMVsoJ9JVCSFwY&sid=25fbd6cb&sni=www.apple.com&fp=chrome&spx=%2F#M56-24_DE2
```

### Следующий шаг
Нужен доступ к bMSK или bSPB, чтобы:
1. Проверить relay правило (iptables/socat/nginx)
2. Добавить relay на DE2:2086 или DE2:4191
3. Либо создать relay на bSPB для DE2 (как у TR56-06_italy)
