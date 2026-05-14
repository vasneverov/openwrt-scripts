# ЖЕЛЕЗНЫЕ ПРАВИЛА (IRON RULES)

## 0. Tailscale — НИЧЕГО НЕ ДЕЛАТЬ (АБСОЛЮТНЫЙ ЗАПРЕТ)
- **Никогда** не применять kill/killall к tailscale/tailscaled
- **Никогда** не выполнять `service tailscale stop/start/restart/enable/disable`
- **Никогда** не трогать tailscale up (даже --reset)
- **Никогда** не редактировать rc.local (удалять/менять tailscale строки)
- **Никогда** не перезагружать firewall (fw4) — это сносит nftables и Tailscale отваливается
- **Никогда** не применять nft flush — это убивает Tailscale
- **Единственное что можно:** uci commit tailscale (без reload)
- **Если Tailscale упал:** ждать watchdog (2 мин), не дёргать
- **Если точка красная/offline:** не паниковать, watchdog поднимет сам
- **SSH идёт через Tailscale → любой kill/restart = потеря SSH.** Никогда не делать удалённо.
- **Золотое правило: Tailscale работает — не лезь. Tailscale упал — watchdog поднимет, не лезь.**
- **Команда "ныряй" = сразу rescue_generic.sh (через SSH), потом диагностика, потом план лечения. Без самодеятельности. Никаких kill/killall. Никаких действий без одобрения. rescue_generic.sh — единственное что можно делать сразу.**

> **Перед чтением правил — прочитай `.clinerules/karpathy.md` (Karpathy принципы)**
> **Формат ответа — `.clinerules/caveman.md` (кратко, без воды)**
> 
> **Skill lookup:**
> - "прошиваем роутер" → `skills/flash_router_universal.md`
> - "диагностика роутера" → `skills/podkop_repair_guide.md`
> - "создать ключ" → `skills/create_clone_key.md`
> - "причесать роутеры" → `skills/groom-routers/SKILL.md`


## 1. Tailscale — НЕ ТРОГАТЬ (СВЯЩЕННАЯ КОРОВА)
- **Никогда** не перезапускать tailscaled (даже killall)
- **Никогда** не менять tailscale up (даже --reset)
- **Никогда** не перезагружать firewall (fw4) — это сносит nftables и Tailscale отваливается
- **Никогда** не применять nft flush — это убивает Tailscale
- Только сохранять конфиг (uci commit), без reload
- Если Tailscale упал — ждать watchdog (2 мин), не дёргать
- Если точка стала красной/offline — не паниковать, watchdog поднимет сам
- На разных версиях OpenWrt (24.10, 25.12) и podkop (0.4.x, 0.7.x) — Tailscale везде одинаково хрупкий
- **Золотое правило: Tailscale работает — не лезь. Tailscale упал — watchdog поднимет, не лезь.**
- **Критически важно: SSH идёт через Tailscale → убить tailscaled = потерять SSH.** Никогда не убивать tailscaled удалённо. Единственный случай когда можно — физический доступ (провод/консоль).
- **Если Tailscale серый, но LuCI доступен** — это значит podkop/прокси работает, а Tailscale coordination server недоступен. Не трогать — watchdog поднимет сам. LuCI доступен через локальную сеть (192.168.x.x), не через Tailscale.

## 2. Podkop — НЕ ПЕРЕЗАПУСКАТЬ вручную
- Только через watchdog или list_update
- Если нужно применить изменения — перезагрузить роутер целиком

## 3. rescue_generic.sh — применять ТОЛЬКО через SSH
- Не запускать на самом роутере
- Не модифицировать без необходимости
- После применения — проверить check-ip

## 4. Перед любыми изменениями — сохранять бэкап
- /etc/config/network
- /etc/config/podkop
- /etc/config/tailscale
- /etc/rc.local

## 5. Если роутер пропал — не паниковать
- Подождать 2 минуты (watchdog)
- Если не появился — просить перезагрузить питание
- После появления — сразу зайти и проверить

