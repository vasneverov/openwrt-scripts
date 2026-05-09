
# Скилл: Установка и настройка podkop на OpenWrt 25.12 (apk)

> **Целевой роутер:** Cudy WR3000H v1 / TR3000 / M3000
> **OpenWrt:** 25.12.0 (apk, НЕ opkg!)
> **Архитектура:** aarch64_cortex-a53
> **Дата:** 06.05.2026

---

## 1. Проверка совместимости

```bash
# Проверить версию OpenWrt
cat /etc/openwrt_release | grep DISTRIB_RELEASE
# Должно быть: 25.12.0 — значит apk
# Если 24.x — нужен opkg и .ipk пакеты

