# КАТАЛОГ КЛЮЧЕЙ — Relay-схемы и прямые серверы

> Обновлено: 2026-05-11  
> Все панели: логин `ad` / пароль `56`  
> SSH-пароль OpenWrt роутеров: `56756789`

---

## 1. RELAY-СХЕМЫ (готовые, DNAT настроен)

### 1.0 СПб → bSPB → CZ3 (Чехия) — роутерные ключи

| Параметр | Значение |
|----------|----------|
| Relay | bSPB `5.35.84.151:8880` |
| Цель | CZ3 `85.137.164.179:8880` |
| Страна выхода | 🇨🇿 Чехия |
| pbk | `Ef6WCkwNoSXIRWamiaU8j-icLatwufKolHUF1R8G3gs` |
| sid | `b9a82e` |
| SNI | `www.apple.com` |
| Inbound ID (CZ3) | 17 (✅ CZ3_rout_8880) |
| Файл ключей | `ключи/vless_cz3_rout_8880_98.md` (98-107), `ключи/vless_cz3_rout_8880_108.md` (108-120) |

**VLESS URL:**
```
vless://UUID@5.35.84.151:8880?type=grpc&security=reality&mode=gun&serviceName=&pbk=Ef6WCkwNoSXIRWamiaU8j-icLatwufKolHUF1R8G3gs&sid=b9a82e&sni=www.apple.com&fp=chrome&spx=/#ROUTER_ApeCZ3
```


### 1.1 СПб → bSPB → Fin3 (Финляндия)

| Параметр | Значение |
|----------|----------|
| Relay | bSPB `5.35.84.151:4191` |
| Цель | Fin3 `144.31.66.115:4191` |
| Страна выхода | 🇫🇮 Финляндия |
| pbk | `XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw` |
| sid | `932e706c` |
| SNI | `www.apple.com` |
| Inbound ID (Fin3) | 3 (✅ включён, порт 4191, Reality настроен) |
| Скрипт добавления | `tools/add_fin3_client.sh <name> <uuid>` |

**VLESS URL:**
```
vless://UUID@5.35.84.151:4191?type=grpc&security=reality&mode=gun&serviceName=&pbk=XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw&sid=932e706c&sni=www.apple.com&fp=chrome&spx=%2F#ROUTER_Fin3
```

### 1.2 Москва → bMSK → Fin4 (Финляндия)

| Параметр | Значение |
|----------|----------|
| Relay | bMSK `159.194.198.172:5223` |
| Цель | Fin4 `45.155.55.198:4191` |
| Страна выхода | 🇫🇮 Финляндия |
| pbk | `HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI` |
| sid | `4b929012` |
| SNI | `www.apple.com` |
| Inbound ID (Fin4) | 1 |

**VLESS URL:**
```
vless://UUID@159.194.198.172:5223?type=grpc&security=reality&mode=gun&serviceName=&pbk=HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI&sid=4b929012&sni=www.apple.com&fp=chrome&spx=%2F#ROUTER_Fin4
```

### 1.3 Москва → bMSK → Fin4 (Финляндия, порт 2)

| Параметр | Значение |
|----------|----------|
| Relay | bMSK `159.194.198.172:5228` |
| Цель | Fin4 `45.155.55.198:4192` |
| Страна выхода | 🇫🇮 Финляндия |
| pbk | `HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI` |
| sid | `ae2bfb99` |
| SNI | `www.apple.com` |
| Inbound ID (Fin4) | 2 |

**VLESS URL:**
```
vless://UUID@159.194.198.172:5228?type=grpc&security=reality&mode=gun&serviceName=&pbk=HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI&sid=ae2bfb99&sni=www.apple.com&fp=chrome&spx=%2F#ROUTER_Fin4_2
```

### 1.4 Москва → bMSK → PL5 (Польша)

| Параметр | Значение |
|----------|----------|
| Relay | bMSK `159.194.198.172:5323` |
| Цель | PL5 `91.92.46.229:4191` |
| Страна выхода | 🇵🇱 Польша |
| pbk | `4TCLYNy_kglu_bpE5n3Gx0yQ7L8TJQKRLATLgnXbtEw` |
| sid | `b5023350` |
| SNI | `www.apple.com` |
| Inbound ID (PL5) | 1 |

**VLESS URL:**
```
vless://UUID@159.194.198.172:5323?type=grpc&security=reality&mode=gun&serviceName=&pbk=4TCLYNy_kglu_bpE5n3Gx0yQ7L8TJQKRLATLgnXbtEw&sid=b5023350&sni=www.apple.com&fp=chrome&spx=%2F#ROUTER_PL5
```

