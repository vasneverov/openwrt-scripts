#!/usr/bin/env python3
import json, base64, http.server, urllib.request, urllib.parse, ssl, http.cookiejar
import socketserver, concurrent.futures
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

CFG = json.load(open("/opt/subscription/config.json"))
PANELS = CFG["panels"]
RU_IP = CFG["ru_vps_ip"]
PORT = int(CFG["sub_port"])
SUPPORT_URL = CFG.get("support_url", "tg://resolve?domain=vasneverov")
SUPPORT_TEXT = CFG.get("support_text", "Vasya na svyazi")
DESCRIPTION = CFG.get("profile_description", "")
GROUP_NAME = CFG.get("group_name", "")
PORT_NAMES = CFG.get("port_names", {})

CERT = "/etc/letsencrypt/live/white.theredhat.su/fullchain.pem"
KEY  = "/etc/letsencrypt/live/white.theredhat.su/privkey.pem"
PANEL_TIMEOUT = 8

def tcp_ok(host, port, timeout=2):
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


BUNDLE1_STATE_FILE = "/opt/subscription/bundle1_active.json"
BUNDLE1_PANELS = {
    "https://89.125.196.83:5050/5050",
    "https://cz3.theredhat.su:5050/5050",
    "https://hpl4.theredhat.su:5050/5050",
    "https://151.243.198.86:5050/5050",
}

BUNDLE2_STATE_FILE = "/opt/subscription/bundle2_active.json"
BUNDLE2_PANELS = {
    "https://cz4.theredhat.su:5050/5050",
    "https://151.243.198.86:5050/5050",
    "https://144.31.66.115:5050/5050",
}

BUNDLE3_STATE_FILE = "/opt/subscription/bundle3_active.json"

BUNDLE1 = [
    {"url": "https://cz3.theredhat.su:5050/5050", "name": "CZ3 🇨🇿", "host": "85.137.164.179", "port": 2082},
    {"url": "https://hpl4.theredhat.su:5050/5050", "name": "PL4 🇵🇱", "host": "hpl4.theredhat.su", "port": 2083},
    {"url": "https://151.243.198.86:5050/5050", "name": "Italy 🇮🇹", "host": "151.243.198.86", "port": 2083},
    {"url": "https://89.125.196.83:5050/5050", "name": "Fin 🇫🇮", "host": "89.125.196.83", "port": 2083},
]

BUNDLE2 = [
    {"url": "https://cz4.theredhat.su:5050/5050", "name": "CZ4 🇨🇿", "host": "193.124.56.2", "port": 2088},
    {"url": "https://151.243.198.86:5050/5050", "name": "Italy 🇮🇹", "host": "151.243.198.86", "port": 2083},
    {"url": "https://144.31.66.115:5050/5050", "name": "Fin3 🇫🇮", "host": "144.31.66.115", "port": 2083},
]

BUNDLE3 = [
    {"url": "https://hostde.theredhat.su:5050/5050", "name": "DE 🇩🇪", "host": "192.91.186.242", "port": 5223},
    {"url": "https://144.31.66.115:5050/5050", "name": "Fin3 🇫🇮", "host": "144.31.66.115", "port": 2083},
    {"url": "https://45.155.54.25:5050/5050", "name": "FR 🇫🇷", "host": "45.155.54.25", "port": 2084},
]

BUNDLE3_PANELS = {
    "https://45.155.54.25:5050/5050",
    "https://hostde.theredhat.su:5050/5050",
    "https://144.31.66.115:5050/5050",
}



