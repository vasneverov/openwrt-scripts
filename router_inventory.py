"""Router inventory updater for MEMORY.md.
Called from DeepSeekProcessor._phase_execute when router_events are detected.
"""
import logging
import re
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)


def apply_router_updates(vault_path: Path, events: list) -> int:
    """Apply router inventory updates to MEMORY.md.
    
    Args:
        vault_path: Path to vault directory
        events: List of router events from DeepSeek JSON
    
    Returns:
        Number of events applied
    """
    mpath = vault_path / "MEMORY.md"
    if not mpath.exists() or not events:
        return 0
    
    content = mpath.read_text(encoding="utf-8")
    changed = False
    today = date.today().strftime("%d.%m")
    applied = 0
    
    for evt in events:
        rid = evt.get("router_id", "").upper().strip()
        action = evt.get("action", "").lower().strip()
        client = evt.get("client", "").strip()
        amount = evt.get("amount", 0)
        bank = evt.get("bank", "").strip()
        location = evt.get("location", "").strip()
        status_note = evt.get("status_note", "").strip()
        
        if not rid or not action:
            continue
        
        # Already in inventory?
        if rid in content:
            if action == "podkluchen":
                # Update existing line: mark as connected
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if rid in line:
                        old_line = line
                        new_line = line.rstrip()
                        # Remove pending marker, add connected
                        new_line = new_line.replace("не подключён ⏳", f"✅ ПОДКЛЮЧЁН {today}")
                        new_line = new_line.replace("не подключен ⏳", f"✅ ПОДКЛЮЧЁН {today}")
                        if "ПОДКЛЮЧЁН" not in new_line and "подключён" not in new_line:
                            new_line += f" ✅ ПОДКЛЮЧЁН {today}"
                        if new_line != old_line:
                            content = content.replace(old_line, new_line)
                            changed = True
                            applied += 1
                            logger.info("ROUTER: %s connected %s", rid, today)
                        break
                continue
            elif action == "vozvrat":
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if rid in line:
                        old_line = line
                        new_line = f"⛔ ВОЗВРАТ {today}. Была: {old_line.lstrip('- *').strip()}"
                        content = content.replace(old_line, new_line)
                        changed = True
                        applied += 1
                        logger.info("ROUTER: %s returned %s", rid, today)
                        break
                continue
            else:
                # Router exists, skip adding duplicate
                logger.info("ROUTER: %s already tracked, skip %s", rid, action)
                continue
        
        # Build new inventory line
        if action == "proshil":
            line = f"- **{rid}** → ✅ прошит {today}"
            if location:
                line += f", точка «{location}»"
            if client:
                line += f", клиент: {client}"
        elif action == "prodan":
            line = f"- **{rid}** → "
            if client:
                line += f"{client} "
            line += f"✅ ПРОДАН {today}"
            if amount and bank:
                amt_str = f"{amount:,}".replace(",", " ")
                line += f", {amt_str} ₽ {bank}"
            if status_note:
                line += f", {status_note}"
            else:
                line += ", не подключён ⏳"
        elif action == "otpravlen":
            line = f"- **{rid}** → "
            if client:
                line += f"{client} "
            line += f"отправлен {today}"
            if amount and bank:
                amt_str = f"{amount:,}".replace(",", " ")
                line += f", {amt_str} ₽ {bank}"
            line += ", не подключён ⏳"
        elif action == "zakupka":
            line = f"- **Закупка {today}:** {client or 'роутеры'}"
            if amount:
                amt_str = f"{amount:,}".replace(",", " ")
                line += f" — −{amt_str} ₽ {bank}"
        else:
            continue
        
        # Find insertion point by series
        series = None
        for s in ["M78-", "M56-", "Z56-", "TR56-", "TR30-", "S78-"]:
            if rid.startswith(s):
                series = s
                break
        
        if series:
            last_pat = re.compile(r"^- \*?\*?" + re.escape(series) + r"[^ ]+.*$", re.MULTILINE)
            matches = list(last_pat.finditer(content))
            if matches:
                insert_pos = matches[-1].end()
                content = content[:insert_pos] + "\n" + line + content[insert_pos:]
                changed = True
                applied += 1
            else:
                sep = content.rfind("\n---\n")
                if sep > 0:
                    content = content[:sep] + "\n" + line + "\n" + content[sep:]
                    changed = True
                    applied += 1
        else:
            sep = content.rfind("\n---\n")
            if sep > 0:
                content = content[:sep] + "\n" + line + "\n" + content[sep:]
                changed = True
                applied += 1
        
        logger.info("ROUTER: added %s (%s) — %s", rid, action, client or "no client")
    
    if changed:
        mpath.write_text(content, encoding="utf-8")
        logger.info("MEMORY.md updated: %d router events applied", applied)
    
    return applied
