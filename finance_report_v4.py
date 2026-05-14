"""Financial report generator v4 — fixed parser, matches Claude Code output format."""
import re
import logging
from datetime import date, datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def _num(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def _parse_amt(amt_raw: str) -> tuple[float, bool]:
    amt = amt_raw.replace(" ", "").replace("\u202f", "").replace("₽", "").replace(",", "")
    sign = "+" if "+" in amt else ("−" if "−" in amt else ("-" if "-" in amt else ""))
    amt = amt.replace("+", "").replace("−", "").replace("-", "")
    try:
        val = float(amt)
        if sign in ("−", "-"):
            val = -val
        return val, val > 0
    except (ValueError, TypeError):
        return 0.0, False


def _parse_daily_entries(fin_block: str) -> dict:
    """Parse all ### Сегодня sections. Returns {month_key: {name, router: {count, sum}, vpn: {count, sum}}}."""
    months = {}
    month_names = {"2026-03": "Март", "2026-04": "Апрель", "2026-05": "Май", "2026-06": "Июнь"}

    for section in re.finditer(
        r"### Сегодня \((.+?)\)\n(.*?)(?=\n### |\n<!-- END|\Z)", fin_block, re.DOTALL
    ):
        day_str = section.group(1)
        body = section.group(2)
        month_key = day_str[:7]
        
        if month_key not in months:
            months[month_key] = {
                "name": month_names.get(month_key, month_key),
                "router": {"count": 0, "sum": 0},
                "vpn": {"count": 0, "sum": 0},
            }
        mn = months[month_key]

        lines = body.replace("||", "|\n|").split("\n")
        for line in lines:
            if "|" not in line or "Время" in line or "---" in line:
                continue
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) < 3:
                continue
            cat = parts[1].lower() if len(parts) > 1 else ""
            amt_raw = parts[2] if len(parts) > 2 else ""
            if amt_raw in ("—", "", " ", "TBD"):
                continue

            val, is_income = _parse_amt(amt_raw)
            if not is_income:
                continue

            if "роутер" in cat:
                mn["router"]["count"] += 1
                mn["router"]["sum"] += int(val)
            if "vpn_phone" in cat or "vpn" in cat:
                mn["vpn"]["count"] += 1
                mn["vpn"]["sum"] += int(val)

    return months


