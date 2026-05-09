# VPN RELAY SETUP — Промпт для Claude Code

Ты — Claude Code. Твоя задача: развернуть инфраструктуру обхода белых списков РКН для нового пользователя.
Работай строго последовательно. После каждого этапа сообщай статус.

Схема которую строим:
```
Клиент/Happ → RU сервер (российский IP) → iptables DNAT → CZ сервер (Xray/Reality)
                       ↓
              Сервер подписок (выдаёт vless:// с RU IP)
```

---

## ШАГ 0 — Сбор данных

Прежде чем начать — спроси у пользователя все данные одним сообщением:

```
Мне нужны данные для настройки. Пожалуйста, предоставь:

**RU сервер (российский IP — relay):**
- IP адрес
- SSH: логин и пароль
- 3x-ui панель: URL (например http://IP:54321), логин, пароль
- Есть ли на сервере собственный Xray/VPN? (важно для портов)

**CZ сервер (европейский — exit node):**
- IP адрес
- SSH: логин и пароль
- 3x-ui панель: URL, логин, пароль

**Данные для подписки:**
- Telegram username владельца (для кнопки поддержки в Happ, например: myname)
- Название профиля в Happ (ASCII только, например: Boss VPN)
- Домен для сервера подписок (указывает на RU сервер, например: sub.example.com)
```

Сохрани все данные в переменные и используй далее. Никогда не выводи пароли в сообщениях пользователю.

---

## ШАГ 1 — Диагностика серверов

Подключись к обоим серверам по SSH и собери информацию.

### 1.1 RU сервер
```bash
# Проверь ОС, форвардинг, занятые порты
uname -a
cat /proc/sys/net/ipv4/ip_forward
ss -tlnp | grep -E 'xray|x-ui|nginx'
iptables -t nat -L PREROUTING -n --line-numbers 2>/dev/null | head -30
systemctl status subscription.service 2>/dev/null | head -5
```

Проверь:
- [ ] Форвардинг включён (=1)?
- [ ] Какие порты уже заняты собственным xray (если есть)?
- [ ] Уже есть сервер подписок?

### 1.2 CZ сервер
```bash
uname -a
ss -tlnp | grep -E 'xray|x-ui'
ufw status 2>/dev/null || iptables -L INPUT -n | head -20
```

Проверь:
- [ ] 3x-ui запущен?
- [ ] UFW активен?
- [ ] Какие порты уже открыты?

Выведи итог диагностики пользователю перед продолжением.

---

## ШАГ 2 — Настройка RU relay

### 2.1 IP форвардинг + оптимизация
```bash
# Включить форвардинг если выключен
grep -q "net.ipv4.ip_forward=1" /etc/sysctl.conf || echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf

# BBR (снижает потери пакетов)
grep -q "tcp_congestion_control=bbr" /etc/sysctl.conf || {
  echo "net.core.default_qdisc=fq" >> /etc/sysctl.conf
  echo "net.ipv4.tcp_congestion_control=bbr" >> /etc/sysctl.conf
}
sysctl -p

# MSS clamping (критично для Telegram-звонков на LTE!)
iptables -t mangle -C FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu 2>/dev/null \
  || iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu
```

### 2.2 Выбор портов для DNAT

Используй только порты которые НЕ заняты собственным xray на RU сервере.

Хорошие порты (выглядят как легальный трафик):
| Порт | Легенда |
|------|---------|
| 2086 | Cloudflare HTTP |
| 2087 | Cloudflare HTTPS |
| 2095 | Cloudflare HTTP |
| 2096 | Cloudflare HTTPS |
| 993  | IMAP SSL |
| 465  | SMTP SSL |
| 587  | SMTP submission |
| 8880 | HTTP alternative |
| 8008 | HTTP alternative |

Выбери 3-5 портов (не конфликтующих с занятыми). Запиши выбранные порты — они будут использоваться в инбаундах CZ сервера (порты должны совпадать!).

### 2.3 Настройка DNAT

