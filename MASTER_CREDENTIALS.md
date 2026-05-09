Элскейл дерп вообще на четыреста сорок третье порту нам вообще не нужен. Удали его. Я его отключил и сказал удалить.# MASTER CREDENTIALS — полный справочник доступов

> Обновлено: 2026-04-30  
> Единая точка правды для всех паролей, IP, соответствий

---

## РОУТЕРЫ OpenWrt

| Параметр | Значение |
|----------|----------|
| SSH пароль (все роутеры) | `56756789` |
| SSH флаги (OpenWrt 25.12) | `-o PreferredAuthentications=password -o PubkeyAuthentication=no` |
| LAN IP (при подключении кабелем) | `192.168.5.1` |
| WiFi SSID / пароль | `@open` / `56756789` |
| Панели X-UI (все роутеры) | логин `ad` / пароль `56` |

```bash
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no \
  -o PreferredAuthentications=password -o PubkeyAuthentication=no \
  root@<TAILSCALE_IP>
```

---

## СЕРВЕРЫ — SSH и панели

### sbrain 🇩🇪 — Second Brain бот (Германия)
| Параметр | Значение |
|----------|----------|
| IP | `144.31.244.181` |
| SSH пользователь | `root` |
| SSH пароль | `Ujkjdf56` |
| Назначение | Second Brain Telegram бот, обработка daily entries |
| Структура | `/home/sbrain/sbrain/vault/` — Obsidian vault |
| Skill | `/home/sbrain/sbrain/vault/.claude/skills/dbrain-processor/SKILL.md` |

```bash
sshpass -p 'Ujkjdf56' ssh -o StrictHostKeyChecking=no root@144.31.244.181
```

---

### PL4 🇵🇱 — Главный управляющий сервер
| Параметр | Значение |
|----------|----------|
| IP | `82.38.66.75` |
| SSH пароль | `T-RUeIl9%+` |
| Панель X-UI | https://hpl4.theredhat.su:5050/5050/ (ad/56) |
| Что работает | router-monitor бот, XUI бот (`/opt/xui-bot/`), subscription cron |
| Tailscale | `hpl4.theredhat.su` |

```bash
sshpass -p 'T-RUeIl9%+' ssh root@82.38.66.75
```

---

### bMSK 🇷🇺 — Relay Москва
| Параметр | Значение |
|----------|----------|
| IP | `159.194.198.172` |
| SSH пароль | `Ujkjdf56#` |
| Панель X-UI | https://159.194.198.172:5050/5050/ (ad/56) |
| Назначение | Relay для Москвы → Fin4 |
| Relay порты | 5223 → Fin4:4191, 5228 → Fin4:4192, 5323 → PL5:4191, 5328 → PL5:4192, 8853 (YT direct) |

```bash
sshpass -p 'Ujkjdf56#' ssh root@159.194.198.172
```

---

### Fin3 🇫🇮 — Финляндия 3
| Параметр | Значение |
|----------|----------|
| IP | `144.31.66.115` |
| SSH пароль | `Ujkjdf56` |
| Панель X-UI | https://144.31.66.115:5050/5050/ (ad/56) |
| Назначение | Основной выходной узел для СПб роутеров |
| Инбаунды | 4190 (fin2_4190), 4191 (relay через bSPB), 2083 (bundle2) |
| pbk (4191) | `XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw` |
| sid (4191) | `932e706c` |

```bash
sshpass -p 'Ujkjdf56' ssh root@144.31.66.115
```

---

### Fin4 🇫🇮 — Финляндия 4
| Параметр | Значение |
|----------|----------|
| IP | `45.155.55.198` |
| SSH пароль | `duqwgjXiT4FRrc` |
| Панель X-UI | https://45.155.55.198:5050/5050/ (ad/56) |
| Назначение | Основной выходной узел для Москвы |
| Инбаунды | 4191 (relay bMSK:5223), 4192 (relay bMSK:5228) |
| pbk | `HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI` |
| sid (4191) | `4b929012`, sid (4192) `ae2bfb99` |

```bash
sshpass -p 'duqwgjXiT4FRrc' ssh root@45.155.55.198
```

---

