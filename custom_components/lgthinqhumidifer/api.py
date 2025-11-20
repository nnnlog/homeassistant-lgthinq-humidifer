"""API Client for LG ThinQ Humidifier."""

import logging
import uuid
import aiohttp
from .const import (
    LGE_AUTH_BASE_URL,
    THINQ_API_BASE_URL,
    API_KEY,
    APP_TYPE,
    APP_LEVEL,
    APP_OS,
    SERVICE_CODE,
    COUNTRY_CODE,
    LANGUAGE_CODE,
    SERVICE_PHASE,
    ORIGIN_MOBILE,
    ORIGIN_WEB,
    LOGIN_TYPE,
    THINQ_APP_VER,
    USER_AGENT_MOBILE,
    USER_AGENT_WEB,
    DEVICE_TYPE_HUMIDIFIER,
)

_LOGGER = logging.getLogger(__name__)


class LGThinQAPI:
    """LG ThinQ API Client."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        refresh_token: str = None,
        client_id_mobile: str = None,
        client_id_web: str = None,
    ):
        """Initialize the API client."""
        self._session = session
        self._refresh_token = refresh_token
        self._client_id_mobile = client_id_mobile
        self._client_id_web = client_id_web
        self._access_token = None
        self._user_no = None

    @property
    def refresh_token(self):
        """Return the refresh token."""
        return self._refresh_token

    async def async_login(self, refresh_token: str = None):
        """Login using refresh token."""
        if refresh_token:
            self._refresh_token = refresh_token

        if not self._refresh_token:
            raise ValueError("Refresh token is required")

        if not self._client_id_mobile:
            raise ValueError("Client ID Mobile is required")

        url = f"{LGE_AUTH_BASE_URL}/realms/LGE-MP/protocol/openid-connect/token"
        headers = {
            "X-Api-Key": API_KEY,
            "X-Thinq-App-Ver": THINQ_APP_VER,
            "X-Thinq-App-Type": APP_TYPE,
            "X-Thinq-App-Level": APP_LEVEL,
            "X-Thinq-App-Os": APP_OS,
            "X-Service-Code": SERVICE_CODE,
            "X-Country-Code": COUNTRY_CODE,
            "X-Language-Code": LANGUAGE_CODE,
            "X-Service-Phase": SERVICE_PHASE,
            "X-Client-Id": self._client_id_mobile,
            "X-Message-Id": str(uuid.uuid4()),
            "X-Origin": ORIGIN_MOBILE,
            "X-Thinq-App-Logintype": LOGIN_TYPE,
            "Accept": "application/json",
            "Authorization": "Basic TEdFX1RIUV9BUFBfQU9TX1BSRF8wMDE6Q2MxSDVra2s2QU9LVzJnVHdJaHM4ejdMY1VORUpYbDI=",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": USER_AGENT_MOBILE,
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
            "scope": "SVC202",
        }

        async with self._session.post(url, headers=headers, data=data) as response:
            response.raise_for_status()
            result = await response.json()
            self._access_token = result["access_token"]
            self._refresh_token = result.get("refresh_token", self._refresh_token)

        # After login, get user info to get user_no
        await self._async_get_user_info()

        return self._access_token

    async def _async_get_user_info(self):
        """Get user info to retrieve user_no."""
        url = f"{LGE_AUTH_BASE_URL}/realms/LGE-MP/protocol/lge-openid-connect/userinfo"
        headers = {
            "Accept": "application/json",
            "X-Api-Key": API_KEY,
            "X-Thinq-App-Ver": THINQ_APP_VER,
            "X-Thinq-App-Type": APP_TYPE,
            "X-Thinq-App-Level": APP_LEVEL,
            "X-Thinq-App-Os": APP_OS,
            "X-Service-Code": SERVICE_CODE,
            "X-Country-Code": COUNTRY_CODE,
            "X-Language-Code": LANGUAGE_CODE,
            "X-Service-Phase": SERVICE_PHASE,
            "X-Client-Id": self._client_id_mobile,
            "X-Message-Id": str(uuid.uuid4()),
            "X-Origin": ORIGIN_MOBILE,
            "Authorization": f"Bearer {self._access_token}",
            "User-Agent": USER_AGENT_MOBILE,
        }

        async with self._session.get(url, headers=headers) as response:
            response.raise_for_status()
            result = await response.json()
            self._user_no = result.get("user_no")

    async def async_get_devices(self):
        """Get list of humidifier devices."""
        if not self._access_token:
            await self.async_login()

        # 1. Get Homes
        url = f"{THINQ_API_BASE_URL}/v1/service/homes"
        headers = self._get_common_headers()

        async with self._session.get(url, headers=headers) as response:
            response.raise_for_status()
            result = await response.json()
            homes = result.get("result", {}).get("item", [])

        devices = []
        # 2. Get Devices for each home
        for home in homes:
            home_id = home["homeId"]
            url = f"{THINQ_API_BASE_URL}/v1/service/homes/{home_id}"
            async with self._session.get(url, headers=headers) as response:
                response.raise_for_status()
                result = await response.json()
                home_devices = result.get("result", {}).get("devices", [])
                for device in home_devices:
                    if device.get("deviceType") == DEVICE_TYPE_HUMIDIFIER:
                        devices.append(device)
        return devices

    async def async_get_device_status(self, device_id: str):
        """Get device status snapshot."""
        if not self._access_token:
            await self.async_login()

        url = f"{THINQ_API_BASE_URL}/v1/service/devices/{device_id}"
        headers = self._get_common_headers(is_web=True)

        async with self._session.get(url, headers=headers) as response:
            response.raise_for_status()
            result = await response.json()
            return result.get("result", {})

    async def async_set_mode(self, device_id: str, mode: int):
        """Set operation mode."""
        if not self._access_token:
            await self.async_login()

        url = f"{THINQ_API_BASE_URL}/v1/service/devices/{device_id}/control-sync"
        headers = self._get_common_headers(is_web=True)
        headers["Content-Type"] = "application/json"

        data = {
            "ctrlKey": "basicCtrl",
            "command": "Set",
            "dataKey": "airState.opMode",
            "dataValue": mode,
            "dataSetList": None,
            "dataGetList": None,
        }

        async with self._session.post(url, headers=headers, json=data) as response:
            response.raise_for_status()
            return await response.json()

    def _get_common_headers(self, is_web=False):
        """Get common headers for API calls."""
        client_id = self._client_id_web if is_web else self._client_id_mobile
        if not client_id:
            # Fallback or error if client ID is missing, but it should be there
            raise ValueError("Client ID is missing")

        headers = {
            "X-Thinq-App-Ver": THINQ_APP_VER,
            "X-Thinq-App-Type": APP_TYPE,
            "X-Thinq-App-Level": APP_LEVEL,
            "X-Thinq-App-Os": APP_OS,
            "X-Service-Code": SERVICE_CODE,
            "X-Country-Code": COUNTRY_CODE,
            "X-Language-Code": LANGUAGE_CODE,
            "X-Service-Phase": SERVICE_PHASE,
            "X-Client-Id": client_id,
            "X-Message-Id": str(uuid.uuid4()),
            "X-Origin": ORIGIN_WEB if is_web else ORIGIN_MOBILE,
            "X-Thinq-App-Logintype": LOGIN_TYPE,
            "Authorization": f"Bearer {self._access_token}",
            "X-Api-Key": API_KEY,
            "Accept": "application/json",
            "User-Agent": USER_AGENT_WEB if is_web else USER_AGENT_MOBILE,
        }

        if self._user_no:
            headers["X-User-No"] = self._user_no

        return headers
