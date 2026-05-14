## d-brain session context — 2026-05-12

### Server
- IP: 144.31.244.181
- User: root (sshpass 'Ujkjdf56')
- Bot: @vasyasbrain_bot (id=8522880860)
- Service: d-brain-bot (systemd, user=sbrain)
- Working dir: /home/sbrain/sbrain
- Stale copy: /root/sbrain/

### What was done this session
1. Diagnosed: bot returns flat report (Claude Code single-phase)
2. Found: server rebooted, all DeepSeek changes lost (uncommitted)
3. Restored:
   - `/home/sbrain/sbrain/scripts/deepseek_cli.py` — DeepSeek API wrapper
   - `/home/sbrain/sbrain/src/d_brain/services/processor.py` — DeepSeekProcessor (3-phase)
   - `/home/sbrain/sbrain/src/d_brain/bot/handlers/process.py` — 3-phase handler with progress
4. Synced to `/root/sbrain/` copies
5. Restarted bot — OK

### Key files
| File | Path |
|------|------|
| DeepSeek CLI | `/home/sbrain/sbrain/scripts/deepseek_cli.py` |
| Processor | `/home/sbrain/sbrain/src/d_brain/services/processor.py` |
| Bot handler | `/home/sbrain/sbrain/src/d_brain/bot/handlers/process.py` |
| .env | `/home/sbrain/sbrain/.env` (has DEEPSEEK_API_KEY) |
| systemd | `/etc/systemd/system/d-brain-bot.service` |

### 3-phase pipeline
1. CAPTURE — classify entries → JSON (DeepSeek, 180s timeout)
2. EXECUTE — process entries (save/archive/task) (DeepSeek, 240s timeout)
3. REFLECT — generate HTML report (DeepSeek, 240s timeout)

### Lesson
- Always commit DeepSeek changes to git
- Two paths: `/home/sbrain/sbrain/` (active) and `/root/sbrain/` (stale)
- DEEPSEEK_API_KEY survived reboot
