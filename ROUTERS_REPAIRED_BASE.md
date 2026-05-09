# База отремонтированных роутеров


> **Для AI-агентов:** При запросе на ремонт/диагностику — сначала проверить, есть ли роутер в этой базе.
> Если есть — прочитать соответствующий урок в `memory-lessons/` перед действиями.
> **Цель:** Никогда не возвращаться к уже отремонтированному роутеру.

---

## Сводная таблица (все роутеры за всю историю)

| # | Имя роутера | Tailscale IP | Модель | OpenWrt | Дата ремонта | Проблема | Решение | Статус |
|---|---|---|---|---|---|---|---|---|
| 1 | **M56-13** | 100.76.253.51 | Cudy M3000 v2 | — | 24.04.2026 | WAN не работал после прошивки | Перепрошит v2-yt8821 с force upgrade | ✅ |
| 2 | **S78-44** | 100.85.102.22 | Cudy WR3000S v1 | — | 26.04.2026 | Main красный, telegram 000 | Создан bSPB ключ, YT секция, community_lists, exclude_ntp | ✅ |
| 3 | **Vasin_BOSS** | 100.122.66.80 | — | — | 03.05.2026 | Main красный, UUID пропал | Новый UUID на PL5 через sqlite3 | ✅ |
| 4 | **S78-44 (повторно)** | 100.85.102.22 | Cudy WR3000S v1 | — | 04.05.2026 | Reality verification failed | Исправлен pbk для PL5 | ✅ |
| 5 | **TR56-06 (alex-jpn)** | 100.113.119.79 | — | — | 06.05.2026 | Tailscale не защищён, YT не работал | Iron Rules, новые ключи bMSK:993 + bMSK→Fin4 | ✅ |
| 6 | **S78-40** | 100.118.37.35 | — | — | 06.05.2026 | GitHub CDN блокировка, 7 красных плашек | mixed proxy, локальные .srs файлы | ✅ |
| 7 | **z56-117 (s-rogachev)** | 100.87.253.107 | Cudy WR3000H v1 | 25.12.0 | 06.05.2026 | Podkop сломан, sing-box-tiny | Полная переустановка podkop v0.7.14 | ✅ |
| 8 | **z56-119** | 100.116.242.113 | — | — | 06.05.2026 | Main красный, YT зелёный | Ключи скопированы с z56-117 | ✅ |
| 9 | **17-usievicha10-6** | — | Xiaomi AX3000T | 24.10.1 | 06.05.2026 | Установка podkop v0.7.14 | Через itdog install.sh | ✅ |
| 10 | **tr56-09** | 100.116.130.9 | — | — | 07.05.2026 | raw.githubusercontent.com блокировка | /etc/hosts для 2 рабочих IP | ✅ |
| 11 | **tr56-08 (nikita-doc-sochi)** | 100.79.40.126 | — | — | 07.05.2026 | raw.githubusercontent.com блокировка | podkop-fix-lists.sh | ✅ |
| 12 | **TR5608 (Сочи)** | 100.79.40.126 | — | — | 07.05.2026 | too many open files | Лимит 65536 в /etc/init.d/sing-box | ✅ |
| 13 | **z56-84** | — | — | — | 07.05.2026 | Настройка podkop с нуля | bMSK→Fin4 main + bMSK:465 YT | ✅ |
| 14 | **19-ternovsky (Сочи)** | 100.88.218.14 | Xiaomi AX3000T | 24.10.1 | 08.05.2026 | Podkop не работал, GitHub блокировка | Новый ключ CZ2, 21 список, fw4-fix | ✅ |
| 15 | **tr-boss-00** | 100.123.243.33 | — | — | 08.05.2026 | WiFi WAN, rescue сломал интернет | network.wan.ifname=phy1-sta0 | ✅ |
| 16 | **z56-08 (Сочи)** | 100.79.40.126 | — | 25.12.0 | 08.05.2026 | Podkop not running, Россия вместо Польши | Перезапуск podkop + fw4-fix update | ✅ |
| 17 | **z56-85** | 100.79.216.88 | — | — | 08.05.2026 | firewall reload сломал Tailscale | rescue_generic.sh исправлен, убран reload | ✅ |
| 18 | **z56-119 (повторно)** | 100.116.242.113 | — | — | 09.05.2026 | YT красный, Main зелёный | YT удалён, youtube в main, watchdog'ы | ✅ |
| 19 | **z56-104 (Anton116)** | 100.115.247.93 | — | 24.10.5 | 09.05.2026 | YT 000 (отдельный профиль) | YT удалён, youtube в main, exclude_ntp=1 | ✅ |
| 20 | **tr56-04 (doc-dom)** | 100.82.166.40 | Cudy TR3000 v1 | 25.12.0 | 09.05.2026 | YT 000 (отдельный профиль) | YT удалён, youtube в main, fw4-fix, лимит 65536 | ✅ |
| 21 | **007-ufa** | 100.99.195.91 | Cudy WR3000E v1 | 24.10.2 | 09.05.2026 | YT 000 (отдельный профиль) | YT удалён, youtube в main, fw4-fix, лимит 65536 | ✅ |
| 22 | **e-008-tvoy-oblik** | 100.83.104.61 | Cudy WR3000E v1 | 24.10.5 | 09.05.2026 | YT 000 (отдельный профиль) | YT удалён, youtube в main, fw4-fix, лимит 65536 | ✅ |
| 23 | **H-01** | 100.117.186.39 | Cudy WR3000H | 25.12.0 | 09.05.2026 | Tailscale бесконечный цикл авторизации | direct_domains для tailscale.com | ✅ |
| 24 | **TR30-15 (Костянкин)** | **100.91.60.113** | **Cudy TR3000 v1** | **24.10.0** | **09.05.2026** | **WhatsApp/Instagram/Facebook 000** | **21 community_list (добавлены geoblock, block)** | **✅** |
| 25 | **M78-03 (Вера Гришина)** | **100.100.82.6** | **—** | **24.10 (M78)** | **09.05.2026** | **Calls + YT профили, podkop not running** | **Calls/YT удалены, 20 lists (v0.7.10 без roblox), exclude_ntp, fw_mode** | **✅** |


