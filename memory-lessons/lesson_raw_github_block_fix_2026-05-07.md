# Урок: Обход блокировки raw.githubusercontent.com для podkop

**Дата:** 2026-05-07
**Роутер:** tr56-09 (100.116.130.9)
**Провайдер:** Teleservis (Жуковский)

## Проблема

Podkop не мог обновить community subnet листы (meta.lst, telegram.lst и т.д.).
Логи podkop:
```
[warn] Attempt 1/3 to download http://127.0.0.1/Subnets/IPv4/telegram.lst failed
```

## Диагностика

1. **DNS работает** — `raw.githubusercontent.com` резолвится в 185.199.108-111.133
2. **Ping работает** — 20ms, 0% loss
3. **Traceroute работает** — 4 hops до Fastly CDN
4. **curl с `--resolve`** — 2 из 4 IP работают (108.133, 109.133), 2 не работают (110.133, 111.133)
5. **curl без `--resolve`** — HTTP 200 за 0.14с (попадает на рабочий IP)
6. **wget** — работает (HTTP 200)

**Вывод:** Провайдер блокирует часть IP-адресов Fastly CDN (185.199.110.133, 185.199.111.133). DNS возвращает все 4 IP, и wget/podkop может попасть на заблокированный.

## Решение

Добавить только рабочие IP в `/etc/hosts`:

```bash
echo "185.199.108.133 raw.githubusercontent.com" >> /etc/hosts
echo "185.199.109.133 raw.githubusercontent.com" >> /etc/hosts
```

После этого podkop обновляет листы успешно:
```
✅ Lists update completed successfully
```

## Скрипт для автоматизации

Создан `tools/fix-raw-github.sh` — универсальный скрипт для всех роутеров:

```bash
sh fix-raw-github.sh                    # проверить и починить
sh fix-raw-github.sh --check-only       # только проверить
```

Скрипт:
1. Проверяет DNS резолвинг
2. Проверяет /etc/hosts
3. Тестирует каждый из 4 IP через `curl --resolve`
4. Проверяет wget (как podkop)
5. Добавляет только рабочие IP в /etc/hosts
6. Запускает `podkop list_update`

Добавлен в cron на роутере:
```
0 3 * * * /bin/sh /root/fix-raw-github.sh
```

## Важные открытия

1. **`raw.githubusercontent.com` НЕ ЗАБЛОКИРОВАН полностью** — блокируются только некоторые IP Fastly CDN
2. **`github.com` работает** — .srs файлы качаются через `github.com/itdoginfo/allow-domains/releases/latest/download/`
3. **`mixed_proxy_enabled=1` ломает sing-box** — при `proxy_config_type 'url'` mixed proxy несовместим
4. **`download_lists_via_proxy=1` не работает** — tproxy не является HTTP-прокси

## Для раскатки на другие роутеры

1. Скопировать `tools/fix-raw-github.sh` на роутер
2. Добавить в cron: `0 3 * * * /bin/sh /root/fix-raw-github.sh`
3. Скрипт сам определит рабочие IP и обновит /etc/hosts
