# Уроки сессии 02.05.2026 — TR30-06 прошивка

## Результат
TR30-06 (Cudy TR3000 v1) — успешно прошит. Tailscale 100.110.171.124, n78rout.

## Ключи
- Main: `vless://5c92cf0e-86be-4990-a33e-c6fa5c3dbbfc@159.194.198.172:5223?type=grpc&security=reality&mode=gun&serviceName=&pbk=HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI&sid=4b929012&sni=www.apple.com&fp=chrome&spx=%2F#TR30-06-main`
- YT: `vless://20e00475-3a48-4bab-88b6-ce6fc0c31e38@159.194.198.172:8853?type=grpc&security=reality&mode=gun&serviceName=&pbk=g5eg_BKQJLVbPxryppyE0AGpQB_HKHPGkOJN9I6bSzI&sid=1cbf0359&sni=www.apple.com&fp=chrome&spx=%2F#TR30-06-YT`

## Уроки

### 1. TFTP recovery для Cudy TR3000 v1
- IP Мака: **192.168.1.88** (не 192.168.0.x!)
- IP роутера: 192.168.1.1
- Файл: `recovery.bin` — обязательно **initramfs** (~8.8M), не sysupgrade
- Vendor recovery firmware: ~25.8M с сайта cudy.com (тоже работает)
- tftpd64 папка: `~/Downloads/tftpd64/` = `\\Mac\Home\Downloads\tftpd64\` в Windows

### 2. Промежуточная прошивка Cudy (23.05-SNAPSHOT)
- Cudy TR3000 v1 после vendor recovery поднимается на OpenWrt **23.05-SNAPSHOT**
- Это промежуточная прошивка — с неё нормально заливать OpenWrt 25.12 через sysupgrade
- Openmode напрямую через sysupgrade с vendor firmware может не зайти

### 3. Шьём по воздуху
- Роутер без WAN кабеля получает интернет через WiFi клиент
- Алгоритм: сканировать сети → спросить пароль → настроить wwan sta интерфейс
- После прошивки убрать wwan: SSH оборвётся при network restart — это нормально
- Подключён по кабелю = не лезть в Tailscale, использовать 192.168.5.1

### 4. GitHub заблокирован с роутера
- gunanovo.github.io недоступен с роутера напрямую
- Решение: скачать APK на Мак → scp на роутер

### 5. Полный отчёт = таблица 4 колонки
- Когда пользователь говорит "полный отчёт" — стандартная ╔══╗ таблица 4 столбика

### 6. Если SSH обрывается при network restart
- Это нормально — команды уже выполнились до обрыва
- Не паниковать, не лезть в Tailscale если есть кабель