---

## Подробно по каждому роутеру

### 1. M56-13 (24.04.2026)
- **IP:** 100.76.253.51
- **Проблема:** WAN не работал после прошивки — ошибочно прошили v1 вместо v2-yt8821
- **Решение:** Перепрошит v2-yt8821 с force upgrade
- **Урок:** `memory-lessons/lesson_m3000_v2_wan_fix_2026-04-24.md`
- **Правило:** Год серийника определяет прошивку (24→v1, 25→v2-yt8821)

### 2. S78-44 (26.04.2026)
- **IP:** 100.85.102.22
- **Учётка:** ne78va
- **Проблема:** Main красный, telegram 000
- **Решение:** Создан bSPB ключ, YT секция (uppercase), community_lists, exclude_ntp=1
- **Урок:** `memory-lessons/lesson_session_2026-04-26_bundle_failover_s78.md`

### 3. Vasin_BOSS (03.05.2026)
- **IP:** 100.122.66.80
- **Учётка:** vas.neverov
- **Проблема:** Main красный, UUID пропал из proxy_string
- **Решение:** Новый UUID `5e7d5930-3c59-4c33-8195-a212f1c2e181` на PL5 через sqlite3
- **Урок:** `memory-lessons/repair_vasin_boss_2026-05-03.md`

### 4. S78-44 (повторно, 04.05.2026)
- **IP:** 100.85.102.22
- **Проблема:** Reality verification failed
- **Решение:** Исправлен pbk для PL5: `RQN8c9kjYV_jlTCgeHIIidKgfQbEeg12Hd5_sfiBURs`, sid: `b5023350`
- **Урок:** `memory-lessons/lesson_2026-05-04_s78-44_pl5_pbk_fix.md`

### 5. TR56-06 (alex-jpn, 06.05.2026)
- **IP:** 100.113.119.79
- **Проблема:** Tailscale не защищён Iron Rules, YT не работал
- **Решение:** Iron Rules (fw_mode=none, init.d disabled, rc.local, watchdog), новые ключи bMSK:993 (YT) + bMSK→Fin4 (main)
- **Урок:** `memory-lessons/repair_tr56-06_2026-05-06.md`, `memory-lessons/lesson_tr56-06_podkop_repair_2026-05-06.md`

