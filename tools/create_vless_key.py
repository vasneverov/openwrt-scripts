#!/usr/bin/env python3
"""
Универсальный скрипт для создания VLESS ключей на X-UI панелях.

Использование:
    python3 create_vless_key.py --router rom5office --panel fin3
    python3 create_vless_key.py --router myrouter --panel begetspb --inbound 4

Панели (predifined):
    - fin3: 144.31.66.115:5050, inbound 2 (WL_rout_fin3_4191)
    - begetspb: 5.35.84.151:5050, inbound 1 (main)
    - begetspb-yt: 5.35.84.151:5050, inbound 4 (YouTube direct)

Ручная настройка:
    --panel-ip, --panel-port, --inbound-id, --relay-ip, --relay-port, --pbk, --sid
"""

import argparse
import asyncio
import json
import ssl
import uuid
import sys

# Предустановленные конфигурации панелей
PANELS = {
    "fin3": {
        "ip": "144.31.66.115",
        "port": "5050",
        "inbound_id": 3,  # После восстановления 25.04.2026
        "label": "Fin3",
        "relay_ip": "5.35.84.151",
        "relay_port": "4191",
        "pbk": "XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw",
        "sid": "932e706c",
        "default_expiry_days": 365,  # Стандарт: 1 год
        "default_traffic_gb": 1000,  # Стандарт: 1 TB
    },
    "begetspb": {
        "ip": "5.35.84.151",
        "port": "5050",
        "inbound_id": 1,
        "label": "bSPB_direct",
        "relay_ip": "5.35.84.151",
        "relay_port": "6443",
        "pbk": "me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM",
        "sid": "ddcb53b3",
    },
    "begetspb-yt": {
        "ip": "5.35.84.151",
        "port": "5050",
        "inbound_id": 4,
        "label": "bSPB_direct_8853",
        "relay_ip": "5.35.84.151",
        "relay_port": "8853",
        "pbk": "me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM",
        "sid": "ddcb53b3",
    },
}

USERNAME = "ad"
PASSWORD = "56"
SNI = "www.apple.com"


def create_vless_key(uuid_str: str, relay_ip: str, relay_port: str, pbk: str, sid: str, label: str) -> str:
    """Generate VLESS key URL."""
    return (
        f"vless://{uuid_str}@{relay_ip}:{relay_port}?"
        f"type=grpc&security=reality&mode=gun&serviceName=&"
        f"pbk={pbk}&sid={sid}&sni={SNI}&fp=chrome&spx=%2F"
        f"#{label}"
    )


