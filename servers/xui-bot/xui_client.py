import aiohttp
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class XUIClient:
    def __init__(self, url: str, username: str, password: str):
        self.url = url.rstrip("/")
        self.username = username
        self.password = password
        self._session: Optional[aiohttp.ClientSession] = None
        self._timeout = aiohttp.ClientTimeout(total=10)

    async def login(self) -> bool:
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            jar = aiohttp.CookieJar(unsafe=True)  # allow cookies from bare IP addresses
            self._session = aiohttp.ClientSession(timeout=self._timeout, connector=connector, cookie_jar=jar)
            resp = await self._session.post(
                f"{self.url}/login",
                json={"username": self.username, "password": self.password},
            )
            data = await resp.json()
            if data.get("success"):
                return True
            await self._session.close()
            self._session = None
            return False
        except Exception as e:
            logger.error(f"XUI login error: {e}")
            if self._session:
                await self._session.close()
                self._session = None
            return False

    async def logout(self):
        if self._session:
            try:
                await self._session.get(f"{self.url}/logout")
            except Exception:
                pass
            finally:
                await self._session.close()
                self._session = None

    async def test_connection(self) -> bool:
        try:
            if not await self.login():
                return False
            resp = await self._session.get(f"{self.url}/panel/api/inbounds/list")
            data = await resp.json()
            return data.get("success", False)
        except Exception as e:
            logger.error(f"XUI test_connection error: {e}")
            return False
        finally:
            await self.logout()

    async def get_inbound_info(self, inbound_id: int) -> Optional[dict]:
        try:
            resp = await self._session.get(
                f"{self.url}/panel/api/inbounds/get/{inbound_id}"
            )
            data = await resp.json()
            if data.get("success"):
                return data.get("obj")
            return None
        except Exception as e:
            logger.error(f"XUI get_inbound_info error: {e}")
            return None

    async def create_client(
        self,
        inbound_id: int,
        email: str,
        note: str,
        traffic_bytes: int,
        expiry_ms: int,
        client_uuid: str = None,
    ) -> Optional[dict]:
        import uuid, json
        client_uuid = client_uuid or str(uuid.uuid4())
        payload = {
            "id": inbound_id,
            "settings": json.dumps({
                "clients": [
                    {
                        "id": client_uuid,
                        "email": email,
                        "limitIp": 0,
                        "totalGB": traffic_bytes,
                        "expiryTime": expiry_ms,
                        "enable": True,
                        "tgId": "",
                        "subId": "",
                        "comment": note,
                    }
                ]
            }),
        }
        try:
            resp = await self._session.post(
                f"{self.url}/panel/api/inbounds/addClient",
                json=payload,
            )
            data = await resp.json()
            if data.get("success"):
                return {"uuid": client_uuid, "email": email}
            logger.error(f"XUI create_client failed: {data}")
            return None
        except Exception as e:
            logger.error(f"XUI create_client error: {e}")
            return None

    async def get_all_clients(self, inbound_id: int) -> list:
        try:
            inbound = await self.get_inbound_info(inbound_id)
            if not inbound:
                return []
            import json as _json
            settings = inbound.get("settings", "{}")
            if isinstance(settings, str):
                settings = _json.loads(settings)
            return settings.get("clients", [])
        except Exception as e:
            logger.error(f"XUI get_all_clients error: {e}")
            return []

    async def get_client_stats(self, email: str) -> Optional[dict]:
        try:
            resp = await self._session.get(
                f"{self.url}/panel/api/inbounds/getClientTraffics/{email}"
            )
            data = await resp.json()
            if data.get("success"):
                return data.get("obj")
            return None
        except Exception as e:
            logger.error(f"XUI get_client_stats error: {e}")
            return None

    async def get_server_status(self) -> Optional[dict]:
        try:
            resp = await self._session.get(f"{self.url}/server/status")
            data = await resp.json()
            if data.get("success"):
                return data.get("obj")
            return None
        except Exception as e:
            logger.error(f"XUI get_server_status error: {e}")
            return None

    async def get_inbounds_list(self) -> list:
        try:
            resp = await self._session.get(f"{self.url}/panel/api/inbounds/list")
            data = await resp.json()
            if data.get("success"):
                return data.get("obj") or []
            return []
        except Exception as e:
            logger.error(f"XUI get_inbounds_list error: {e}")
            return []

    async def clone_inbound(self, source_inbound: dict, new_remark: str, new_port: int) -> bool:
        import json as _json
        payload = {
            "up": 0,
            "down": 0,
            "total": 0,
            "remark": new_remark,
            "enable": True,
            "expiryTime": 0,
            "listen": source_inbound.get("listen", ""),
            "port": new_port,
            "protocol": source_inbound.get("protocol", "vless"),
            "settings": source_inbound.get("settings", "{}"),
            "streamSettings": source_inbound.get("streamSettings", "{}"),
            "sniffing": source_inbound.get("sniffing", "{}"),
            "allocate": source_inbound.get("allocate", "{}"),
        }
        # Убедимся что settings без клиентов (чистый инбаунд)
        try:
            settings = payload["settings"]
            if isinstance(settings, str):
                settings = _json.loads(settings)
            settings["clients"] = []
            payload["settings"] = _json.dumps(settings)
        except Exception:
            pass
        try:
            resp = await self._session.post(
                f"{self.url}/panel/api/inbounds/add",
                json=payload,
            )
            data = await resp.json()
            if data.get("success"):
                return data.get("obj", {}).get("id")
            return None
        except Exception as e:
            logger.error(f"XUI clone_inbound error: {e}")
            return None

    async def update_client_expiry(
        self,
        inbound_id: int,
        client_uuid: str,
        client: dict,
        new_expiry_ms: int,
    ) -> bool:
        import json
        updated = {**client, "expiryTime": new_expiry_ms}
        payload = {
            "id": inbound_id,
            "settings": json.dumps({"clients": [updated]}),
        }
        try:
            resp = await self._session.post(
                f"{self.url}/panel/api/inbounds/updateClient/{client_uuid}",
                json=payload,
            )
            data = await resp.json()
            return data.get("success", False)
        except Exception as e:
            logger.error(f"XUI update_client_expiry error: {e}")
            return False

    async def update_client_params(
        self,
        inbound_id: int,
        client_uuid: str,
        client: dict,
        new_expiry_ms: int | None = None,
        new_traffic_bytes: int | None = None,
    ) -> bool:
        import json
        updated = {**client}
        if new_expiry_ms is not None:
            updated["expiryTime"] = new_expiry_ms
        if new_traffic_bytes is not None:
            updated["totalGB"] = new_traffic_bytes
        payload = {
            "id": inbound_id,
            "settings": json.dumps({"clients": [updated]}),
        }
        try:
            resp = await self._session.post(
                f"{self.url}/panel/api/inbounds/updateClient/{client_uuid}",
                json=payload,
            )
            data = await resp.json()
            return data.get("success", False)
        except Exception as e:
            logger.error(f"XUI update_client_params error: {e}")
            return False

    async def get_online_clients(self) -> list:
        try:
            resp = await self._session.post(f"{self.url}/panel/api/inbounds/onlines")
            data = await resp.json()
            if data.get("success"):
                return data.get("obj") or []
            return []
        except Exception as e:
            logger.error(f"XUI get_online_clients error: {e}")
            return []

    async def delete_client(self, inbound_id: int, uuid: str) -> bool:
        try:
            resp = await self._session.post(
                f"{self.url}/panel/api/inbounds/{inbound_id}/delClient/{uuid}"
            )
            data = await resp.json()
            return data.get("success", False)
        except Exception as e:
            logger.error(f"XUI delete_client error: {e}")
            return False

    async def restart_xray(self) -> bool:
        try:
            resp = await self._session.post(f"{self.url}/server/restartXrayService")
            data = await resp.json()
            return data.get("success", False)
        except Exception as e:
            logger.error(f"XUI restart_xray error: {e}")
            return False