### 6. S78-40 (06.05.2026)
- **IP:** 100.118.37.35
- **Проблема:** GitHub CDN блокировка, 7 красных плашек в LuCI
- **Решение:** mixed proxy включён, 21 .srs файл скачан через туннель, конфиг переключен на file:// URL
- **Урок:** `memory-lessons/lesson_s78-40_github_block_success_2026-05-06.md`, `memory-lessons/lesson_podkop_github_cdn_blocked_2026-05-06.md`

### 7. z56-117 (s-rogachev, 06.05.2026)
- **IP:** 100.87.253.107
- **Модель:** Cudy WR3000H v1, OpenWrt 25.12.0
- **Проблема:** Podkop сломан, sing-box-tiny вместо полного, GitHub заблокирован
- **Решение:** Полная очистка, установка podkop v0.7.14 через .apk с компа, 20 списков + YT профиль
- **Урок:** `memory-lessons/lesson_z56-117_podkop_reinstall_crash_2026-05-06.md`

### 8. z56-119 (06.05.2026)
- **IP:** 100.116.242.113
- **Проблема:** Main красный, YT зелёный
- **Решение:** Ключи скопированы с z56-117 (wbr-03)
- **Урок:** `memory-lessons/lesson_z56-119_podkop_keys_2026-05-06.md`

### 9. 17-usievicha10-6 (06.05.2026)
- **Модель:** Xiaomi AX3000T, OpenWrt 24.10.1
- **Проблема:** Установка podkop v0.7.14
- **Решение:** Через itdog install.sh (wget + heredoc)
- **Урок:** `memory-lessons/lesson_itdog_install_2026-05-06.md`

### 10. tr56-09 (07.05.2026)
- **IP:** 100.116.130.9
- **Провайдер:** Teleservis (Жуковский)
- **Проблема:** raw.githubusercontent.com блокировка (2 из 4 IP)
- **Решение:** /etc/hosts для 185.199.108.133 и 185.199.109.133
- **Урок:** `memory-lessons/lesson_raw_github_block_fix_2026-05-07.md`

### 11. tr56-08 (nikita-doc-sochi, 07.05.2026)
- **IP:** 100.79.40.126
- **Проблема:** raw.githubusercontent.com блокировка
- **Решение:** podkop-fix-lists.sh + cron
- **Урок:** `memory-lessons/lesson_sochi_raw_github_fix_2026-05-07.md`

### 12. TR5608 (Сочи, 07.05.2026)
- **IP:** 100.79.40.126
- **Проблема:** too many open files (4096), YouTube/Instagram/Netflix не работают
- **Решение:** Лимит 65536 в /etc/init.d/sing-box
- **Урок:** `memory-lessons/lesson_s78-40_singbox_too_many_open_files_2026-05-07.md`

### 13. z56-84 (07.05.2026)
- **Проблема:** Настройка podkop с нуля
- **Решение:** bMSK→Fin4 main + bMSK:465 YT, 20 списков
- **Урок:** `memory-lessons/lesson_z56-84_podkop_setup_2026-05-07.md`

### 14. 19-ternovsky (Сочи, 08.05.2026)
- **IP:** 100.88.218.14
- **Модель:** Xiaomi AX3000T, OpenWrt 24.10.1
- **Проблема:** Podkop не работал, GitHub блокировка
- **Решение:** Новый ключ CZ2 (c8adcc65-87df-4a49-89fa-12127503e67b), 21 список, fw4-fix
- **Урок:** `memory-lessons/lesson_19-ternovsky_full_diag_and_key_2026-05-08.md`

### 15. tr-boss-00 (08.05.2026)
- **IP:** 100.123.243.33
- **Проблема:** WiFi WAN, rescue_generic.sh сломал интернет (добавил eth0)
- **Решение:** network.wan.ifname=phy1-sta0
- **Урок:** `memory-lessons/lesson_tr-boss-00_wifi_wan_fix_2026-05-08.md`

### 16. z56-08 (Сочи, 08.05.2026)
- **IP:** 100.79.40.126
- **OpenWrt:** 25.12.0
- **Проблема:** Podkop not running, Россия вместо Польши
- **Решение:** Перезапуск podkop + fw4-fix update
- **Урок:** `memory-lessons/lesson_z56-08_podkop_final_main_out_2026-05-08.md`

