# Урок: Настройка YT-out через bMSK:465 — нужно открыть порт в firewall

## Проблема
Настроили podkop на z56-84 (Казань) с YT-секцией, указывающей на bMSK:465.
sing-box запущен, конфиг валидный, но YouTube не открывается (HTTP 000).

## Диагностика
1. Проверили, что inbound 9 на bMSK настроен правильно (Reality + gRPC, порт 465)
2. Проверили, что UUID клиента есть в config.json xray
3. xray слушает порт 465 (ss -tlnp показал LISTEN)
4. **НО:** curl с роутера до bMSK:465 не проходит (connection refused за 0.15 сек)
5. При этом ping до bMSK работает (25ms)

## Корень проблемы
На bMSK в iptables/firewall **не был открыт порт 465**.
В iptables были открыты: 2090, 5328, 5323, 5228, 5223, 5050, 8853 — но не 465.

## Решение
На сервере bMSK:
```bash
iptables -I INPUT -p tcp --dport 465 -j ACCEPT
iptables -I INPUT -p udp --dport 465 -j ACCEPT
# Сохранить:
netfilter-persistent save  # или iptables-save > /etc/iptables/rules.v4
```

## Важное правило
**При создании нового inbound на нестандартном порту — всегда проверять, открыт ли порт в firewall сервера!**
xray может слушать порт, но firewall может блокировать входящие соединения.

## Проверка
```bash
# На сервере:
ss -tlnp | grep <PORT>          # слушает ли xray
iptables -L INPUT -n -v | grep <PORT>  # пропускает ли firewall

# С клиента:
curl -sL -o /dev/null -w "HTTP %{http_code} Time: %{time_total}s\n" --max-time 10 "https://<SERVER_IP>:<PORT>"
# HTTP 000 + малое время (< 1 сек) = connection refused (firewall)
# HTTP 000 + большое время (> 5 сек) = timeout (нет маршрута)
```