## 6. check-ip — обязательная проверка после любого ремонта
- Через прокси (как LAN-клиент) — должен быть польский IP
- Напрямую (с роутера) — должен быть российский IP
- Все 10 сайтов должны быть доступны

## 7. WAN ifname — проверять перед добавлением
- Если default route идёт через WiFi (phy*-sta0) — НЕ добавлять ifname=eth0
- Использовать реальный WAN-интерфейс

## 8. fw4-fix — НЕ использовать nft flush
- nft flush table inet PodkopTable сносит всё, включая правила Tailscale
- Вместо этого: просто перезапустить podkop (/etc/init.d/podkop restart)

## 9. Watchdog'ы — ставить всегда
- ts-watchdog.sh — каждые 2 минуты
- podkop-watchdog.sh — каждые 2 минуты
- route-watchdog.sh — каждые 2 минуты

## 10. rc.local — всегда с tailscaled
- tailscaled должен запускаться через rc.local, а не через init.d
- init.d/tailscale должен быть DISABLED

## 11. fw_mode — всегда none
- tailscale.settings.fw_mode = none (userspace-networking)
- Никогда не менять на nftables

## 12. exclude_ntp — всегда 1
- podkop.settings.exclude_ntp = 1

## 13. enable_output_network_interface — всегда 1
- podkop.settings.enable_output_network_interface = 1

## 14. Community lists — обновлять после rescue
- /usr/bin/podkop list_update
- Проверять, что списки загрузились

## 15. После rescue — не перезагружать роутер
- Все изменения применяются на лету
- Перезагрузка только если что-то пошло не так

## 16. При подключении к новому роутеру — сначала диагностика
- sing-box работает?
- Podkop статус?
- WAN ifname?
- Default route?
- Таблица podkop?
- Community lists?
- Tailscale статус?
- Интернет есть?

## 17. Если роутер не отвечает по Tailscale — не дёргать
- Подождать watchdog
- Попросить перезагрузить питание
- Не пытаться чинить вслепую

## 18. Все действия — логировать
- Каждый шаг — в вывод
- Каждый урок — в memory-lessons/
- Каждое изменение — коммитить в git

## 19. Пароль везде одинаковый — 56756789
- Не менять
- Не спрашивать
- Использовать sshpass

## 20. Если что-то пошло не так — откатывать изменения
- Вернуть network.wan.ifname
- Вернуть fw_mode
- Вернуть rc.local
- Перезагрузить роутер

## 21. Никогда не применять скрипты на роутер, к которому нет доступа
- Если роутер пропал — сначала восстановить связь
- Потом применять изменения

## 22. При работе с роутером через Tailscale — всегда проверять связь перед действиями
- ping -c 3 100.x.x.x
- ssh -o ConnectTimeout=5
- Если нет связи — не делать ничего

## 23. Если скрипт что-то ломает — исправлять скрипт, а не роутер
- Анализировать, что пошло не так
- Исправлять rescue_generic.sh
- Добавлять проверки
- Писать урок

## 24. Новая схема: ОДИН ключ, ОДИН профиль (с 09.05.2026)
- Создаём ТОЛЬКО один ключ main через relay
- YouTube-профиль НЕ создаём
- YouTube работает через community_list 'youtube' (3-й в списке после telegram, meta)
- 21 список в community_lists — все через один профиль

## 25. НИКОГДА не перезагружать firewall (fw4) на работающем Tailscale
- `/etc/init.d/firewall reload` на OpenWrt 25.12+ (fw4) **перезаписывает nftables**
- Это сбрасывает все правила, включая те, что Tailscale добавил для своей работы
- **Результат:** Tailscale теряет связь, роутер пропадает из сети
- **Решение:** Только сохранять конфиг (`uci commit firewall`), НЕ reload
- tailscale0 добавится в зону LAN при следующей перезагрузке роутера
- **Урок:** `memory-lessons/lesson_tr-boss-00_wifi_wan_fix_2026-05-08.md`

