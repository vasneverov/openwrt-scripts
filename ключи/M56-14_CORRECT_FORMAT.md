# M56-14 — Правильный формат ключей (без mode=gun)
## Создано: 2026-04-25

### Формат ключей (ВАЖНО!)
**БЕЗ `mode=gun` и `serviceName=`!**

### Main (Fin3)
```
vless://4ab48c6e-ec84-462f-992a-9337ba85c530@5.35.84.151:4191?type=grpc&security=reality&pbk=XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw&fp=chrome&sni=www.apple.com&sid=932e706c&spx=%2F#M56-14_Fin3
```

### YouTube (bSPB)
```
vless://7b854cfe-de52-430d-9b14-75ba67c8a016@5.35.84.151:8853?type=grpc&security=reality&pbk=me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM&fp=chrome&sni=www.apple.com&sid=ddcb53b3&spx=%2F#M56-14_bSPB
```

---

## Шаблон для M56-15..22

### Fin3 Main (через relay 5.35.84.151:4191)
- pbk: `XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw`
- sid: `932e706c`
- Формат: `vless://UUID@5.35.84.151:4191?type=grpc&security=reality&pbk=XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw&fp=chrome&sni=www.apple.com&sid=932e706c&spx=%2F`

### bSPB YT (direct 5.35.84.151:8853)
- pbk: `me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM`
- sid: `ddcb53b3`
- Формат: `vless://UUID@5.35.84.151:8853?type=grpc&security=reality&pbk=me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM&fp=chrome&sni=www.apple.com&sid=ddcb53b3&spx=%2F`

### ⚠️ НЕ использовать:
- ~~`mode=gun`~~
- ~~`serviceName=`~~