### PL5 🇵🇱 — Польша 5
| Параметр | Значение |
|----------|----------|
| IP | `91.92.46.229` |
| SSH пароль | `6pI3gBvJtVxjea` |
| Панель X-UI | https://91.92.46.229:5050/5050/ (ad/56) |
| Назначение | Выходной узел для Москвы (через bMSK relay) |
| Инбаунды | 4191 (relay bMSK:5323), 4192 (relay bMSK:5328) |
| pbk | `4TCLYNy_kglu_bpE5n3Gx0yQ7L8TJQKRLATLgnXbtEw` |
| sid (4191) | `b5023350`, sid (4192) `3e980e42` |

```bash
sshpass -p '6pI3gBvJtVxjea' ssh root@91.92.46.229
```

---

### PL6 🇵🇱 — Польша 6 (NaiveProxy)
| Параметр | Значение |
|----------|----------|
| IP | `91.92.46.152` |
| SSH пароль | `AXD0tm4ru942ij` |
| Панель X-UI | https://91.92.46.152:5050/5050/ (ad/56) |
| Назначение | NaiveProxy Caddy + X-UI (инбаунды 5223, 5228) |
| Caddy Docker | `naive-caddy` — порты 80/443, forwardproxy |
| Caddy пользователи | `vasya56` / `56neverov` (старый), `naive` / `56756789` (для бота) |
| Домен | `open.theredhat.su` |
| Relay | bMSK:5443 → PL6:443 (DNAT) |

```bash
sshpass -p 'AXD0tm4ru942ij' ssh root@91.92.46.152
```

---

### bSPB ��🇺 — Relay Санкт-Петербург (Beget)
| Параметр | Значение |
|----------|----------|
| IP | `5.35.84.151` |
| SSH пароль | `dRzEcGR*P!3%` (порт 22, открывается после ребута) |
| Панель X-UI | https://5.35.84.151:5050/5050/ (ad/56) |
| Subscription | https://white.theredhat.su:8888 |
| Relay порты | 4191 → Fin3:4191, 2090 → Italy:2086, 8448 → CZ2, 8853 (YT direct) |
| pbk (4191→Fin3) | `XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw` |
| pbk (2090→Italy) | `OBa4LZ0lL0j9RS52fgCw68jWqkvr_yakmpsolbiqgVI` |
| pbk (8853 direct) | `me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM` |

---

### FR 🇫🇷 — Франция
| Параметр | Значение |
|----------|----------|
| IP | `45.155.54.25` |
| SSH пароль | `TXmX0rVnLGBPe3` |
| Панель X-UI | https://45.155.54.25:5050/5050/ (ad/56) |
| Назначение | Выходной узел №2 для mieru (авторотация с Italy) |

```bash
sshpass -p 'TXmX0rVnLGBPe3' ssh root@45.155.54.25
```

---

### Italy 🇮🇹 — Италия
| Параметр | Значение |
|----------|----------|
| IP | `151.243.198.86` |
| SSH пароль | `Ujkjdf56+` |
| Панель X-UI | https://151.243.198.86:5050/5050/ (ad/56) |
| Инбаунды | 2083 (bundle1/2), 2086 (relay через bSPB:2090) |
| pbk (2086) | `OBa4LZ0lL0j9RS52fgCw68jWqkvr_yakmpsolbiqgVI` |

```bash
sshpass -p 'Ujkjdf56+' ssh root@151.243.198.86
```

---

### Fin2 🇫🇮 — Финляндия 2 (Bundle 1)
| Параметр | Значение |
|----------|----------|
| IP | `89.125.196.83` |
| Панель X-UI | https://89.125.196.83:5050/5050/ (ad/56) |
| Инбаунды | 4190 (WL_rout_fin2_4190), 2083 (WL_fin2_2525 — bundle1) |

---

## X-UI СЕРВЕРЫ (полный список)

Все серверы: логин `ad` / пароль `56`

