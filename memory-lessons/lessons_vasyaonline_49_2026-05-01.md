# Уроки VasyaOnline_49 (49-й Пузиков) — 01.05.2026

## Факты сессии

- **Роутер:** VasyaOnline_49 (49-й Пузиков)
- **Tailscale IP:** 100.84.25.54
- **Учётка:** vas.neverov (01)
- **Город:** Москва (предполагается)
- **Модель:** TR30-25 (предполагается по rescue-скрипту)

## Проблема

Роутер был offline, периодически появлялся в Tailscale на короткое время (~5-15 секунд) после перезагрузки.
Требовалось поймать окно доступа и закинуть rescue-скрипт.

## Процесс восстановления

### 1. Мониторинг Tailscale
```bash
until tailscale ping -c 1 --timeout 3s 100.84.25.54 2>/dev/null | grep -q "pong"; do
    echo "Waiting for VasyaOnline_49..."
    sleep 3
done
```

### 2. Подключение SSH
- Пароль: 56756789 (стандартный)
- Проблема: wget не работал (сеть ещё не поднялась полностью)
- Решение: Локальная копия скрипта через stdin

### 3. Rescue-скрипт выполнен
Команда:
```bash
cat rescue_tr30-25.sh | sshpass -p "56756789" ssh root@100.84.25.54 "cat > /tmp/rescue.sh && sh /tmp/rescue.sh"
```

## Результат применения rescue-скрипта

| Параметр | Было | Стало |
|----------|------|-------|
| fw_mode | ? | none |
| init.d/tailscale | ? | disabled |
| exclude_ntp | ? | 1 |
| Calls профиль | ? | удалён |
| community_lists | ? | telegram meta первыми |
| sing-box | ? | RUNNING |
| Tailscale | offline | ONLINE |

## Вывод

✅ Роутер восстановлен
✅ Tailscale стабилен
✅ sing-box работает

---
Создано: 2026-05-01 21:04
