# Урок: Обход блокировки raw.githubusercontent.com — Сочи

**Дата:** 2026-05-07
**Роутер:** tr56-08-nikita-doc-sochi (100.79.40.126)
**Провайдер:** Сочи (неизвестно, но те же симптомы)

## Проблема

Podkop не мог обновить часть community subnet листов (ovh.lst, digitalocean.lst, cloudfront.lst).

Логи podkop:
```
[warn] Attempt 1/3 to download https://raw.githubusercontent.com/.../ovh.lst failed
[warn] Attempt 1/3 to download https://raw.githubusercontent.com/.../digitalocean.lst failed
[warn] Attempt 1/3 to download https://raw.githubusercontent.com/.../cloudfront.lst failed
```

При этом `✅ Lists update completed successfully` — часть листов скачалась, часть нет.

## Диагностика

1. **DNS работает** — резолвит все 4 IP (185.199.108-111.133)
2. **Ping работает** — 80ms, 0% loss
3. **curl обычный** — HTTP 200 за 0.29с (попадает на рабочий IP)
4. **curl с `--resolve`** — 2 из 4 IP работают (108.133, 109.133), 2 не работают (110.133, 111.133)
5. **wget** — OK (потому что тоже может попасть на рабочий IP)
6. **/etc/hosts** — пусто (нет записей)

**Вывод:** Абсолютно та же проблема, что на tr56-09 (Жуковский). Провайдер блокирует 185.199.110.133 и 185.199.111.133.

## Решение

Применён `podkop-fix-lists.sh`:
1. Скопирован на роутер: `/root/podkop-fix-lists.sh`
2. Запущен: `sh /root/podkop-fix-lists.sh`
3. Добавлены 2 рабочих IP в `/etc/hosts`
4. Запущен `podkop list_update` — все 10 листов скачались успешно
5. Добавлен в cron: `0 3 * * * /bin/sh /root/podkop-fix-lists.sh --cron`

## Вывод

**Проблема массовая.** Два разных провайдера (Teleservis в Жуковском и неизвестный в Сочи) блокируют одни и те же IP Fastly CDN. Это значит, что `podkop-fix-lists.sh` нужно раскатать на **все** роутеры, где podkop не обновляет листы.

## Скрипт для раскатки

```bash
# На любом роутере с podkop:
wget -q -O /root/podkop-fix-lists.sh \
  "https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/tools/podkop-fix-lists.sh"
chmod +x /root/podkop-fix-lists.sh
sh /root/podkop-fix-lists.sh
echo "0 3 * * * /bin/sh /root/podkop-fix-lists.sh --cron" >> /etc/crontabs/root
```
