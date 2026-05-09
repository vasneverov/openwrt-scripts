# Инфраструктура RU relay + сервер подписок
## Инструкция по развёртыванию с нуля

Схема позволяет обходить белые списки РКН: клиент подключается к российскому IP,
трафик прозрачно пробрасывается на европейский сервер.

```
Клиент/Роутер → RU relay (российский IP) → DNAT → EU сервер (Xray/Reality)
```

---

## Часть 1. RU relay сервер

**Требования:** VPS с российским IP, Ubuntu 22/24, root доступ.

### 1.1 Включить форвардинг пакетов

```bash
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
sysctl -p
```

### 1.2 BBR + MSS clamping (для стабильности gRPC на LTE)

```bash
# BBR
echo "net.core.default_qdisc=fq" >> /etc/sysctl.conf
echo "net.ipv4.tcp_congestion_control=bbr" >> /etc/sysctl.conf
sysctl -p

# MSS clamping (важно для Telegram-звонков на LTE)
iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu
```

### 1.3 DNAT правила (один порт = один сервер, без конфликтов!)

```bash
# CZ3 (85.137.164.179)
iptables -t nat -A PREROUTING -p tcp --dport 2086 -j DNAT --to-destination 85.137.164.179:2086
# ... добавить все нужные порты

# PL4 (82.38.66.75)
iptables -t nat -A PREROUTING -p tcp --dport 993 -j DNAT --to-destination 82.38.66.75:993
# ... добавить все нужные порты

# MASQUERADE для каждого EU сервера
iptables -t nat -A POSTROUTING -d 85.137.164.179 -j MASQUERADE
iptables -t nat -A POSTROUTING -d 82.38.66.75 -j MASQUERADE

# Сохранить
apt install -y iptables-persistent
netfilter-persistent save
```

**⚠️ Правила:** каждый порт → только один сервер. Дубли = конфликт, трафик идёт не туда.
**⚠️ Проверить** что порт не занят собственным xray на relay (если он там есть).

---

## Часть 2. EU серверы (3x-ui + Xray)

### 2.1 Установка 3x-ui

```bash
bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)
```

### 2.2 Создание инбаундов

- Протокол: **VLESS + Reality + gRPC**
- SNI: `www.apple.com` (для серверов с apple-донором) или `www.sony.com`
- Порт инбаунда = порт в DNAT на relay (один к одному!)

### 2.3 Открыть порты в UFW

```bash
# ⚠️ Обязательно! 3x-ui не открывает UFW автоматически
ufw allow 2086/tcp
ufw allow 993/tcp
# ... все порты инбаундов
```

**⚠️ Симптом забытого UFW:** Xray слушает порт (видно в `ss -tlnp`), но соединение не проходит.

---

## Часть 3. Сервер подписок

Развернуть на RU relay (или отдельном сервере). Выдаёт vless:// ссылки с RU IP.

### 3.1 Структура файлов

```
/opt/subscription/
  server.py       — HTTP-сервер подписок
  config.json     — список панелей, RU IP, контакты
```

### 3.2 config.json

```json
{
  "panels": [
    {"url": "https://cz3.example.com:5050/5050", "user": "ad", "pass": "56"},
    {"url": "https://pl4.example.com:5050/5050", "user": "ad", "pass": "56"}
  ],
  "ru_vps_ip": "1.2.3.4",
  "sub_port": "8888",
  "support_url": "tg://resolve?domain=yourtg",
  "support_text": "Your Name"
}
```

### 3.3 Ключевые HTTP заголовки

```python
self.send_header("Profile-Title", "Vasya na svyazi")          # заголовок в Happ
self.send_header("Profile-Web-Page-Url", "tg://resolve?...")  # ссылка
self.send_header("Support-Url", "tg://resolve?...")           # ⚠️ нужен для иконки Telegram в Happ
self.send_header("Subscription-Userinfo", "upload=X; download=Y; total=Z; expire=T")
```