## 26. Ключи для нового роутера — брать с работающего
- При настройке нового роутера брать ключи с уже работающего роутера той же конфигурации
- Не изобретать новые ключи, не менять порты/pbk/sid/sni
- Менять только UUID (если нужен уникальный для каждого роутера)
- Или не менять ничего — если ключи общие
- Сначала поставить ключи как есть, убедиться что работает, потом думать об оптимизации

## 27. После каждого важного действия — ОБЯЗАТЕЛЬНЫЙ git push
- **Безоговорочно пушить всё на GitHub после:**
  - Прошивки роутера → commit + push
  - Диагностики → commit + push
  - Ремонта → commit + push
  - Сохранения урока → commit + push
  - Изменения любого файла в проекте → commit + push
- **Порядок действий:**
  1. `git add -A && git status` — проверить что меняется
  2. `git commit -m "описание"` — краткий список (что, какой роутер, результат)
  3. `git push origin main` — пуш в origin (основной репозиторий)
  4. Если push заблокирован — разобраться и исправить, не оставлять незапушенным
- **Отчёт пользователю:** после пуша показать:
  - ✅ Что запушено (какие коммиты)
  - ✅ Какие уроки сохранены и куда
  - ✅ Краткий результат работы
- **Цель:** компьютер ↔ GitHub ↔ телефон (Termius + DeepSeek) — всегда синхронизировано

## 28. Перед диагностикой роутера — сначала читать IRON_RULES.md
- **Особенно шаг 6** (tailscale0 в LAN зону через device, без reload)
- **Особенно шаг 25** (НИКОГДА не reload firewall)
- Проверить, что в fix-tailscale-openwrt.sh написано про tailscale0

## 29. Community lists — ЗАВИСИТ ОТ ВЕРСИИ PODKOP (порядок ВАЖЕН)
- **Порядок имеет значение:** telegram, meta, youtube — первые три
- **Для podkop v0.7.14 — 21 список (с roblox):**
  1. telegram, 2. meta, 3. youtube, 4. anime, 5. cloudflare, 6. cloudfront, 7. digitalocean, 8. discord, 9. google_ai, 10. google_play, 11. hdrezka, 12. hetzner, 13. hodca, 14. news, 15. ovh, 16. porn, 17. roblox, 18. tiktok, 19. twitter, 20. geoblock, 21. block
- **Для podkop v0.7.10 — 20 списков (БЕЗ roblox):**
  1. telegram, 2. meta, 3. youtube, 4. anime, 5. cloudflare, 6. cloudfront, 7. digitalocean, 8. discord, 9. google_ai, 10. google_play, 11. hdrezka, 12. hetzner, 13. hodca, 14. news, 15. ovh, 16. porn, 17. tiktok, 18. twitter, 19. geoblock, 20. block
- **Проверка:** `uci get podkop.main.community_lists | wc -w` — 21 для v0.7.14, 20 для v0.7.10
- **Как узнать версию:** `opkg list-installed | grep podkop`
- **Доступные сервисы в podkop v0.7.14:** russia_inside, russia_outside, ukraine_inside, geoblock, block, porn, news, anime, youtube, hdrezka, tiktok, google_ai, google_play, hodca, discord, meta, twitter, cloudflare, cloudfront, digitalocean, hetzner, ovh, telegram, roblox
- **Доступные сервисы в podkop v0.7.10:** те же, но БЕЗ roblox
- **НЕ добавлять:** google_meet, whatsapp — их нет в podkop v0.7.14
- **WhatsApp/Instagram/Facebook** входят в `meta` — отдельные списки для них не нужны
- **Причина:** podkop валидирует списки через `$COMMUNITY_SERVICES` в `/usr/lib/podkop/constants.sh`. Если списка там нет — podkop падает с `fatal: Invalid service`
- **При настройке нового роутера:** сначала проверить версию podkop, потом ставить списки
- **Урок:** `memory-lessons/lesson_z56-104_repair_2026-05-09.md`

## 30. Всегда загружать flash_router_universal.md при работе с роутером
- Даже если прошивка не нужна — загрузить скилл, взять шаги 7 (tailscale авторизация) и 8 (спасительные скрипты)
- Не действовать самому — скилл содержит проверенные шаги
- **Урок:** `memory-lessons/lesson_2026-05-11_tr-boss-00_consilium_errors.md`