### 17. z56-85 (08.05.2026)
- **IP:** 100.79.216.88
- **Проблема:** firewall reload сломал Tailscale
- **Решение:** rescue_generic.sh исправлен — убран `/etc/init.d/firewall reload`
- **Урок:** `memory-lessons/lesson_z56-85_firewall_reload_tailscale_crash_2026-05-08.md`

### 18. z56-119 (повторно, 09.05.2026)
- **IP:** 100.116.242.113
- **Проблема:** YT красный, Main зелёный
- **Решение:** YT удалён, youtube в main (3-й после telegram, meta), watchdog'ы
- **Урок:** `memory-lessons/lesson_z56-119_repair_2026-05-09.md`

### 19. z56-104 (Anton116, 09.05.2026)
- **IP:** 100.115.247.93
- **OpenWrt:** 24.10.5
- **Проблема:** YT 000 (отдельный профиль)
- **Решение:** YT удалён, youtube в main, exclude_ntp=1, enable_output_network_interface=1, watchdog'ы
- **Урок:** `memory-lessons/lesson_z56-104_repair_2026-05-09.md`

### 20. tr56-04 (doc-dom, 09.05.2026)
- **IP:** 100.82.166.40
- **Модель:** Cudy TR3000 v1, OpenWrt 25.12.0
- **Провайдер:** Дом.ru (СПб), WAN IP 88.210.8.246
- **Учётка:** TS3 (56papezde@gmail.com)
- **Проблема:** YT 000 (отдельный профиль, bSPB:8853 не отвечал)
- **Решение:** YT удалён, youtube в main, fw4-fix, лимит 65536, /etc/hosts для GitHub, cron
- **Урок:** `memory-lessons/lesson_tr56-04_podkop_repair_2026-05-09.md`

### 21. 007-ufa (09.05.2026)
- **IP:** 100.99.195.91
- **Модель:** Cudy WR3000E v1, OpenWrt 24.10.2
- **Провайдер:** Уфа, WAN IP 100.96.134.179 (CGNAT)
- **Учётка:** 56papezde@gmail.com
- **Проблема:** YT 000 (отдельный профиль)
- **Решение:** YT удалён, youtube в main, fw4-fix, лимит 65536, /etc/hosts для GitHub, cron
- **Урок:** `memory-lessons/lesson_007-ufa_podkop_repair_2026-05-09.md`

### 22. e-008-tvoy-oblik (09.05.2026)
- **IP:** 100.83.104.61
- **Модель:** Cudy WR3000E v1, OpenWrt 24.10.5
- **Учётка:** 56papezde@gmail.com
- **Проблема:** YT 000 (отдельный профиль)
- **Решение:** YT удалён, youtube в main, fw4-fix, лимит 65536, /etc/hosts для GitHub, cron
- **Урок:** `memory-lessons/lesson_e-008-tvoy-oblik_repair_2026-05-09.md`

### 23. H-01 (09.05.2026)
- **IP:** 100.117.186.39
- **Модель:** Cudy WR3000H, OpenWrt 25.12.0
- **Проблема:** Tailscale бесконечный цикл авторизации (long-poll обрывался через прокси)
- **Решение:** direct_domains для tailscale.com, controlplane.tailscale.com, login.tailscale.com
- **Урок:** `memory-lessons/lesson_h01_tailscale_auth_loop_2026-05-09.md`

### 24. TR30-15 (Костянкин, 09.05.2026)
- **IP:** 100.91.60.113
- **Модель:** Cudy TR3000 v1, OpenWrt 24.10.0
- **Учётка:** ne78va@ (tr30-15-kostyankin)
- **Провайдер:** неизвестно, WAN IP 178.67.61.230
- **Проблема:** WhatsApp/Instagram/Facebook 000 (не хватало geoblock и block в community_lists)
- **Решение:** Добавлены geoblock и block → 21 community_list, podkop restart
- **Ключ:** M56-05_CZ2_rout_8448 (Чехия через CZ2 relay, 5.35.84.151:8448)
- **Результат:** ✅ 21 список, sing-box running, YouTube 301, Telegram 200, Cloudflare trace CZ
- **Урок:** информация в `ROUTERS_REPAIRED_BASE.md`

