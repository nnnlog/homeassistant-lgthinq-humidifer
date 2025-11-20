"""Select entity for LG ThinQ Humidifier."""

import logging
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODE_TO_STR, STR_TO_MODE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LG ThinQ Humidifier select entity."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    entities = []
    for device_id, device in coordinator.data.items():
        entities.append(LGThinQHumidifierMode(coordinator, api, device))

    async_add_entities(entities)


class LGThinQHumidifierMode(CoordinatorEntity, SelectEntity):
    """Representation of a LG ThinQ Humidifier Mode Select."""

    def __init__(self, coordinator, api, device):
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device["deviceId"]
        self._attr_name = f"{device['alias']} Mode"
        self._attr_unique_id = f"{device['deviceId']}_mode"
        self._attr_options = list(MODE_TO_STR.values())

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        device_data = self.coordinator.data.get(self._device_id)
        if not device_data:
            return None

        op_mode = device_data.get("snapshot", {}).get("airState.opMode")
        return MODE_TO_STR.get(op_mode)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        mode = STR_TO_MODE.get(option)
        if mode is None:
            _LOGGER.error("Invalid mode selected: %s", option)
            return

        try:
            await self._api.async_set_mode(self._device_id, mode)
            # Optimistically update the state
            # In a real scenario, we might want to wait for the next poll or manually refresh
            # But for better UX, we can try to refresh immediately
            await self.coordinator.async_request_refresh()
        except Exception as e:
            _LOGGER.error("Failed to set mode: %s", e)