def generate(vault_path: Path, day: date) -> str:
    memory_path = vault_path / "MEMORY.md"
    if not memory_path.exists():
        return f"📊 <b>Обработка за {day.strftime('%d.%m.%Y')}</b>"

    memory_text = memory_path.read_text(encoding="utf-8")
    fin_start = memory_text.find("## ФИНАНСЫ [LIVE]")
    fin_end = memory_text.find("<!-- END ФИНАНСЫ -->")
    fin_block = ""
    if fin_start >= 0 and fin_end >= 0:
        fin_block = memory_text[fin_start:fin_end + len("<!-- END ФИНАНСЫ -->")]

    lines = []
    day_str = day.isoformat()
    day_display = day.strftime("%d.%m.%Y")

    lines.append(f"📊 <b>Обработка за {day_display}</b>")
    lines.append("")

    # ── 1. TODAY ENTRIES (only today) ──
    today_pat = rf"### Сегодня \({day_str}\)\n(.*?)(?=\n### |\n<!-- END|\Z)"
    today_m = re.search(today_pat, fin_block, re.DOTALL)
    today_entries = []
    today_income = 0
    today_expense = 0

    if today_m:
        body = today_m.group(1).replace("||", "|\n|")
        for line in body.split("\n"):
            if "|" not in line or "Время" in line or "---" in line:
                continue
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) < 4:
                continue
            cat_raw = parts[1]
            amt_raw = parts[2]
            bank = parts[3]

            # Skip empty/metadata rows
            if cat_raw in ("—", "") or "—" in cat_raw[:3]:
                continue
            if amt_raw in ("—", "", "TBD"):
                continue

            val, is_income = _parse_amt(amt_raw)
            
            # Build display
            cat_clean = cat_raw.strip()
            display = f"• {cat_clean}: {amt_raw} ({bank})" if amt_raw and amt_raw != "—" else f"• {cat_clean}"
            today_entries.append(display)

            if is_income:
                today_income += int(val)
            elif val < 0:
                today_expense += int(abs(val))

    if today_entries:
        lines.append("📝 <b>ЗАПИСИ ДНЯ:</b>")
        for e in today_entries:
            lines.append(e)
        lines.append("")

    # ── 2. DAY TOTAL ──
    netto = today_income - today_expense
    lines.append(f"💰 <b>ИТОГО ЗА ДЕНЬ:</b>")
    lines.append(f"Доходы: +{_num(today_income)} ₽")
    lines.append(f"Расходы: −{_num(today_expense)} ₽")
    lines.append(f"Нетто: {_num(netto)} ₽")
    lines.append("")

    # ── 3. ANTON ──
    anton_today = []
    anton_all_total = 0
    for section in re.finditer(
        r"### Сегодня \((.+?)\)\n(.*?)(?=\n### |\n<!-- END|\Z)", fin_block, re.DOTALL
    ):
        sec_date = section.group(1)
        for line in section.group(2).split("\n"):
            if "Антон потратил" in line and "~~" not in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 3:
                    val, _ = _parse_amt(parts[2])
                    anton_all_total += int(val)
                    if sec_date == day_str:
                        anton_today.append((parts[0] if len(parts) > 0 else "?", int(val)))

    if anton_today or anton_all_total > 0:
        lim_m = re.search(r"лимит\s*(\d+)\s*к", memory_text)
        limit = int(lim_m.group(1)) * 1000 if lim_m else 55000
        remaining = limit - anton_all_total
        lines.append("👤 <b>АНТОН ПОТРАТИЛ:</b>")
        if anton_today:
            details = " + ".join(str(a[1]) for a in anton_today)
            lines.append(f"Сегодня: {_num(sum(a[1] for a in anton_today))} ₽ ({details})")
        lines.append(f"Итого: {_num(anton_all_total)} / {_num(limit)} ₽ (осталось {_num(remaining)} ₽)")
        lines.append("")

    # ── 4. WEIGHT ──
    weight_entries = []
    for section in re.finditer(
        r"### Сегодня \((.+?)\)\n(.*?)(?=\n### |\n<!-- END|\Z)", fin_block, re.DOTALL
    ):
        d = section.group(1)
        body = section.group(2)
        wm = re.search(r"весы\s*\|\s*(\d+\.\d+)\s*кг", body, re.IGNORECASE)
        if wm:
            weight_entries.append((d, float(wm.group(1))))

    if weight_entries:
        weight_entries.sort(key=lambda x: x[0], reverse=True)
        last_w = weight_entries[0][1]
        lines.append(f"⚖️ <b>ВЕС:</b> {last_w:.1f} кг ({weight_entries[0][0]})")
        if len(weight_entries) >= 2:
            prev_w = weight_entries[1][1]
            diff = last_w - prev_w
            if abs(diff) > 0.01:
                arrow = "⚠️" if diff > 0 else "✅"
                lines.append(f"Тренд: {prev_w:.1f} → {last_w:.1f} ({'+' if diff > 0 else ''}{diff:.1f} кг {arrow})")
        lines.append("")

    # ── 5. ROUTER SALES ──
    months = _parse_daily_entries(fin_block)
    
    router_data = []
    for mk in sorted(months.keys()):
        md = months[mk]
        if md["router"]["count"] > 0:
            router_data.append((md["name"], mk, md["router"]))

    if router_data:
        lines.append("🛜 <b>ПРОДАЖИ РОУТЕРОВ:</b>")
        tc, ts = 0, 0
        for name, mk, d in router_data:
            lines.append(f"{name}: {d['count']} шт. → ~{_num(d['sum'])} ₽")
            tc += d["count"]
            ts += d["sum"]
        lines.append(f"<b>Всего: {tc} шт. → ~{_num(ts)} ₽</b>")
        lines.append("")

    # ── 6. VPN ──
    vpn_data = []
    for mk in sorted(months.keys()):
        md = months[mk]
        if md["vpn"]["count"] > 0:
            vpn_data.append((md["name"], mk, md["vpn"]))

    if vpn_data:
        lines.append("📱 <b>VPN В ТЕЛЕФОН:</b>")
        tc, ts = 0, 0
        for name, mk, d in vpn_data:
            lines.append(f"{name}: ~{d['count']} уст. → ~{_num(d['sum'])} ₽")
            tc += d["count"]
            ts += d["sum"]
        lines.append(f"<b>Всего: ~{tc} уст. → ~{_num(ts)} ₽</b>")
        lines.append("")

    # ── 7. BALANCES ──
    bal_m = re.search(r"### Балансы карт.*?(?=\n### |\n<!-- END|\Z)", memory_text, re.DOTALL)
    if bal_m:
        lines.append(f"💳 <b>БАЛАНСЫ КАРТ (расч. {day.strftime('%d.%m')}):</b>")
        total_rub, total_usd = 0, 0
        for line in bal_m.group().split("\n"):
            if "|" not in line or "Карта" in line or "---" in line:
                continue
            pts = [p.strip() for p in line.split("|") if p.strip()]
            if len(pts) >= 2:
                val_m = re.search(r"\$\s*(\d+)|([\d\s]+)\s*(?:₽)", pts[1])
                if val_m:
                    try:
                        if val_m.group(1):
                            total_usd += int(val_m.group(1))
                            lines.append(f"{pts[0]}: ${val_m.group(1)}")
                        else:
                            val = int(val_m.group(2).replace(" ", ""))
                            total_rub += val
                            lines.append(f"{pts[0]}: ~{_num(val)} ₽")
                    except ValueError:
                        continue
        lines.append(f"<b>💼 ИТОГО: ~{_num(total_rub)} ₽</b>")
        if total_usd:
            lines[-1] = f"<b>💼 ИТОГО: ~{_num(total_rub)} ₽ + ${total_usd}</b>"
        lines.append("")

    # ── 8. DEBTORS ──
    debtors = []
    in_debt = False
    for line in memory_text.split("\n"):
        if re.search(r"Д[ОЕ]Л[ГИ]|ДЕБИТОР|Должник", line, re.IGNORECASE):
            in_debt = True
            continue
        if in_debt:
            if line.strip().startswith("|"):
                pts = [p.strip() for p in line.split("|") if p.strip()]
                if len(pts) >= 2 and pts[0] not in ("Имя", "—", "", "~~"):
                    if "~~" not in pts[0]:
                        name = pts[0]
                        summary = pts[1] if len(pts) > 1 else ""
                        status = pts[2] if len(pts) > 2 and pts[2] else ""
                        debtors.append((name, summary, status))
            elif line.strip().startswith("##") or (line.strip() == "" and len(debtors) > 0):
                if len(debtors) > 0:
                    break

    if debtors:
        lines.append("📋 <b>ДЕБИТОРКА:</b>")
        for d in debtors:
            name, summary, status = d
            parts = [f"• {name} — {summary}"]
            if status and "возвращён" not in status.lower():
                parts.append(status)
            lines.append(" ".join(parts))
        lines.append("")

    # ── 9. MEMORY UPDATES ──
    lines.append("🧠 <b>MEMORY.md обновлён:</b>")
    lines.append(f"• ФИНАНСЫ {day_display} → {len(today_entries)} записей")
    if router_data:
        for name, mk, d in router_data:
            lines.append(f"• Роутеры {name}: {d['count']} шт. / {_num(d['sum'])} ₽")
    if vpn_data:
        for name, mk, d in vpn_data:
            lines.append(f"• VPN {name}: ~{d['count']} уст. / {_num(d['sum'])} ₽")
    if debtors:
        for d in debtors:
            lines.append(f"• Должники → {d[0]}: {d[1]}")
    lines.append("")

    lines.append("---")
    lines.append(f"<i>Обработано {len(today_entries)} записей за ~{datetime.now().strftime('%M')} мин</i>")

    return "\n".join(lines)