## 31. direct_domains для tailscale — ставить ДО tailscale up
- Перед tailscale up обязательно добавить в podkop:
  - `tailscale.com`
  - `controlplane.tailscale.com`
  - `login.tailscale.com`
- Без этого tailscale не может достучаться до coordination server через прокси
- После добавления — `/etc/init.d/podkop restart`
- **Урок:** `memory-lessons/lesson_2026-05-11_tr-boss-00_consilium_errors.md`

## 32. После tailscale up — проверять fw_mode и init.d
- `uci get tailscale.settings.fw_mode` — должно быть `none`
- `/etc/init.d/tailscale enabled` — должно быть DISABLED
- Если не совпадает — исправить сразу
- **Урок:** `memory-lessons/lesson_2026-05-11_tr-boss-00_consilium_errors.md`

## 33. На OpenWrt не использовать nohup
- `nohup` отсутствует на OpenWrt
- Использовать: `(cmd &)` или `cmd &`
- **Урок:** `memory-lessons/lesson_2026-05-11_tr-boss-00_consilium_errors.md`

## 34. russia_inside — НИКОГДА не оставлять в списках podkop
- 21 список: telegram, meta, youtube, geoblock, block, porn, news, anime, discord, twitter, hdrezka, tiktok, cloudflare, google_ai, google_play, hodca, roblox, hetzner, ovh, digitalocean, cloudfront
- youtube — третий (после telegram и meta)
- russia_inside удалять сразу после любой установки/переустановки podkop
- Проверка: `uci show podkop.main.community_lists | grep russia` → если есть — удалять
- Команда: `uci del_list podkop.main.community_lists="russia_inside" && uci commit podkop`

## 35. SSH добавление клиента на DE2 — ТОЛЬКО через base64
- `python3 -c "..."` через SSH ломает экранирование — НЕ ИСПОЛЬЗОВАТЬ
- Правильно: написать Python-скрипт → base64 → cat | ssh 'base64 -d | python3'
- После добавления: `grep UUID /usr/local/x-ui/bin/config.json` — обязательно
- Потом: `systemctl restart xray-direct && systemctl is-active xray-direct`

## 36. Podkop секция `main` — ТИП ДОЛЖЕН БЫТЬ `section` (НЕ `main`, НЕ `extra`)
- **Правильный тип:** `config section 'main'` (в файле `/etc/config/podkop`)
- **Проверка:** `grep '^config' /etc/config/podkop | grep -v settings`
  - Должно быть: `config section 'main'`
  - НЕПРАВИЛЬНО: `config main 'main'` (тип `main`) — Podkop 0.7.x не найдёт proxy_string
  - НЕПРАВИЛЬНО: `config extra 'main'` (тип `extra`) — LuCI JS не отрендерит, Podkop не найдёт
- **Почему:** Podkop CLI (0.7.x) ищет `config_foreach _check_outbound_section "section"` — ТОЛЬКО тип `section`
  LuCI JS form использует `form.TypedSection, "section"` — ТОЛЬКО тип `section`
- **Как сломать:** Открыть Podkop в LuCI (Yandex/Chrome), увидеть пустоту, нажать "Add Section" → "Save". LuCI перезапишет тип на `extra`, proxy_string пропадёт.
- **Как чинить:** `uci delete podkop.main && uci set podkop.main="section"` — пересоздать с type, восстановить proxy_string и списки
- **Для старых podkop (0.4.x):** Тоже менять `main` → `section` (podkop 0.4.x итерациирует ВСЕ секции, тип не важен, но на будущее совместимо)
- **НИКОГДА не добавлять в конфиг** `config dashboard` или `config diagnostic` — LuCI JS их хардкодит через `cfgsections`, в конфиге они не нужны, только засоряют outbound checks
- **Проверка одним SSH:** `grep '^config' /etc/config/podkop | grep -v settings` — убедиться, что нет `extra` или `main`
