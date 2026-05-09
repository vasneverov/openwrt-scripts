# АРХИТЕКТУРА ИНФРАСТРУКТУРЫ — Справочник для ремонта роутеров

> **Железное правило:** Читать этот файл ПЕРЕД созданием ключей.
> Здесь точное соответствие портов, pbk, sid для всех серверов.

---

## Схема работы VPN

```
Клиент → Роутер (podkop+sing-box) → bMSK (relay) → Target Server (Fin/PL/IT etc.)
                              ↓
                         YT (bMSK:8853 direct)
```

**bMSK** — единый relay для всех направлений.

---

## bMSK Relay (Москва) — 159.194.198.172

| bMSK Порт | Куда | Target IP | Target Порт | pbk | sid |
|-----------|------|-----------|-------------|-----|-----|
| **5223** | Fin4:4191 | 45.155.55.198 | 4191 | `HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI` | `4b929012` |
| **5228** | Fin4:4192 | 45.155.55.198 | 4192 | `HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI` | `ae2bfb99` |
| **5323** | PL5:4191 | 91.92.46.229 | 4191 | `b5023350fb2f11b06f96b913767262c1c177778d7eb99f6e3c5e5f8d8d8b083` | `b5023350` |
| **5328** | PL5:4192 | 91.92.46.229 | 4192 | `b5023350fb2f11b06f96b913767262c1c177778d7eb99f6e3c5e5f8d8d8b083` | `b5023350` |
| **8443** | PL6:5223 | 91.92.46.152 | 5223 | `VHyvy-r9QlEPTsi4mk-o7Fm_pHdknIEal4gjSIfEHDs` | `abcd1234` |
| **8880** | PL6:5228 | 91.92.46.152 | 5228 | `B13kRiGPLxYxU262OY53_DeuWJ3zn10wg1A_2O--qmQ` | `efab5678` |
| **8853** | bMSK direct | — | — | `g5eg_BKQJLVbPxryppyE0AGpQB_HKHPGkOJN9I6bSzI` | `1cbf0359` |

**bMSK SSH:** `Ujkjdf56#`

---

## Target Servers

### Fin4 (Финляндия) — 45.155.55.198
| Inbound | Порт | pbk | sid | SSH Пароль |
|---------|------|-----|-----|------------|
| 1 | 4191 | `HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI` | `4b929012` | `duqwgjXiT4FRrc` |
| 2 | 4192 | `HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI` | `ae2bfb99` | `duqwgjXiT4FRrc` |

### PL5 (Польша) — 91.92.46.229
| Inbound | Порт | pbk | sid | SSH Пароль |
|---------|------|-----|-----|------------|
| 1 | 4191 | `b5023350fb2f11b06f96b913767262c1c177778d7eb99f6e3c5e5f8d8d8b083` | `b5023350` | `6pI3gBvJtVxjea` |
| 2 | 4192 | `b5023350fb2f11b06f96b913767262c1c177778d7eb99f6e3c5e5f8d8d8b083` | `b5023350` | `6pI3gBvJtVxjea` |

### PL6 (Польша) — 91.92.46.152
| Inbound | Порт | pbk | sid | SSH Пароль |
|---------|------|-----|-----|------------|
| 1 | 5223 | `VHyvy-r9QlEPTsi4mk-o7Fm_pHdknIEal4gjSIfEHDs` | `abcd1234` | `AXD0tm4ru942ij` |
| 2 | 5228 | `B13kRiGPLxYxU262OY53_DeuWJ3zn10wg1A_2O--qmQ` | `efab5678` | `AXD0tm4ru942ij` |

---

## Региональные схемы

| Регион | Main | YT | Причина |
|--------|------|----|---------|
| **Москва** | Fin4 через bMSK:5223 | bMSK:8853 | Стандарт |
| **Питер** | PL6 через bMSK:8443 ИЛИ Fin4:5228 | bMSK:8853 | Провайдер блокирует 5223/5323 |
| **Провайдер блокирует** | PL6:8443 или bMSK:8880 | bMSK:8853 | Экстренные порты |

---

## Алгоритм выбора порта

1. **Проверить порт через check_vless.py**
2. Если refused → порт заблокирован, пробовать следующий
3. Для Питера сразу начинать с 8443/8880

---

## Формат ключей

### Main (через relay)
```
vless://UUID@159.194.198.172:PORT?type=grpc&security=reality&mode=gun&serviceName=&pbk=PBK&sid=SID&sni=www.apple.com&fp=chrome&spx=%2F#ROUTER-main-relay
```

### YT (bMSK direct)
```
vless://UUID@159.194.198.172:8853?type=grpc&security=reality&mode=gun&serviceName=&pbk=g5eg_BKQJLVbPxryppyE0AGpQB_HKHPGkOJN9I6bSzI&sid=1cbf0359&sni=www.apple.com&fp=chrome&spx=%2F#ROUTER-YT
```

---

*Обновлено: 2026-05-05*
