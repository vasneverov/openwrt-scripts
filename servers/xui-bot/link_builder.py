import json
import base64
from urllib.parse import urlencode, quote
import logging

logger = logging.getLogger(__name__)


def _get_host_from_url(url: str) -> str:
    """Extract host from panel URL, stripping protocol and port."""
    url = url.rstrip("/")
    if "://" in url:
        url = url.split("://", 1)[1]
    if ":" in url:
        url = url.rsplit(":", 1)[0]
    return url


def build_link(
    inbound_info: dict,
    client_uuid: str,
    client_password: str,
    profile_name: str,
    panel_url: str = "",
) -> str:
    try:
        protocol = inbound_info.get("protocol", "vless")
        port = inbound_info.get("port", 443)

        stream_settings = inbound_info.get("streamSettings", {})
        if isinstance(stream_settings, str):
            stream_settings = json.loads(stream_settings)

        network = stream_settings.get("network", "tcp")
        security = stream_settings.get("security", "none")

        # Determine host
        host = _get_host_from_url(panel_url) if panel_url else "127.0.0.1"
        reality_settings = stream_settings.get("realitySettings", {})
        ws_settings = stream_settings.get("wsSettings", {})
        grpc_settings = stream_settings.get("grpcSettings", {})

        if protocol == "vless":
            return _build_vless(
                client_uuid, host, port, network, security,
                reality_settings, ws_settings, grpc_settings, profile_name
            )
        elif protocol == "vmess":
            return _build_vmess(
                client_uuid, host, port, network, security,
                ws_settings, reality_settings, stream_settings, profile_name
            )
        elif protocol == "trojan":
            return _build_trojan(
                client_password, host, port, security,
                reality_settings, ws_settings, profile_name
            )
        else:
            logger.warning(f"Unsupported protocol: {protocol}")
            return ""
    except Exception as e:
        logger.error(f"build_link error: {e}")
        return ""


def _build_vless(
    uuid: str, host: str, port: int, network: str, security: str,
    reality_settings: dict, ws_settings: dict, grpc_settings: dict, profile_name: str
) -> str:
    params = {"type": network, "security": security}

    if security == "reality":
        s = reality_settings.get("settings", {})
        pub_key = reality_settings.get("publicKey") or s.get("publicKey", "")
        fingerprint = reality_settings.get("fingerprint") or s.get("fingerprint", "chrome")
        server_names = reality_settings.get("serverNames") or s.get("serverNames", [])
        short_ids = reality_settings.get("shortIds") or s.get("shortIds", [""])
        sni = server_names[0] if server_names else ""
        sid = short_ids[0] if short_ids else ""
        params.update({
            "pbk": pub_key,
            "fp": fingerprint,
            "sni": sni,
            "sid": sid,
            "spx": "/",
        })
        if network == "tcp":
            params["flow"] = "xtls-rprx-vision"
    elif security == "tls":
        params["sni"] = host

    if network == "ws":
        ws_path = ws_settings.get("path", "/")
        ws_host = ws_settings.get("headers", {}).get("Host", host)
        params["path"] = ws_path
        params["host"] = ws_host
    elif network == "grpc":
        service_name = grpc_settings.get("serviceName", "")
        multi_mode = grpc_settings.get("multiMode", False)
        params["serviceName"] = service_name
        params["mode"] = "multi" if multi_mode else "gun"

    query = urlencode(params)
    encoded_name = quote(profile_name)
    return f"vless://{uuid}@{host}:{port}?{query}#{encoded_name}"


def _build_vmess(
    uuid: str, host: str, port: int, network: str, security: str,
    ws_settings: dict, reality_settings: dict, stream_settings: dict, profile_name: str
) -> str:
    tls = "tls" if security in ("tls", "reality") else ""
    sni = host if tls else ""
    ws_path = ws_settings.get("path", "/") if network == "ws" else ""
    ws_host = ws_settings.get("headers", {}).get("Host", "") if network == "ws" else ""

    config = {
        "v": "2",
        "ps": profile_name,
        "add": host,
        "port": str(port),
        "id": uuid,
        "aid": "0",
        "scy": "auto",
        "net": network,
        "type": "none",
        "host": ws_host,
        "path": ws_path,
        "tls": tls,
        "sni": sni,
    }
    encoded = base64.b64encode(json.dumps(config).encode()).decode()
    return f"vmess://{encoded}"


def _build_trojan(
    password: str, host: str, port: int, security: str,
    reality_settings: dict, ws_settings: dict, profile_name: str
) -> str:
    params = {"security": security}

    if security == "reality":
        server_names = reality_settings.get("serverNames") or reality_settings.get("settings", {}).get("serverNames", [])
        sni = server_names[0] if server_names else host
        params["sni"] = sni
    elif security == "tls":
        params["sni"] = host

    query = urlencode(params)
    encoded_name = quote(profile_name)
    return f"trojan://{password}@{host}:{port}?{query}#{encoded_name}"