Для каждого выбранного порта:
```bash
CZ_IP="[IP CZ сервера]"
PORT=[выбранный порт]

# DNAT: входящий трафик на PORT → CZ сервер
iptables -t nat -A PREROUTING -p tcp --dport $PORT -j DNAT --to-destination $CZ_IP:$PORT
```

После всех портов — MASQUERADE:
```bash
iptables -t nat -A POSTROUTING -d $CZ_IP -j MASQUERADE
```

Сохранить правила:
```bash
apt install -y iptables-persistent
netfilter-persistent save
```

Проверить:
```bash
iptables -t nat -L PREROUTING -n
```

---

## ШАГ 3 — Настройка CZ сервера (3x-ui + инбаунды)

### 3.1 Проверить/установить 3x-ui

Если 3x-ui не установлен:
```bash
bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)
```

Если установлен — продолжай.

### 3.2 Найти хороший SNI донор

Для Reality нужен сайт с поддержкой HTTP/2 и близким пингом. Проверь с CZ сервера:
```bash
for sni in www.apple.com www.microsoft.com www.google.com www.cloudflare.com; do
  result=$(curl -so /dev/null -w "%{time_connect}" --max-time 3 https://$sni 2>/dev/null)
  echo "$sni: ${result}s"
done
```

Выбери самый быстрый (обычно `www.apple.com` или `www.cloudflare.com`).

### 3.3 Создать инбаунды через API 3x-ui

Для каждого выбранного порта создай инбаунд.

Сначала авторизуйся в панели — получи сессионную куку:
```bash
PANEL_URL="[URL панели CZ]"
PANEL_USER="[логин]"
PANEL_PASS="[пароль]"

# Авторизация
curl -sk -c /tmp/xui_cookie.txt -X POST "$PANEL_URL/login" \
  -d "username=$PANEL_USER&password=$PANEL_PASS"
```

Создай инбаунд (VLESS + Reality + gRPC):
```bash
PORT=[порт]
SNI="www.apple.com"  # или выбранный SNI

# Получить ключи Reality (если нет — сгенерировать)
# Найти бинарик xray:
XRAY_BIN=$(find /usr/local/x-ui -name "xray-linux-*" -type f 2>/dev/null | head -1)
# Сгенерировать пару ключей:
$XRAY_BIN x25519

PUBKEY="[публичный ключ Reality]"
PRIVKEY="[приватный ключ Reality]"
SHORT_ID=$(openssl rand -hex 8)

curl -sk -b /tmp/xui_cookie.txt -X POST "$PANEL_URL/panel/api/inbounds/add" \
  -H "Content-Type: application/json" \
  -d "{
    \"remark\": \"WhiteL_${PORT}\",
    \"enable\": true,
    \"protocol\": \"vless\",
    \"port\": $PORT,
    \"settings\": \"{\\\"clients\\\":[],\\\"decryption\\\":\\\"none\\\"}\",
    \"streamSettings\": \"{\\\"network\\\":\\\"grpc\\\",\\\"security\\\":\\\"reality\\\",\\\"realitySettings\\\":{\\\"show\\\":false,\\\"dest\\\":\\\"$SNI:443\\\",\\\"xver\\\":0,\\\"serverNames\\\":[\\\"$SNI\\\"],\\\"privateKey\\\":\\\"$PRIVKEY\\\",\\\"shortIds\\\":[\\\"$SHORT_ID\\\"]},\\\"grpcSettings\\\":{\\\"serviceName\\\":\\\"api\\\"}}\",
    \"sniffing\": \"{\\\"enabled\\\":true,\\\"destOverride\\\":[\\\"http\\\",\\\"tls\\\",\\\"quic\\\"]}\"
  }"
```

**⚠️ КРИТИЧНО:** для gRPC Reality поле `flow` должно быть ПУСТЫМ (flow=xtls-rprx-vision только для TCP!).

### 3.4 Открыть порты в UFW

```bash
for PORT in [список портов через пробел]; do
  ufw allow $PORT/tcp
done
ufw reload
```

Проверить:
```bash
ss -tlnp | grep xray
ufw status | grep -E '[0-9]+'
```

