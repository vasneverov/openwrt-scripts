#!/usr/bin/env python3
"""
Сортирует серверы по возрасту (новые → старые) и добавляет цветную точку в кнопку.
Возраст определяется по самому раннему expiryTime среди всех клиентов сервера.
Запускать внутри Docker-контейнера.
"""
import asyncio, aiohttp, aiosqlite, json, ssl, time, os, re, datetime

DB_PATH = os.getenv("DB_PATH", "./data/bot.db")
NOW_MS = int(time.time() * 1000)

# Границы для цветов (относительно самого старого клиента)
GREEN_THRESHOLD  = NOW_MS + 4  * 30 * 24 * 3600 * 1000   # > 4 мес в будущем → новый
YELLOW_THRESHOLD = NOW_MS - 6  * 30 * 24 * 3600 * 1000   # от -6 мес до +4 мес → средний
# < -6 мес (истёк >6 мес назад) → старый

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE


def strip_dot(name: str) -> str:
    return re.sub(r'^[🟢🟡🔴]\s*', '', name).strip()


def dot_for(min_expiry_ms):
    if min_expiry_ms is None:
        return "🟢"  # нет клиентов → новый сервер
    if min_expiry_ms > GREEN_THRESHOLD:
        return "🟢"
    elif min_expiry_ms > YELLOW_THRESHOLD:
        return "🟡"
    else:
        return "🔴"


async def get_min_expiry(session, url):
    t = aiohttp.ClientTimeout(total=12)
    try:
        r = await session.post(f"{url}/login",
            json={"username": "ad", "password": "56"}, timeout=t, ssl=ssl_ctx)
        body = await r.json(content_type=None)
        if not body.get("success"):
            return None, "auth fail"

        r2 = await session.get(f"{url}/panel/api/inbounds/list", timeout=t, ssl=ssl_ctx)
        data = await r2.json(content_type=None)
        inbounds = data.get("obj") or []

        expiries = []
        for inb in inbounds:
            s = inb.get("settings", "{}")
            if isinstance(s, str):
                try: s = json.loads(s)
                except: continue
            for c in s.get("clients", []):
                exp = c.get("expiryTime", 0)
                if exp and exp > 0:
                    expiries.append(exp)

        return (min(expiries) if expiries else None), "ok"
    except asyncio.TimeoutError:
        return None, "timeout"
    except Exception as e:
        return None, str(e)[:40]


async def main():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM servers ORDER BY id") as c:
            servers = [dict(r) for r in await c.fetchall()]

    print(f"\nСерверов в БД: {len(servers)}")
    print("Опрашиваю панели...\n")

    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [get_min_expiry(session, s["url"]) for s in servers]
        expiries = await asyncio.gather(*tasks)

    # Собираем результаты
    data = []
    for server, (min_exp, status) in zip(servers, expiries):
        data.append((server, min_exp, status))

    # Сортируем: None (нет клиентов) → самый новый (inf)
    # Высокий min_expiry = клиенты истекают поздно = скорее всего новый сервер
    data.sort(key=lambda x: x[1] if x[1] is not None else float('inf'), reverse=True)

    # Показываем план
    print(f"  {'#':>2}  {'ДОТ'}  {'СЕРВЕР':<22}  {'MIN EXPIRY':<12}  СТАТУС")
    print("  " + "─" * 65)
    for i, (server, min_exp, status) in enumerate(data, 1):
        dot = dot_for(min_exp)
        clean = strip_dot(server["button_name"])
        if min_exp:
            dt = datetime.datetime.fromtimestamp(min_exp / 1000).strftime('%Y-%m-%d')
        else:
            dt = "—"
        print(f"  {i:>2}.  {dot}  {clean:<22}  {dt:<12}  {status}")

    print("\nОбновляю БД...")

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM servers")
        for server, min_exp, _ in data:
            dot = dot_for(min_exp)
            clean_name = strip_dot(server["button_name"])
            new_name = f"{dot} {clean_name}"
            await db.execute(
                """INSERT INTO servers
                   (key, button_name, country_flag, url, username, password, inbound_id, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (server["key"], new_name, server["country_flag"], server["url"],
                 server["username"], server["password"], server["inbound_id"], server["is_active"])
            )
        await db.commit()

    print("Готово. Серверы пересортированы и точки обновлены.\n")


if __name__ == "__main__":
    asyncio.run(main())