**⚠️ `Support-Url` обязателен** — без него иконка Telegram в Happ не показывается.
**⚠️ Profile-Title** — только ASCII (Cyrillic/emoji вызывают UnicodeEncodeError в BaseHTTPServer).

### 3.4 Логика поиска клиента

Искать UUID в двух местах (новые клиенты не сразу попадают в clientStats):
1. `clientStats` — клиент уже подключался хотя бы раз
2. `settings.clients` — клиент только создан, ещё не подключался

### 3.5 Формирование имени профиля

```python
nick = email.split("_")[0]   # часть email до первого _
profile_name = f"{nick}_{remark}"   # Boss_WhiteL_PL4_2052 🇵🇱
```

### 3.6 systemd сервис

```ini
[Unit]
Description=Subscription Server
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/subscription/server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
systemctl enable subscription
systemctl start subscription
```

### 3.7 HTTPS (Let's Encrypt)

Нужен домен, указывающий на RU relay. Certbot + nginx reverse proxy на порт 8888.

---

## Часть 4. Router инбаунды (Podkop/OpenWRT)

Отдельные инбаунды специально для роутеров. Клиенты получают прямую vless:// ссылку
(не подписку) и вставляют её в Podkop вручную.

### 4.1 Хорошие порты для router инбаундов

| Порт | Легенда | Примечание |
|------|---------|------------|
| 465 | SMTPS | email |
| 587 | SMTP submission | email |
| 993 | IMAPS | email |
| 995 | POP3S | email |
| 8880 | HTTP alt | Cloudflare |
| 8008 | HTTP alt | Cloudflare |

### 4.2 Генерация vless ссылок для роутеров

Ссылка должна содержать **RU relay IP** и **порт из DNAT**, иначе не пройдёт через белый список.

```
vless://UUID@RU_RELAY_IP:PORT?type=grpc&security=reality&mode=gun
  &pbk=PUBLIC_KEY&sid=SHORT_ID&sni=SNI&fp=chrome#ClientName
```

Параметры брать из инбаунда панели (streamSettings → realitySettings).

### 4.3 Массовое создание клиентов

```python
# скрипт: логин в панель через curl → addClient API
# email маска: Z56-88_ApeCZ3, Z56-89_ApeCZ3, ...
# трафик: 1000 * 1024**3 байт
# срок: datetime(год, месяц, день, 23, 59, 59).timestamp() * 1000
```

---

## Часть 5. Диагностика

### Порт закрыт на EU сервере
```bash
# Проверка
ss -tlnp | grep xray           # Xray слушает?
ufw status                     # UFW открыт?
ufw allow PORT/tcp             # открыть
```

### Конфликт DNAT
```bash
iptables -t nat -L PREROUTING -n --line-numbers
# Один порт → два сервера = трафик идёт к первому правилу
# Удалять: iptables -t nat -D PREROUTING НОМЕР (с конца!)
```

### Клиент не находится в подписке (404)
- Проверить есть ли UUID в `settings.clients` (не только в `clientStats`)
- Новый клиент появляется в `clientStats` только после первого подключения

### Нет иконки Telegram в Happ
- Добавить заголовок `Support-Url` (не только `Profile-Web-Page-Url`)

### Xray не слушает новый порт
- Перезапустить Xray через панель: `/server/restartXrayService`
- Открыть порт в UFW на EU сервере

---

## Чек-лист при добавлении нового EU сервера

- [ ] Установить 3x-ui, создать инбаунды
- [ ] Открыть порты в UFW на EU сервере
- [ ] Добавить DNAT правила на RU relay (уникальный порт для каждого инбаунда)
- [ ] Добавить MASQUERADE для нового EU IP
- [ ] Добавить панель в config.json сервера подписок
- [ ] Перезапустить subscription.service
- [ ] Проверить: `curl -si https://relay:8888/sub/TEST_UUID`
