"""The LG ThinQ Humidifier integration."""

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import LGThinQAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SELECT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up LG ThinQ Humidifier from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)
    refresh_token = entry.data["refresh_token"]
    client_id_mobile = entry.data.get("client_id_mobile")
    client_id_web = entry.data.get("client_id_web")

    def token_update_callback(new_refresh_token: str):
        """Update refresh token in config entry when it changes."""
        hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, "refresh_token": new_refresh_token},
        )
        _LOGGER.debug("Refresh token updated in config entry")

    api = LGThinQAPI(
        session,
        refresh_token,
        client_id_mobile,
        client_id_web,
        token_update_callback=token_update_callback,
    )

    try:
        await api.async_login()
    except Exception as e:
        _LOGGER.error("Failed to login: %s", e)
        return False

    async def async_update_data():
        """Fetch data from API."""
        try:
            # Fetch all devices and their status
            devices = await api.async_get_devices()
            data = {}
            for device in devices:
                device_id = device["deviceId"]
                # We might need to fetch status individually if get_devices doesn't return full snapshot
                # Based on API summary, get_devices (home detail) returns snapshot.
                # But let's be safe and use the snapshot from get_devices if available,
                # or call get_device_status if needed.
                # The API summary says "Get Home Detail & Devices" returns snapshot.
                # So async_get_devices() which calls that should have the data.
                # However, to be robust and follow the "polling" requirement for status,
                # we should probably ensure we have the latest status.
                # Since async_get_devices calls the home endpoint, it gets the latest status.
                data[device_id] = device
            return data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=5),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