def check_bundle_with_fallback(bundle_list, default_panel, state, state_file=None):
    """Проверяет доступность серверов в бандле, возвращает первый рабочий"""
    active_panel = state.get("active_panel", default_panel)
    active_name = state.get("active_name", "")
    
    # Находим хост и порт для активного сервера
    for panel in bundle_list:
        if panel["url"] == active_panel:
            if tcp_ok(panel["host"], panel["port"], timeout=2):
                return state
            break
    
    # Если активный недоступен, ищем рабочий среди остальных
    for panel in bundle_list:
        if panel["url"] != active_panel:
            if tcp_ok(panel["host"], panel["port"], timeout=2):
                new_state = {"active_panel": panel["url"], "active_name": panel["name"], "fallback": True}
                if state_file:
                    try:
                        json.dump(new_state, open(state_file, "w"), ensure_ascii=False)
                    except Exception:
                        pass
                return new_state
    
    # Если ничего не работает, возвращаем default
    return {"active_panel": default_panel, "active_name": "Default", "fallback": True}

def load_bundle1_state():
    try:
        return json.load(open(BUNDLE1_STATE_FILE))
    except Exception:
        return {"active_panel": "https://cz3.theredhat.su:5050/5050", "active_name": "CZ3 🇨🇿"}


def load_bundle2_state():
    try:
        return json.load(open(BUNDLE2_STATE_FILE))
    except Exception:
        return {"active_panel": "https://cz4.theredhat.su:5050/5050", "active_name": "CZ4 🇨🇿"}


def load_bundle3_state():
    try:
        return json.load(open(BUNDLE3_STATE_FILE))
    except Exception:
        return {"active_panel": "https://hostde.theredhat.su:5050/5050", "active_name": "DE 🇩🇪"}


def derive_public_key(private_key_b64):
    try:
        padded = private_key_b64 + "=" * (-len(private_key_b64) % 4)
        priv_bytes = base64.urlsafe_b64decode(padded)
        pub_bytes = X25519PrivateKey.from_private_bytes(priv_bytes).public_key().public_bytes_raw()
        return base64.urlsafe_b64encode(pub_bytes).decode().rstrip("=")
    except Exception:
        return ""


cz_ssl = ssl.create_default_context()
cz_ssl.check_hostname = False
cz_ssl.verify_mode = ssl.CERT_NONE


def make_opener():
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar),
        urllib.request.HTTPSHandler(context=cz_ssl)
    )


def get_inbounds(panel):
    opener = make_opener()
    purl = panel["url"]
    data = json.dumps({"username": panel["user"], "password": panel["pass"]}).encode()
    opener.open(urllib.request.Request(purl + "/login",
        data=data, headers={"Content-Type": "application/json"}), timeout=PANEL_TIMEOUT)
    return json.loads(opener.open(
        urllib.request.Request(purl + "/panel/api/inbounds/list"),
        timeout=PANEL_TIMEOUT).read())["obj"]


def search_panel(panel, uuid):
    """Ищет UUID в одной панели. Возвращает список (port, pbk, sni, sid, network, path, remark, up, down, total, expiry_ms, email, panel_url)."""
    results = []
    panel_url = panel.get("url", "")
    port_override = panel.get("port_override", {})
    try:
        inbounds = get_inbounds(panel)
    except Exception:
        return results
    for ib in inbounds:
        stream = json.loads(ib["streamSettings"])
        reality = stream.get("realitySettings", {})
        network = stream.get("network", "tcp")
        nested = reality.get("settings", {})
        pub_key = nested.get("publicKey", "")
        if not pub_key:
            pub_key = derive_public_key(reality.get("privateKey", ""))
        sni = (reality.get("serverNames") or [""])[0]
        sid = (reality.get("shortIds") or [""])[0]
        path = stream.get("splithttpSettings", {}).get("path", "/")
        remark = ib.get("remark", "RU-relay")

        for cs in ib.get("clientStats", []):
            if cs["uuid"] == uuid:
                eff_port = port_override.get(str(ib["port"]), ib["port"])
                results.append((eff_port, pub_key, sni, sid, network, path, remark,
                                cs.get("up", 0), cs.get("down", 0),
                                cs.get("total", 0), cs.get("expiryTime", 0),
                                cs.get("email", ""), panel_url))
                break
        else:
            try:
                clients = json.loads(ib.get("settings", "{}")).get("clients", [])
                for c in clients:
                    if c.get("id") == uuid:
                        eff_port = port_override.get(str(ib["port"]), ib["port"])
                        results.append((eff_port, pub_key, sni, sid, network, path, remark,
                                        0, 0,
                                        c.get("totalGB", 0) * 1024**3, c.get("expiryTime", 0),
                                        c.get("email", ""), panel_url))
                        break
            except Exception:
                pass
    return results