### 3.5 Записать параметры инбаундов

После создания — получи данные инбаундов:
```bash
curl -sk -b /tmp/xui_cookie.txt "$PANEL_URL/panel/api/inbounds/list" | python3 -m json.tool
```

Запиши для каждого инбаунда: `inbound_id`, `port`, `pubkey`, `shortId`, `sni`.

---

## ШАГ 4 — Сервер подписок на RU сервере

### 4.1 Создать файлы

```bash
mkdir -p /opt/subscription
```

Создай `/opt/subscription/config.json`:
```json
{
  "panels": [
    {
      "url": "[URL панели CZ без trailing slash]",
      "user": "[логин]",
      "pass": "[пароль]"
    }
  ],
  "ru_vps_ip": "[IP RU сервера]",
  "sub_port": "8888",
  "support_url": "tg://resolve?domain=[telegram username владельца]",
  "support_text": "[название профиля ASCII]"
}
```

### 4.2 Создать server.py

```python
#!/usr/bin/env python3
"""Subscription server — выдаёт vless:// ссылки с RU IP для Happ/Sing-Box."""

import json, ssl, urllib.request, urllib.parse, base64, http.server, logging, re
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

CONFIG = json.loads(Path("/opt/subscription/config.json").read_text())
PANELS = CONFIG["panels"]
RU_IP = CONFIG["ru_vps_ip"]
SUB_PORT = int(CONFIG["sub_port"])
SUPPORT_URL = CONFIG["support_url"]
SUPPORT_TEXT = CONFIG["support_text"]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def panel_login(panel):
    data = urllib.parse.urlencode({"username": panel["user"], "password": panel["pass"]}).encode()
    req = urllib.request.Request(f"{panel['url']}/login", data=data, method="POST")
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx),
                                         urllib.request.HTTPCookieProcessor())
    opener.open(req)
    return opener


def get_inbounds(opener, panel):
    req = urllib.request.Request(f"{panel['url']}/panel/api/inbounds/list")
    resp = opener.open(req)
    return json.loads(resp.read())["obj"] or []


def find_client(uuid_search):
    """Ищет UUID во всех панелях. Возвращает (inbound, client_email, panel_url) или None."""
    for panel in PANELS:
        try:
            opener = panel_login(panel)
            for inbound in get_inbounds(opener, panel):
                # Ищем в clientStats
                stats_req = urllib.request.Request(
                    f"{panel['url']}/panel/api/inbounds/list"
                )
                # Ищем в settings.clients
                try:
                    settings = json.loads(inbound.get("settings", "{}"))
                    clients = settings.get("clients", [])
                    for c in clients:
                        if c.get("id") == uuid_search:
                            return inbound, c, panel
                except Exception:
                    pass
                # Ищем в clientStats
                for stat in (inbound.get("clientStats") or []):
                    if stat.get("email", "").startswith(uuid_search[:8]):
                        # дополнительная проверка через settings
                        try:
                            settings = json.loads(inbound.get("settings", "{}"))
                            for c in settings.get("clients", []):
                                if c.get("id") == uuid_search:
                                    return inbound, c, panel
                        except Exception:
                            pass
        except Exception as e:
            log.warning(f"Panel {panel['url']} error: {e}")
    return None


def build_vless(uuid, inbound, ru_ip):
    """Строит vless:// ссылку с RU IP."""
    try:
        stream = json.loads(inbound.get("streamSettings", "{}"))
        reality = stream.get("realitySettings", {})
        grpc = stream.get("grpcSettings", {})
        port = inbound["port"]
        sni = (reality.get("serverNames") or [""])[0]
        pubkey = reality.get("settings", {}).get("publicKey", "")
        short_ids = reality.get("shortIds") or [""]
        sid = short_ids[0] if short_ids else ""
        service = grpc.get("serviceName", "api")
        remark = urllib.parse.quote(inbound.get("remark", "VPN"))
        return (f"vless://{uuid}@{ru_ip}:{port}"
                f"?type=grpc&security=reality&mode=gun"
                f"&pbk={pubkey}&sid={sid}&sni={sni}&fp=chrome"
                f"&serviceName={service}#{remark}")
    except Exception as e:
        log.error(f"build_vless error: {e}")
        return None


def get_userinfo(inbound, email):
    """Возвращает строку Subscription-Userinfo."""
    try:
        for stat in (inbound.get("clientStats") or []):
            if stat.get("email") == email:
                up = stat.get("up", 0)
                down = stat.get("down", 0)
                total = stat.get("total", 0)
                expire = stat.get("expiryTime", 0) // 1000
                return f"upload={up}; download={down}; total={total}; expire={expire}"
    except Exception:
        pass
    return ""


class SubHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        log.info(f"{self.client_address[0]} {fmt % args}")

    def do_GET(self):
        path = self.path.strip("/")
        parts = path.split("/")
        if len(parts) == 2 and parts[0] == "sub":
            uuid = parts[1]
            result = find_client(uuid)
            if not result:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Not found")
                return
            inbound, client, panel = result
            email = client.get("email", uuid)
            link = build_vless(uuid, inbound, RU_IP)
            if not link:
                self.send_response(500)
                self.end_headers()
                return
            body = base64.b64encode(link.encode()).decode()
            userinfo = get_userinfo(inbound, email)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Profile-Title", SUPPORT_TEXT)
            self.send_header("Profile-Web-Page-Url", SUPPORT_URL)
            self.send_header("Support-Url", SUPPORT_URL)
            if userinfo:
                self.send_header("Subscription-Userinfo", userinfo)
            self.end_headers()
            self.wfile.write(body.encode())
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", SUB_PORT), SubHandler)
    log.info(f"Subscription server listening on :{SUB_PORT}")
    server.serve_forever()
```