### 1.5 Москва → bMSK → PL5 (Польша, порт 2)

| Параметр | Значение |
|----------|----------|
| Relay | bMSK `159.194.198.172:5328` |
| Цель | PL5 `91.92.46.229:4192` |
| Страна выхода | 🇵🇱 Польша |
| pbk | `4TCLYNy_kglu_bpE5n3Gx0yQ7L8TJQKRLATLgnXbtEw` |
| sid | `3e980e42` |
| SNI | `www.apple.com` |
| Inbound ID (PL5) | 2 |

**VLESS URL:**
```
vless://UUID@159.194.198.172:5328?type=grpc&security=reality&mode=gun&serviceName=&pbk=4TCLYNy_kglu_bpE5n3Gx0yQ7L8TJQKRLATLgnXbtEw&sid=3e980e42&sni=www.apple.com&fp=chrome&spx=%2F#ROUTER_PL5_2
```

### 1.6 СПб → bSPB → Italy (Италия)

| Параметр | Значение |
|----------|----------|
| Relay | bSPB `5.35.84.151:2090` |
| Цель | Italy `151.243.198.86:2086` |
| Страна выхода | 🇮🇹 Италия |
| pbk | `OBa4LZ0lL0j9RS52fgCw68jWqkvr_yakmpsolbiqgVI` |
| sid | `c30f9fec74087d32` |
| SNI | `www.apple.com` |
| Inbound ID (Italy) | 2 |

**VLESS URL:**
```
vless://UUID@5.35.84.151:2090?type=grpc&security=reality&mode=gun&serviceName=&pbk=OBa4LZ0lL0j9RS52fgCw68jWqkvr_yakmpsolbiqgVI&sid=c30f9fec74087d32&sni=www.apple.com&fp=chrome&spx=%2F#ROUTER_Italy
```

### 1.7 СПб → bSPB → CZ2 (Чехия)

| Параметр | Значение |
|----------|----------|
| Relay | bSPB `5.35.84.151:8448` |
| Цель | CZ2 `92.61.71.14:8448` |
| Страна выхода | 🇨🇿 Чехия |
| pbk | `FyCxYT4Ku_RyR7r2dZYo...` (уточнить) |
| sid | `dcaa` |
| SNI | `www.apple.com` |
| Inbound ID (CZ2) | 18 |

---

## 2. ПРЯМЫЕ СЕРВЕРЫ (без relay)

### 2.1 bSPB direct — YT (Россия, СПб)

| Параметр | Значение |
|----------|----------|
| Сервер | bSPB `5.35.84.151:8853` |
| Страна | 🇷🇺 Россия (СПб) |
| pbk | `me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM` |
| sid | `ddcb53b3` |
| SNI | `www.apple.com` |
| Inbound ID (bSPB) | 4 |

**VLESS URL:**
```
vless://UUID@5.35.84.151:8853?type=grpc&security=reality&mode=gun&serviceName=&pbk=me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM&sid=ddcb53b3&sni=www.apple.com&fp=chrome&spx=%2F#ROUTER_bSPB_YT
```

### 2.2 bMSK direct — YT (Россия, Москва)

| Параметр | Значение |
|----------|----------|
| Сервер | bMSK `159.194.198.172:8853` |
| Страна | 🇷🇺 Россия (Москва) |
| pbk | `g5eg_BKQJLVbPxryppyE0AGpQB_HKHPGkOJN9I6bSzI` |
| sid | `1cbf0359` |
| SNI | `www.apple.com` |
| Inbound ID (bMSK) | 1 |

**VLESS URL:**
```
vless://UUID@159.194.198.172:8853?type=grpc&security=reality&mode=gun&serviceName=&pbk=g5eg_BKQJLVbPxryppyE0AGpQB_HKHPGkOJN9I6bSzI&sid=1cbf0359&sni=www.apple.com&fp=chrome&spx=%2F#ROUTER_bMSK_YT
```

### 2.3 HipLT direct (Латвия) — УСТАРЕВШИЙ

| Параметр | Значение |
|----------|----------|
| Сервер | `92.118.170.193:8443` |
| Страна | 🇱🇻 Латвия |
| pbk | `xejYY0atZkxOxGNo_GS2...` |
| sid | `c0` |
| Inbound ID | 2 |
| Статус | ⚠️ Устаревший — заменяем на relay |

### 2.4 CZ2 direct (Чехия)

| Параметр | Значение |
|----------|----------|
| Сервер | `92.61.71.14:8448` |
| Страна | 🇨🇿 Чехия |
| pbk | `FyCxYT4Ku_RyR7r2dZYo...` |
| sid | `dcaa` |
| Inbound ID | 18 |

---

