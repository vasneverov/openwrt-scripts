# VPN Settings — PL4

## Сервер

| Параметр | Значение |
|---|---|
| IP | `82.38.66.75` |
| Hostname | `PL4.red` |
| SSH user | `root` |
| SSH password | `T-RUeIl9%+` |
| ОС | Debian/Ubuntu |

## Панель 3x-ui

| Параметр | Значение |
|---|---|
| URL | `https://82.38.66.75:5050/5050/panel/inbounds` |
| Порт | `5050` |
| basePath | `/5050/` |
| Логин | `ad` |
| Пароль | `56` |
| Версия | 2.8.11 |
| БД | `/etc/x-ui/x-ui.db` |
| SSL cert | `/etc/x-ui/ssl/fullchain.pem` (самоподписной на IP, 10 лет) |

## Инбаунды

### pl4_rout — gRPC + Reality (порт 5228)

| Параметр | Значение |
|---|---|
| Порт | `5228` (push notifications Android) |
| Протокол | VLESS |
| Transport | gRPC |
| Security | Reality |
| Flow | **пустой** (Vision flow только для TCP!) |
| SNI | `www.consilium.europa.eu` |
| Dest | `www.consilium.europa.eu:443` |
| Fingerprint | `chrome` |
| Sniffing | `http`, `tls`, `quic`, `fakedns` |
| gRPC serviceName | `api` |
| Пользователь | `grpc_hostPL4🇵🇱` |
| Трафик | 1000 МБ |
| Срок | 1 год |

### pl4_00 — xHTTP + Reality (порт 5223)

| Параметр | Значение |
|---|---|
| Порт | `5223` (push notifications iOS) |
| Протокол | VLESS |
| Transport | xHTTP |
| Security | Reality |
| Flow | **пустой** |
| SNI | `www.pge.pl` |
| Dest | `www.pge.pl:443` |
| Fingerprint | `chrome` |
| Sniffing | `http`, `tls`, `quic`, `fakedns` |
| xHTTP mode | `packet-up` |
| xHTTP path | `/api/v1/data` |
| xPaddingBytes | `100-1000` |
| Пользователь | `xhttp_hostPL4🇵🇱` |
| Трафик | 1000 МБ |
| Срок | 1 год |

## SNI-сканер — лучшие результаты (с VPS, март 2025)

| SNI | Пинг | H2 | Пригодность |
|---|---|---|---|
| `www.consilium.europa.eu` | 10ms | ✓ | ★★★ идеал gRPC |
| `www.pge.pl` | 27ms | ✓ | ★★★ идеал xHTTP |
| `www.bayer.com` | 32ms | ✓ | ★★ запасной |
| `www.philips.com` | 37ms | ✓ | ★★ запасной |
| `www.siemens.com` | 39ms | ✓ | ★★ запасной |
| `www.ecb.europa.eu` | 44ms | ✓ | ★★ запасной |
| `www.dw.com` | 46ms | ✓ | ★ |

## Тонкие настройки xray (routing template)

Хранится в БД: `settings` → `key=xrayTemplateConfig`

- **Routing**: приватные IP и BitTorrent → blocked
- **DNS**: DoH `https://1.1.1.1/dns-query` для не-CN доменов
- **Log**: loglevel = warning, access = none

## Важные нюансы

- `flow=xtls-rprx-vision` — **только для TCP**. Для gRPC и xHTTP — пустое поле
- `totalGB` в БД хранится в **байтах** (1000 МБ = `1048576000`, 1 ГБ = `1073741824`)
- `expiryTime` в **миллисекундах** Unix timestamp
- `stream_settings` должен содержать `realitySettings.settings.publicKey` (для работы info-кнопки в панели)
- `client_traffics.email` должен совпадать с `inbounds.settings.clients[].email` включая эмодзи
- `datepicker=gregorian` в settings — без этого отображается персидский календарь
- webBasePath `/5050/` — все API вызовы идут через `/5050/panel/...`
- IPv6 отключён на уровне ядра (`sysctl.conf` + GRUB)

## Файлы

| Файл | Описание |
|---|---|
| `/etc/x-ui/x-ui.db` | SQLite БД панели |
| `/etc/x-ui/ssl/fullchain.pem` | TLS сертификат |
| `/etc/x-ui/ssl/privkey.pem` | Приватный ключ TLS |
| `/usr/local/x-ui/bin/config.json` | Сгенерированный конфиг xray (перезаписывается при рестарте) |
| `/usr/local/x-ui/bin/xray-linux-amd64` | Бинарник xray 26.2.6 |
| `CLAUDECODE/VPN/sni-scanner.py` | SNI-сканер (CLI) |
| `CLAUDECODE/VPN/sni-scanner-app.py` | SNI-сканер (GUI для macOS) |
