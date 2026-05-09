#!/usr/bin/env python3
"""Добавить клиента на PL5 (inbound 1, порт 4191)"""
import sqlite3, json, time, uuid, sys

uid = str(uuid.uuid4())
email = sys.argv[1] if len(sys.argv) > 1 else "gorbacheva228"

conn = sqlite3.connect("/etc/x-ui/x-ui.db")
row = conn.execute("SELECT settings FROM inbounds WHERE id=1").fetchone()
data = json.loads(row[0])

data["clients"].append({
    "id": uid,
    "email": email,
    "limitIp": 0,
    "totalGB": 1099511627776,
    "expiryTime": int((time.time() + 365*24*3600)*1000),
    "enable": True,
    "tgId": "",
    "subId": "",
    "comment": ""
})

conn.execute("UPDATE inbounds SET settings=? WHERE id=1", [json.dumps(data)])
conn.commit()

# Проверка
row2 = conn.execute("SELECT settings FROM inbounds WHERE id=1").fetchone()
data2 = json.loads(row2[0])
last = data2["clients"][-1]
print(f"UUID={last['id']}")
print(f"EMAIL={last['email']}")
print(f"ENABLE={last['enable']}")
print(f"TOTAL={len(data2['clients'])}")