## 3. ДОПОЛНИТЕЛЬНЫЕ ИНБАУНДЫ (для podkop/спецзадач)

### 3.1 bMSK — низкие порты (для podkop)

| Порт | Inbound ID | Назначение | pbk | sid |
|------|-----------|------------|-----|-----|
| 465 | 9 | bMSK_465_TR30-25 | — | `a3f7b2c1` |
| 993 | 8 | bMSK_993 | — | `1d0385b7` |
| 110 | 10 | bMSK_110_z56-102 | — | `b4e8c3d2` |
| 587 | 21 | bMSK_587_relay_Fin4 | — | `1cbf0359` |

### 3.2 bSPB — дополнительные

| Порт | Inbound ID | Назначение | pbk | sid |
|------|-----------|------------|-----|-----|
| 6443 | 1 | bSPB_6443 | `IltXRYeXrYkNGI7ieroM...` | `c89b9149` |
| 7443 | 2 | bSPB_direct_7443 | `cCXxseSlh1Hm2WpQLAeS...` | `7466a158ea30c518` |
| 548 | 5 | bSPB_test_548 | `mPG21r8snOkQCu0XTqXv...` | `54800001` |

### 3.3 Italy — личный и роутерный

| Порт | Inbound ID | Назначение | pbk | sid |
|------|-----------|------------|-----|-----|
| 2083 | 1 | italy.red (личный) | `OBa4LZ0lL0j9RS52fgCw...` | `c30f9fec74087d32` |
| 2086 | 2 | italy.red_rout (роутеры) | `OBa4LZ0lL0j9RS52fgCw...` | `c30f9fec74087d32` |

### 3.4 Fin3 — личный inbound

| Порт | Inbound ID | Назначение | pbk | sid |
|------|-----------|------------|-----|-----|
| 2083 | 1 | Fin3 (личный) | `XJC_sc4MP6pFj2FNNGUu...` | `cc84f90d` |

---

## 4. ТОПОЛОГИЯ (схема)

```
СПб роутер
  ├─ main ──► bSPB:4191 ──[DNAT]──► Fin3:4191    🇫🇮
  ├─ main ──► bSPB:2090 ──[DNAT]──► Italy:2086   🇮🇹
  ├─ main ──► bSPB:8448 ──[DNAT]──► CZ2:8448     🇨🇿
  └─ YT  ──► bSPB:8853  (прямой)                 🇷🇺

Москва роутер
  ├─ main ──► bMSK:5223 ──[DNAT]──► Fin4:4191    🇫🇮
  ├─ main ──► bMSK:5228 ──[DNAT]──► Fin4:4192    🇫🇮
  ├─ main ──► bMSK:5323 ──[DNAT]──► PL5:4191     🇵🇱
  ├─ main ──► bMSK:5328 ──[DNAT]──► PL5:4192     🇵🇱
  └─ YT  ──► bMSK:8853  (прямой)                 🇷🇺
```

---

## 5. ПРАВИЛА СОЗДАНИЯ КЛЮЧА

1. **Определить город роутера:**
   - СПб → relay bSPB (5.35.84.151)
   - Москва → relay bMSK (159.194.198.172)

2. **Выбрать страну выхода:**
   - Финляндия → Fin3 (через bSPB) или Fin4 (через bMSK)
   - Польша → PL5 (через bMSK)
   - Италия → Italy (через bSPB)
   - Чехия → CZ2 (через bSPB)

3. **Создать клиента на целевом сервере:**
   - Fin3: `tools/add_fin3_client.sh <name> <uuid>` (inbound 3)
   - Fin4: через API панели (inbound 1 или 2)
   - PL5: через API панели (inbound 1 или 2)
   - Italy: через API панели (inbound 2)

4. **Перезагрузить xray** после добавления:
   - Через API: `POST /panel/api/server/restartXrayService`
   - Или `kill -9` PID xray на сервере

5. **Проверить ключ:** `python3 check_vless.py <vless_url>`

---

## 6. СКРИПТЫ ДЛЯ СОЗДАНИЯ КЛИЕНТОВ

| Скрипт | Сервер | Inbound | Порт |
|--------|--------|---------|------|
| `tools/add_fin3_client.sh <name> <uuid>` | Fin3 | 3 | 4191 |
| `add_bmsk_client.py <uuid> <email>` | bMSK | 9 | 465 |
| `add_pl5_client.py <email>` | PL5 | 1 | 4191 |
| `add_xui_client.py <uuid> <email>` | bSPB | 4 | 8853 |

> ⚠️ Нужен универсальный скрипт `create_vless_key.py`, который принимает сервер, inbound_id, имя роутера и город — и делает всё сам.