async def create_key(
    router_name: str,
    panel_config: dict,
    custom_email: str = None,
    dry_run: bool = False,
) -> str:
    """Create VLESS key on X-UI panel."""

    panel_ip = panel_config["ip"]
    panel_port = panel_config["port"]
    inbound_id = panel_config["inbound_id"]
    relay_ip = panel_config["relay_ip"]
    relay_port = panel_config["relay_port"]
    pbk = panel_config["pbk"]
    sid = panel_config["sid"]
    label_base = panel_config["label"]

    # Generate email
    if custom_email:
        email = custom_email
    else:
        email = f"{router_name}-{label_base.lower().replace('_', '-')}"

    print(f"🔐 Connecting to panel {panel_ip}:{panel_port}...")
    print(f"📧 Email will be: {email}")

    if dry_run:
        print("📝 DRY RUN: Would create client with above email")
        return None

    # Setup SSL context
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # Import aiohttp here to fail gracefully if not installed
    try:
        import aiohttp
    except ImportError:
        print("❌ Error: aiohttp not installed. Run: pip install aiohttp")
        sys.exit(1)

    base_url = f"https://{panel_ip}:{panel_port}/{panel_port}"

    async with aiohttp.ClientSession() as session:
        # Login
        login_url = f"{base_url}/login"
        resp = await session.post(login_url, json={"username": USERNAME, "password": PASSWORD}, ssl=ctx)

        if resp.status != 200:
            print(f"❌ Login failed: HTTP {resp.status}")
            return None

        set_cookie = resp.headers.get("Set-Cookie", "")
        if "3x-ui=" not in set_cookie:
            print("❌ Login failed: No 3x-ui cookie in response")
            return None

        cookie = set_cookie.split("3x-ui=")[1].split(";")[0]
        print(f"✅ Logged in")

        headers = {"Cookie": f"3x-ui={cookie}"}

        # Get existing clients
        print(f"\n📋 Checking inbound {inbound_id}...")
        get_url = f"{base_url}/panel/api/inbounds/get/{inbound_id}"
        resp = await session.get(get_url, headers=headers, ssl=ctx)

        if resp.status != 200:
            print(f"❌ Failed to get inbound: HTTP {resp.status}")
            return None

        data = await resp.json(content_type=None)
        inbound = data.get("obj", {})
        settings = json.loads(inbound.get("settings", "{}"))
        clients = settings.get("clients", [])

        print(f"Found {len(clients)} existing clients")

        # Check if email already exists
        for c in clients:
            if c.get("email") == email:
                print(f"⚠️ Client with email '{email}' already exists!")
                existing_uuid = c.get("id")
                print(f"   Existing UUID: {existing_uuid}")
                # Return existing key
                key = create_vless_key(existing_uuid, relay_ip, relay_port, pbk, sid, email)
                return key

        # Generate new UUID
        new_uuid = str(uuid.uuid4())
        print(f"\n🆕 Generated UUID: {new_uuid}")

        # Calculate limits from panel config (default: 365 days, 1 TB)
        import time
        expiry_days = panel_config.get("default_expiry_days", 365)
        traffic_gb = panel_config.get("default_traffic_gb", 1000)

        # Convert to milliseconds timestamp (expiryTime)
        expiry_ms = int((time.time() + expiry_days * 24 * 60 * 60) * 1000)
        # Convert GB to bytes (totalGB)
        traffic_bytes = int(traffic_gb * 1024 * 1024 * 1024)

        print(f"⏱️  Expiry: {expiry_days} days ({expiry_ms})")
        print(f"📊 Traffic limit: {traffic_gb} GB ({traffic_bytes} bytes)")

        # Create payload
        payload = {
            "id": inbound_id,
            "settings": json.dumps({
                "clients": [
                    {
                        "id": new_uuid,
                        "email": email,
                        "limitIp": 0,
                        "enable": True,
                        "expiryTime": expiry_ms,
                        "totalGB": traffic_bytes,
                        "tgId": "",
                        "subId": "",
                        "comment": "",
                    }
                ]
            }),
        }

        # Add client
        print(f"\n📝 Adding client...")
        add_url = f"{base_url}/panel/api/inbounds/addClient"
        resp = await session.post(add_url, json=payload, headers=headers, ssl=ctx)

        if resp.status != 200:
            text = await resp.text()
            print(f"❌ Failed to add client: HTTP {resp.status} - {text}")
            return None

        result = await resp.json(content_type=None)
        if result.get("success"):
            print(f"✅ Client added successfully!")
            key = create_vless_key(new_uuid, relay_ip, relay_port, pbk, sid, email)
            return key
        else:
            print(f"❌ API error: {result}")
            return None


def main():
    parser = argparse.ArgumentParser(
        description="Create VLESS key for router on X-UI panel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --router rom5office --panel fin3
  %(prog)s --router myrouter --panel begetspb --email custom-email
  %(prog)s --router test --panel-ip 1.2.3.4 --panel-port 5050 --inbound-id 2

Predefined panels: fin3, begetspb, begetspb-yt
        """
    )

    parser.add_argument("--router", "-r", required=True, help="Router name/identifier")
    parser.add_argument("--panel", "-p", choices=list(PANELS.keys()), help="Predefined panel config")
    parser.add_argument("--email", "-e", help="Custom email (default: router-panel_label)")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Show what would be done without creating")

    # Manual panel configuration
    parser.add_argument("--panel-ip", help="Panel IP address")
    parser.add_argument("--panel-port", default="5050", help="Panel port (default: 5050)")
    parser.add_argument("--inbound-id", type=int, help="Inbound ID")
    parser.add_argument("--relay-ip", help="Relay/connect IP for VLESS key")
    parser.add_argument("--relay-port", help="Relay port for VLESS key")
    parser.add_argument("--pbk", help="Public key for REALITY")
    parser.add_argument("--sid", help="Short ID for REALITY")

    args = parser.parse_args()

    # Build panel config
    if args.panel:
        panel_config = PANELS[args.panel].copy()
        print(f"📡 Using predefined panel: {args.panel}")
    elif args.panel_ip and args.inbound_id and args.relay_ip and args.relay_port and args.pbk and args.sid:
        panel_config = {
            "ip": args.panel_ip,
            "port": args.panel_port,
            "inbound_id": args.inbound_id,
            "relay_ip": args.relay_ip,
            "relay_port": args.relay_port,
            "pbk": args.pbk,
            "sid": args.sid,
            "label": "custom",
        }
        print(f"📡 Using manual panel configuration")
    else:
        parser.error("Either --panel or all manual options (--panel-ip, --inbound-id, etc.) must be provided")

    # Run async function
    key = asyncio.run(create_key(args.router, panel_config, args.email, args.dry_run))

    if key:
        print(f"\n🔑 VLESS KEY:")
        print(key)
        print(f"\n✅ Key ready for router: {args.router}")
        return 0
    else:
        print(f"\n❌ Failed to create key")
        return 1


if __name__ == "__main__":
    sys.exit(main())
