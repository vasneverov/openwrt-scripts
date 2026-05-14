# Lesson: DE2 pbk — check_vless READY но ключ красный

## Дата
2026-05-13

## Проблема
Для M56-24 создан ключ через bMSK:5423 → DE2:4191. Создатель взял pbk `NY0rf1MTb_iYL1tTS_XjKPYfEAtBLWSFPt-LjNtC_nI` — неверный. Правильный pbk: `iR2cEt9NRvsSsuXR1f5cBgWZSkEzkmQjK5PX9YMt2Qo`.

**Ключ с неверным pbk:** check_vless → TCP+TLS OK → ● READY ✓✓✓
**На роутере:** sing-box → connection refused, sing-box лог: reality handshake failed

## Почему check_vless показал READY

flow:
1. TCP → relay bMSK:5423 доступен ✅
2. TLS → relay отвечает ✅ (Reality handshake на relay, не на DE2)
3. pbk `NY0rf1MT...` НЕ в XUI_SERVERS → server checks SKIP
4. **Вывод:** `● READY (TCP+TLS OK, server checks skipped)` ← ложно-положительный

check_vless **не может** проверить Reality на relay — relay не xray, он просто проксирует трафик. Handshake идёт до relay, а pbk нужен на конечном сервере.

## Исправлено

### 1. check_vless.py
- Неизвестные pbk теперь выводятся **красным предупреждением**:
  `pbk неизвестен — server checks пропущены!`
  `Возможно pbk неверный. Сверь с RELAY_REFERENCE.json`

### 2. skills/create_vless_key/SKILL.md
- Добавлен раздел "⚠️ ВАЖНО: pbk должен быть правильным"
- Список серверов с одинаковым pbk на все порты (DE2, Fin4, PL5, Italy)
- Инструкция: pbk брать из RELAY_REFERENCE.json, не из панели

### 3. lesson_2026-05-13_de2_create_key_no_panel.md
- Исправлены pbk для 4191 и 4192 — теперь везде `iR2cEt9NRvsSsuXR1f5cBgWZSkEzkmQjK5PX9YMt2Qo`
- Добавлено ⚠️ КРИТИЧЕСКОЕ ПРАВИЛО про одинаковый pbk

## Вывод

**check_vless НЕ гарантирует что ключ рабочий.**
- TCP+TLS проходят через relay → relay отвечает → READY
- pbk валидируется только на конечном сервере
- Ошибка pbk = ключ красный на роутере, хотя check_vless зелёный
- **Всегда сверяй pbk с RELAY_REFERENCE.json**
- Для DE2 pbk ВСЕГДА `iR2cEt9NRvsSsuXR1f5cBgWZSkEzkmQjK5PX9YMt2Qo`