| Название | URL панели | Страна |
|----------|-----------|--------|
| AdminVPS FIN | https://217.11.167.181:9090/9090/panel/ | 🇫🇮 |
| Wiesel EST | https://94.156.236.241:5050/5050/ | 🇪🇪 |
| W_NL | https://45.88.67.154:5050/5050/ | 🇳🇱 |
| AdminDE | https://206.245.159.131:5050/5050/ | 🇩🇪 |
| HOSTKEY US | https://162.120.19.181:5050/5050/ | 🇺🇸 |
| wPL | https://138.124.72.238:5050/5050/panel/ | 🇵🇱 |
| wNL2 (NL2) | https://panelred.xxxtream.net:5050/5050/panel/ | 🇳🇱 |
| wRU2 | https://ru2panel.8bit.ca:5050/5050/ | 🇷🇺 |
| ApeCZ | https://cz.8bit.ca:5050/5050/ | 🇨🇿 |
| HipLT | https://92.118.170.193:5050/5050/panel/ | 🇱🇹 |
| Fin2 (HostFin) | https://89.125.196.83:5050/5050/ | 🇫🇮 |
| ApeCZ2 (CZ2) | https://cz2.theredhat.su:5050/5050/ | 🇨🇿 |
| HandyRU | https://handyru.theredhat.su:5050/5050/ | 🇷🇺 |
| IPhoster PL | https://plhoster.theredhat.su:5050/5050/ | 🇵🇱 |
| HostRU | https://hostru.theredhat.su:5050/5050/ | 🇷🇺 |
| ipHoster DE | https://hostde.theredhat.su:5050/5050/ | 🇩🇪 |
| ipHoster PL2 | https://pl2iph.theredhat.su:5050/5050/ | 🇵🇱 |
| PL3host | https://pl3host.theredhat.su:5050/5050/ | 🇵🇱 |
| **PL4** | https://hpl4.theredhat.su:5050/5050/ | 🇵🇱 |
| **BegetSPB (bSPB)** | https://5.35.84.151:5050/5050/ | 🇷🇺 |
| ApeCZ3 (CZ3) | https://cz3.theredhat.su:5050/5050/ | 🇨🇿 |
| **Fin3** | https://144.31.66.115:5050/5050/ | 🇫🇮 |
| **Fin4** | https://45.155.55.198:5050/5050/ | 🇫🇮 |
| **bMSK** | https://159.194.198.172:5050/5050/ | 🇷🇺 |
| **Italy** | https://151.243.198.86:5050/5050/ | 🇮🇹 |
| **Fin2** | https://89.125.196.83:5050/5050/ | 🇫🇮 |
| **CZ4** | https://193.124.56.2:5050/5050/ | 🇨🇿 |
| **FR** | https://45.155.54.25:5050/5050/ | 🇫🇷 |

---

## TAILSCALE ТОКЕНЫ

| # | Учётка | Tailnet | Серии роутеров |
|---|--------|---------|----------------|
| TS1 | vas.neverov@gmail.com | vas.neverov@gmail.com | TR30, некоторые Z56, cudy |
| TS2 | ne78va@gmail.com | ne78va@gmail.com | S78, M78, zXIA |
| TS3 | 56papezde@gmail.com | 56papezde@gmail.com | TR56, Z56 (большинство) |
| TS4 | n78rout@gmail.com | n78rout@gmail.com | M56, Z56-124..126, TR56-08..10 |

| Учётка | Токен |
|--------|-------|
| TS1 vas.neverov | `tskey-api-ktBh42VtRj11CNTRL-RBTDhNJYzdNNqr7wNTfLdNC6PncxBk63B` |
| TS2 ne78va | `tskey-api-kW1ujQ5i2w11CNTRL-wRvm7o2eCkiEfK7M1fhhjiq763ztrBsx` |
| TS3 56papezde | `tskey-api-k7CKy5KXg421CNTRL-UbV7qjoSeKAbB4Akb1VrJAB6NhfpLkYL` |
| TS4 n78rout | `tskey-api-krWQYxzw1511CNTRL-28hSufddDkPy7RxcKzcdjPS24aFRZLh2` |

Обновление токенов:
```bash
sshpass -p 'T-RUeIl9%+' ssh root@82.38.66.75 'cat /opt/router-monitor/.env'
```

---

## TELEGRAM БОТЫ

| Бот | Назначение | BOT_TOKEN | ADMIN_ID |
|-----|-----------|-----------|----------|
| router-monitor | Мониторинг роутеров | `8724456912:AAHAz0H7os2H2dFl9wqnLZ2C8lbgEqg4GE0` | `50949302` |
| vasyaVPN (@vasyaVPNbot) | XUI управление | `7522740777:AAH97UDULbuevaw0vS0IDw3gb4wsuhODm5A` | `50949302` |
| bundle monitor | Статус серверов | `7522740777:AAH97UDULbuevaw0vS0IDw3gb4wsuhODm5A` | `50949302` |

