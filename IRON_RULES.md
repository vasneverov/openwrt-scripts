# ЖЕЛЕЗНЫЕ ПРАВИЛА (IRON RULES)

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

## 27. После каждого важного действия — автоматический git push в router-lab
- После прошивки роутера → commit + push
- После диагностики → commit + push
- После ремонта → commit + push
- После сохранения урока → commit + push
- После изменения любого файла в проекте → commit + push
- Коммит с кратким списком изменений (что сделано, какой роутер, результат)
- Пуш в remote `router-lab` (не origin!)
- Если push заблокирован — разобраться и исправить, не оставлять незапушенным
- **Цель:** компьютер ↔ GitHub (router-lab) ↔ телефон (Termius + DeepSeek) — всегда синхронизировано

## 28. Перед диагностикой роутера — сначала читать IRON_RULES.md
- **Особенно шаг 6** (tailscale0 в LAN зону через device, без reload)
- **Особенно шаг 25** (НИКОГДА не reload firewall)
- Проверить, что в fix-tailscale-openwrt.sh написано про tailscale0

## 29. 21 community_list — ЭТАЛОННЫЙ СПИСОК (порядок ВАЖЕН)
- **Порядок имеет значение:** telegram, meta, youtube — первые три
- **Полный список (21):**
  1. telegram
  2. meta
  3. youtube
  4. anime
  5. cloudflare
  6. cloudfront
  7. digitalocean
  8. discord
  9. google_ai
  10. google_play
  11. hdrezka
  12. hetzner
  13. hodca
  14. news
  15. ovh
  16. porn
  17. roblox
  18. tiktok
  19. twitter
  20. geoblock
  21. block
- **Проверка:** `uci get podkop.main.community_lists | wc -w` должно быть 21
- **Доступные сервисы в podkop v0.7.14:** russia_inside, russia_outside, ukraine_inside, geoblock, block, porn, news, anime, youtube, hdrezka, tiktok, google_ai, google_play, hodca, discord, meta, twitter, cloudflare, cloudfront, digitalocean, hetzner, ovh, telegram, roblox
- **НЕ добавлять:** google_meet, whatsapp — их нет в podkop v0.7.14
- **WhatsApp/Instagram/Facebook** входят в `meta` — отдельные списки для них не нужны
- **Причина:** podkop v0.7.14 валидирует списки через `$COMMUNITY_SERVICES` в `/usr/lib/podkop/constants.sh`. Если списка там нет — podkop падает с `fatal: Invalid service`
- **При настройке нового роутера:** скопировать этот список как есть, без изменений
- **Урок:** `memory-lessons/lesson_z56-104_repair_2026-05-09.md`
