# Справочник VPN-серверов и релеев

> Обновлено: 2026-04-28  
> Все панели: логин `ad` / пароль `56`  
> SSH-пароль для OpenWrt роутеров: `56756789`

---

## ПРАВИЛА РАСПРЕДЕЛЕНИЯ ПО РОУТЕРАМ

| Роутер | main | YT |
|--------|------|----|
| **СПб** | bSPB:4191 → Fin3 (Finnish IP) | bSPB:8853 (Russian IP) |
| **Москва** | bMSK:5223 → Fin4 (Finnish IP) | bMSK:8853 (Russian IP) |
| **Особые случаи** | bSPB:2090 → Italy (Italian IP) | — |

**Железные правила:**
- `main` — ВСЕГДА через relay, НИКОГДА direct
- `YT` — direct (российский IP нужен для YouTube)
- `calls` — удалять везде, `telegram+meta` переносить первыми в `main`
- `user_domain_list_type` — везде `disabled`, `user_domains_text` удалять
- **Перед созданием relay ВСЕГДА спрашивать город** → СПб = bSPB:4191→Fin3 / Москва = bMSK:5223→Fin4
- Скрипт создания клиента на Fin3: `add_fin3_client.sh <name> <uuid>` (не curl вручную!)

---

## RELAY-СЕРВЕРЫ (российские, точки входа)

### bSPB — Beget Санкт-Петербург (`5.35.84.151`)

| Параметр | Значение |
|----------|----------|
| IP | `5.35.84.151` |
| Панель | https://5.35.84.151:5050/5050/ |
| SSH | пароль неизвестен (доступ через панель) |
| Назначение | Relay-сервер для СПб роутеров |

**Relay-порты (DNAT на целевые серверы):**

| Порт bSPB | → | Целевой сервер | Назначение | pbk | sid |
|-----------|---|----------------|------------|-----|-----|
| **4191** | → | Fin3 `144.31.66.115:4191` | Main для СПб | `XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw` | `932e706c` |
| **2090** | → | Italy `151.243.198.86:2086` | Main Italy-вариант | `OBa4LZ0lL0j9RS52fgCw68jWqkvr_yakmpsolbiqgVI` | `c30f9fec74087d32` |
| **8448** | → | CZ2 `92.61.71.14:8448` | — | — | — |
| **5443** | → | PL6 `91.92.46.152:443` | NaiveProxy relay | — | — |

**Прямые инбаунды на bSPB:**

| Порт | Назначение | pbk | sid | Inbound ID |
|------|------------|-----|-----|------------|
| **8853** | YT direct (bSPB_direct_8853) | `me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM` | `ddcb53b3` | 4 |

**Формат VLESS для main (relay → Fin3):**
```
vless://UUID@5.35.84.151:4191?type=grpc&security=reality&mode=gun&serviceName=&pbk=XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw&sid=932e706c&sni=www.apple.com&fp=chrome&spx=%2F#ROUTER_Fin3
```

**Формат VLESS для YT (direct bSPB):**
```
vless://UUID@5.35.84.151:8853?type=grpc&security=reality&mode=gun&serviceName=&pbk=me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM&sid=ddcb53b3&sni=www.apple.com&fp=chrome&spx=%2F#ROUTER_bSPB_YT
```

**Формат VLESS для main (relay → Italy):**
```
vless://UUID@5.35.84.151:2090?type=grpc&security=reality&mode=gun&serviceName=&pbk=OBa4LZ0lL0j9RS52fgCw68jWqkvr_yakmpsolbiqgVI&sid=c30f9fec74087d32&sni=www.apple.com&fp=chrome&spx=%2F#ROUTER_Italy
```

---

### bMSK — Beget Москва (`159.194.198.172`)

| Параметр | Значение |
|----------|----------|
| IP | `159.194.198.172` |
| Панель | https://159.194.198.172:5050/5050/ |
| SSH | `Ujkjdf56#` |
| Назначение | Relay-сервер для Москвы + YT direct |

**Relay-порты (DNAT → Fin4):**