---

## SUBSCRIPTION СЕРВЕР

| Параметр | Значение |
|----------|----------|
| URL | https://white.theredhat.su:8888 |
| IP | `5.35.84.151` (bSPB) |
| Файлы | `/opt/subscription/` на bSPB |
| Бандл1 стейт | `/opt/subscription/bundle1_active.json` |
| Логи мониторинга | `/var/log/monitor_vpn.log` (на PL4) |
| Cron мониторинга | каждые 2 часа 9-23 МСК (на PL4) |

---

## BUNDLE СТРУКТУРА

### Bundle 1 (CZ3 🇨🇿 / PL4 🇵🇱 / NL2 🇳🇱 / Fin2 🇫🇮)
Ротация: `/opt/subscription/bundle1_active.json` на bSPB

| Сервер | Host | Порт проверки |
|--------|------|--------------|
| CZ3 | 85.137.164.179 | 2082 |
| PL4 | hpl4.theredhat.su | 2083 |
| NL2 | panelred.xxxtream.net | 2083 |
| Fin2 | 89.125.196.83 | 2083 |

### Bundle 2 (CZ4 🇨🇿 / Italy 🇮🇹 / Fin3 🇫🇮)

### Bundle 3 (DE 🇩🇪 / Fin3 🇫🇮 / PL5 🇵🇱)

---

## RELAY ТОПОЛОГИЯ

```
СПб роутер
  ├─ main ──► bSPB:4191 ──[DNAT]──► Fin3:4191  (🇫🇮 финский IP)
  ├─ main ──► bSPB:2090 ──[DNAT]──► Italy:2086 (🇮🇹 итальянский IP)
  └─ YT   ──► bSPB:8853  (прямой, 🇷🇺 российский IP)

Москва роутер
  ├─ main (Fin4) ──► bMSK:5223 ──[DNAT]──► Fin4:4191  (🇫🇮 финский IP)
  ├─ main (PL5)  ──► bMSK:5323 ──[DNAT]──► PL5:4191   (🇵🇱 польский IP)
  └─ YT          ──► bMSK:8853  (прямой, 🇷🇺 российский IP)
```

---

## PBK/SID СПРАВОЧНИК

| Сервер | Порт | pbk | sid |
|--------|------|-----|-----|
| Fin3 (direct) | 4191 | `XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw` | `932e706c` |
| bSPB→Fin3 | 4191 | `XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw` | `932e706c` |
| bSPB→Italy | 2090 | `OBa4LZ0lL0j9RS52fgCw68jWqkvr_yakmpsolbiqgVI` | `c30f9fec74087d32` |
| bSPB direct YT | 8853 | `me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM` | `ddcb53b3` |
| Fin4 (bMSK:5223) | 4191 | `HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI` | `4b929012` |
| Fin4 (bMSK:5228) | 4192 | `HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI` | `ae2bfb99` |
| PL5 (bMSK:5323)  | 4191 | `4TCLYNy_kglu_bpE5n3Gx0yQ7L8TJQKRLATLgnXbtEw` | `b5023350` |
| PL5 (bMSK:5328)  | 4192 | `4TCLYNy_kglu_bpE5n3Gx0yQ7L8TJQKRLATLgnXbtEw` | `3e980e42` |
| bMSK direct YT | 8853 | (см. SERVERS_RELAY_REFERENCE.md) | — |

---

## БЫСТРЫЕ КОМАНДЫ

```bash
# Проверить все X-UI серверы
cd ~/CLAUDECODE/servers/xui-bot && python3 check_servers.py

# Запустить мониторинг вручную
sshpass -p 'T-RUeIl9%+' ssh root@82.38.66.75 \
  "cd /opt/xui-bot && BOT_TOKEN=7522740777:AAH97UDULbuevaw0vS0IDw3gb4wsuhODm5A ADMIN_ID=50949302 python3 monitor_vpn.py"

# Создать ключ на Fin3
~/CLAUDECODE/tools/add_fin3_client.sh <name> <uuid>

# Проверить VLESS ключ
echo 'vless://...' | python3 ~/CLAUDECODE/check_vless.py -

# Подключиться к роутеру по Tailscale IP
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no \
  -o PreferredAuthentications=password -o PubkeyAuthentication=no \
  root@<TAILSCALE_IP>
```