### 4.3 Systemd сервис

```bash
cat > /etc/systemd/system/subscription.service << 'EOF'
[Unit]
Description=Subscription Server
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/subscription/server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable subscription
systemctl start subscription
systemctl status subscription
```

### 4.4 HTTPS через Let's Encrypt (нужен домен)

Домен должен указывать на RU сервер (A-запись). Затем:

```bash
apt install -y certbot
# Временно остановить всё что слушает 80:
# (если nginx — nginx -s stop, если другое — аналогично)

certbot certonly --standalone -d [домен] --non-interactive --agree-tos -m admin@[домен]

# Пути к сертификатам:
# /etc/letsencrypt/live/[домен]/fullchain.pem
# /etc/letsencrypt/live/[домен]/privkey.pem
```

Обнови `server.py` — добавь SSL обёртку перед `server.serve_forever()`:

```python
import ssl
server = http.server.HTTPServer(("0.0.0.0", SUB_PORT), SubHandler)
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.load_cert_chain(
    "/etc/letsencrypt/live/[домен]/fullchain.pem",
    "/etc/letsencrypt/live/[домен]/privkey.pem"
)
server.socket = ctx.wrap_socket(server.socket, server_side=True)
log.info(f"Subscription server (HTTPS) listening on :{SUB_PORT}")
server.serve_forever()
```

Также обнови `config.json` — добавь поле `"domain"` и используй его в sub_url.

### 4.5 Открыть порт 8888 на RU сервере

```bash
ufw allow 8888/tcp 2>/dev/null || iptables -I INPUT -p tcp --dport 8888 -j ACCEPT
```

### 4.6 Проверить сервер подписок

```bash
# Должен ответить 404 (сервер работает, UUID не найден)
curl -si https://[домен]:8888/sub/test-uuid | head -5
```

---

## ШАГ 5 — Создание пользователей

### 5.1 Создать пользователей через API

Для каждого пользователя (запроси у владельца: сколько, на каком инбаунде, какой срок):

