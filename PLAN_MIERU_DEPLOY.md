# План развёртывания mieru — ПОЛНЫЙ ОТЧЁТ

## Статус: ✅ РАБОТАЕТ

## Топология

```
Клиент (Mac/iPhone) → bMSK (159.194.198.172:2012) → Italy/FR (socks5) → Интернет
```

## Серверная инфраструктура

### 1. bMSK (159.194.198.172) — точка входа
- **SSH:** root@159.194.198.172 / Ujkjdf56#
- **mita v3.32.0** — порт 2012 TCP
- **Пользователь:** bmsk-mieru / Ujkjdf56#
- **Egress:** через socks5 на Italy или FR (авторотация)
- **Скрипт ротации:** `/opt/mieru/rotate.sh` (каждый час по cron)
  - Чётный час UTC → Italy
  - Нечётный час UTC → FR
  - Если сервер недоступен → переключается на другой
- **Лог:** `/var/log/mieru_rotate.log`

### 2. Italy (151.243.198.86) — socks5 выход
- **SSH:** root@151.243.198.86 / Ujkjdf56+
- **microsocks** на 0.0.0.0:1080
- **mita v3.32.0** — порт 2012 TCP (прямой доступ)
- **Пользователь mita:** vas / Ujkjdf56_mieru_italy

### 3. FR (45.155.54.25) — socks5 выход
- **SSH:** root@45.155.54.25 / TXmX0rVnLGBPe3
- **microsocks** на 0.0.0.0:1080
- **mita v3.32.0** — порт 2012 TCP (прямой доступ)
- **Пользователь mita:** vas / Ujkjdf56_mieru_fr

## Клиентские конфиги

### Для Karing (iPhone/Mac) — подключение через bMSK
```
Server: 159.194.198.172
Port: 2012
Protocol: mieru
Username: bmsk-mieru
Password: Ujkjdf56#
MTU: 1400
Multiplexing: LOW
```

### Для прямого подключения к Italy
```
Server: 151.243.198.86
Port: 2012
Protocol: mieru
Username: vas
Password: Ujkjdf56_mieru_italy
MTU: 1400
```

### Для прямого подключения к FR
```
Server: 45.155.54.25
Port: 2012
Protocol: mieru
Username: vas
Password: Ujkjdf56_mieru_fr
MTU: 1400
```

## Команды управления

### Проверка статуса на bMSK
```bash
sshpass -p 'Ujkjdf56#' ssh root@159.194.198.172 "mita status && mita describe config"
```

### Принудительная ротация на Italy
```bash
sshpass -p 'Ujkjdf56#' ssh root@159.194.198.172 "
cat > /tmp/switch_italy.json << 'EOF'
{
    \"egress\": {
        \"proxies\": [
            {\"name\":\"italy\",\"protocol\":\"SOCKS5_PROXY_PROTOCOL\",\"host\":\"151.243.198.86\",\"port\":1080},
            {\"name\":\"fr\",\"protocol\":\"SOCKS5_PROXY_PROTOCOL\",\"host\":\"45.155.54.25\",\"port\":1080}
        ],
        \"rules\": [{\"ipRanges\":[\"*\"],\"domainNames\":[\"*\"],\"action\":\"PROXY\",\"proxyNames\":[\"italy\"]}]
    }
}
EOF
mita apply config /tmp/switch_italy.json"
```

### Принудительная ротация на FR
```bash
sshpass -p 'Ujkjdf56#' ssh root@159.194.198.172 "
cat > /tmp/switch_fr.json << 'EOF'
{
    \"egress\": {
        \"proxies\": [
            {\"name\":\"italy\",\"protocol\":\"SOCKS5_PROXY_PROTOCOL\",\"host\":\"151.243.198.86\",\"port\":1080},
            {\"name\":\"fr\",\"protocol\":\"SOCKS5_PROXY_PROTOCOL\",\"host\":\"45.155.54.25\",\"port\":1080}
        ],
        \"rules\": [{\"ipRanges\":[\"*\"],\"domainNames\":[\"*\"],\"action\":\"PROXY\",\"proxyNames\":[\"fr\"]}]
    }
}
EOF
mita apply config /tmp/switch_fr.json"
```

### Тест соединения с Mac
```bash
/tmp/mieru test
```

### Просмотр лога ротации
```bash
sshpass -p 'Ujkjdf56#' ssh root@159.194.198.172 "tail -f /var/log/mieru_rotate.log"
```

## Что сделано

- [x] Установлен mita v3.32.0 на bMSK, Italy, FR
- [x] Настроен mieru клиент на Mac
- [x] Настроен egress на bMSK (прокси-цепочка через Italy/FR)
- [x] Установлен microsocks на Italy и FR
- [x] Написан скрипт авторотации Italy ↔ FR
- [x] Добавлен cron для ротации каждый час
- [x] Протестировано: bMSK → Italy (538ms), bMSK → FR (519ms)
- [x] Протестировано прямое подключение к Italy и FR
