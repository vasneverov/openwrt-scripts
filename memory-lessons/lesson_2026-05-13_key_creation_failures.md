---
name: Уроки создания ключей VLESS — M56-24
metadata:
  type: feedback
critical: true
date: 2026-05-13
---

# Уроки создания ключей VLESS (M56-24)

## Ошибки и их причины

### Ошибка 1: Неправильный порт в ключе

**Что было:**
- Добавил UUID в inbound 1 на bSPB (port 6443)
- В ключе указал port 8880
- Результат: ключ не работает

**Почему:**
- xray на сервере слушает на порту inbound
- Если UUID в inbound 1 (port 6443), то и в ключе должен быть port 6443

**Правильно:**
```bash
# Проверить порт inbound перед созданием ключа
sqlite3 /etc/x-ui/x-ui.db "SELECT id,port FROM inbounds WHERE id=1"
# ID=1, Port=6443

# В ключе использовать тот же порт
vless://UUID@IP:6443?...
```

---

### Ошибка 2: xray не запущен на сервере

**Что было:**
- Добавил UUID в sqlite
- Не проверил что xray запущен
- check_vless показал READY, но ключ не работал

**Почему:**
- check_vless проверяет только TCP+TLS handshake
- Reality handshake проходит с ЛЮБЫМ UUID
- Но xray должен быть запущен чтобы принимать трафик

**Правильно:**
```bash
# После добавления UUID проверить xray
pgrep xray || echo "❌ xray NOT running"

# Если не запущен — запустить
/usr/local/x-ui/x-ui start &
```

---

### Ошибка 3: Неправильный pbk/sid для релея

**Что было:**
- Использовал pbk/sid из справочника
- Но не проверил актуальность

**Почему:**
- pbk/sid должны соответствовать inbound на сервере
- Если несоответствие — Reality handshake не пройдёт

**Правильно:**
```bash
# Проверить pbk/sid на сервере перед созданием ключа
sqlite3 /etc/x-ui/x-ui.db "SELECT stream_settings FROM inbounds WHERE id=X"
# Извлечь pbk и sid из stream_settings
```

---

## Железное правило создания ключей (новое)

```
1. Проверить inbound (id, port, pbk, sid) на сервере
2. Создать UUID
3. Добавить в sqlite конкретного inbound
4. Проверить что xray запущен (pgrep xray)
5. Проверить UUID в config.json (grep -c 'UUID')
6. check_vless.py → ● READY ✓✓✓
7. Вставить в роутер ТОЛЬКО после READY
```

---

## Проблемные серверы (2026-05-13)

| Сервер | Статус | Решение |
|--------|--------|---------|
| bSPB (5.35.84.151) | ❌ xray сломан | Использовать bMSK |
| bMSK (159.194.198.172) | ✅ Работает | Основной релей |
| DE2 (195.26.231.228) | ✅ Работает | Прямой или через bMSK:5423 |

---

## Рабочие схемы (актуальные)

| Relay | Порт | Конечный сервер | pbk | sid |
|-------|------|-----------------|-----|-----|
| bMSK | 587 | Fin4:4191 | XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw | 932e706c |
| bMSK | 8880 | CZ3 | oLZKxNFuYo1p0iK2YJ5MVQE8zqLgN2qqEik52dYZjjA | 8fee39e3 |
| bMSK | 2090 | Italy:2086 | OBa4LZ0lL0j9RS52fgCw68jWqkvr_yakmpsolbiqgVI | c30f9fec74087d32 |

---

## Почему ключ на CZ3 (inbound 22) не работал для M56-24

**bSPB inbound 22:**
- Port: 8880
- Remark: bMSK_CZ3_relay_8880
- Но xray на bSPB не запущен!

**Решение:**
- Использовать bMSK:8880 напрямую (CZ3 через bMSK)
- Или использовать bMSK:587 → Fin4

---

## Итог M56-24

| Параметр | Значение |
|----------|----------|
| Роутер | M56-24 |
| Ключ работает | ✅ Fin4 через bMSK:587 |
| UUID | 290DBBBF-834C-42CE-B11E-ECC16856A9FB |
| Проблемы с ключами | bSPB сломан, пришлось использовать bMSK |
| Роутер прошит | ✅ Верно |

---

**Why:** bSPB сломан (нет xray), использовал bMSK
**How to apply:** Всегда проверять xray перед созданием ключей