```bash
PANEL_URL="[URL CZ панели]"
INBOUND_ID=[id инбаунда]
NICK="[ник]"
TRAFFIC_GB=1000  # 1000 GB
DAYS=365

# Вычислить срок в ms
EXPIRY_MS=$(python3 -c "
import datetime, time
d = datetime.datetime.now() + datetime.timedelta(days=$DAYS)
d = d.replace(hour=23, minute=59, second=59)
print(int(d.timestamp() * 1000))
")

TRAFFIC_BYTES=$(python3 -c "print($TRAFFIC_GB * 1024**3)")

UUID=$(python3 -c "import uuid; print(uuid.uuid4())")
EMAIL="${NICK}_WhiteL"

curl -sk -b /tmp/xui_cookie.txt -X POST "$PANEL_URL/panel/api/inbounds/addClient" \
  -H "Content-Type: application/json" \
  -d "{
    \"id\": $INBOUND_ID,
    \"settings\": \"{\\\"clients\\\":[{\\\"id\\\":\\\"$UUID\\\",\\\"email\\\":\\\"$EMAIL\\\",\\\"totalGB\\\":$TRAFFIC_BYTES,\\\"expiryTime\\\":$EXPIRY_MS,\\\"enable\\\":true,\\\"tgId\\\":\\\"\\\",\\\"subId\\\":\\\"\\\"}]}\"
  }"

echo "UUID: $UUID"
echo "Sub URL: http://[RU_IP]:8888/sub/$UUID"
```

### 5.2 Проверить ссылку подписки

```bash
curl -si http://[RU_IP]:8888/sub/$UUID
# Должен вернуть 200 и base64 строку
```

### 5.3 Сформировать MD файл с ссылками

Создай файл `SUBSCRIPTION_LINKS.md` в рабочей папке:

```markdown
# VPN Подписки

Сервер подписок: http://[RU_IP]:8888

## Пользователи

| Ник | Ссылка подписки | Трафик | Срок |
|-----|----------------|--------|------|
| [ник] | http://[RU_IP]:8888/sub/[UUID] | 1000 GB | до [дата] |
```

Как вставить в Happ:
1. Скопировать ссылку подписки
2. Открыть Happ → "+" справа вверху → вставить ссылку
3. Профиль появится автоматически

---

## ШАГ 6 — Финальная проверка

```bash
# 1. Форвардинг включён на RU сервере
ssh root@RU_IP "cat /proc/sys/net/ipv4/ip_forward"  # должно быть 1

# 2. DNAT правила на месте
ssh root@RU_IP "iptables -t nat -L PREROUTING -n"

# 3. Инбаунды на CZ сервере активны
ssh root@CZ_IP "ss -tlnp | grep xray"

# 4. Порты открыты на CZ сервере
ssh root@CZ_IP "ufw status"

# 5. Сервер подписок отвечает
curl -si http://RU_IP:8888/sub/TEST | head -3

# 6. Подписка возвращает данные для реального UUID
curl -si http://RU_IP:8888/sub/$UUID | head -5
```

Выведи итоговый отчёт:
```
✅ RU relay: форвардинг + DNAT настроены
✅ CZ сервер: [N] инбаундов активны на портах [список]
✅ Сервер подписок: http://[RU_IP]:8888 — работает
✅ Создано пользователей: [N]

Файл с ссылками: SUBSCRIPTION_LINKS.md
```

---

## Важные нюансы (прочти перед началом)

- **DNAT порты = порты инбаундов**: если на RU сервере DNAT на порт 2086 → на CZ сервере инбаунд ДОЛЖЕН слушать порт 2086
- **gRPC Reality без flow**: поле flow оставлять ПУСТЫМ для gRPC (xtls-rprx-vision только для TCP/TLS)
- **UFW на CZ**: 3x-ui не открывает порты в UFW автоматически — открывать вручную
- **Собственный Xray на RU сервере**: если есть — не трогать его порты при DNAT (конфликт убьёт оба сервиса)
- **Новый клиент 404**: UUID появляется в clientStats только после первого подключения; сервер подписок ищет и в settings.clients — поэтому работает сразу после создания
- **Profile-Title только ASCII**: Cyrillic/emoji вызывают ошибку в BaseHTTPServer
- **Telegram иконка в Happ**: нужен заголовок `Support-Url` (не только `Profile-Web-Page-Url`)