| Порт bMSK | → | Целевой сервер | pbk | sid |
|-----------|---|----------------|-----|-----|
| **5223** | → | Fin4 `45.155.55.198:4191` | `HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI` | `4b929012` |
| **5228** | → | Fin4 `45.155.55.198:4192` | `HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI` | `ae2bfb99` |
| **5323** | → | PL5 `91.92.46.229:4191`  | `4TCLYNy_kglu_bpE5n3Gx0yQ7L8TJQKRLATLgnXbtEw` | `b5023350` |
| **5328** | → | PL5 `91.92.46.229:4192`  | `4TCLYNy_kglu_bpE5n3Gx0yQ7L8TJQKRLATLgnXbtEw` | `3e980e42` |

**Прямые инбаунды на bMSK:**

| Порт | Назначение | pbk | sid | Inbound ID |
|------|------------|-----|-----|------------|
| **8853** | YT direct (bmsk_yt_rout_8853) | `g5eg_BKQJLVbPxryppyE0AGpQB_HKHPGkOJN9I6bSzI` | `1cbf0359` | 1 |

**Формат VLESS для main (relay → Fin4):**
```
vless://UUID@159.194.198.172:5223?type=grpc&security=reality&mode=gun&serviceName=&pbk=HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI&sid=4b929012&sni=www.apple.com&fp=chrome&spx=%2F#ROUTER_Fin4
```

**Формат VLESS для YT (direct bMSK):**
```
vless://UUID@159.194.198.172:8853?type=grpc&security=reality&mode=gun&serviceName=&pbk=g5eg_BKQJLVbPxryppyE0AGpQB_HKHPGkOJN9I6bSzI&sid=1cbf0359&sni=www.apple.com&fp=chrome&spx=%2F#ROUTER_bMSK_YT
```

---

## ЦЕЛЕВЫЕ СЕРВЕРЫ (финские и другие, точки выхода)

### Fin3 — Финляндия 3 (`144.31.66.115`)

| Параметр | Значение |
|----------|----------|
| IP | `144.31.66.115` |
| Панель | https://144.31.66.115:5050/5050/ |
| Скрипт добавления | `/Users/vas/CLAUDECODE/tools/add_fin3_client.sh <name> <uuid>` |

**Инбаунды:**

| ID | Порт | Remark | Для кого | pbk | sid |
|----|------|--------|----------|-----|-----|
| 1 | 2083 | Fin3 | Не-роутеры (личные) | — | — |
| 3 | 4191 | WL_rout_fin3_4191 | Роутеры через bSPB relay | `XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw` | `932e706c` |

> **Клиентов добавлять через скрипт:** `add_fin3_client.sh` — не вручную!

---

### Fin4 — Финляндия 4 (`45.155.55.198`)

| Параметр | Значение |
|----------|----------|
| IP | `45.155.55.198` |
| Панель | https://45.155.55.198:5050/5050/ |

**Инбаунды:**

| ID | Порт | Remark | Relay вход | pbk | sid |
|----|------|--------|------------|-----|-----|
| 1 | 4191 | fin4_rout_1 | bMSK:5223 | `HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI` | `4b929012` |
| 2 | 4192 | fin4_rout_2 | bMSK:5228 | `HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI` | `ae2bfb99` |

---

### Italy — Италия (`151.243.198.86`)

| Параметр | Значение |
|----------|----------|
| IP | `151.243.198.86` |
| Панель | https://151.243.198.86:5050/5050/ |

**Инбаунды:**

| ID | Порт | Remark | Relay вход | pbk | sid |
|----|------|--------|------------|-----|-----|
| 2 | 2086 | italy.red_rout | bSPB:2090 | `OBa4LZ0lL0j9RS52fgCw68jWqkvr_yakmpsolbiqgVI` | `c30f9fec74087d32` |

### PL5 — Польша 5 (`91.92.46.229`)

| Параметр | Значение |
|----------|----------|
| IP | `91.92.46.229` |
| Панель | https://91.92.46.229:5050/5050/ |

**Инбаунды:**

| ID | Порт | Remark | Relay вход | pbk | sid |
|----|------|--------|------------|-----|-----|
| 1 | 4191 | pl5_rout_1 | bMSK:5323 | `4TCLYNy_kglu_bpE5n3Gx0yQ7L8TJQKRLATLgnXbtEw` | `b5023350` |
| 2 | 4192 | pl5_rout_2 | bMSK:5328 | `4TCLYNy_kglu_bpE5n3Gx0yQ7L8TJQKRLATLgnXbtEw` | `3e980e42` |