### 25. M78-03 (Вера Гришина, 09.05.2026)
- **IP:** 100.100.82.6
- **OpenWrt:** 24.10 (M78)
- **Версия podkop:** v0.7.10
- **Проблема:** Calls + YT профили, podkop not running
- **Решение:** Calls/YT удалены, 20 community lists (v0.7.10 без roblox), exclude_ntp=1, fw_mode=none
- **Ключ:** ApeCZ_rout_01-M78-03_cz (через cz.8bit.ca:8443)
- **Результат:** ✅ podkop running, Google 200, YouTube 200
- **Урок:** `memory-lessons/lesson_m78-03_repair_2026-05-09.md`


---

## Общие паттерны (из всех ремонтов)

### Паттерн #1: YT профиль отдельно → не работает
**Симптом:** YouTube 000, Main зелёный, YT красный/недоступен
**Решение:** Удалить YT профиль, добавить youtube в main (3-й после telegram, meta)
**Встречается:** tr56-04, 007-ufa, e-008, z56-119, z56-104, TR56-06 — **6 роутеров**

### Паттерн #2: Не хватает community_lists
**Симптом:** Сайты из meta (WhatsApp/Instagram/Facebook) не открываются
**Решение:** Проверить количество списков (должно быть 21), добавить недостающие
**Встречается:** TR30-15 (Костянкин)

### Паттерн #3: GitHub CDN / raw.githubusercontent.com блокировка
**Симптом:** Красные плашки "Cannot download", списки не обновляются
**Решение:** /etc/hosts для рабочих IP, mixed proxy, локальные .srs файлы
**Встречается:** S78-40, tr56-09, tr56-08, 19-ternovsky, z56-117 — **5 роутеров**

### Паттерн #4: fw4-fix не установлен
**Симптом:** forwarded трафик не маркируется, некоторые сайты не работают
**Решение:** Установить podkop-fw4-fix.sh
**Встречается:** tr56-04, 007-ufa, e-008, 19-ternovsky — **4 роутера**

### Паттерн #5: Лимит open files 4096
**Симптом:** sing-box падает при нагрузке, YouTube/Netflix не работают
**Решение:** procd_set_param limits "nofile=65536 65536" в /etc/init.d/sing-box
**Встречается:** tr56-04, 007-ufa, e-008, TR5608 — **4 роутера**

### Паттерн #6: Tailscale не защищён Iron Rules
**Симптом:** Tailscale падает при reload firewall, теряет авторизацию после ребута
**Решение:** fw_mode=none, init.d disabled, rc.local, watchdog
**Встречается:** TR56-06, z56-85, H-01 — **3 роутера**

---

## Справочная информация

### Все Tailscale IP отремонтированных роутеров
| IP | Имя | Дата ремонта |
|---|---|---|
| 100.76.253.51 | M56-13 | 24.04.2026 |
| 100.85.102.22 | S78-44 | 26.04.2026 / 04.05.2026 |
| 100.122.66.80 | Vasin_BOSS | 03.05.2026 |
| 100.113.119.79 | TR56-06 (alex-jpn) | 06.05.2026 |
| 100.118.37.35 | S78-40 | 06.05.2026 |
| 100.87.253.107 | z56-117 (s-rogachev) | 06.05.2026 |
| 100.116.242.113 | z56-119 | 06.05.2026 / 09.05.2026 |
| 100.116.130.9 | tr56-09 | 07.05.2026 |
| 100.79.40.126 | tr56-08 / TR5608 / z56-08 (Сочи) | 07-08.05.2026 |
| 100.88.218.14 | 19-ternovsky (Сочи) | 08.05.2026 |
| 100.123.243.33 | tr-boss-00 | 08.05.2026 |
| 100.79.216.88 | z56-85 | 08.05.2026 |
| 100.115.247.93 | z56-104 (Anton116) | 09.05.2026 |
| 100.82.166.40 | tr56-04 (doc-dom) | 09.05.2026 |
| 100.99.195.91 | 007-ufa | 09.05.2026 |
| 100.83.104.61 | e-008-tvoy-oblik | 09.05.2026 |
| 100.117.186.39 | H-01 | 09.05.2026 |
| **100.91.60.113** | **TR30-15 (Костянкин)** | **09.05.2026** |
| **100.100.82.6** | **M78-03 (Вера Гришина)** | **09.05.2026** |


### Пароль для всех роутеров
`56756789`

---

*Создано: 09.05.2026 | Обновлять после каждого нового ремонта*