def find_all_clients(uuid):
    """Параллельный поиск UUID по всем панелям."""
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(PANELS)) as executor:
        futures = {executor.submit(search_panel, panel, uuid): panel for panel in PANELS}
        for future in concurrent.futures.as_completed(futures):
            try:
                results.extend(future.result())
            except Exception:
                pass
    return results


def build_link(uuid, port, pbk, sni, sid, network, path, remark, email, name_override=None):
    if name_override:
        profile_name = name_override
    else:
        nick = email.split("_")[0] if email else ""
        custom_name = PORT_NAMES.get(str(port))
        if custom_name:
            profile_name = (nick + " " + custom_name) if nick else custom_name
        else:
            profile_name = (nick + "_" + remark) if nick else remark

    if network == "splithttp":
        params = ("type=xhttp&security=reality"
                  "&pbk=" + urllib.parse.quote(pbk) +
                  "&sid=" + sid + "&sni=" + sni + "&fp=chrome")
    elif network == "tcp":
        params = ("type=tcp&security=reality"
                  "&pbk=" + urllib.parse.quote(pbk) +
                  "&sid=" + sid + "&sni=" + sni + "&fp=chrome")
    else:
        params = ("type=grpc&security=reality&mode=gun&serviceName=&spx=%2F"
                  "&pbk=" + urllib.parse.quote(pbk) +
                  "&sid=" + sid + "&sni=" + sni + "&fp=chrome")

    full_name = (GROUP_NAME + " - " + profile_name) if GROUP_NAME else profile_name
    name = urllib.parse.quote(full_name)
    return "vless://" + uuid + "@" + RU_IP + ":" + str(port) + "?" + params + "#" + name


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def send_header(self, keyword, value):
        if not hasattr(self, "_headers_buffer"):
            self._headers_buffer = []
        self._headers_buffer.append((keyword + ": " + value + "\r\n").encode("utf-8"))

    def do_GET(self):
        if not self.path.startswith("/sub/"):
            self.send_response(404); self.end_headers(); return
        uuid = self.path[5:].strip("/")
        try:
            results = find_all_clients(uuid)
            if not results:
                self.send_response(404); self.end_headers()
                self.wfile.write(b"client not found"); return

            # Bundle1 rotation
            b1_state = check_bundle_with_fallback(BUNDLE1, "https://cz3.theredhat.su:5050/5050", load_bundle1_state(), BUNDLE1_STATE_FILE)
            active_panel = b1_state.get("active_panel", "")
            b1_entries = [r for r in results if r[12] in BUNDLE1_PANELS]
            non_b1_entries = [r for r in results if r[12] not in BUNDLE1_PANELS]

            is_bundle1 = len(b1_entries) >= 2
            if is_bundle1 and active_panel:
                active_b1 = [r for r in b1_entries if r[12] == active_panel]
                if not active_b1:
                    active_b1 = b1_entries[:1]
                results = active_b1 + non_b1_entries

            # Bundle2 rotation (CZ4 + Italy + Fin3)
            b2_state = check_bundle_with_fallback(BUNDLE2, "https://cz4.theredhat.su:5050/5050", load_bundle2_state(), BUNDLE2_STATE_FILE)
            active_panel2 = b2_state.get("active_panel", "")
            b2_entries = [r for r in results if r[12] in BUNDLE2_PANELS]

            is_bundle2 = len(b2_entries) >= 2
            if is_bundle2 and active_panel2:
                active_b2 = [r for r in b2_entries if r[12] == active_panel2]
                if not active_b2:
                    active_b2 = b2_entries[:1]
                results = [r for r in results if r[12] not in BUNDLE2_PANELS] + active_b2

            # Bundle3 rotation (DE + Fin3)
            b3_state = check_bundle_with_fallback(BUNDLE3, "https://hostde.theredhat.su:5050/5050", load_bundle3_state(), BUNDLE3_STATE_FILE)
            active_panel3 = b3_state.get("active_panel", "")
            b3_entries = [r for r in results if r[12] in BUNDLE3_PANELS]
            non_b3_b2_entries = [r for r in results if r[12] not in BUNDLE3_PANELS or r[12] in BUNDLE2_PANELS]

            is_bundle3 = len(b3_entries) >= 2
            if is_bundle3 and active_panel3:
                active_b3 = [r for r in b3_entries if r[12] == active_panel3]
                if not active_b3:
                    active_b3 = b3_entries[:1]
                results = [r for r in results if r[12] not in BUNDLE3_PANELS] + active_b3

            links = []
            for r in results:
                port, pbk, sni, sid, network, path, remark, up, down, total, expiry_ms, email, panel_url = r
                real_nick = email.split("_")[0] if email else ""
                if is_bundle1 and panel_url in BUNDLE1_PANELS:
                    flag = b1_state.get("active_name", "").split()[-1] if b1_state.get("active_name") else "🇪🇺"
                    name_override = (flag + " " + real_nick + " А1").strip()
                    links.append(build_link(uuid, port, pbk, sni, sid, network, path, remark, email, name_override))
                elif is_bundle2 and panel_url in BUNDLE2_PANELS:
                    flag = b2_state.get("active_name", "").split()[-1] if b2_state.get("active_name") else "🇪🇺"
                    name_override = (flag + " " + real_nick + " А2").strip()
                    links.append(build_link(uuid, port, pbk, sni, sid, network, path, remark, email, name_override))
                elif is_bundle3 and panel_url in BUNDLE3_PANELS:
                    flag = b3_state.get("active_name", "").split()[-1] if b3_state.get("active_name") else "🇪🇺"
                    name_override = (flag + " " + real_nick + " А3").strip()
                    links.append(build_link(uuid, port, pbk, sni, sid, network, path, remark, email, name_override))
                else:
                    links.append(build_link(uuid, port, pbk, sni, sid, network, path, remark, email))

            body = "\n".join(links)
            if DESCRIPTION:
                body = "# " + DESCRIPTION + "\n// " + DESCRIPTION + "\n" + body
            encoded = base64.b64encode(body.encode()).decode()

            r0 = results[0]
            up, down, total, expiry_ms = r0[7], r0[8], r0[9], r0[10]
            expire_sec = int(expiry_ms / 1000) if expiry_ms else 0
            userinfo = "upload=" + str(up) + "; download=" + str(down) + "; total=" + str(total) + "; expire=" + str(expire_sec)

            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Profile-Title", SUPPORT_TEXT)
            self.send_header("Profile-Web-Page-Url", SUPPORT_URL)
            self.send_header("Support-Url", SUPPORT_URL)
            self.send_header("Subscription-Userinfo", userinfo)
            if DESCRIPTION:
                self.send_header("Profile-Description", DESCRIPTION)
                self.send_header("profile-description", DESCRIPTION)
                self.send_header("X-Profile-Description", DESCRIPTION)
            self.end_headers()
            self.wfile.write(encoded.encode())
        except Exception as e:
            self.send_response(500); self.end_headers()
            self.wfile.write(str(e).encode())


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


if __name__ == "__main__":
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(CERT, KEY)
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
    print("Subscription server (HTTPS, threaded) on :" + str(PORT))
    srv.serve_forever()