**Формат VLESS для main (московская схема → PL5):**
```
vless://UUID@159.194.198.172:5323?type=grpc&security=reality&mode=gun&serviceName=&pbk=4TCLYNy_kglu_bpE5n3Gx0yQ7L8TJQKRLATLgnXbtEw&sid=b5023350&sni=www.apple.com&fp=chrome&spx=%2F#ROUTER_PL5
```

---

## ПРЯМЫЕ СЕРВЕРЫ (direct, не relay)

### bSPB direct 8853 (YT, российский IP)
Описан выше в разделе bSPB.

### bMSK direct 8853 (YT, российский IP)
Описан выше в разделе bMSK.

### wRU2 (`ru2panel.8bit.ca`)
| Параметр | Значение |
|----------|----------|
| Панель | https://ru2panel.8bit.ca:5050/5050/ |
| Порт | 8443 |
| SNI | `api.vk.com` |
| Назначение | YT альтернатива (некоторые старые роутеры) |

### HipLT (`92.118.170.193`) — УСТАРЕВШИЙ
| Параметр | Значение |
|----------|----------|
| Панель | https://92.118.170.193:5050/5050/ |
| Статус | ⚠️ Устаревший — заменяем на relay |

---

## ОСТАЛЬНЫЕ СЕРВЕРЫ (не используются для роутеров)

| Имя | URL панели | Назначение |
|-----|------------|------------|
| AdminVPS FIN | https://217.11.167.181:9090/9090/panel/ | — |
| Wiesel EST | https://94.156.236.241:5050/5050/panel/ | — |
| W NL | https://45.88.67.154:5050/5050/panel/ | — |
| HOSTKEY US | https://162.120.19.181:5050/5050/panel/ | — |
| wPL | https://138.124.72.238:5050/5050/panel/ | — |
| wNL2 | https://panelred.xxxtream.net:5050/5050/panel/ | — |
| ApeCZ | https://cz.8bit.ca:5050/5050/panel/ | — |
| Fin2 (HostFin) | https://89.125.196.83:5050/5050/ | — |
| ApeCZ2 | https://cz2.theredhat.su:5050/5050/panel/ | — |
| HandyRU | https://handyru.theredhat.su:5050/5050/panel/ | YT альтернатива |
| IPhoster PL | https://plhoster.theredhat.su:5050/5050/panel/ | — |
| ipHoster DE | https://hostde.theredhat.su:5050/5050/panel/ | — |
| ipHoster PL2 | https://pl2iph.theredhat.su:5050/5050/panel/ | — |
| PL3host | https://pl3host.theredhat.su:5050/5050/panel/ | — |
| PL4host | https://hpl4.theredhat.su:5050/5050/panel/ | SSH: `T-RUeIl9%+` |
| ApeCZ3 | https://cz3.theredhat.su:5050/5050/panel/ | — |

---

## ТОПОЛОГИЯ RELAY (схема)

```
СПб роутер
    │
    ├─ main ──► bSPB:4191 ──[DNAT]──► Fin3:4191 (🇫🇮 Finnish IP)
    ├─ main ──► bSPB:2090 ──[DNAT]──► Italy:2086 (🇮🇹 Italian IP)
    └─ YT  ──► bSPB:8853  (прямой, 🇷🇺 Russian IP)

Москва роутер
    │
    ├─ main ──► bMSK:5223 ──[DNAT]──► Fin4:4191 (🇫🇮 Finnish IP)
    └─ YT  ──► bMSK:8853  (прямой, 🇷🇺 Russian IP)
```

---

## СКРИПТЫ

| Скрипт | Назначение |
|--------|------------|
| `/Users/vas/CLAUDECODE/tools/add_fin3_client.sh <name> <uuid>` | Добавить клиента на Fin3 inbound 3 |
| `/Users/vas/CLAUDECODE/check_vless.py <key_file>` | Проверить VLESS ключ (нужен READY перед установкой) |
| `/Users/vas/CLAUDECODE/add_all_m56_clients.py` | Массовое добавление M56 серии |
