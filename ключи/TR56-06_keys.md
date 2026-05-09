# Ключи для TR56-06 (Москва, роутер 100.113.119.79)
Созданы: 06.05.2026

---

## 1. YT Direct — bMSK:993 (низкий порт, не блокируется провайдером)
**IP:** 159.194.198.172 | **Порт:** 993 | **SNI:** www.apple.com | **Transport:** gRPC+Reality

```
vless://c4549530-e8c2-4794-be9f-d7b034212e0e@159.194.198.172:993?type=grpc&security=reality&mode=gun&serviceName=&pbk=yxRiFPlbjjcodOzcbVuntFdpnzFnXLF1Nj9bma3H-lQ&sid=1d0385b7&sni=www.apple.com&fp=chrome&spx=%2F#TR56-06_bMSK_YT_993
```

**Статус:** ✅ Работает (TCP+TLS OK)

---

## 2. Main через relay — bMSK:5223 → Fin4:4191 (Польша 4)
**Relay IP:** 159.194.198.172 | **Relay Port:** 5223 | **Fin4:** 45.155.55.198:4191
**SNI:** www.apple.com | **Transport:** gRPC+Reality

```
vless://c4549530-e8c2-4794-be9f-d7b034212e0e@159.194.198.172:5223?type=grpc&security=reality&mode=gun&serviceName=&pbk=HfbTqAITJraOSM3J+yHpedrv+lKKe41IkU5m+4yPbHI&sid=4b929012&sni=www.apple.com&fp=chrome&spx=%2F#TR56-06_Fin4
```

**Статус:** ✅ Работает (TCP+TLS OK)

---

## Параметры для подкопа (podkop)

### YT профиль (Direct)
```
server=159.194.198.172
server_port=993
method=vless
password=c4549530-e8c2-4794-be9f-d7b034212e0e
plugin=v2ray-plugin
plugin_opts=grpc;mode=gun;host=www.apple.com;reality;pbk=yxRiFPlbjjcodOzcbVuntFdpnzFnXLF1Nj9bma3H-lQ;sid=1d0385b7;spx=/;fp=chrome
```

### Main профиль (через relay)
```
server=159.194.198.172
server_port=5223
method=vless
password=c4549530-e8c2-4794-be9f-d7b034212e0e
plugin=v2ray-plugin
plugin_opts=grpc;mode=gun;host=www.apple.com;reality;pbk=HfbTqAITJraOSM3J+yHpedrv+lKKe41IkU5m+4yPbHI;sid=4b929012;spx=/;fp=chrome
```
